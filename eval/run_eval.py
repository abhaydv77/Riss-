from __future__ import annotations

import csv
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABELS_PATH = os.path.join(ROOT, "data", "label.json")
LAYA_PATH = os.path.join(ROOT, "eval", "results", "laya_scores_small.json")
LLM_PATH = os.path.join(ROOT, "eval", "results", "llm_scores_small.json")
OUT_CSV = os.path.join(ROOT, "eval", "results", "comparison.csv")
OUT_LAYA_CSV = os.path.join(ROOT, "eval", "results", "laya_consistency.csv")

ORDER = ["good", "maybe", "poor"]


def load_json(path):
    with open(path) as f:
        return json.load(f)


def build_index(records, key_fields=("brief_id", "creator_id")):
    idx = {}
    for r in records:
        key = tuple(r[k] for k in key_fields)
        idx[key] = r
    return idx


def normalize_laya(r):
    n = r["noul_scores"]
    probs = {k: n[k] for k in ("niche_match", "audience_match", "budget_fit")}
    laya_score = r["laya_score"]
    bools = {k: probs[k] > 0.5 for k in probs}
    return probs, laya_score, bools


def normalize_llm(r):
    return {
        "niche_match": r["niche_match"],
        "audience_match": r["audience_match"],
        "budget_fit": r["budget_fit"],
    }, r["overall_fit"], {
        "niche_match": r["niche_match"],
        "audience_match": r["audience_match"],
        "budget_fit": r["budget_fit"],
    }


def label_rank(label):
    return ORDER.index(label)


def rank_from_layavote(probs):
    good_p = probs["niche_match"] * 0.4 + probs["audience_match"] * 0.4 + probs["budget_fit"] * 0.2
    return good_p


def rank_from_llm(bools):
    good_p = sum(1 for v in bools.values() if v) / 3.0
    return good_p


def precision_at(ranked_labels, k):
    if not ranked_labels:
        return 0.0
    top_k = ranked_labels[:k]
    return sum(1 for l in top_k if l == 0) / k


def dcg(ranked_labels):
    return sum(l / (i + 1) for i, l in enumerate(ranked_labels))


def ndcg_at(ranked_labels, k=5):
    if not ranked_labels:
        return 0.0
    binary = [1 if l == 0 else 0 for l in ranked_labels[:k]]
    ideal = sorted(binary, reverse=True)[:k]
    dcg_val = dcg(binary)
    idcg_val = dcg(ideal)
    if idcg_val == 0:
        return 0.0
    return dcg_val / idcg_val


def mrr(ranked_labels, true_idx):
    for i, l in enumerate(ranked_labels):
        if l == true_idx:
            return 1.0 / (i + 1)
    return 0.0


def compute_metrics(scored_pairs, label_idx_int, ranks_func):
    all_prec3, all_prec5, all_mrr, all_ndcg = [], [], [], []
    for brief_id in sorted(set(p["brief_id"] for p in scored_pairs)):
        brief_pairs = [p for p in scored_pairs if p["brief_id"] == brief_id]
        brief_pairs.sort(key=ranks_func, reverse=True)
        ranked = [label_idx_int.get((p["brief_id"], p["creator_id"]), -1) for p in brief_pairs]
        # Ground truth: find the creator whose label is the "best" for this brief
        true_label = None
        for p in scored_pairs:
            if p["brief_id"] == brief_id:
                true_label = p["true_label"]
                break
        true_idx = ORDER.index(true_label) if true_label else -1
        all_prec3.append(precision_at(ranked, 3))
        all_prec5.append(precision_at(ranked, 5))
        all_mrr.append(mrr(ranked, true_idx))
        all_ndcg.append(ndcg_at(ranked[:5]))

    n = len(all_prec3)
    return {
        "precision@3": sum(all_prec3) / n,
        "precision@5": sum(all_prec5) / n,
        "MRR": sum(all_mrr) / n,
        "NDCG@5": sum(all_ndcg) / n,
    }


def main():
    labels = load_json(LABELS_PATH)
    laya = load_json(LAYA_PATH)
    llm = load_json(LLM_PATH)

    label_idx = build_index(labels)
    laya_idx = build_index(laya)
    llm_idx = build_index(llm)

    all_keys = set(label_idx) | set(laya_idx) | set(llm_idx)
    missing = {k: [] for k in all_keys}
    for k in all_keys:
        if k not in label_idx:
            missing[k].append("label")
        if k not in laya_idx:
            missing[k].append("laya")
        if k not in llm_idx:
            missing[k].append("llm")

    orphans = {k: v for k, v in missing.items() if v}
    if orphans:
        print(f"WARNING: {len(orphans)} pairs missing from one or more files:")
        for k, srcs in orphans.items():
            print(f"  {k}: missing from {', '.join(srcs)}")
    else:
        print("All pairs present in all three files. No orphans.")

    # Join: iterate over label entries as the canonical set
    scored_pairs = []
    for l in labels:
        key = (l["brief_id"], l["creator_id"])
        l_record = label_idx[key]
        l_laya = laya_idx.get(key)
        l_llm = llm_idx.get(key)

        probs, laya_score, laya_bools = normalize_laya(l_laya) if l_laya else (None, None, None)
        llm_bools, llm_score, _ = normalize_llm(l_llm) if l_llm else (None, None, None)

        scored_pairs.append({
            "brief_id": l["brief_id"],
            "creator_id": l["creator_id"],
            "true_label": l["label"],
            "laya_score": laya_score,
            "laya_probs": probs,
            "laya_bools": laya_bools,
            "llm_score": llm_score,
            "llm_bools": llm_bools,
            "laya_latency": l_laya["latency"] if l_laya else None,
            "llm_latency_ms": l_llm["latency_ms"] if l_llm else None,
            "llm_provider": l_llm.get("provider") if l_llm else None,
        })

    # Step 2: Compute accuracy, precision, MRR, NDCG
    label_idx_map = {(p["brief_id"], p["creator_id"]): p["true_label"] for p in scored_pairs}
    label_idx_int = {(p["brief_id"], p["creator_id"]): ORDER.index(p["true_label"]) for p in scored_pairs}

    for p in scored_pairs:
        p["_pred"] = p["laya_score"]
    laya_acc = sum(1 for p in scored_pairs if p["laya_score"] == p["true_label"]) / len(scored_pairs)
    for p in scored_pairs:
        p["_pred"] = p["llm_score"]
    llm_acc = sum(1 for p in scored_pairs if p["llm_score"] == p["true_label"]) / len(scored_pairs)

    laya_ranks = lambda p: rank_from_layavote(p["laya_probs"]) if p["laya_probs"] else 0
    llm_ranks = lambda p: rank_from_llm(p["llm_bools"]) if p["llm_bools"] else 0

    laya_metrics = compute_metrics(scored_pairs, label_idx_int, laya_ranks)
    laya_metrics["accuracy"] = laya_acc
    llm_metrics = compute_metrics(scored_pairs, label_idx_int, llm_ranks)
    llm_metrics["accuracy"] = llm_acc

    # Step 3: Laya self-consistency check
    inconsistent = []
    for p in scored_pairs:
        if p["laya_score"] is None or p["laya_probs"] is None:
            continue
        probs = p["laya_probs"]
        score = p["laya_score"]
        flag = False
        if score == "good" and any(v <= 0.5 for v in probs.values()):
            flag = True
        if score == "poor" and all(v > 0.5 for v in probs.values()):
            flag = True
        if flag:
            inconsistent.append(p)

    n_inconsistent = len(inconsistent)
    n_laya_total = len([p for p in scored_pairs if p["laya_score"] is not None])
    inconv_pct = (n_inconsistent / n_laya_total * 100) if n_laya_total else 0

    # Step 4: Laya-vs-LLM agreement
    agreements = sum(
        1 for p in scored_pairs
        if p["laya_score"] is not None and p["llm_score"] is not None and p["laya_score"] == p["llm_score"]
    )
    agreement_rate = agreements / len(scored_pairs) * 100

    # Step 5: Latency
    laya_latencies = [p["laya_latency"] for p in scored_pairs if p["laya_latency"] is not None]
    laya_avg_ms = (sum(laya_latencies) / len(laya_latencies) * 1000) if laya_latencies else 0
    llm_latencies = [p["llm_latency_ms"] for p in scored_pairs if p["llm_latency_ms"] is not None]
    llm_avg_ms = sum(llm_latencies) / len(llm_latencies) if llm_latencies else 0

    gemini_lat = [p["llm_latency_ms"] for p in scored_pairs if p["llm_provider"] == "gemini" and p["llm_latency_ms"] is not None]
    groq_lat = [p["llm_latency_ms"] for p in scored_pairs if p["llm_provider"] == "groq" and p["llm_latency_ms"] is not None]
    gemini_avg = sum(gemini_lat) / len(gemini_lat) if gemini_lat else 0
    groq_avg = sum(groq_lat) / len(groq_lat) if groq_lat else 0

    # Print summary
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)

    print(f"\n--- Overall Accuracy ---")
    print(f"  Laya:   {laya_acc:.4f} ({sum(1 for p in scored_pairs if p['laya_score'] == p['true_label'])}/{len(scored_pairs)})")
    print(f"  LLM:    {llm_acc:.4f} ({sum(1 for p in scored_pairs if p['llm_score'] == p['true_label'])}/{len(scored_pairs)})")

    print(f"\n--- Per-brief Precision@3, Precision@5, MRR, NDCG@5 ---")
    print(f"{'Method':<8} {'Prec@3':>8} {'Prec@5':>8} {'MRR':>8} {'NDCG@5':>8}")
    print(f"{'-'*40}")
    print(f"{'Laya':<8} {laya_metrics['precision@3']:>8.4f} {laya_metrics['precision@5']:>8.4f} {laya_metrics['MRR']:>8.4f} {laya_metrics['NDCG@5']:>8.4f}")
    print(f"{'LLM':<8} {llm_metrics['precision@3']:>8.4f} {llm_metrics['precision@5']:>8.4f} {llm_metrics['MRR']:>8.4f} {llm_metrics['NDCG@5']:>8.4f}")

    print(f"\n--- Laya Self-Consistency Check ---")
    print(f"  Inconsistent pairs: {n_inconsistent}/{n_laya_total} ({inconv_pct:.1f}%)")
    for p in inconsistent[:5]:
        print(f"    {p['brief_id']}/{p['creator_id']}: score={p['laya_score']}, probs={p['laya_probs']}")

    print(f"\n--- Laya vs LLM Agreement ---")
    print(f"  Agreement rate: {agreement_rate:.1f}% ({agreements}/{len(scored_pairs)} pairs)")

    print(f"\n--- Latency (ms) ---")
    print(f"  Laya avg:   {laya_avg_ms:.1f}ms")
    print(f"  LLM avg:    {llm_avg_ms:.1f}ms")
    print(f"    Gemini:   {gemini_avg:.1f}ms ({len(gemini_lat)} pairs)")
    print(f"    Groq:     {groq_avg:.1f}ms ({len(groq_lat)} pairs)")

    # Write comparison.csv
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["method", "accuracy", "precision@3", "precision@5", "mrr", "ndcg@5", "avg_latency_ms"])
        writer.writerow(["laya", laya_acc, laya_metrics["precision@3"], laya_metrics["precision@5"],
                         laya_metrics["MRR"], laya_metrics["NDCG@5"], laya_avg_ms])
        writer.writerow(["llm", llm_acc, llm_metrics["precision@3"], llm_metrics["precision@5"],
                         llm_metrics["MRR"], llm_metrics["NDCG@5"], llm_avg_ms])
    print(f"\nWritten: {OUT_CSV}")

    # Write laya_consistency.csv
    with open(OUT_LAYA_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["brief_id", "creator_id", "laya_score", "niche_match", "audience_match",
                         "budget_fit", "inconsistent"])
        for p in scored_pairs:
            if p["laya_probs"] is None:
                continue
            probs = p["laya_probs"]
            score = p["laya_score"]
            flag = False
            if score == "good" and any(v <= 0.5 for v in probs.values()):
                flag = True
            if score == "poor" and all(v > 0.5 for v in probs.values()):
                flag = True
            writer.writerow([p["brief_id"], p["creator_id"], score, probs["niche_match"],
                             probs["audience_match"], probs["budget_fit"], flag])
    print(f"Written: {OUT_LAYA_CSV}")


if __name__ == "__main__":
    main()
