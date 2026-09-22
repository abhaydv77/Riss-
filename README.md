# Riss — Creator/Brand Matching Pipeline

Vector retrieval + explainable scoring for matching brand briefs to creators.

## Structure

```
├── data/
│   ├── raw/              # creators_batch1..10.json, brands_batch1..5.json
│   ├── creators.json     # merged, 500
│   ├── brands.json       # merged, 50
│   └── labels.json       # manual labels, eval subset (10 brands x 10)
├── src/
│   ├── generate_merge.py # merges raw batches into final json
│   ├── embed_store.py    # embeds + stores in vector db (Chroma)
│   ├── retrieve.py       # vector search: brief -> top-k creators
│   ├── score_laya.py     # laya scoring on retrieved pairs
│   ├── score_llm.py      # llm baseline scoring (same pairs)
│   └── rank.py           # combines + outputs ranked results
├── eval/
│   ├── run_eval.py       # deepeval-based eval script
│   └── results/
│       └── comparison.csv# vector-only vs laya vs llm scores
├── db/                   # chroma persistent storage
├── requirements.txt
└── README.md
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional, for LLM scoring
```

Synthetic demo data (seed=42) is already in `data/raw/`; re-merge anytime with:

```bash
python -m src.generate_merge
```

## Pipeline

```bash
# 1. embed + store (Chroma persistent in ./db; TF-IDF fallback with --force-fallback)
python -m src.embed_store
# 2. retrieve
python -m src.retrieve --brand-id b01 --top-k 10
# 3a. laya score a pair
python -m src.score_laya --brand-id b01 --creator-id c001
# 3b. llm baseline score (uses OPENAI_API_KEY if set, else offline baseline)
python -m src.score_llm --brand-id b01 --creator-id c001
# 4. ranked results (methods: vector | laya | llm | hybrid)
python -m src.rank --brand-id b01 --top-k 20 --method hybrid
# 5. eval -> eval/results/comparison.csv
python -m eval.run_eval --top-k 10
```

Without heavy deps installed, retrieval/ranking/eval run on a zero-dependency
token-overlap scorer; install `requirements.txt` for Chroma + sentence-transformers
(`all-MiniLM-L6-v2`) and deepeval metrics.

## Scoring

- **vector**: cosine similarity of brief vs creator text, min-max normalized 0–100.
- **laya** (`src/score_laya.py`): explainable 0–100 =
  niche_overlap 40 + audience_fit 20 + engagement 15 + style_tone 15 + brand_affinity 10.
- **llm** (`src/score_llm.py`): OpenAI baseline (JSON `{total, rationale}`) or offline
  keyword-jaccard baseline when no key is set.
- **rank** final = `0.3*vector + 0.5*laya + 0.2*llm` (hybrid; see `--method`).

## Eval

`eval/run_eval.py` ranks top-k per brand for each method and reports
HitRate@K, MRR, NDCG@K vs `data/labels.json`, plus an AVG row per method.
Uses deepeval when installed, native IR metrics otherwise.
