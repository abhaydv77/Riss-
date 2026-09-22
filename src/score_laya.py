import json
import os
import time

import laya

BRANDS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "brands.json")
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db")
COLLECTION_NAME = "creators"


def retrieve(brief_dict, k=15):
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


# Question schema defined once, reused for every pair — don't rebuild inside the hot loop.
def build_questions(brief, creator):
    return {
        "niche_match": {
            "type": "noul",
            "instructions": (
                f"Is the creator's niche a match for the brand's target niche? "
                f"Brand niche: {brief.get('target_niche', [])}, creator niche: {creator.get('niche', [])}"
            ),
        },
        "audience_match": {
            "type": "noul",
            "instructions": (
                f"Is the creator's audience a match for the brand's target audience? "
                f"Brand targets {brief.get('target_age', '')} in {brief.get('target_geo', [])}, "
                f"creator audience is {creator.get('audience_age', '')} in {creator.get('audience_geo', [])}"
            ),
        },
        "budget_fit": {
            "type": "noul",
            "instructions": (
                f"Does the creator fit the brand's budget tier? "
                f"Brand budget tier: {brief.get('budget_tier', '')}, creator followers: {creator.get('followers', 0)}"
            ),
        },
        "overall_fit": {
            "type": "choice",
            "instructions": "What is the overall fit between this creator and the brand?",
            "criteria": {
                "good": "Strong fit across all dimensions",
                "maybe": "Partial fit, some gaps",
                "poor": "Poor fit",
            },
        },
    }


def score_laya(agent, brief, creator):
    """agent must be a pre-loaded laya.load(...) object — never load inside this function."""
    state = {
        "brand_name": brief.get("brand_name", ""),
        "brief_text": brief.get("brief_text", ""),
        "creator_name": creator.get("name", ""),
        "creator_handle": creator.get("handle", ""),
        "creator_niche": creator.get("niche", []),
        "creator_audience_age": creator.get("audience_age", ""),
        "creator_audience_geo": creator.get("audience_geo", []),
        "past_brand_categories": creator.get("past_brand_categories", []),
        "content_style": creator.get("content_style", ""),
    }
    questions = build_questions(brief, creator)

    t0 = time.time()
    result = agent.predict(state, questions)
    latency = time.time() - t0

    return result, latency


if __name__ == "__main__":
    with open(BRANDS_PATH) as f:
        brands = json.load(f)

    brief = brands[0]

    # Load ONCE, outside any loop. This is the ~76s cost — it should happen exactly once per process.
    t_load = time.time()
    agent = laya.load("convaiinnovations/laya")
    print(f"model loaded in {time.time() - t_load:.1f}s")

    pairs = retrieve(brief, k=15)

    total_latency = 0.0
    for pair in pairs:
        creator = pair["creator"]
        result, latency = score_laya(agent, brief, creator)
        total_latency += latency

        noul_scores = {
            "niche_match": result["answers"]["niche_match"]["noul"],
            "audience_match": result["answers"]["audience_match"]["noul"],
            "budget_fit": result["answers"]["budget_fit"]["noul"],
        }
        overall = result["answers"]["overall_fit"]["choice"]

        print(
            f"{creator['creator_id']} {creator['name']}: "
            f"noul={noul_scores} overall={overall} "
            f"latency={latency*1000:.1f}ms"
        )

    print(f"\nTotal latency: {total_latency:.3f}s for {len(pairs)} pairs "
          f"(avg {total_latency/len(pairs)*1000:.1f}ms/pair)")