# Guapd Smart Feed

**Research prototype** for a creator-brand matching system.

## Current Phase

**Phase 1: Data Generation + Embeddings + ChromaDB Retrieval**

This is the foundation phase. Only data, vector retrieval, and ChromaDB are in place.

Future phases will add:
- Laya decision gate (KEEP / UNCERTAIN / DROP)
- LLM fallback for uncertain cases
- Final ranked creator feed
- Evaluation and fine-tuning

## Architecture

```
Brand Brief
    ↓
Query Builder
    ↓
Embedding Model (all-MiniLM-L6-v2)
    ↓
ChromaDB (cosine similarity)
    ↓
Top-K Candidate Creators
```

### Important

Vector retrieval is **candidate generation**. It is NOT the final creator-brand matching decision.

The full pipeline will be:

```
Top-K Candidates
    ↓
Laya (decision gate)
    ↓
KEEP / UNCERTAIN / DROP
    ↓
LLM fallback (for UNCERTAIN cases)
    ↓
Ranking
    ↓
Final Feed
```

The retrieval layer is isolated from the Laya and LLM layers.

## Folder Structure

```
guapd-smart-feed/
│
├── data/
│   ├── brands.json              # 10 brand campaign briefs
│   ├── creators.json            # 40 creator profiles
│   └── chroma/                  # Persistent ChromaDB database (gitignored)
│
├── retrieval/
│   ├── __init__.py
│   ├── config.py                # Centralized model and path configuration
│   ├── embeddings.py            # Rich text builders for creators and brands
│   ├── query_builder.py         # Converts brand briefs to retrieval queries
│   ├── chroma_store.py          # Persistent ChromaDB storage and indexing
│   ├── retrieve.py              # Vector search: brief → top-K creators
│   ├── cli.py                   # CLI for testing retrieval
│   └── __init__.py
│
├── scripts/
│   ├── generate_data.py         # Generate synthetic data
│   └── build_index.py           # Build the ChromaDB index
│
├── tests/
│   └── test_retrieval.py        # Retrieval layer tests
│
├── requirements.txt
├── README.md
└── .gitignore
```

## What Retrieval Does

1. Convert a brand brief into a rich searchable text string
2. Embed it with `all-MiniLM-L6-v2` (local, lightweight)
3. Query ChromaDB for the most similar creator embeddings
4. Return top-K creators with metadata and cosine distance

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Generate data
python scripts/generate_data.py

# Build the index
python scripts/build_index.py

# Or rebuild from scratch
python scripts/build_index.py --rebuild

# Test retrieval for a specific brand
python retrieval/cli.py b01 --top-k 10

# Run tests
python -m pytest tests/test_retrieval.py -v
```

## Data Contract

### `creators.json` (40 creators)
Each creator has: `creator_id`, `name`, `primary_niche`, `secondary_niches`, `bio`,
`location`, `languages`, `platforms`, `followers`, `engagement_rate`,
`average_views`, `audience_age_range`, `audience_gender_distribution`,
`audience_locations`, `content_types`, `content_style`, `rate_card`,
`past_brand_categories`, `interests`, `posting_frequency`.

The dataset includes realistic variation:
- **Obvious strong matches**: correct niche, audience, location, platform
- **Obvious poor matches**: wrong niche, wrong audience, wrong geography
- **Ambiguous matches**: partially aligned but not a clear fit
- **Budget mismatches**: creator too expensive for the brand
- **Size mismatches**: creator too small or too large
- **Platform mismatches**: brand needs TikTok but creator only has a blog

### `brands.json` (10 brands)
Each brand has: `brand_id`, `brand_name`, `industry`, `product`, `campaign_title`,
`campaign_goal`, `campaign_description`, `target_audience`, `target_age_range`,
`target_gender`, `target_locations`, `required_creator_niches`,
`preferred_creator_niches`, `creator_size_preference`, `minimum_followers`,
`maximum_followers`, `budget`, `currency`, `content_types`, `platforms`,
`tone`, `mandatory_requirements`, `preferred_traits`, `excluded_traits`.

## Data Generation Details

The synthetic dataset is designed like a real creator-brand marketplace:

- Fitness brands match with fitness creators, lifestyle creators, gaming creators,
  beauty creators — plus creators who fit niche but not audience, audience but
  not niche, or everything except budget.
- Beauty brands have similar variety across niches, geographies, and audience sizes.
- Gaming, tech, food, travel, fashion, parenting brands each have their own
  spread of matching and non-matching creators.

## Notes

This is a clean research prototype. No frontend, no agent framework, no LLM
judge, no Laya gate. Just data + embeddings + vector retrieval.
