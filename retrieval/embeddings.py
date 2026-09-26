"""Build rich natural-language searchable documents from creator profiles and brand briefs."""
from __future__ import annotations

from retrieval.config import EMBEDDING_MODEL


def build_creator_text(creator: dict) -> str:
    """Convert a creator profile into a rich natural-language searchable document.

    Preserves all structured information relevant for matching: niche, audience,
    location, language, platform, followers, engagement, content style, content
    type, past brand categories, rates, and interests.
    """
    name = creator.get("name", "")
    primary_niche = creator.get("primary_niche", "")
    secondary_niches = creator.get("secondary_niches", [])
    bio = creator.get("bio", "")
    location = creator.get("location", "")
    languages = creator.get("languages", [])
    platforms = creator.get("platforms", [])
    followers = creator.get("followers", 0)
    engagement_rate = creator.get("engagement_rate", 0.0)
    average_views = creator.get("average_views", 0)
    audience_age_range = creator.get("audience_age_range", "")
    audience_gender = creator.get("audience_gender_distribution", {})
    audience_locations = creator.get("audience_locations", [])
    content_types = creator.get("content_types", [])
    content_style = creator.get("content_style", "")
    rate_card = creator.get("rate_card", "")
    past_brand_categories = creator.get("past_brand_categories", [])
    interests = creator.get("interests", [])
    posting_frequency = creator.get("posting_frequency", "")

    gender_text = ", ".join(f"{k}: {int(v * 100)}%" for k, v in audience_gender.items()) if audience_gender else ""

    parts = [
        f"{name} is a {primary_niche} creator.",
        f"Secondary niches include {', '.join(secondary_niches)}.",
        bio,
        f"Based in {location}.",
        f"Languages: {', '.join(languages)}.",
        f"Platforms: {', '.join(platforms)}.",
        f"Followers: {followers:,}. Engagement rate: {engagement_rate:.1%}. Average views: {average_views:,}.",
        f"Audience age range: {audience_age_range}. Audience gender: {gender_text}.",
        f"Audience locations: {', '.join(audience_locations)}.",
        f"Content types: {', '.join(content_types)}.",
        f"Content style: {content_style}.",
        f"Rate card: {rate_card}.",
        f"Past brand categories: {', '.join(past_brand_categories)}.",
        f"Interests: {', '.join(interests)}.",
        f"Posting frequency: {posting_frequency}.",
    ]

    return " ".join(p for p in parts if p)


def build_brief_text(brand: dict) -> str:
    """Convert a brand brief into a natural-language retrieval query.

    Emphasizes campaign goal, target audience, niche, location, platform,
    content type, and creator traits.
    """
    brand_name = brand.get("brand_name", "")
    industry = brand.get("industry", "")
    product = brand.get("product", "")
    campaign_title = brand.get("campaign_title", "")
    campaign_goal = brand.get("campaign_goal", "")
    campaign_description = brand.get("campaign_description", "")
    target_audience = brand.get("target_audience", "")
    target_age_range = brand.get("target_age_range", "")
    target_gender = brand.get("target_gender", "")
    target_locations = brand.get("target_locations", [])
    required_creator_niches = brand.get("required_creator_niches", [])
    preferred_creator_niches = brand.get("preferred_creator_niches", [])
    content_types = brand.get("content_types", [])
    platforms = brand.get("platforms", [])
    tone = brand.get("tone", "")
    mandatory_requirements = brand.get("mandatory_requirements", [])
    preferred_traits = brand.get("preferred_traits", [])
    excluded_traits = brand.get("excluded_traits", [])

    parts = [
        f"{brand_name} is a {industry} brand launching '{campaign_title}'.",
        f"Campaign goal: {campaign_goal}",
        f"Product: {product}",
        f"Target audience: {target_audience}. Age range: {target_age_range}. Gender: {target_gender}.",
        f"Target locations: {', '.join(target_locations)}.",
        f"Required creator niches: {', '.join(required_creator_niches)}.",
        f"Preferred creator niches: {', '.join(preferred_creator_niches)}.",
        f"Preferred content types: {', '.join(content_types)}.",
        f"Preferred platforms: {', '.join(platforms)}.",
        f"Desired tone: {tone}.",
        f"Mandatory requirements: {', '.join(mandatory_requirements)}.",
        f"Preferred creator traits: {', '.join(preferred_traits)}.",
        f"Excluded creator traits: {', '.join(excluded_traits)}.",
        campaign_description,
    ]

    return " ".join(p for p in parts if p)


__all__ = ["EMBEDDING_MODEL", "build_creator_text", "build_brief_text"]
