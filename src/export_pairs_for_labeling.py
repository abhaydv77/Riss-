from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from retrieve import retrieve

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRANDS_PATH = os.path.join(ROOT, "data", "brands.json")
OUT_PATH = os.path.join(ROOT, "data", "pairs_to_label.json")


def main():
    with open(BRANDS_PATH) as f:
        brands = json.load(f)

    pairs = []
    for brand in brands:
        results = retrieve(brand, k=5)
        for r in results:
            pairs.append({
                "brief_id": brand["brand_id"],
                "brand_name": brand["brand_name"],
                "creator_id": r["creator"]["creator_id"],
                "creator_name": r["creator"]["name"],
                "handle": r["creator"]["handle"],
                "niche": r["creator"].get("niche", []),
                "audience_geo": r["creator"].get("audience_geo", []),
                "target_geo": brand.get("target_geo", []),
                "score": r["score"],
            })

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(pairs, f, indent=2)

    print(f"Exported {len(pairs)} pairs -> {OUT_PATH}")


if __name__ == "__main__":
    main()
