"""Persistent ChromaDB storage for creator embeddings."""
from __future__ import annotations

import json
import os
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer

from retrieval.config import CHROMA_DB_DIR, COLLECTION_NAME, EMBEDDING_MODEL, BATCH_SIZE
from retrieval.embeddings import build_creator_text


def get_model() -> SentenceTransformer:
    """Load the sentence-transformers embedding model."""
    return SentenceTransformer(EMBEDDING_MODEL)


def get_collection(rebuild: bool = False) -> chromadb.Collection:
    """Get or create the ChromaDB collection for creators.

    Args:
        rebuild: If True, delete the existing collection first.
    """
    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    if rebuild:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
        embedding_function=None,
    )


def _sanitize_metadata(creator: dict) -> dict[str, Any]:
    """Sanitize creator data for ChromaDB metadata.

    Nested dicts and complex types are serialized as JSON strings
    since ChromaDB metadata only supports str, int, float, bool, list, or None.
    """
    sanitized = {}
    for k, v in creator.items():
        if isinstance(v, (dict, list)):
            sanitized[k] = json.dumps(v)
        elif isinstance(v, (int, float, str, bool)) or v is None:
            sanitized[k] = v
        else:
            sanitized[k] = str(v)
    return sanitized


def add_creators(
    creators: list[dict],
    model: SentenceTransformer | None = None,
    collection: chromadb.Collection | None = None,
    rebuild: bool = False,
) -> None:
    """Add creators to the collection with pre-computed embeddings.

    Stores full creator metadata alongside embeddings.
    Skips creators already indexed by creator_id.
    """
    if collection is None:
        collection = get_collection(rebuild=rebuild)
    if model is None:
        model = get_model()

    existing_ids = set(collection.get()["ids"]) if collection.count() > 0 else set()

    new_creators = [c for c in creators if c["creator_id"] not in existing_ids]
    skipped = len(creators) - len(new_creators)

    if skipped > 0:
        print(f"Skipped {skipped} already-indexed creators.")

    if not new_creators:
        print("All creators already indexed. Nothing to add.")
        return

    for i in range(0, len(new_creators), BATCH_SIZE):
        batch = new_creators[i : i + BATCH_SIZE]
        ids = [c["creator_id"] for c in batch]
        texts = [build_creator_text(c) for c in batch]
        embeddings = model.encode(texts, convert_to_numpy=True).tolist()
        metadatas = [_sanitize_metadata(c) for c in batch]
        collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        print(f"Added {min(i + BATCH_SIZE, len(new_creators))}/{len(new_creators)} creators")


def load_creators(path: str | None = None) -> list[dict]:
    """Load creators from a JSON file."""
    if path is None:
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "creators.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_brands(path: str | None = None) -> list[dict]:
    """Load brands from a JSON file."""
    if path is None:
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "brands.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _deserialize_metadata(metadata: dict) -> dict:
    """Deserialize JSON strings in ChromaDB metadata back to original types."""
    result = {}
    for k, v in metadata.items():
        if isinstance(v, str):
            try:
                result[k] = json.loads(v)
            except (json.JSONDecodeError, ValueError):
                result[k] = v
        else:
            result[k] = v
    return result


def get_creator_by_id(collection: chromadb.Collection, creator_id: str) -> dict | None:
    """Retrieve a single creator's metadata by ID."""
    results = collection.get(ids=[creator_id])
    if results.get("metadatas") and results["metadatas"]:
        return _deserialize_metadata(results["metadatas"][0])
    return None


__all__ = ["get_model", "get_collection", "add_creators", "load_creators", "load_brands", "get_creator_by_id"]
