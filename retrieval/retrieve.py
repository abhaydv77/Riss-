"""Vector retrieval: brand brief -> top-K creators."""
from __future__ import annotations

import chromadb
from sentence_transformers import SentenceTransformer

from retrieval.config import CHROMA_DB_DIR, COLLECTION_NAME, EMBEDDING_MODEL
from retrieval.embeddings import build_brief_text
from retrieval.query_builder import build_brand_query
from retrieval.chroma_store import _deserialize_metadata


def retrieve_creators(
    brand: dict,
    top_k: int = 10,
    model: SentenceTransformer | None = None,
    collection: chromadb.Collection | None = None,
) -> list[dict]:
    """Retrieve top-K creator candidates for a brand brief.

    Converts the brand brief into a natural-language query, embeds it,
    and queries ChromaDB for the most similar creators.

    Args:
        brand: A brand brief dict with campaign details, target audience, etc.
        top_k: Number of top results to return.
        model: Optional pre-loaded sentence-transformers model.
        collection: Optional pre-loaded ChromaDB collection.

    Returns:
        List of dicts with creator_id, name, distance, and metadata.
    """
    if collection is None:
        client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
    if model is None:
        model = SentenceTransformer(EMBEDDING_MODEL)

    query_text = build_brand_query(brand)
    query_embedding = model.encode([query_text], convert_to_numpy=True).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
    )

    creators = []
    for i in range(len(results["ids"][0])):
        creator_id = results["ids"][0][i]
        raw_metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
        metadata = _deserialize_metadata(raw_metadata)
        distance = float(results["distances"][0][i]) if results.get("distances") else 0.0
        creators.append({
            "creator_id": creator_id,
            "name": metadata.get("name", ""),
            "distance": distance,
            "metadata": metadata,
        })

    return creators


__all__ = ["retrieve_creators"]
