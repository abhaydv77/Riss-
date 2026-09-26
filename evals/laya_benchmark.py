"""One-pair runtime probe for the exact Laya evaluation path.

This intentionally evaluates only the first brand/creator pair and does not
read or write the full prediction checkpoint.
"""
from __future__ import annotations

import json
import platform
import resource
import time
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from laya.client import get_agent, predict_batch
from laya.decision import evaluate_creator
from laya.questions import QUESTIONS
from laya.state_builder import build_state

def peak_rss_mb() -> float:
    # macOS reports ru_maxrss in bytes; Linux reports KiB.
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value / (1024 * 1024) if platform.system() == "Darwin" else value / 1024


def main() -> None:
    brands = json.loads((ROOT / "data/brands.json").read_text())
    creators = json.loads((ROOT / "data/creators.json").read_text())
    brand, creator = brands[0], creators[0]

    init_start = time.perf_counter()
    agent = get_agent()  # same singleton initialization invoked by laya_eval.py
    init_seconds = time.perf_counter() - init_start
    rss_after_load = peak_rss_mb()

    first_start = time.perf_counter()
    first = evaluate_creator(brand, creator, agent=agent)
    first_seconds = time.perf_counter() - first_start
    rss_after_first = peak_rss_mb()

    second_start = time.perf_counter()
    second = evaluate_creator(brand, creator, agent=agent)
    second_seconds = time.perf_counter() - second_start
    rss_after_second = peak_rss_mb()

    # Same pair/state and questions, through the SDK batch entry point used by
    # laya_eval.py. Batch size one isolates API overhead from batch throughput.
    state = build_state(brand, creator)
    batch_start = time.perf_counter()
    batch_raw = predict_batch([state], QUESTIONS, batch_size=1, agent=agent)
    batch_seconds = time.perf_counter() - batch_start
    rss_after_batch = peak_rss_mb()

    import torch

    model = getattr(agent, "model", None)
    parameter_devices = sorted({str(p.device) for p in model.parameters()}) if model is not None else []
    elapsed_for_400 = init_seconds + first_seconds + 399 * second_seconds
    print(json.dumps({
        "pair": {"brand_id": brand["brand_id"], "creator_id": creator["creator_id"]},
        "model": "convaiinnovations/laya",
        "seconds": {
            "initialization": init_seconds,
            "first_prediction_via_evaluate_creator": first_seconds,
            "second_prediction_via_evaluate_creator": second_seconds,
            "one_item_batch_prediction": batch_seconds,
            "estimated_400_pairs_including_one_load": elapsed_for_400,
        },
        "batch_one_item_speedup_vs_second_single": second_seconds / batch_seconds if batch_seconds else None,
        "memory_peak_rss_mb": {
            "after_load": rss_after_load,
            "after_first": rss_after_first,
            "after_second": rss_after_second,
            "after_batch": rss_after_batch,
        },
        "device": {
            "platform_machine": platform.machine(),
            "agent_device": str(getattr(agent, "device", "unknown")),
            "model_parameter_devices": parameter_devices,
            "cuda_available": torch.cuda.is_available(),
            "mps_available": bool(getattr(torch.backends, "mps", None) and torch.backends.mps.is_available()),
            "torch_threads": torch.get_num_threads(),
        },
        "response_valid": all(k in first["laya"] for k in ("final_decision", "niche_fit")) and len(batch_raw) == 1,
        "single_and_batch_decisions": {
            "first": first["laya"]["final_decision"]["choice"],
            "second": second["laya"]["final_decision"]["choice"],
            "batch_raw_count": len(batch_raw),
        },
        "note": "One-item batch measures API overhead only; it cannot quantify multi-pair throughput scaling.",
    }, indent=2))


if __name__ == "__main__":
    main()
