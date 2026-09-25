"""Generate synthetic creator/brand data for local development.

Creates realistic creator profiles and brand campaign briefs.
Output:
    data/creators.json  (500 creators)
    data/brands.json    (50 brands)
"""
from __future__ import annotations

import json
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")

NICHES = ["fitness", "beauty", "skincare", "fashion", "food", "travel", "tech", "gaming",
          "finance", "parenting", "home-decor", "sustainability", "sports", "music", "photography"]
PLATFORMS = ["instagram", "tiktok", "youtube"]
GEOS = ["US", "UK", "DE", "FR", "ES", "IN", "BR", "global"]
AGES = ["13-17", "18-24", "25-34", "35-44", "45+"]
STYLES = ["authentic vlog storytelling", "minimal aesthetic reels", "high-energy skits",
          "educational tutorials", "cinematic reviews", "cozy lifestyle diaries", "bold street style"]
TONES = ["playful and bold", "authentic and warm", "minimal and premium", "educational and clear",
         "luxurious and aspirational", "fun gen-z humor", "trustworthy expert"]
CATS = ["skincare", "fashion", "food & beverage", "travel", "fintech", "fitness",
        "gaming", "home & living", "beauty", "consumer tech"]
FIRST = ["Maya", "Liam", "Sofia", "Noah", "Ava", "Lucas", "Mia", "Ethan", "Zoe", "Leo",
         "Nora", "Finn", "Ivy", "Kai", "Lena", "Omar", "Priya", "Diego", "Hana", "Tom"]
LAST = ["Chen", "Garcia", "Kim", "Patel", "Muller", "Rossi", "Silva", "Nguyen", "Haddad", "Khan",
        "Novak", "Smith", "Lopez", "Dubois", "Tanaka", "Ali", "Sharma", "Costa", "Weber", "Brown"]
LOCATIONS = ["Mumbai", "Delhi", "Bangalore", "São Paulo", "Berlin", "London",
             "Los Angeles", "New York", "Dubai", "Seoul"]
RATE_TIERS = [("₹500–₹2,000", "₹50000–₹200000"), ("₹2,000–₹5,000", "₹200000–₹500000"),
              ("₹5,000–₹15,000", "₹500000–₹1500000"), ("₹15,000–₹50,000", "₹1500000–₹5000000")]
DELIVERABLES = ["static post", "reel", "story", "long-form video", "carousel",
                "live session", "blog article", "podcast mention", "youtube short"]


def make_creator(i: int, seed: int = 42) -> dict:
    rng = random.Random(seed + i)
    n1, n2 = rng.sample(NICHES, 2)
    plat = rng.choice(PLATFORMS)
    followers = max(1500, min(int(rng.lognormvariate(10.2, 1.1)), 2_000_000))
    er = round(rng.uniform(0.008, 0.07), 4)
    name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
    style = rng.choice(STYLES)
    past = sorted(rng.sample(CATS, rng.randint(1, 3)))
    loc = rng.choice(LOCATIONS)
    _, rate_inr = rng.choice(RATE_TIERS)
    dels = sorted(rng.sample(DELIVERABLES, rng.randint(2, 4)))
    bio = (f"{n1} & {n2} creator sharing {style}. "
           f"{rng.randint(2, 9)}y creating {plat} content for {rng.choice(AGES)} audience.")
    return {
        "creator_id": f"c{i:03d}",
        "name": name,
        "handle": "@" + name.lower().replace(" ", "_") + str(i),
        "platform": plat,
        "niche": sorted([n1, n2]),
        "bio": bio,
        "followers": followers,
        "avg_engagement_rate": er,
        "audience_age": rng.choice(AGES),
        "audience_geo": sorted(rng.sample(GEOS, rng.randint(1, 2))),
        "content_style": style,
        "past_brand_categories": past,
        "location": loc,
        "rate_range_inr": rate_inr,
        "deliverable_types": dels,
    }


def make_brand(j: int, seed: int = 42) -> dict:
    rng = random.Random(seed + j)
    cat = CATS[j % len(CATS)]
    niche_map = {"skincare": ["skincare", "beauty"], "fashion": ["fashion", "beauty"],
                 "food & beverage": ["food"], "travel": ["travel", "photography"],
                 "fintech": ["finance", "tech"], "fitness": ["fitness", "sports"],
                 "gaming": ["gaming", "tech"], "home & living": ["home-decor", "sustainability"],
                 "beauty": ["beauty", "skincare"], "consumer tech": ["tech", "photography"]}
    tone = TONES[j % len(TONES)]
    geo = sorted(rng.sample(["US", "UK", "DE", "global"], rng.randint(1, 2)))
    age = AGES[j % len(AGES)]
    brief = (f"Launch campaign for {cat} targeting {age} in {'/'.join(geo)}. "
             f"Looking for {', '.join(niche_map[cat])} creators with {tone} tone. "
             f"Goal: authentic {rng.choice(['reviews', 'tutorials', 'day-in-life', 'unboxings'])} that convert.")
    return {
        "brand_id": f"b{j:02d}",
        "brand_name": f"{cat.title().replace(' & ', '_')}Co {j}",
        "category": cat,
        "brief_text": brief,
        "target_niche": niche_map[cat],
        "target_geo": geo,
        "target_age": age,
        "budget_tier": rng.choice(["micro", "mid", "macro"]),
        "tone": tone,
    }


def main() -> None:
    random.seed(42)
    creators = [make_creator(i) for i in range(1, 501)]
    brands = [make_brand(j) for j in range(1, 51)]

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(os.path.join(DATA_DIR, "creators.json"), "w", encoding="utf-8") as f:
        json.dump(creators, f, indent=2, ensure_ascii=False)
    with open(os.path.join(DATA_DIR, "brands.json"), "w", encoding="utf-8") as f:
        json.dump(brands, f, indent=2, ensure_ascii=False)

    print(f"Generated {len(creators)} creators and {len(brands)} brands")
    print(f"  -> data/creators.json")
    print(f"  -> data/brands.json")


if __name__ == "__main__":
    main()
