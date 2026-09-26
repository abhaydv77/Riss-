"""Centralized configuration for the retrieval layer."""
from __future__ import annotations

import os

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHROMA_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "chroma")
COLLECTION_NAME = "creators"
BATCH_SIZE = 20
