"""Build the ChromaDB index from data/creators.json."""
from __future__ import annotations

import os
from retrieval.chroma_store import add_creators, load_creators, get_collection


def main() -> None:
    rebuild = "--rebuild" in __import__("sys").argv
    creators = load_creators()
    collection = get_collection(rebuild=rebuild)
    add_creators(creators, collection=collection, rebuild=rebuild)
    print("Index built successfully.")


if __name__ == "__main__":
    main()
