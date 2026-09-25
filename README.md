# Guapd Smart Feed

**Research prototype** for a creator-brand matching system.

## Current Phase

This is the **foundation phase**. Only data, vector retrieval, and ChromaDB are in place.

Future phases will add:
- Laya decision gate (KEEP / UNCERTAIN / DROP)
- LLM fallback for uncertain cases
- Final ranked creator feed
- Evaluation and fine-tuning

## Architecture

```
Brand Brief
    ↓
Text conversion
    ↓
Sentence-transformer embedding
    ↓
ChromaDB similarity search
    ↓
Top-K candidate creators
```

The retrieval layer is isolated from the future Laya and LLM layers.

## Folder Structure

```
guapd-smart-feed/
│
├── data/
│   ├── brands.json          # Brand campaign briefs
│   └── creators.json        # Creator profiles
│
├── retrieval/
│   ├── __init__.py
│   ├── embeddings.py        # Text conversion for creators and brands
│   ├── chroma_store.py      # Persistent ChromaDB storage
│   └── retrieve.py          # Vector search: brief -> top-K creators
│
├── scripts/
│   ├── generate_data.py     # Generate synthetic data
│   └── build_index.py       # Build the ChromaDB index
│
├── tests/
│   └── test_retrieval.py    # Retrieval layer tests
│
├── requirements.txt
├── README.md
└── .gitignore
```

## What Retrieval Does

1. Convert a brand brief into a searchable text string
2. Embed it with `all-MiniLM-L6-v2`
3. Query ChromaDB for the most similar creator embeddings
4. Return top-K creators with metadata and similarity scores

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Generate data
python scripts/generate_data.py

# Build the index
python scripts/build_index.py

# Run tests
python -m unittest tests/test_retrieval.py
```

## Data Contract

### `creators.json`
Each creator has: `creator_id`, `name`, `handle`, `platform`, `niche`, `bio`,
`followers`, `avg_engagement_rate`, `audience_age`, `audience_geo`,
`content_style`, `past_brand_categories`, `location`, `rate_range_inr`,
`deliverable_types`.

### `brands.json`
Each brand has: `brand_id`, `brand_name`, `category`, `brief_text`,
`target_niche`, `target_geo`, `target_age`, `budget_tier`, `tone`.

## Notes

This is a clean research prototype. No frontend, no agent framework, no LLM
judge, no Laya gate. Just data + embeddings + vector retrieval.
