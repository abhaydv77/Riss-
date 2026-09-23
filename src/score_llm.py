from __future__ import annotations

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "db")
COLLECTION_NAME = "creators"
BRANDS_PATH = os.path.join(ROOT, "data", "small_brands.json")
OUT_PATH = os.path.join(ROOT, "llm_scores_small.json")
MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")
_TOKEN = re.compile(r"[a-z0-9]+")


def retrieve(brief_dict, k=5):
    import chromadb
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    query_text = brief_dict.get("brief_text", "")
    if not query_text:
        niche = " ".join(brief_dict.get("target_niche", []))
        geo = " ".join(brief_dict.get("target_geo", []))
        query_text = f"{niche} {brief_dict.get('target_age', '')} {geo} {brief_dict.get('tone', '')}".strip()
    results = collection.query(query_texts=[query_text], n_results=k)
    creators = []
    for i in range(len(results["ids"][0])):
        creators.append({"creator": results["metadatas"][0][i], "score": results["distances"][0][i]})
    return creators


def _tok(s):
    return set(_TOKEN.findall(s.lower()))


def offline_score(brand, creator):
    bt = _tok(f"{brand.get('brand_name')} {brand.get('category')} {brand.get('brief_text')} {' '.join(brand.get('target_niche', []))} {' '.join(brand.get('target_geo', []))} {brand.get('tone', '')}")
    ct = _tok(f"{creator.get('name')} {creator.get('handle')} {creator.get('bio')} {' '.join(creator.get('niche', []))} {creator.get('content_style')} {creator.get('past_brand_categories')}")
    j = len(bt & ct) / max(1, len(bt | ct))
    total = round(100 * (0.15 + 0.85 * min(1.0, j * 4)), 2)
    return total


def llm_score(brand, creator):
    if os.environ.get("OPENAI_API_KEY"):
        try:
            from openai import OpenAI
            client = OpenAI()
            prompt = (
                f"You are ranking influencer-brand fit. Score 0-100.\n"
                f"BRAND: {brand.get('brand_name')} ({brand.get('category')}): {brand.get('brief_text')}\n"
                f"CREATOR: {creator.get('name')} @{creator.get('handle')}: {creator.get('bio')}\n"
                f"Reply ONLY with JSON like {{\"total\": 82}}"
            )
            resp = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": prompt}], temperature=0)
            raw = resp.choices[0].message.content or "{}"
            data = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
            return float(data.get("total", 50.0))
        except Exception:
            pass
    return offline_score(brand, creator)


def main():
    with open(BRANDS_PATH) as f:
        brands = json.load(f)

    scores = []
    for brand in brands:
        results = retrieve(brand, k=5)
        for r in results:
            creator = r["creator"]
            score = llm_score(brand, creator)
            scores.append({
                "brief_id": brand["brand_id"],
                "creator_id": creator["creator_id"],
                "llm_score": score,
            })

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2)

    print(f"Scored {len(scores)} pairs -> {OUT_PATH}")


if __name__ == "__main__":
    main()
