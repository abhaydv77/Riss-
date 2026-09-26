# Retrieval Baseline v0

## System

- **Embedding model:** all-MiniLM-L6-v2
- **Vector database:** ChromaDB (persistent, /Volumes/mac/Riss/data/chroma)
- **Number of brands:** 10
- **Number of creators:** 40
- **K:** 3
- **Ground-truth pairs:** 400

## Overall Metrics

| Metric | Value |
|---|---|
| Strict Precision@3 | 0.5000 |
| Relaxed Precision@3 | 0.7000 |
| Good Hit Rate@3 | 0.8000 |
| Good/Maybe Hit Rate@3 | 0.9000 |
| MRR@3 | 0.7000 |

## Per-Brand Results

| Brand | Rank 1 | Label | Rank 2 | Label | Rank 3 | Label | Good@3 | P@3 |
|---|---|---|---|---|---|---|---|---|
| FitNova | c20 | poor | c31 | poor | c37 | poor | 0 | 0.00 |
| GlowEssence | c05 | good | c15 | poor | c39 | poor | 1 | 0.33 |
| GameVault | c09 | good | c10 | poor | c33 | good | 2 | 0.67 |
| AthleVibe | c18 | good | c19 | poor | c06 | poor | 1 | 0.33 |
| MoneyWise | c29 | good | c16 | good | c14 | good | 3 | 1.00 |
| PurePlate | c12 | good | c35 | good | c40 | good | 3 | 1.00 |
| Elysian Travel | c28 | maybe | c13 | good | c22 | maybe | 1 | 0.33 |
| TinyNest | c21 | maybe | c30 | maybe | c15 | poor | 0 | 0.00 |
| NovaTech | c14 | good | c20 | good | c38 | good | 3 | 1.00 |
| VitalityCo | c24 | maybe | c34 | good | c26 | maybe | 1 | 0.33 |

## Observations

- **8 out of 10 brands** retrieved at least one good creator in Top-3.
- **2 out of 10 brands** retrieved no good creator in Top-3.
- **2 out of 10 brands** had all 3 retrieved creators labeled poor.
- **6 brands** had a good creator at rank 1.
- **1 brands** had no good creator but had at least one maybe creator in Top-3.

## Chroma Distances

Distance is cosine distance. Lower means more similar.

- **FitNova**: rank 1: 0.3235 (poor), rank 2: 0.3279 (poor), rank 3: 0.3682 (poor)
- **GlowEssence**: rank 1: 0.3135 (good), rank 2: 0.4082 (poor), rank 3: 0.4128 (poor)
- **GameVault**: rank 1: 0.4286 (good), rank 2: 0.4430 (poor), rank 3: 0.4640 (good)
- **AthleVibe**: rank 1: 0.3082 (good), rank 2: 0.4117 (poor), rank 3: 0.4386 (poor)
- **MoneyWise**: rank 1: 0.4563 (good), rank 2: 0.5240 (good), rank 3: 0.5283 (good)
- **PurePlate**: rank 1: 0.4788 (good), rank 2: 0.5143 (good), rank 3: 0.5152 (good)
- **Elysian Travel**: rank 1: 0.4480 (maybe), rank 2: 0.4510 (good), rank 3: 0.4594 (maybe)
- **TinyNest**: rank 1: 0.4928 (maybe), rank 2: 0.5096 (maybe), rank 3: 0.5711 (poor)
- **NovaTech**: rank 1: 0.4427 (good), rank 2: 0.4567 (good), rank 3: 0.4603 (good)
- **VitalityCo**: rank 1: 0.4260 (maybe), rank 2: 0.4925 (good), rank 3: 0.4962 (maybe)

