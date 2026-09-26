"""Run the base Laya zero-shot domain evaluation and Top-10 feed experiment."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import warnings
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from laya.client import MODEL_ID
from laya.client import get_agent, predict_batch
from laya.decision import evaluate_creator, normalize_response, prediction_from_raw
from laya.questions import QUESTIONS
from laya.state_builder import build_state

EVALS = ROOT / "evals"
LABELS_PATH = EVALS / "label.json"
BASELINE_JSON = EVALS / "reports" / "retrieval_baseline_v0.json"
PREDICTIONS_JSON = EVALS / "laya_predictions_v0.json"
REPORT_JSON = EVALS / "reports" / "laya_baseline_v0.json"
REPORT_MD = EVALS / "reports" / "laya_baseline_v0.md"
GROUND_TRUTH_TO_DECISION = {"good": "KEEP", "maybe": "UNCERTAIN", "poor": "DROP"}
DECISION_TO_GROUND_TRUTH = {v: k for k, v in GROUND_TRUTH_TO_DECISION.items()}
GROUND_TRUTH_CLASSES = ("good", "maybe", "poor")
DECISIONS = ("KEEP", "UNCERTAIN", "DROP")
DIMENSIONS = (
    "niche_fit", "audience_fit", "geography_fit", "platform_fit",
    "budget_fit", "creator_size_fit", "campaign_fit",
)
BATCH_SIZE = 8


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_and_validate_inputs() -> tuple[list[dict], list[dict], list[dict], dict]:
    brands = read_json(ROOT / "data" / "brands.json")
    creators = read_json(ROOT / "data" / "creators.json")
    labels = read_json(LABELS_PATH)
    expected = {(b["brand_id"], c["creator_id"]) for b in brands for c in creators}
    label_map: dict[tuple[str, str], dict] = {}
    for row in labels:
        pair = (row["brand_id"], row["creator_id"])
        if pair in label_map:
            raise ValueError(f"Duplicate ground-truth pair: {pair}")
        label_map[pair] = row
    missing, extra = expected - label_map.keys(), label_map.keys() - expected
    if len(brands) != 10 or len(creators) != 40 or len(labels) != 400:
        raise ValueError(
            f"Expected 10 brands, 40 creators, and 400 labels; got "
            f"{len(brands)}, {len(creators)}, and {len(labels)}"
        )
    if missing or extra:
        raise ValueError(f"Ground-truth coverage mismatch: missing={len(missing)}, extra={len(extra)}")
    return brands, creators, labels, label_map


def training_ground_truth(label_row: dict) -> dict:
    """Project existing labels/reasoning into answer choices without inventing unknowns."""
    reason = label_row.get("reasoning", {})
    gt: dict[str, Any] = {}
    value_maps = {
        "niche_fit": {"strong": "strong", "partial": "partial", "weak": "none"},
        "audience_fit": {"strong": "strong", "partial": "partial", "weak": "none"},
        "geography_fit": {"strong": "strong", "partial": "partial", "weak": "none"},
        "platform_fit": {"strong": "strong", "partial": "partial", "weak": "none"},
        "budget_fit": {"fit": "strong", "mismatch": "none", "unknown": "partial", "uncertain": "partial"},
        "creator_size_fit": {"fit": "strong", "near": "partial", "outside": "none"},
        "campaign_fit": {"strong": "strong", "partial": "partial", "weak": "none"},
    }
    for source, mapping in value_maps.items():
        original_key = "creator_size_fit" if source == "creator_size_fit" else source
        value = reason.get(original_key)
        if value in mapping:
            gt[source] = mapping[value]
    final = GROUND_TRUTH_TO_DECISION.get(label_row.get("label"))
    if final:
        gt["final_decision"] = final
    return gt


def confusion_matrix(rows: list[dict]) -> dict[str, dict[str, int]]:
    matrix = {label: {decision: 0 for decision in (*DECISIONS, "NO_PREDICTION")} for label in GROUND_TRUTH_CLASSES}
    for row in rows:
        if row.get("success"):
            actual = row["ground_truth_label"]
            predicted = row["laya"]["final_decision"]["choice"]
            matrix[actual][predicted] += 1
        else:
            matrix[row["ground_truth_label"]]["NO_PREDICTION"] += 1
    return matrix


def class_metrics(rows: list[dict]) -> dict[str, dict[str, float | int]]:
    metrics = {}
    for decision, gt_label in DECISION_TO_GROUND_TRUTH.items():
        tp = sum(1 for r in rows if r.get("success") and r["ground_truth_label"] == gt_label and r["laya"]["final_decision"]["choice"] == decision)
        fp = sum(1 for r in rows if r.get("success") and r["ground_truth_label"] != gt_label and r["laya"]["final_decision"]["choice"] == decision)
        fn = sum(1 for r in rows if r["ground_truth_label"] == gt_label and (not r.get("success") or r["laya"]["final_decision"]["choice"] != decision))
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        metrics[decision] = {"support": tp + fn, "predicted": tp + fp, "precision": precision, "recall": recall, "f1": f1}
    return metrics


def error_dimension_analysis(rows: list[dict]) -> dict[str, list[dict]]:
    groups = {dimension: [] for dimension in DIMENSIONS}
    for row in rows:
        if not row.get("success"):
            continue
        gt = row["ground_truth_answers"]
        for dimension in DIMENSIONS:
            expected = gt.get(dimension)
            predicted = row["laya"].get(dimension, {}).get("choice")
            if expected is not None and predicted != expected and len(groups[dimension]) < 10:
                groups[dimension].append({
                    "brand_id": row["brand_id"],
                    "creator_id": row["creator_id"],
                    "expected": expected,
                    "predicted": predicted,
                    "confidence": row["laya"][dimension]["confidence"],
                })
    return groups


def calculate_metrics(rows: list[dict], brands: list[dict]) -> dict:
    success = [r for r in rows if r.get("success")]
    correct = [r for r in success if r["laya"]["final_decision"]["choice"] == GROUND_TRUTH_TO_DECISION[r["ground_truth_label"]]]
    # Failed pairs remain in the accuracy denominator as incorrect outcomes.
    accuracy = len(correct) / len(rows) if rows else 0.0
    good_rows = [r for r in rows if r["ground_truth_label"] == "good"]
    maybe_rows = [r for r in rows if r["ground_truth_label"] == "maybe"]
    poor_rows = [r for r in rows if r["ground_truth_label"] == "poor"]
    good_retention = sum(1 for r in good_rows if r.get("success") and r["laya"]["final_decision"]["choice"] == "KEEP") / len(good_rows) if good_rows else 0.0
    poor_rejection = sum(1 for r in poor_rows if r.get("success") and r["laya"]["final_decision"]["choice"] == "DROP") / len(poor_rows) if poor_rows else 0.0
    maybe_uncertainty = sum(1 for r in maybe_rows if r.get("success") and r["laya"]["final_decision"]["choice"] == "UNCERTAIN") / len(maybe_rows) if maybe_rows else 0.0
    hard_errors = {
        "good_to_DROP": sum(1 for r in good_rows if r.get("success") and r["laya"]["final_decision"]["choice"] == "DROP"),
        "poor_to_KEEP": sum(1 for r in poor_rows if r.get("success") and r["laya"]["final_decision"]["choice"] == "KEEP"),
    }
    confidence_correct = [r["laya"]["final_decision"]["confidence"] for r in correct]
    confidence_incorrect = [
        r["laya"]["final_decision"]["confidence"] for r in success
        if r["laya"]["final_decision"]["choice"] != GROUND_TRUTH_TO_DECISION[r["ground_truth_label"]]
    ]
    all_confidences = [r["laya"]["final_decision"]["confidence"] for r in success]
    bins = ((0.0, .5, "<0.50"), (.5, .7, "0.50-0.69"), (.7, .9, "0.70-0.89"), (.9, 1.000001, "0.90-1.00"))
    confidence_distribution = {}
    for low, high, name in bins:
        matches = [r for r in success if low <= r["laya"]["final_decision"]["confidence"] < high]
        confidence_distribution[name] = {
            "count": len(matches),
            "correct": sum(1 for r in matches if r["laya"]["final_decision"]["choice"] == GROUND_TRUTH_TO_DECISION[r["ground_truth_label"]]),
        }
    high_confidence_errors = [
        {"brand_id": r["brand_id"], "creator_id": r["creator_id"], "ground_truth": r["ground_truth_label"],
         "decision": r["laya"]["final_decision"]["choice"], "confidence": r["laya"]["final_decision"]["confidence"]}
        for r in success
        if r["laya"]["final_decision"]["confidence"] >= .8
        and r["laya"]["final_decision"]["choice"] != GROUND_TRUTH_TO_DECISION[r["ground_truth_label"]]
    ]
    per_brand = []
    for brand in brands:
        subset = [r for r in rows if r["brand_id"] == brand["brand_id"]]
        good = [r for r in subset if r["ground_truth_label"] == "good"]
        maybe = [r for r in subset if r["ground_truth_label"] == "maybe"]
        poor = [r for r in subset if r["ground_truth_label"] == "poor"]
        brand_correct = sum(1 for r in subset if r.get("success") and r["laya"]["final_decision"]["choice"] == GROUND_TRUTH_TO_DECISION[r["ground_truth_label"]])
        per_brand.append({
            "brand_id": brand["brand_id"], "brand_name": brand["brand_name"],
            "attempted": len(subset), "successful": sum(bool(r.get("success")) for r in subset),
            "accuracy": brand_correct / len(subset) if subset else 0.0,
            "good_retention": sum(1 for r in good if r.get("success") and r["laya"]["final_decision"]["choice"] == "KEEP") / len(good) if good else None,
            "poor_rejection": sum(1 for r in poor if r.get("success") and r["laya"]["final_decision"]["choice"] == "DROP") / len(poor) if poor else None,
            "maybe_uncertainty": sum(1 for r in maybe if r.get("success") and r["laya"]["final_decision"]["choice"] == "UNCERTAIN") / len(maybe) if maybe else None,
        })
    return {
        "accuracy": accuracy,
        "confusion_matrix": confusion_matrix(rows),
        "per_class": class_metrics(rows),
        "good_retention": good_retention,
        "poor_rejection": poor_rejection,
        "maybe_uncertainty": maybe_uncertainty,
        "hard_error_rate": {
            **hard_errors,
            "count": sum(hard_errors.values()),
            "denominator": len(rows),
            "rate": sum(hard_errors.values()) / len(rows) if rows else 0.0,
        },
        "confidence": {
            "average_correct": sum(confidence_correct) / len(confidence_correct) if confidence_correct else None,
            "average_incorrect": sum(confidence_incorrect) / len(confidence_incorrect) if confidence_incorrect else None,
            "distribution": confidence_distribution,
            "high_confidence_incorrect_count": len(high_confidence_errors),
            "high_confidence_incorrect_examples": high_confidence_errors[:30],
        },
        "dimension_errors": error_dimension_analysis(rows),
        "ambiguous_cases": [
            {"brand_id": r["brand_id"], "creator_id": r["creator_id"], "ground_truth": r["ground_truth_label"],
             "decision": r["laya"]["final_decision"]["choice"], "confidence": r["laya"]["final_decision"]["confidence"]}
            for r in success if r["ground_truth_label"] == "maybe"
            and r["laya"]["final_decision"]["choice"] != "UNCERTAIN"
        ][:30],
        "per_brand": per_brand,
    }


def run_domain_evaluation(brands: list[dict], creators: list[dict], label_map: dict) -> list[dict]:
    results_by_pair: dict[tuple[str, str], dict] = {}
    if PREDICTIONS_JSON.exists():
        for previous in read_json(PREDICTIONS_JSON):
            pair = (previous.get("brand_id"), previous.get("creator_id"))
            if pair in label_map:
                if previous.get("success"):
                    raw = previous.get("laya", {}).get("raw_response")
                    if raw:
                        previous["laya"] = {**normalize_response(raw), "raw_response": raw}
                results_by_pair[pair] = previous
    total = len(brands) * len(creators)
    jobs = [
        (brand, creator, label_map[(brand["brand_id"], creator["creator_id"])])
        for brand in brands for creator in creators
        if (brand["brand_id"], creator["creator_id"]) not in results_by_pair
    ]
    agent = get_agent()

    def base_entry(brand: dict, creator: dict, label_row: dict) -> dict:
        ground_truth = training_ground_truth(label_row)
        return {
            "brand_id": brand["brand_id"], "creator_id": creator["creator_id"],
            "ground_truth_label": label_row["label"],
            "ground_truth": ground_truth, "ground_truth_answers": ground_truth,
            "success": False,
        }

    for start in range(0, len(jobs), BATCH_SIZE):
        batch = jobs[start:start + BATCH_SIZE]
        states = [build_state(brand, creator) for brand, creator, _ in batch]
        try:
            raw_results = predict_batch(states, QUESTIONS, batch_size=BATCH_SIZE, agent=agent)
            if not isinstance(raw_results, list) or len(raw_results) != len(batch):
                raise ValueError(f"SDK returned {len(raw_results) if isinstance(raw_results, list) else 'non-list'} results for {len(batch)} states")
        except Exception as batch_exc:
            # Isolate a batch-level failure so every pair still gets a recorded result.
            print(f"Batch at pair {start + 1} failed ({batch_exc}); retrying its pairs individually.", flush=True)
            raw_results = [None] * len(batch)

        for index, ((brand, creator, label_row), state, raw) in enumerate(zip(batch, states, raw_results)):
            pair = (brand["brand_id"], creator["creator_id"])
            entry = base_entry(brand, creator, label_row)
            try:
                if raw is None:
                    entry.update(evaluate_creator(brand, creator, agent=agent))
                else:
                    entry.update(prediction_from_raw(brand, creator, raw, state=state, questions=QUESTIONS))
                entry["success"] = True
            except Exception as exc:
                # Retry malformed per-state batch outputs once through the SDK's single-state path.
                if raw is not None:
                    try:
                        entry.update(evaluate_creator(brand, creator, agent=agent))
                        entry["success"] = True
                    except Exception as retry_exc:
                        exc = retry_exc
                if not entry["success"]:
                    entry["state"] = state
                    entry["questions"] = QUESTIONS
                    entry["model"] = MODEL_ID
                    entry["error"] = f"{type(exc).__name__}: {exc}"
                    if raw is not None:
                        entry["raw_response"] = raw
                    print(f"  FAILED {brand['brand_id']}/{creator['creator_id']}: {entry['error']}", flush=True)
            results_by_pair[pair] = entry

        ordered = [results_by_pair[(b["brand_id"], c["creator_id"])]
                   for b in brands for c in creators
                   if (b["brand_id"], c["creator_id"]) in results_by_pair]
        write_json_atomic(PREDICTIONS_JSON, ordered)
        print(f"Evaluated {len(results_by_pair)}/{total} pairs", flush=True)
    return [results_by_pair[(b["brand_id"], c["creator_id"])] for b in brands for c in creators]


def validate_predictions(predictions: list[dict], brands: list[dict], creators: list[dict]) -> None:
    expected = {(b["brand_id"], c["creator_id"]) for b in brands for c in creators}
    seen = [(r.get("brand_id"), r.get("creator_id")) for r in predictions]
    if len(seen) != len(set(seen)):
        raise ValueError("Duplicate Laya prediction pair IDs")
    if set(seen) != expected or len(seen) != 400:
        raise ValueError(f"Laya prediction coverage error: {len(seen)} rows, {len(expected - set(seen))} missing")
    for row in predictions:
        if row.get("success"):
            laya_answers = row.get("laya", {})
            if any(key not in laya_answers for key in (*DIMENSIONS, "final_decision")):
                raise ValueError(f"Malformed Laya prediction at {row['brand_id']}/{row['creator_id']}")


def retrieve_and_decide_feed(brands: list[dict], creators: list[dict], label_map: dict, predictions: list[dict]) -> dict:
    """Evaluate Laya decisions over each brand's retrieved Top-10 in original rank order."""
    from retrieval.chroma_store import get_collection, get_model
    from retrieval.retrieve import retrieve_creators

    model = get_model()
    collection = get_collection()
    pred_by_pair = {(r["brand_id"], r["creator_id"]): r for r in predictions}
    baseline = read_json(BASELINE_JSON)
    baseline_by_brand = {row["brand_id"]: row for row in baseline["per_brand"]}
    per_brand = []
    all_items = []
    feeds = []
    for brand in brands:
        retrieved = retrieve_creators(brand, top_k=10, model=model, collection=collection)
        items = []
        for rank, candidate in enumerate(retrieved, 1):
            pair = (brand["brand_id"], candidate["creator_id"])
            prediction = pred_by_pair[pair]
            item = {
                "rank": rank,
                "creator_id": candidate["creator_id"],
                "name": candidate["name"],
                "distance": candidate["distance"],
                "ground_truth": label_map[pair]["label"],
                "decision": prediction["laya"]["final_decision"]["choice"] if prediction.get("success") else None,
                "confidence": prediction["laya"]["final_decision"]["confidence"] if prediction.get("success") else None,
                "prediction_error": prediction.get("error"),
            }
            items.append(item)
            all_items.append({"brand_id": brand["brand_id"], **item})
        keep = [x for x in items if x["decision"] == "KEEP"]
        uncertain = [x for x in items if x["decision"] == "UNCERTAIN"]
        dropped = [x for x in items if x["decision"] == "DROP"]
        retained = keep + uncertain
        good = [x for x in items if x["ground_truth"] == "good"]
        maybe = [x for x in items if x["ground_truth"] == "maybe"]
        poor = [x for x in items if x["ground_truth"] == "poor"]
        summary = {
            "brand_id": brand["brand_id"], "brand_name": brand["brand_name"],
            "retrieved_count": len(items), "keep_count": len(keep),
            "uncertain_count": len(uncertain), "drop_count": len(dropped),
            "retained_count": len(retained),
            "good_retrieved": len(good),
            "good_retained": sum(x["decision"] != "DROP" for x in good),
            "good_retention_rate": sum(x["decision"] != "DROP" for x in good) / len(good) if good else None,
            "maybe_retrieved": len(maybe),
            "maybe_retained": sum(x["decision"] != "DROP" for x in maybe),
            "poor_retrieved": len(poor),
            "poor_removed": sum(x["decision"] == "DROP" for x in poor),
            "poor_removal_rate": sum(x["decision"] == "DROP" for x in poor) / len(poor) if poor else None,
            "false_drops": sum(x["ground_truth"] in ("good", "maybe") and x["decision"] == "DROP" for x in items),
            "false_keeps": sum(x["ground_truth"] == "poor" and x["decision"] in ("KEEP", "UNCERTAIN") for x in items),
            "prediction_failures": sum(x["decision"] is None for x in items),
        }
        summary["baseline_chroma_top3"] = {
            "good": sum(x["label"] == "good" for x in baseline_by_brand[brand["brand_id"]]["retrieved"]),
            "maybe": sum(x["label"] == "maybe" for x in baseline_by_brand[brand["brand_id"]]["retrieved"]),
            "poor": sum(x["label"] == "poor" for x in baseline_by_brand[brand["brand_id"]]["retrieved"]),
            "retrieved_count": 3,
        }
        per_brand.append(summary)
        feeds.append({"brand_id": brand["brand_id"], "brand_name": brand["brand_name"],
                      "candidate_feed": retained, "excluded_drops": dropped})

    total = lambda field: sum(item[field] for item in per_brand)
    totals = {
        "retrieved_count": total("retrieved_count"), "retained_count": total("retained_count"),
        "good_retrieved": total("good_retrieved"), "good_retained": total("good_retained"),
        "good_retention_rate": total("good_retained") / total("good_retrieved") if total("good_retrieved") else None,
        "maybe_retrieved": total("maybe_retrieved"), "maybe_retained": total("maybe_retained"),
        "poor_retrieved": total("poor_retrieved"), "poor_removed": total("poor_removed"),
        "poor_removal_rate": total("poor_removed") / total("poor_retrieved") if total("poor_retrieved") else None,
        "false_drops": total("false_drops"), "false_keeps": total("false_keeps"),
        "prediction_failures": total("prediction_failures"),
        "baseline_chroma_top3": {
            "good": sum(x["baseline_chroma_top3"]["good"] for x in per_brand),
            "maybe": sum(x["baseline_chroma_top3"]["maybe"] for x in per_brand),
            "poor": sum(x["baseline_chroma_top3"]["poor"] for x in per_brand),
            "retrieved_count": 30,
        },
    }
    return {"name": "laya_feed_v0", "description": "Chroma Top-10 followed by Laya; KEEP then UNCERTAIN in original retrieval order; DROP excluded.",
            "baseline_comparison": "Original retrieval_baseline_v0 report read without modification.",
            "totals": totals, "per_brand": per_brand, "feeds": feeds, "top10_predictions": all_items}


def write_report_markdown(report: dict) -> None:
    m = report["metrics"]
    lines = [
        "# Laya Baseline v0", "", "## Objective", "",
        "This experiment measures the base zero-shot Laya model on the Guapd creator-brand matching domain before fine-tuning. ChromaDB remains the candidate retrieval layer; Laya makes decisions only about brand/creator pairs.",
        "", "## Model", "", f"`{report['model']}` (base English checkpoint; no typed-decisions subfolder).", "",
        f"SDK package version: `{report['sdk_version']}`.", "", "## Dataset", "",
        f"{report['dataset']['brands']} brands; {report['dataset']['creators']} creators; {report['dataset']['pairs']} complete pairs.",
        f"Pairs attempted: {report['run']['attempted']}; successful: {report['run']['successful']}; failed: {report['run']['failed']}.",
        "", "## Decision schema", "",
        "One SDK call per pair asks eight typed choice questions: niche fit, audience fit, geography fit, platform fit, budget fit, creator-size fit, campaign fit, and final decision (KEEP/UNCERTAIN/DROP). The state contains matching-relevant brand and creator fields. Raw SDK answers, confidence, probabilities, state, and question definitions are saved for reproducibility and future dataset design.",
        "", "Ground-truth labels are mapped as good→KEEP, maybe→UNCERTAIN, poor→DROP for evaluation only. The source labels are unchanged. Dimension targets are projected only from available `reasoning` fields in `label.json`; unavailable values are omitted.",
        "", "## Results", "",
        f"- **Accuracy:** {m['accuracy']:.4f}",
        f"- **Good retention (good→KEEP):** {m['good_retention']:.4f}",
        f"- **Poor rejection (poor→DROP):** {m['poor_rejection']:.4f}",
        f"- **Maybe uncertainty (maybe→UNCERTAIN):** {m['maybe_uncertainty']:.4f}",
        f"- **Hard errors:** good→DROP {m['hard_error_rate']['good_to_DROP']}; poor→KEEP {m['hard_error_rate']['poor_to_KEEP']}; total rate {m['hard_error_rate']['rate']:.4f}.",
        "", "### Confusion matrix", "",
        "Rows are ground truth; columns are Laya decisions. Failed predictions are shown separately.", "",
        "| Ground truth | KEEP | UNCERTAIN | DROP | No prediction |", "|---|---:|---:|---:|---:|",
    ]
    for gt in GROUND_TRUTH_CLASSES:
        row = m["confusion_matrix"][gt]
        lines.append(f"| {gt} | {row['KEEP']} | {row['UNCERTAIN']} | {row['DROP']} | {row['NO_PREDICTION']} |")
    lines.extend(["", "### Precision / recall / F1", "", "| Decision | Support | Precision | Recall | F1 |", "|---|---:|---:|---:|---:|"])
    for decision in DECISIONS:
        row = m["per_class"][decision]
        lines.append(f"| {decision} | {row['support']} | {row['precision']:.4f} | {row['recall']:.4f} | {row['f1']:.4f} |")
    lines.extend(["", "### Confidence", "",
                  f"Average confidence on correct decisions: {fmt(m['confidence']['average_correct'])}.",
                  f"Average confidence on incorrect decisions: {fmt(m['confidence']['average_incorrect'])}.",
                  f"High-confidence incorrect decisions (confidence ≥ 0.80): {m['confidence']['high_confidence_incorrect_count']}.",
                  "", "| Confidence band | Predictions | Correct |", "|---|---:|---:|"])
    for band, row in m["confidence"]["distribution"].items():
        lines.append(f"| {band} | {row['count']} | {row['correct']} |")
    if report.get("runtime_warnings"):
        lines.append("")
        lines.append("SDK runtime warnings:")
        lines.extend(f"- {warning}" for warning in report["runtime_warnings"])
        lines.append("The warning reported concerns the SDK's 11+ option temperature bucket; each experiment question has three choices. Raw per-question probabilities and both SDK confidence fields are retained for inspection.")
    lines.extend(["", "### Per-brand results", "", "| Brand | Accuracy | Good retention | Poor rejection | Maybe→UNCERTAIN | Successful/40 |", "|---|---:|---:|---:|---:|---:|"])
    for row in m["per_brand"]:
        lines.append(f"| {row['brand_name']} | {row['accuracy']:.3f} | {fmt(row['good_retention'])} | {fmt(row['poor_rejection'])} | {fmt(row['maybe_uncertainty'])} | {row['successful']}/40 |")
    lines.extend(["", "## Error analysis", "", "Dimension disagreements are measured against existing `reasoning` fields, not inferred from Laya's final decision. The list shows up to 10 examples per dimension.", ""])
    for dim in DIMENSIONS:
        examples = m["dimension_errors"][dim]
        lines.append(f"### {dim.replace('_', ' ').title()} ({len(examples)} listed disagreements)")
        if examples:
            lines.extend(["", "| Pair | Expected | Laya | Confidence |", "|---|---|---|---:|"])
            for ex in examples:
                lines.append(f"| {ex['brand_id']}/{ex['creator_id']} | {ex['expected']} | {ex['predicted']} | {ex['confidence']:.3f} |")
        else:
            lines.append("")
            lines.append("No disagreements recorded in the listed sample.")
        lines.append("")
    lines.append("### Ambiguous and overconfident cases")
    lines.append("")
    lines.append(f"Ground-truth maybe pairs routed to KEEP or DROP: {len(m['ambiguous_cases'])} listed (up to 30). High-confidence incorrect cases: {m['confidence']['high_confidence_incorrect_count']} (up to 30 saved in JSON).")
    if m["ambiguous_cases"]:
        lines.extend(["", "| Pair | Ground truth | Decision | Confidence |", "|---|---|---|---:|"])
        for ex in m["ambiguous_cases"][:15]:
            lines.append(f"| {ex['brand_id']}/{ex['creator_id']} | {ex['ground_truth']} | {ex['decision']} | {ex['confidence']:.3f} |")
    lines.extend(["", "## Retrieval + Laya results", "",
                  "The experiment retrieves Top-10 with the existing ChromaDB pipeline, applies the already-computed Laya decisions, keeps KEEP first and UNCERTAIN second while preserving retrieval order inside each group, and excludes DROP. The original retrieval baseline files were read only.", "",
                  f"- Baseline Chroma Top-3: {report['feed']['totals']['baseline_chroma_top3']['good']} good, {report['feed']['totals']['baseline_chroma_top3']['maybe']} maybe, {report['feed']['totals']['baseline_chroma_top3']['poor']} poor among 30 candidates.",
                  f"- Laya feed from Top-10: {report['feed']['totals']['good_retained']} / {report['feed']['totals']['good_retrieved']} good retained ({fmt(report['feed']['totals']['good_retention_rate'])}); {report['feed']['totals']['poor_removed']} / {report['feed']['totals']['poor_retrieved']} poor removed ({fmt(report['feed']['totals']['poor_removal_rate'])}); {report['feed']['totals']['maybe_retained']} / {report['feed']['totals']['maybe_retrieved']} maybe retained.",
                  f"- False drops (good/maybe dropped): {report['feed']['totals']['false_drops']}; false keeps (poor not dropped): {report['feed']['totals']['false_keeps']}.",
                  "", "| Brand | Baseline Top-3 good/maybe/poor | Top-10 good retained | Poor removed | Maybe retained | False drops | False keeps |", "|---|---:|---:|---:|---:|---:|---:|"])
    for row in report["feed"]["per_brand"]:
        base = row["baseline_chroma_top3"]
        lines.append(f"| {row['brand_name']} | {base['good']}/{base['maybe']}/{base['poor']} | {row['good_retained']}/{row['good_retrieved']} | {row['poor_removed']}/{row['poor_retrieved']} | {row['maybe_retained']}/{row['maybe_retrieved']} | {row['false_drops']} | {row['false_keeps']} |")
    lines.extend(["", "## Observations", "", "Metrics are descriptive of this 400-pair benchmark and these saved Chroma Top-10 candidates. They do not establish that Laya improves the candidate feed; compare the reported retention/removal counts and error types before making that claim.", "",
                  "## Fine-tuning candidates", "",
                  "Use the saved pair state, typed questions, existing-label-derived ground-truth answers, raw response, and decision confidence to inspect disagreements. Dimension targets are omitted only when the corresponding source reasoning field is unavailable. No model training was performed.", ""])
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def fmt(value) -> str:
    return "n/a" if value is None else f"{value:.4f}"


def main() -> int:
    brands, creators, labels, label_map = load_and_validate_inputs()
    print(f"Loaded {len(brands)} brands, {len(creators)} creators, {len(labels)} complete ground-truth pairs.")
    with warnings.catch_warnings(record=True) as caught_warnings:
        warnings.simplefilter("always")
        predictions = run_domain_evaluation(brands, creators, label_map)
    runtime_warnings = sorted({str(w.message) for w in caught_warnings})
    validate_predictions(predictions, brands, creators)
    successful = sum(bool(row.get("success")) for row in predictions)
    failed = len(predictions) - successful
    metrics = calculate_metrics(predictions, brands)
    print(f"Domain evaluation: attempted={len(predictions)}, successful={successful}, failed={failed}.")

    feed = retrieve_and_decide_feed(brands, creators, label_map, predictions)
    try:
        from importlib.metadata import version
        sdk_version = version("laya")
    except Exception:
        sdk_version = "unknown"
    report = {
        "experiment": "laya_baseline_v0",
        "model": MODEL_ID,
        "sdk_version": sdk_version,
        "runtime_warnings": runtime_warnings,
        "dataset": {"brands": len(brands), "creators": len(creators), "pairs": len(labels)},
        "run": {"attempted": len(predictions), "successful": successful, "failed": failed},
        "batch_size": BATCH_SIZE,
        "ground_truth_mapping": GROUND_TRUTH_TO_DECISION,
        "metrics": metrics,
        "feed": feed,
    }
    write_json_atomic(REPORT_JSON, report)
    write_report_markdown(report)
    print(f"Saved pair predictions: {PREDICTIONS_JSON}")
    print(f"Saved report: {REPORT_MD}")
    print(f"Saved JSON report: {REPORT_JSON}")
    print(json.dumps({"accuracy": metrics["accuracy"], "confusion_matrix": metrics["confusion_matrix"],
                      "good_retention": metrics["good_retention"], "poor_rejection": metrics["poor_rejection"],
                      "confidence": metrics["confidence"], "feed_totals": feed["totals"]}, indent=2))
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
