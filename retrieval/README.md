# Retrieval Module

The **retrieval layer** is responsible for converting brand briefs into semantically
similar creator candidates using local sentence-transformers embeddings and ChromaDB.

> **This is candidate generation only.** It does NOT make final matching decisions.
> That comes later with Laya.

---

## Folder Structure

```
retrieval/
├── __init__.py          # Public API exports
├── config.py            # Centralized configuration (model, paths)
├── embeddings.py        # Text builders for creators and brands
├── query_builder.py     # Converts brand briefs to retrieval queries
├── chroma_store.py      # Persistent ChromaDB storage and indexing
├── retrieve.py          # Core retrieve_creators() function
└── cli.py               # CLI interface for testing retrieval
```

---

## Module-by-Module Breakdown

### `config.py` — Centralized Configuration

Single source of truth for all retrieval-layer settings.

```python
EMBEDDING_MODEL = "all-MiniLM-L6-v2"    # Lightweight local embedding model
CHROMA_DB_DIR = "data/chroma"           # Persistent ChromaDB directory
COLLECTION_NAME = "creators"            # ChromaDB collection name
BATCH_SIZE = 20                         # Batch size for indexing
```

**Why centralized?** Changing the embedding model requires editing exactly
one line. The model name is never hard-coded across multiple files.

---

### `embeddings.py` — Text Document Builders

Converts structured JSON profiles into rich natural-language strings suitable
for embedding. Two functions:

#### `build_creator_text(creator: dict) -> str`

Takes a creator profile and produces a comprehensive natural-language document
that preserves all matching-relevant information:

```
Sarah Khan is a fitness creator.
Secondary niches include sports, wellness.
Certified CrossFit athlete and nutrition coach based in Mumbai...
Based in Mumbai, India.
Languages: Hindi, English.
Platforms: Instagram, YouTube.
Followers: 185,000. Engagement rate: 4.2%. Average views: 320,000.
Audience age range: 18-30. Audience gender: female: 72%, male: 28%.
Audience locations: India, UAE, Singapore.
Content types: workout, nutrition, healthy lifestyle.
Content style: energetic and motivational.
Rate card: ₹15,000–₹50,000.
Past brand categories: fitness, sports, health apps.
Interests: gym, running, yoga.
Posting frequency: 4-5 posts/week.
```

Fields captured for matching:
- **Identity** — name, bio
- **Niche** — primary and secondary
- **Location** — creator's base city/country
- **Language** — content languages
- **Platform** — where they post
- **Metrics** — followers, engagement rate, average views
- **Audience** — age range, gender distribution, geographic distribution
- **Content** — types, style
- **Commercial** — rate card, past brand categories, interests, posting frequency

#### `build_brief_text(brand: dict) -> str`

Takes a brand brief and produces a natural-language query that emphasizes
all matching criteria:

```
FitNova is a Fitness & Wellness brand launching 'Move Anywhere Campaign'.
Campaign goal: Drive awareness and sales of affordable home fitness equipment...
Product: Home workout equipment and resistance bands.
Target audience: Young Indian women aged 18-30...
Target locations: India, UAE, Singapore.
Required creator niches: fitness.
Preferred creator niches: fitness, nutrition, wellness, yoga.
Preferred content types: workout, nutrition, healthy lifestyle.
Preferred platforms: Instagram, YouTube.
Desired tone: energetic and motivational.
Mandatory requirements: must be based in India or South Asia...
Preferred creator traits: authentic, motivational, relatable, female-led.
Excluded creator traits: luxury-focused, male-dominated audience...
```

Fields captured for matching:
- **Brand identity** — name, industry, product, campaign title
- **Goal** — campaign goal, description
- **Target audience** — age range, gender, locations
- **Niche requirements** — required and preferred niches
- **Content requirements** — types, platforms, tone
- **Constraints** — mandatory requirements, preferred/excluded traits

---

### `query_builder.py` — Brand Query Builder

Converts a brand brief into a retrieval query string.

```python
def build_brand_query(brand: dict) -> str:
```

Currently delegates to `build_brief_text()`. This separation allows future
enhancements such as:
- Adding semantic weights to different query components
- Filtering query text based on brand-specific rules
- Augmenting with keyword expansion or synonym enrichment

**Important:** No arbitrary weights are hard-coded here. The retrieval stage
is purely semantic. Hard constraints and weighting will be handled by Laya.

---

### `chroma_store.py` — Persistent ChromaDB Storage

Handles all ChromaDB operations: initialization, indexing, and querying.

#### Key Functions

| Function | Purpose |
|---|---|
| `get_model()` | Loads the sentence-transformers model |
| `get_collection(rebuild=False)` | Gets or creates the ChromaDB collection |
| `add_creators(creators, model, collection, rebuild)` | Indexes creators with embeddings |
| `load_creators(path)` | Loads creators from `data/creators.json` |
| `load_brands(path)` | Loads brands from `data/brands.json` |
| `get_creator_by_id(collection, creator_id)` | Retrieves a single creator's metadata |

#### Metadata Sanitization

ChromaDB metadata only supports `str`, `int`, `float`, `bool`, `list`, or `None`.
Nested dicts (like `audience_gender_distribution`) are automatically serialized
to JSON strings by `_sanitize_metadata()` before storage, and deserialized by
`_deserialize_metadata()` when retrieved.

#### Dedup Safety

`add_creators()` checks existing IDs before inserting. Running the index build
repeatedly will not create duplicates.

```python
existing_ids = set(collection.get()["ids"]) if collection.count() > 0 else set()
new_creators = [c for c in creators if c["creator_id"] not in existing_ids]
```

#### Persistent Storage

The ChromaDB database lives at `data/chroma/` and persists across sessions.
The `chroma.sqlite3` file and its WAL files are gitignored.

---

### `retrieve.py` — Core Retrieval

The main entry point for retrieving creator candidates.

```python
def retrieve_creators(
    brand: dict,
    top_k: int = 10,
    model: SentenceTransformer | None = None,
    collection: chromadb.Collection | None = None,
) -> list[dict]:
```

**What it does:**
1. Converts the brand brief to a query string via `build_brand_query()`
2. Embeds the query using `all-MiniLM-L6-v2`
3. Queries ChromaDB for the top-K most similar creator embeddings
4. Returns results with `creator_id`, `name`, `distance`, and full `metadata`

**What it does NOT do:**
- Make good/maybe/poor decisions — that is Laya's job
- Apply filters or constraints — that comes later
- Rank creators — that comes later

**Return format:**

```python
[
    {
        "creator_id": "c031",
        "name": "Aarav Mehta",
        "distance": 0.3279,
        "metadata": {
            "primary_niche": "fitness",
            "location": "Bangalore",
            "followers": 155000,
            "platforms": ["youtube", "tiktok"],
            # ... all other creator fields
        }
    },
    ...
]
```

**Distance interpretation:**
- Lower distance = more similar
- Typical range: 0.0 (identical) to 1.0 (completely different)
- Cosine similarity distance via ChromaDB's `hnsw:space: cosine`

---

### `cli.py` — Command-Line Interface

Quick testing tool for retrieval:

```bash
# Search for creators matching brand b01, top 10 results
python retrieval/cli.py b01 --top-k 10

# Rebuild index first, then search
python retrieval/cli.py b03 --top-k 5 --rebuild
```

**Output:**
```
Brand: FitNova (b01)
Campaign: Move Anywhere Campaign
Industry: Fitness & Wellness
...

Top 5 retrieved creators:

  1. c031 — Aarav Mehta — distance: 0.3279 | niche: fitness | followers: 155,000 | location: Bangalore, India | platforms: youtube, tiktok
  2. c035 — Priya Nair — distance: 0.3820 | niche: fitness | followers: 135,000 | location: Chennai, India | platforms: youtube, instagram
  ...
```

---

### `__init__.py` — Public API

Exports all public functions for `from retrieval import *` usage:

```python
from retrieval import (
    get_model, get_collection, add_creators,
    load_creators, load_brands, get_creator_by_id,
    retrieve_creators,
    build_creator_text, build_brief_text,
    build_brand_query,
    EMBEDDING_MODEL, CHROMA_DB_DIR, COLLECTION_NAME,
)
```

---

## Data Flow

```
data/creators.json
        │
        ▼
┌──────────────────────┐
│  chroma_store.py     │
│  load_creators()     │
│  _sanitize_metadata()│
│  add_creators()      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  embeddings.py       │
│  build_creator_text()│
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  config.py           │
│  get_model()         │
│  all-MiniLM-L6-v2    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  ChromaDB            │
│  data/chroma/        │
│  collection: creators│
└──────────┬───────────┘
           │
           ▼
Brand Brief ──query_builder──▶ query text
        │
        ▼
   embeddings ──▶ ChromaDB query
        │
        ▼
   retrieve_creators() ──▶ Top-K candidates
        │
        ▼
   [Laya phase → next]
```

---

## Usage Examples

### Programmatic Usage

```python
from retrieval import retrieve_creators, load_brands, load_creators
from retrieval.chroma_store import get_collection, add_creators
from retrieval.config import EMBEDDING_MODEL

# Load data and build index (do once)
creators = load_creators()
brands = load_brands()
collection = get_collection(rebuild=True)

# Add creators (also do once)
from sentence_transformers import SentenceTransformer
model = SentenceTransformer(EMBEDDING_MODEL)
add_creators(creators, model=model, collection=collection)

# Retrieve for a brand
brand = brands[0]  # b01
results = retrieve_creators(brand, top_k=10)

for r in results:
    print(f"{r['creator_id']}: {r['name']} (distance: {r['distance']:.4f})")
```

### CLI Usage

```bash
# Rebuild index and search
python retrieval/cli.py b01 --top-k 10 --rebuild

# Search without rebuild
python retrieval/cli.py b05 --top-k 5
```

---

## Index Build

To rebuild the entire index from scratch:

```bash
python scripts/build_index.py --rebuild
```

Or without rebuild (skips already-indexed creators):

```bash
python scripts/build_index.py
```

Output:
```
Added 20/40 creators
Added 40/40 creators

Index built successfully.
  Number of creators indexed: 40
  Collection name: creators
  Embedding model: all-MiniLM-L6-v2
  Database location: retrieval/config.py (CHROMA_DB_DIR)
```

---

## Testing

```bash
python -m pytest tests/test_retrieval.py -v
```

Test coverage:
- **TestEmbeddings** — `build_creator_text` and `build_brief_text` include expected fields
- **TestChromaStore** — Adding creators, duplicate prevention
- **TestRetrieve** — Returns correct top_k, no duplicate IDs
- **TestIntegration** — Loads 40 creators, 10 brands, collection loads, unknown brand handling

---

## Important Notes

1. **Retrieval is candidate generation only.** It answers "which creators are
   semantically relevant?" — not "which creators should we pick?"

2. **No manual weights.** The query builder does not assign arbitrary weights
   to different fields. All matching is done through semantic embedding similarity.

3. **Distance is cosine distance.** Lower means more similar. Do not interpret
   distance thresholds as quality scores — that's Laya's job.

4. **Metadata is serialized.** Complex fields like `audience_gender_distribution`
   are stored as JSON strings in ChromaDB and deserialized on retrieval.

5. **Running `add_creators()` is safe to repeat.** It checks existing IDs and
   skips already-indexed creators.

6. **The embedding model is local.** `all-MiniLM-L6-v2` runs on CPU with no
   API calls. No internet connection needed after the model is downloaded.
