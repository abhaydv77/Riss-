from __future__ import annotations

import argparse
import json
import os

import chromadb
from sentence_transformers import SentenceTransformer

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "creators.json")
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db")
MODEL_NAME = "all-MiniLM-L6-v2"
COLLECTION_NAME = "creators"


def build_text(creator):
    niche = " ".join(creator.get("niche", []))
    audience_age = creator.get("audience_age", "")
    audience_geo = creator.get("audience_geo", [])
    audience_geo_str = ", ".join(audience_geo)
    audience = f"{audience_age} {audience_geo_str}".strip()
    past_brands = " ".join(creator.get("past_brand_categories", []))
    deliverable_types = " ".join(creator.get("deliverable_types", []))
    text = f"{niche} {audience} {past_brands} {deliverable_types}".strip()
    text += f" audience in {audience_geo_str}"
    return text.strip()


def main():
    with open(DATA_PATH) as f:
        creators = json.load(f)

    client = chromadb.PersistentClient(path=DB_PATH)
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    model = SentenceTransformer(MODEL_NAME)

    batch_size = 20
    for i in range(0, len(creators), batch_size):
        batch = creators[i : i + batch_size]
        texts = [build_text(c) for c in batch]
        embeddings = model.encode(texts)

        ids = [c["creator_id"] for c in batch]
        metadatas = [{**{k: v for k, v in c.items()}, "audience_geo_str": ", ".join(c.get("audience_geo", []))} for c in batch]
        documents = texts

        collection.add(
            ids=ids,
            embeddings=embeddings.tolist(),
            metadatas=metadatas,
            documents=documents,
        )

        print(f"Embedded {min(i + batch_size, len(creators))}/{len(creators)} creators")

    print(f"Done. Total: {len(creators)} creators in collection '{COLLECTION_NAME}'.")


if __name__ == "__main__":
    main()
