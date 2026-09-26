"""Validate complete brand/creator ground-truth coverage."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVALS = Path(__file__).resolve().parent
REASONING_FIELDS = {
    "niche_match",
    "audience_match",
    "geography_match",
    "platform_match",
    "budget_fit",
    "creator_size_fit",
    "campaign_fit",
}
ALLOWED_LABELS = {"good", "maybe", "poor"}


def main() -> int:
    brands = json.loads((ROOT / "data" / "brands.json").read_text(encoding="utf-8"))
    creators = json.loads((ROOT / "data" / "creators.json").read_text(encoding="utf-8"))
    labels = json.loads((EVALS / "label.json").read_text(encoding="utf-8"))

    brand_ids = {brand["brand_id"] for brand in brands}
    creator_ids = {creator["creator_id"] for creator in creators}
    expected = {(brand_id, creator_id) for brand_id in brand_ids for creator_id in creator_ids}
    seen: set[tuple[str, str]] = set()
    errors: list[str] = []

    for index, row in enumerate(labels):
        pair = (row.get("brand_id"), row.get("creator_id"))
        if pair[0] not in brand_ids:
            errors.append(f"row {index}: unknown brand_id {pair[0]!r}")
        if pair[1] not in creator_ids:
            errors.append(f"row {index}: unknown creator_id {pair[1]!r}")
        if pair in seen:
            errors.append(f"row {index}: duplicate pair {pair}")
        seen.add(pair)
        if row.get("label") not in ALLOWED_LABELS:
            errors.append(f"row {index}: invalid label {row.get('label')!r}")
        reasoning = row.get("reasoning")
        if not isinstance(reasoning, dict):
            errors.append(f"row {index}: reasoning must be an object")
        else:
            missing = REASONING_FIELDS - reasoning.keys()
            if missing:
                errors.append(f"row {index}: missing reasoning fields {sorted(missing)}")
        if not isinstance(row.get("reason"), str) or not row["reason"].strip():
            errors.append(f"row {index}: reason must be a non-empty string")

    missing_pairs = expected - seen
    unexpected_pairs = seen - expected
    if missing_pairs:
        errors.append(f"missing {len(missing_pairs)} expected pairs")
    if unexpected_pairs:
        errors.append(f"found {len(unexpected_pairs)} unexpected pairs")
    if len(labels) != len(brands) * len(creators):
        errors.append(
            f"total pair count is {len(labels)}, expected {len(brands) * len(creators)}"
        )

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        f"Validation passed: {len(brands)} brands × {len(creators)} creators "
        f"= {len(labels)} unique, complete pairs."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
