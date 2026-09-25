"""Persistent ChromaDB storage for creator embeddings."""
from __future__ import annotations

import json
import os
from typing import Literal

import chromadb
from sentence_transformers import SentenceTransformer

from .embeddings import build_creator_text

MODEL_NAME = "all-MiniLM-L6-v2"
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db")
COLLECTION_NAME = "creators"


def get_model() -> SentenceTransformer:
    """Load the sentence-transformers embedding model."""
    return SentenceTransformer(MODEL_NAME)


def get_collection(rebuild: bool = False) -> chromadb.Collection:
    """Get or create the ChromaDB collection for creators.

    Args:
        rebuild: If True, delete the existing collection first.
    """
    client = chromadb.PersistentClient(path=DB_DIR)
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


def add_creators(
    creators: list[dict],
    model: SentenceTransformer | None = None,
    collection: chromadb.Collection | None = None,
    rebuild: bool = False,
) -> None:
    """Add creators to the collection with pre-computed embeddings.

    Stores full creator metadata alongside embeddings.
    """
    if collection is None:
        collection = get_collection(rebuild=rebuild)
    if model is None:
        model = get_model()

    for i in range(0, len(creators), 20):
        batch = creators[i : i + 20]
        ids = [c["creator_id"] for c in batch]
        texts = [build_creator_text(c) for c in batch]
        embeddings = model.encode(texts, convert_to_numpy=True).tolist()
        metadatas = [{k: v for k, v in c.items()} for c in batch]
        collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        print(f"Added {min(i + 20, len(creators))}/{len(creators)} creators")


def load_creators(path: str | None = None) -> list[dict]:
    """Load creators from a JSON file."""
    if path is None:
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "creators.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)
