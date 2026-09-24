from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from retrieve import retrieve

BRANDS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "brands.json")

def main():
    with open(BRANDS_PATH) as f:
        brands = json.load(f)

    total_briefs = len(brands)
    briefs_with_mismatch = 0
    briefs_with_zero_overlap = 0

    for brand in brands:
        brief_id = brand["brand_id"]
        target_geo = set(brand.get("target_geo", []))
        results = retrieve(brand, k=5)

        match_count = 0
        for r in results:
            creator_geo = set(r["creator"].get("audience_geo", []))
            if creator_geo & target_geo:
                match_count += 1

        mismatch_count = 5 - match_count
        if match_count == 0:
            briefs_with_zero_overlap += 1
            briefs_with_mismatch += 1
            status = "ALL MISMATCH"
        elif mismatch_count > 0:
            briefs_with_mismatch += 1
            status = f"HAS MISMATCH ({mismatch_count} of 5)"
        else:
            status = "ALL MATCH"

        print(f"Brief {brief_id} ({brand['brand_name']}): target_geo={target_geo}, "
              f"top-5 geo matches: {match_count}/5 — {status}")

    print(f"\nSummary: {total_briefs} briefs total")
    print(f"  All 5 match (0 mismatches): {total_briefs - briefs_with_mismatch}")
    print(f"  Has mismatches: {briefs_with_mismatch}")
    print(f"  All-mismatch (0 overlaps): {briefs_with_zero_overlap}")

if __name__ == "__main__":
    main()
