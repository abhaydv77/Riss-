from __future__ import annotations

import json
import os
import time

import dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv.load_dotenv(os.path.join(ROOT, ".env"))

DB_PATH = os.path.join(ROOT, "db")
COLLECTION_NAME = "creators"
BRANDS_PATH = os.path.join(ROOT, "data", "brands.json")
OUT_PATH = os.path.join(ROOT, "eval", "results", "llm_scores_small.json")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "qwen/qwen3.8-27b")


def retrieve(brief_dict, k=5):
    import chromadb
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
            creators.append({"creator": creator_meta, "score": results["distances"][0][i]})
    return creators[:k]


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
    """Raised when a provider call fails or returns unparseable output."""


def score_gemini(gemini_client, brief, creator):
    from google.genai.types import GenerateContentConfig
    prompt = build_prompt(brief, creator)
    t0 = time.time()
    resp = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=GenerateContentConfig(
            temperature=0,
            max_output_tokens=256,
        ),
    )
    latency = time.time() - t0
    raw = resp.text or ""
    return _parse_response(raw, latency)


def score_groq(groq_client, brief, creator):
    prompt = build_prompt(brief, creator)
    t0 = time.time()
    resp = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=256,
    )
    latency = time.time() - t0
    raw = resp.choices[0].message.content or ""
    return _parse_response(raw, latency)


def _parse_response(raw, latency):
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
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    groq_api_key = os.environ.get("GROQ_API_KEY")
    missing = []
    if not gemini_api_key:
        missing.append("GEMINI_API_KEY")
    if not groq_api_key:
        missing.append("GROQ_API_KEY")
    if missing:
        raise SystemExit(
            f"Missing required env vars: {', '.join(missing)}. "
            "Both are required (Gemini primary, Groq fallback)."
        )

    from google import genai
    from google.genai import errors as genai_errors
    from groq import Groq
    gemini_client = genai.Client(api_key=gemini_api_key)
    groq_client = Groq(api_key=groq_api_key)

    with open(BRANDS_PATH) as f:
        brands = json.load(f)

    results = []
    failures = []
    provider_counts = {"gemini": 0, "groq": 0}

    for bi, brand in enumerate(brands, 1):
        pairs = retrieve(brand, k=5)
        for pi, r in enumerate(pairs, 1):
            creator = r["creator"]
            scored = None
            provider = None
            try:
                try:
                    scored = score_gemini(gemini_client, brand, creator)
                    provider = "gemini"
                    provider_counts["gemini"] += 1
                except genai_errors.APIError as e:
                    if e.code == 429:
                        try:
                            scored = score_groq(groq_client, brand, creator)
                            provider = "groq"
                            provider_counts["groq"] += 1
                        except LLMCallFailed:
                            raise
                    else:
                        raise LLMCallFailed(f"Gemini API error (code {e.code}): {e}")
            except LLMCallFailed as e:
                failures.append({
                    "brief_id": brand["brand_id"],
                    "creator_id": creator["creator_id"],
                    "error": str(e),
                })
                print(f"brief {bi}/{len(brands)} pair {pi}/{len(pairs)}: "
                      f"{creator['creator_id']} -> FAILED: {e}")
                continue

            scored["provider"] = provider
            results.append({
                "brief_id": brand["brand_id"],
                "creator_id": creator["creator_id"],
                **scored,
            })
            print(f"brief {bi}/{len(brands)} pair {pi}/{len(pairs)}: "
                  f"{creator['creator_id']} -> {scored['overall_fit']} "
                  f"({scored['latency_ms']}ms, {provider})")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nScored {len(results)} pairs -> {OUT_PATH}")
    print(f"Provider breakdown: gemini={provider_counts['gemini']}, groq={provider_counts['groq']}")
    if failures:
        fail_path = OUT_PATH.replace(".json", "_failures.json")
        with open(fail_path, "w", encoding="utf-8") as f:
            json.dump(failures, f, indent=2)
        print(f"{len(failures)} pairs FAILED and were skipped -> {fail_path}")
        print("Re-run or investigate these before trusting the eval numbers.")


if __name__ == "__main__":
    main()
