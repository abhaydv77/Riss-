"""Build compact, deterministic state for a brand/creator decision."""
from __future__ import annotations


def _clip(text, limit: int) -> str | None:
    if text is None:
        return None
    text = str(text).strip()
    if len(text) <= limit:
        return text
    clipped = text[:limit].rsplit(" ", 1)[0]
    return clipped + "…"


def _compact_requirement(text: str) -> str:
    """Remove repeated boilerplate without changing the stated requirement."""
    replacements = (
        ("must be based in ", "base: "),
        ("must post in ", "language: "),
        ("must have ", ""),
        ("must create ", "create: "),
        ("must cover ", "cover: "),
        ("must be ", ""),
        ("must ", ""),
    )
    result = text
    for old, new in replacements:
        result = result.replace(old, new)
    return result


def build_state(brand: dict, creator: dict) -> dict:
    """Return matching context in fixed field order and a small token budget.

    The base checkpoint has a 512-token sequence limit, including the question
    and its options. Narrative fields are clipped and redundant metrics are
    omitted so requirements and creator pricing/audience data are not silently
    pushed out of the model input.
    """
    brand_state = {
        "name": brand.get("brand_name"),
        "industry": brand.get("industry"),
        "product": brand.get("product"),
        "campaign_goal": _clip(brand.get("campaign_goal"), 100),
        "campaign_description": _clip(brand.get("campaign_description"), 70),
        "target_audience": _clip(brand.get("target_audience"), 55),
        "age": brand.get("target_age_range"),
        "gender": brand.get("target_gender"),
        "markets": brand.get("target_locations", []),
        "required_niches": brand.get("required_creator_niches", []),
        "preferred_niches": brand.get("preferred_creator_niches", []),
        "follower_bounds": [
            brand.get("minimum_followers"),
            brand.get("maximum_followers"),
            brand.get("creator_size_preference"),
        ],
        "budget": [brand.get("budget"), brand.get("currency")],
        "content": brand.get("content_types", []),
        "platforms": brand.get("platforms", []),
        "tone": brand.get("tone"),
        "mandatory": [_compact_requirement(x) for x in brand.get("mandatory_requirements", [])],
        "preferred_traits": brand.get("preferred_traits", [])[:3],
        "excluded_traits": brand.get("excluded_traits", []),
    }
    creator_state = {
        "name": creator.get("name"),
        "niche": creator.get("primary_niche"),
        "secondary_niches": creator.get("secondary_niches", []),
        "bio": _clip(creator.get("bio"), 70),
        "base": creator.get("location"),
        "languages": creator.get("languages", []),
        "platforms": creator.get("platforms", []),
        "followers": creator.get("followers"),
        "audience_age": creator.get("audience_age_range"),
        "audience_gender": creator.get("audience_gender_distribution", {}),
        "audience_markets": creator.get("audience_locations", []),
        "content": creator.get("content_types", []),
        "style": creator.get("content_style"),
        "rate_card": creator.get("rate_card"),
        "past_brands": creator.get("past_brand_categories", []),
        "interests": creator.get("interests", []),
    }
    return {"brand": brand_state, "creator": creator_state}


__all__ = ["build_state"]
