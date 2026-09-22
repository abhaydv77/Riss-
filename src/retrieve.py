import json
import os
import chromadb

BRANDS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "brands.json")
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db")
COLLECTION_NAME = "creators"


def retrieve(brief_dict, k=15):
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    query_text = brief_dict.get("brief_text", "")
    if not query_text:
        niche = " ".join(brief_dict.get("target_niche", []))
        geo = " ".join(brief_dict.get("target_geo", []))
        query_text = f"{niche} {brief_dict.get('target_age', '')} {geo} {brief_dict.get('tone', '')}".strip()

    results = collection.query(
        query_texts=[query_text],
        n_results=k,
    )

    creators = []
    for i in range(len(results["ids"][0])):
        creators.append({
            "creator": results["metadatas"][0][i],
            "score": results["distances"][0][i],
        })

    return creators


if __name__ == "__main__":
    with open(BRANDS_PATH) as f:
        brands = json.load(f)

    brief = brands[0]
    results = retrieve(brief, k=15)

    print(f"Results for {brief['brand_id']} ({brief['brand_name']}):")
    for r in results:
        c = r["creator"]
        print(f"  {c['creator_id']} {c['name']} ({c['handle']}) - score: {r['score']:.4f}")
