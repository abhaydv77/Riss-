"""Retrieval Baseline v0 evaluation.

Measures the CURRENT ChromaDB retrieval performance against ground-truth labels.

Uses the existing retrieval implementation. Does not modify retrieval logic.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from retrieval.retrieve import retrieve_creators
from retrieval.chroma_store import load_brands, load_creators
from retrieval.config import COLLECTION_NAME, CHROMA_DB_DIR

EVALS = Path(__file__).resolve().parent
LABELS_PATH = EVALS / "label.json"
REPORTS_DIR = EVALS / "reports"
REPORT_MD = REPORTS_DIR / "retrieval_baseline_v0.md"
REPORT_JSON = REPORTS_DIR / "retrieval_baseline_v0.json"
K = 3


def load_labels() -> dict[tuple[str, str], str]:
    """Load ground-truth labels as {(brand_id, creator_id): label}."""
    with open(LABELS_PATH, encoding="utf-8") as f:
        labels = json.load(f)
    return {(row["brand_id"], row["creator_id"]): row["label"] for row in labels}


def retrieve_for_brand(brand: dict) -> list[dict]:
    """Run retrieval and return the top-K results."""
    return retrieve_creators(brand, top_k=K)


def validate_results(
    brands: list[dict],
    creators: list[dict],
    labels: dict[tuple[str, str], str],
    all_results: dict[str, list[dict]],
) -> list[str]:
    """Validate all results before computing metrics."""
    errors = []
    creator_ids = {c["creator_id"] for c in creators}

    for brand in brands:
        brand_id = brand["brand_id"]
        results = all_results[brand_id]

        if len(results) != K:
            errors.append(f"{brand_id}: expected {K} results, got {len(results)}")
            continue

        seen_ids = set()
        for r in results:
            cid = r["creator_id"]
            if cid not in creator_ids:
                errors.append(f"{brand_id}: {cid} not found in creators.json")
            if cid in seen_ids:
                errors.append(f"{brand_id}: duplicate creator {cid} in Top-{K}")
            seen_ids.add(cid)

            pair = (brand_id, cid)
            if pair not in labels:
                errors.append(f"{brand_id}: {cid} not found in label.json")

    if errors:
        print("VALIDATION FAILED:")
        for e in errors:
            print(f"  - {e}")
    return errors


def compute_metrics(
    brand: dict,
    retrieved: list[dict],
    labels: dict[tuple[str, str], str],
) -> dict:
    """Compute per-brand metrics."""
    brand_id = brand["brand_id"]
    retrieved_labels = []

    for r in retrieved:
        cid = r["creator_id"]
        label = labels.get((brand_id, cid), "unknown")
        retrieved_labels.append(label)
        r["label"] = label

    good_in_top3 = sum(1 for l in retrieved_labels if l == "good")
    maybe_or_good_in_top3 = sum(1 for l in retrieved_labels if l in ("good", "maybe"))

    # Strict Precision@3
    strict_p = good_in_top3 / K

    # Relaxed Precision@3
    relaxed_p = maybe_or_good_in_top3 / K

    # Good Hit Rate
    good_hit = 1 if good_in_top3 >= 1 else 0

    # Good/Maybe Hit Rate
    gm_hit = 1 if maybe_or_good_in_top3 >= 1 else 0

    # MRR@3 (good only)
    mrr = 0.0
    for i, label in enumerate(retrieved_labels):
        if label == "good":
            mrr = 1.0 / (i + 1)
            break

    return {
        "strict_precision_at_3": strict_p,
        "relaxed_precision_at_3": relaxed_p,
        "good_hit": good_hit,
        "good_or_maybe_hit": gm_hit,
        "mrr_at_3": mrr,
        "retrieved": [
            {
                "rank": i + 1,
                "creator_id": r["creator_id"],
                "name": r["name"],
                "distance": round(r["distance"], 4),
                "label": r["label"],
            }
            for i, r in enumerate(retrieved)
        ],
    }


def main() -> None:
    # Load data
    brands = load_brands()
    creators = load_creators()
    labels = load_labels()

    print(f"Loaded {len(brands)} brands, {len(creators)} creators, {len(labels)} labels")

    # Run retrieval for every brand
    all_results: dict[str, list[dict]] = {}
    for brand in brands:
        results = retrieve_for_brand(brand)
        all_results[brand["brand_id"]] = results
        print(f"  {brand['brand_id']} ({brand['brand_name']}): {len(results)} creators retrieved")

    # Validate
    errors = validate_results(brands, creators, labels, all_results)
    if errors:
        print("\nValidation failed. Stopping.")
        sys.exit(1)

    # Compute per-brand metrics
    brand_metrics: list[dict] = []
    total_strict = 0.0
    total_relaxed = 0.0
    total_good_hit = 0
    total_gm_hit = 0
    total_mrr = 0.0

    for brand in brands:
        metrics = compute_metrics(brand, all_results[brand["brand_id"]], labels)
        brand_metrics.append({
            "brand_id": brand["brand_id"],
            "brand_name": brand["brand_name"],
            **{k: v for k, v in metrics.items() if k != "retrieved"},
            "retrieved": metrics["retrieved"],
        })
        total_strict += metrics["strict_precision_at_3"]
        total_relaxed += metrics["relaxed_precision_at_3"]
        total_good_hit += metrics["good_hit"]
        total_gm_hit += metrics["good_or_maybe_hit"]
        total_mrr += metrics["mrr_at_3"]

    n_brands = len(brands)
    aggregate = {
        "strict_precision_at_3": round(total_strict / n_brands, 4),
        "relaxed_precision_at_3": round(total_relaxed / n_brands, 4),
        "good_hit_rate_at_3": round(total_good_hit / n_brands, 4),
        "good_or_maybe_hit_rate_at_3": round(total_gm_hit / n_brands, 4),
        "mrr_at_3": round(total_mrr / n_brands, 4),
    }

    # Build JSON output
    output = {
        "system": {
            "embedding_model": "all-MiniLM-L6-v2",
            "vector_database": f"ChromaDB (persistent, {CHROMA_DB_DIR})",
            "collection": COLLECTION_NAME,
            "num_brands": n_brands,
            "num_creators": len(creators),
            "k": K,
            "total_ground_truth_pairs": len(labels),
        },
        "aggregate_metrics": aggregate,
        "per_brand": brand_metrics,
    }

    # Write JSON report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Write Markdown report
    write_markdown(output, aggregate, brand_metrics)

    # Print summary
    print(f"\n{'='*60}")
    print(f"RETRIEVAL BASELINE v0 RESULTS")
    print(f"{'='*60}")
    print(f"Total brands evaluated: {n_brands}")
    print(f"Total retrievals evaluated: {n_brands * K}")
    print(f"Strict Precision@3: {aggregate['strict_precision_at_3']:.4f}")
    print(f"Relaxed Precision@3: {aggregate['relaxed_precision_at_3']:.4f}")
    print(f"Good Hit Rate@3: {aggregate['good_hit_rate_at_3']:.4f}")
    print(f"Good/Maybe Hit Rate@3: {aggregate['good_or_maybe_hit_rate_at_3']:.4f}")
    print(f"MRR@3: {aggregate['mrr_at_3']:.4f}")
    print(f"\nReport saved to: {REPORT_MD}")
    print(f"JSON results saved to: {REPORT_JSON}")


def write_markdown(
    output: dict,
    aggregate: dict,
    brand_metrics: list[dict],
) -> None:
    """Write the Markdown report."""
    lines: list[str] = []

    lines.append("# Retrieval Baseline v0")
    lines.append("")
    lines.append("## System")
    lines.append("")
    lines.append(f"- **Embedding model:** {output['system']['embedding_model']}")
    lines.append(f"- **Vector database:** {output['system']['vector_database']}")
    lines.append(f"- **Number of brands:** {output['system']['num_brands']}")
    lines.append(f"- **Number of creators:** {output['system']['num_creators']}")
    lines.append(f"- **K:** {output['system']['k']}")
    lines.append(f"- **Ground-truth pairs:** {output['system']['total_ground_truth_pairs']}")
    lines.append("")
    lines.append("## Overall Metrics")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append(f"| Strict Precision@3 | {aggregate['strict_precision_at_3']:.4f} |")
    lines.append(f"| Relaxed Precision@3 | {aggregate['relaxed_precision_at_3']:.4f} |")
    lines.append(f"| Good Hit Rate@3 | {aggregate['good_hit_rate_at_3']:.4f} |")
    lines.append(f"| Good/Maybe Hit Rate@3 | {aggregate['good_or_maybe_hit_rate_at_3']:.4f} |")
    lines.append(f"| MRR@3 | {aggregate['mrr_at_3']:.4f} |")
    lines.append("")
    lines.append("## Per-Brand Results")
    lines.append("")
    lines.append("| Brand | Rank 1 | Label | Rank 2 | Label | Rank 3 | Label | Good@3 | P@3 |")
    lines.append("|---|---|---|---|---|---|---|---|---|")

    for bm in brand_metrics:
        r = bm["retrieved"]
        good_count = sum(1 for x in r if x["label"] == "good")
        p3 = bm["strict_precision_at_3"]
        row = f"| {bm['brand_name']} | {r[0]['creator_id']} | {r[0]['label']} | {r[1]['creator_id']} | {r[1]['label']} | {r[2]['creator_id']} | {r[2]['label']} | {good_count} | {p3:.2f} |"
        lines.append(row)

    lines.append("")
    lines.append("## Observations")
    lines.append("")

    # Count observations
    brands_with_good = sum(1 for bm in brand_metrics if bm["good_hit"] == 1)
    brands_no_good = sum(1 for bm in brand_metrics if bm["good_hit"] == 0)
    brands_all_poor = sum(1 for bm in brand_metrics if bm["strict_precision_at_3"] == 0)
    brands_good_rank1 = sum(1 for bm in brand_metrics if bm["retrieved"][0]["label"] == "good")
    brands_only_maybe = sum(1 for bm in brand_metrics if bm["good_hit"] == 0 and bm["good_or_maybe_hit"] == 1)

    lines.append(f"- **{brands_with_good} out of {len(brand_metrics)} brands** retrieved at least one good creator in Top-3.")
    lines.append(f"- **{brands_no_good} out of {len(brand_metrics)} brands** retrieved no good creator in Top-3.")
    lines.append(f"- **{brands_all_poor} out of {len(brand_metrics)} brands** had all 3 retrieved creators labeled poor.")
    lines.append(f"- **{brands_good_rank1} brands** had a good creator at rank 1.")
    lines.append(f"- **{brands_only_maybe} brands** had no good creator but had at least one maybe creator in Top-3.")
    lines.append("")

    # Distance info
    lines.append("## Chroma Distances")
    lines.append("")
    lines.append("Distance is cosine distance. Lower means more similar.")
    lines.append("")
    for bm in brand_metrics:
        r = bm["retrieved"]
        distances = ", ".join(f"rank {x['rank']}: {x['distance']:.4f} ({x['label']})" for x in r)
        lines.append(f"- **{bm['brand_name']}**: {distances}")
    lines.append("")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
