from __future__ import annotations

import json
import os
import chromadb

BRANDS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "brands.json")
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db")
COLLECTION_NAME = "creators"


def retrieve(brief_dict, k=5):
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    query_text = brief_dict.get("brief_text", "")
    if not query_text:
        niche = " ".join(brief_dict.get("target_niche", []))
        geo = " ".join(brief_dict.get("target_geo", []))
        query_text = f"{niche} {brief_dict.get('target_age', '')} {geo} {brief_dict.get('tone', '')}".strip()

    target_geo = set(brief_dict.get("target_geo", []))
    results = collection.query(query_texts=[query_text], n_results=20)

    creators = []
    for i in range(len(results["ids"][0])):
        creator_meta = results["metadatas"][0][i]
        creator_geo = set(creator_meta.get("audience_geo", []))
        if creator_geo & target_geo:
            creators.append({
                "creator": creator_meta,
                "score": results["distances"][0][i],
            })

    return creators[:k]


if __name__ == "__main__":
    with open(BRANDS_PATH) as f:
        brands = json.load(f)

    brief = brands[0]
    results = retrieve(brief, k=5)

    print(f"Results for {brief['brand_id']} ({brief['brand_name']}):")
    for r in results:
        c = r["creator"]
        print(f"  {c['creator_id']} {c['name']} ({c['handle']}) - score: {r['score']:.4f}")
