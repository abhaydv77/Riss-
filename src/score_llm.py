from __future__ import annotations

import json
import os
import time

import dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv.load_dotenv(os.path.join(ROOT, ".env"))

DB_PATH = os.path.join(ROOT, "db")
COLLECTION_NAME = "creators"
BRANDS_PATH = os.path.join(ROOT, "data", "small_brands.json")
OUT_PATH = os.path.join(ROOT, "eval", "results", "llm_scores_small.json")
MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")


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


# Same question schema as score_laya.py's build_questions(), so the two are
# directly comparable in eval — same inputs, same output shape.
def build_prompt(brief, creator):
    return f"""You are evaluating a brand-creator collaboration fit for an influencer
marketing platform. Answer based ONLY on the data given, be strict and honest.

BRAND: {brief.get('brand_name', '')}
Brief: {brief.get('brief_text', '')}
Target niche: {brief.get('target_niche', [])}
Target audience: {brief.get('target_age', '')} in {brief.get('target_geo', [])}
Budget tier: {brief.get('budget_tier', '')}

CREATOR: {creator.get('name', '')} (@{creator.get('handle', '')})
Niche: {creator.get('niche', [])}
Bio: {creator.get('bio', '')}
Audience: {creator.get('audience_age', '')} in {creator.get('audience_geo', [])}
Followers: {creator.get('followers', 0)}
Past brand categories: {creator.get('past_brand_categories', [])}

Answer these four questions and respond with ONLY this JSON, no other text:
{{
  "niche_match": true or false,
  "audience_match": true or false,
  "budget_fit": true or false,
  "overall_fit": "good" or "maybe" or "poor"
}}"""


class LLMCallFailed(Exception):
    """Raised when the Groq call fails or returns unparseable output.
    Deliberately NOT caught silently — a failed pair should be visible,
    not quietly replaced with a fake score."""


def llm_score(client, brief, creator):
    prompt = build_prompt(brief, creator)
    t0 = time.time()
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=256,
    )
    latency = time.time() - t0

    raw = resp.choices[0].message.content or ""
    try:
        start, end = raw.index("{"), raw.rindex("}") + 1
        data = json.loads(raw[start:end])
        niche_match = bool(data["niche_match"])
        audience_match = bool(data["audience_match"])
        budget_fit = bool(data["budget_fit"])
        overall_fit = str(data["overall_fit"]).lower()
        if overall_fit not in ("good", "maybe", "poor"):
            raise ValueError(f"unexpected overall_fit value: {overall_fit!r}")
    except (ValueError, KeyError, IndexError) as e:
        raise LLMCallFailed(f"could not parse response: {raw!r}") from e

    return {
        "niche_match": niche_match,
        "audience_match": audience_match,
        "budget_fit": budget_fit,
        "overall_fit": overall_fit,
        "latency_ms": round(latency * 1000, 1),
    }


def main():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise SystemExit(
            "GROQ_API_KEY not set. This script does not fall back to a fake "
            "score — set the key or don't run it yet."
        )

    from groq import Groq
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    

    with open(BRANDS_PATH) as f:
        brands = json.load(f)

    results = []
    failures = []
    for bi, brand in enumerate(brands, 1):
        pairs = retrieve(brand, k=5)
        for pi, r in enumerate(pairs, 1):
            creator = r["creator"]
            try:
                scored = llm_score(client, brand, creator)
                results.append({
                    "brief_id": brand["brand_id"],
                    "creator_id": creator["creator_id"],
                    **scored,
                })
                print(f"brief {bi}/{len(brands)} pair {pi}/{len(pairs)}: "
                      f"{creator['creator_id']} -> {scored['overall_fit']} "
                      f"({scored['latency_ms']}ms)")
            except LLMCallFailed as e:
                failures.append({
                    "brief_id": brand["brand_id"],
                    "creator_id": creator["creator_id"],
                    "error": str(e),
                })
                print(f"brief {bi}/{len(brands)} pair {pi}/{len(pairs)}: "
                      f"{creator['creator_id']} -> FAILED: {e}")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nScored {len(results)} pairs -> {OUT_PATH}")
    if failures:
        fail_path = OUT_PATH.replace(".json", "_failures.json")
        with open(fail_path, "w", encoding="utf-8") as f:
            json.dump(failures, f, indent=2)
        print(f"{len(failures)} pairs FAILED and were skipped -> {fail_path}")
        print("Re-run or investigate these before trusting the eval numbers.")


if __name__ == "__main__":
    main()