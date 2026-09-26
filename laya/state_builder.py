"""Build concise, deterministic text sections for a brand/creator decision."""
from __future__ import annotations

import json


def _clip(text, limit: int) -> str:
    text = str(text or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "…"


def _compact_requirement(text: str) -> str:
    """Remove repeated boilerplate while preserving each stated requirement."""
    for old, new in (
        ("must be based in ", "base: "),
        ("must post in ", "language: "),
        ("must have ", ""),
        ("must create ", "create: "),
        ("must cover ", "cover: "),
        ("must be ", ""),
        ("must ", ""),
    ):
        text = text.replace(old, new)
    return text


def build_state(brand: dict, creator: dict) -> dict[str, str]:
    """Return two readable structured sections sized for Laya's 512-token limit.

    Long prose fields are clipped at word boundaries. The remaining fields are
    all directly useful to the eight decisions. Keeping each section as concise
    labeled text avoids JSON key overhead and prevents later fields (notably
    rates and audience data) from being silently truncated by the checkpoint.
    """
    budget = f"{brand.get('budget')} {brand.get('currency')}"
    followers = (
        f"{brand.get('minimum_followers')}-{brand.get('maximum_followers')} "
        f"({brand.get('creator_size_preference')})"
    )
    must = "; ".join(_compact_requirement(x) for x in brand.get("mandatory_requirements", []))
    traits = ", ".join(brand.get("preferred_traits", []))
    excluded = ", ".join(brand.get("excluded_traits", []))
    brand_context = (
        f"Brand {brand.get('brand_name')}; industry {brand.get('industry')}; "
        f"product {brand.get('product')}; goal {_clip(brand.get('campaign_goal'), 100)}; "
        f"brief {_clip(brand.get('campaign_description'), 50)}; "
        f"target {_clip(brand.get('target_audience'), 55)}; age {brand.get('target_age_range')}; "
        f"gender {brand.get('target_gender')}; target markets {', '.join(brand.get('target_locations', []))}; "
        f"required niches {', '.join(brand.get('required_creator_niches', []))}; "
        f"preferred niches {', '.join(brand.get('preferred_creator_niches', []))}; "
        f"follower bounds {followers}; budget {budget}; "
        f"content {', '.join(brand.get('content_types', []))}; "
        f"platforms {', '.join(brand.get('platforms', []))}; tone {brand.get('tone')}; "
        f"mandatory requirements {must}; preferred traits {traits}; excluded traits {excluded}."
    )
    gender = json.dumps(creator.get("audience_gender_distribution", {}), sort_keys=True, separators=(",", ":"))
    creator_context = (
        f"Creator {creator.get('name')}; niche {creator.get('primary_niche')}, "
        f"{', '.join(creator.get('secondary_niches', []))}; bio {_clip(creator.get('bio'), 80)}; "
        f"based {creator.get('location')}; languages {', '.join(creator.get('languages', []))}; "
        f"platforms {', '.join(creator.get('platforms', []))}; followers {creator.get('followers')}; "
        f"engagement {creator.get('engagement_rate')}; average views {creator.get('average_views')}; "
        f"audience age {creator.get('audience_age_range')}, gender {gender}, "
        f"locations {', '.join(creator.get('audience_locations', []))}; "
        f"content {', '.join(creator.get('content_types', []))}; style {creator.get('content_style')}; "
        f"rate card {creator.get('rate_card')}; "
        f"past brands {', '.join(creator.get('past_brand_categories', []))}; "
        f"interests {', '.join(creator.get('interests', []))}; "
        f"posting frequency {creator.get('posting_frequency')}."
    )
    return {"brand": brand_context, "creator": creator_context}


__all__ = ["build_state"]
