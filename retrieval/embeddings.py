"""Build text representation from a creator profile for embedding."""
from __future__ import annotations


def build_creator_text(creator: dict) -> str:
    """Convert a creator dict into a single searchable string.

    Concatenates niche, audience, past brand categories,
    and deliverable types into one space-separated string.
    """
    parts = [
        " ".join(creator.get("niche", [])),
        f"{creator.get('audience_age', '')} {' '.join(creator.get('audience_geo', []))}".strip(),
        " ".join(creator.get("past_brand_categories", [])),
        " ".join(creator.get("deliverable_types", [])),
    ]
    return " ".join(p for p in parts if p)


def build_brief_text(brand: dict) -> str:
    """Convert a brand brief dict into a single searchable string."""
    parts = [
        " ".join(brand.get("target_niche", [])),
        f"{brand.get('target_age', '')} {' '.join(brand.get('target_geo', []))}".strip(),
        brand.get("tone", ""),
        brand.get("brief_text", ""),
        brand.get("category", ""),
    ]
    return " ".join(p for p in parts if p)
