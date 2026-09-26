"""Build the ChromaDB index from data/creators.json."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from retrieval.chroma_store import add_creators, load_creators, get_collection


def main() -> None:
    rebuild = "--rebuild" in sys.argv
    creators = load_creators()
    collection = get_collection(rebuild=rebuild)

    add_creators(creators, collection=collection, rebuild=rebuild)

    model_name = "all-MiniLM-L6-v2"
    print(f"\nIndex built successfully.")
    print(f"  Number of creators indexed: {collection.count()}")
    print(f"  Collection name: {collection.name}")
    print(f"  Embedding model: {model_name}")
    print(f"  Database location: retrieval/config.py (CHROMA_DB_DIR)")


if __name__ == "__main__":
    main()
