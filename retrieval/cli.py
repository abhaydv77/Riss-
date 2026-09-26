"""CLI interface for testing creator retrieval."""
from __future__ import annotations

import argparse
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from retrieval.chroma_store import load_brands
from retrieval.retrieve import retrieve_creators


def main() -> None:
    parser = argparse.ArgumentParser(description="Retrieve top-K creators for a brand brief.")
    parser.add_argument("brand_id", help="Brand ID to search for (e.g., b01)")
    parser.add_argument("--top-k", type=int, default=10, help="Number of results to return")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild the index before searching")
    args = parser.parse_args()

    from retrieval.chroma_store import get_collection
    if args.rebuild:
        from retrieval.chroma_store import add_creators, load_creators
        from retrieval.config import EMBEDDING_MODEL
        from sentence_transformers import SentenceTransformer

        creators = load_creators()
        collection = get_collection(rebuild=True)
        model = SentenceTransformer(EMBEDDING_MODEL)
        add_creators(creators, model=model, collection=collection, rebuild=True)

    brands = load_brands()
    brand = None
    for b in brands:
        if b["brand_id"] == args.brand_id:
            brand = b
            break

    if brand is None:
        available = ", ".join(b["brand_id"] for b in brands)
        print(f"Error: Brand ID '{args.brand_id}' not found.")
        print(f"Available brand IDs: {available}")
        sys.exit(1)

    print(f"\nBrand: {brand['brand_name']} ({args.brand_id})")
    print(f"Campaign: {brand['campaign_title']}")
    print(f"Industry: {brand['industry']}")
    print(f"Product: {brand['product']}")
    print(f"Target audience: {brand['target_audience']}")
    print(f"Required niches: {', '.join(brand['required_creator_niches'])}")
    print(f"Preferred niches: {', '.join(brand['preferred_creator_niches'])}")
    print(f"Target locations: {', '.join(brand['target_locations'])}")
    print(f"Platforms: {', '.join(brand['platforms'])}")
    print(f"\nTop {args.top_k} retrieved creators:\n")

    results = retrieve_creators(brand, top_k=args.top_k)
    for i, r in enumerate(results, 1):
        meta = r["metadata"]
        print(
            f"  {i}. {r['creator_id']} — {r['name']} — distance: {r['distance']:.4f}"
            f" | niche: {meta.get('primary_niche', '')}"
            f" | followers: {meta.get('followers', 0):,}"
            f" | location: {meta.get('location', '')}"
            f" | platforms: {', '.join(meta.get('platforms', []))}"
        )

    print()


if __name__ == "__main__":
    main()
