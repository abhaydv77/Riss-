"""Brand query builder: converts brand briefs into retrieval queries."""
from __future__ import annotations

from retrieval.config import EMBEDDING_MODEL
from retrieval.embeddings import build_brief_text


def build_brand_query(brand: dict) -> str:
    """Convert a brand brief into a natural-language retrieval query.

    Emphasizes campaign goal, target audience, niche, location,
    platform, content type, and creator traits.

    Does NOT manually encode arbitrary weights.
    Keeps the retrieval stage semantic.
    """
    return build_brief_text(brand)


__all__ = ["build_brand_query"]
