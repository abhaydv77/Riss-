"""Vector retrieval: brand brief -> top-K creators."""
from __future__ import annotations

from typing import Literal

import chromadb
from sentence_transformers import SentenceTransformer

from .embeddings import build_brief_text, build_creator_text
from .chroma_store import DB_DIR, COLLECTION_NAME, get_model


def retrieve(
    brand: dict,
    k: int = 5,
    model: SentenceTransformer | None = None,
    collection: chromadb.Collection | None = None,
) -> list[dict]:
    """Retrieve top-K creators for a brand brief.

    Args:
        brand: A brand brief dict with brief_text, target_niche, etc.
        k: Number of top results to return.
        model: Optional pre-loaded sentence-transformers model.
        collection: Optional pre-loaded ChromaDB collection.

    Returns:
        List of dicts with creator metadata and vector_score.
    """
    if collection is None:
        client = chromadb.PersistentClient(path=DB_DIR)
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
    if model is None:
        model = get_model()

    query_text = build_brief_text(brand)
    query_embedding = model.encode([query_text], convert_to_numpy=True).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=k,
    )

    creators = []
    for i in range(len(results["ids"][0])):
        score = float(results["distances"][0][i]) if results.get("distances") else 0.0
        creators.append({
            "creator_id": results["ids"][0][i],
            "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
            "document": results["documents"][0][i] if results.get("documents") else "",
            "vector_score": score,
        })

    return creators
