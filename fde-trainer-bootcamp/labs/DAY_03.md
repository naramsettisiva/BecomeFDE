# Day 03 — Embeddings and Vector Search, Built by Hand

**Thu Aug 27, 2026** · Week 1 · Maps to: **Module 01 — Retrieval Foundations** · Backend: **local** · Est. cost: **$0.00–0.50**

> **Before you start — read `learn/DAY_03_LEARN.md` (1:15).**
> Embeddings, distance metrics, chunking, approximate indexes. The lab below assumes it and does not re-explain it.


---

## Why today matters

**FDE lens.** Every failing RAG system you will be parachuted into fails at retrieval,
not generation. The model is rarely the problem; the chunk it never saw is. To debug
that in front of a client you need to actually understand what a vector index is doing,
not just which method to call.

**Trainer lens.** "Embeddings are like a map of meaning" is the single laziest sentence
in AI education. Today you earn a better explanation by implementing the thing. A
trainer who has written cosine similarity in numpy can answer "why did it return that?"
A trainer who has only called `.similarity_search()` cannot.

**Rule of the day: no vector database until 3:00.** You use numpy.

---

## Objectives

1. Compute embeddings, inspect their geometry, and explain dimensionality, normalisation, and cosine vs. dot vs. Euclidean.
2. Implement brute-force k-NN search from scratch and get correct results on the freight corpus.
3. Demonstrate — with your own numbers — three concrete failure modes of pure dense retrieval.
4. Explain HNSW well enough to say *why* it's approximate and what you trade for the speed.

---

## Schedule (5:00)

| Block | Time | What |
|---|---|---|
| 0 | 0:30 | Warm-up |
| 1 | 1:15 | **Learn** — `learn/DAY_03_LEARN.md` |
| 2 | 2:15 | Lab: `minivector.py` from scratch, then Chroma, then compare |
| 3 | 0:30 | Teach-back #3 |
| 4 | 0:30 | Ship + retro |

---

## Block 0 — Warm-up (0:30)

Closed book:

1. Name the three levels of structured output and one failure mode of each.
2. Why does `asyncio.gather` need `return_exceptions=True` in an eval harness?
3. Which HTTP status codes should you retry, and which are a trap?
4. From Day 1: what makes an LLM failure "silent"?

Then: `pytest labs/day02 -q`. Still green? Good. Rerunning yesterday's tests every
morning is a habit worth building — it catches environment drift.

---

## Block 1 — Learn (1:15)

**Read `learn/DAY_03_LEARN.md` and work its examples on paper before continuing.**
Take the self-check at the end. Anything you miss goes on a flashcard and into tomorrow's
warm-up. The material below consolidates the module — it is not a substitute for it.

### 1.1 What an embedding actually is

```bash
python - <<'PY'
import sys; sys.path.insert(0, "src")
import numpy as np
from fdekit import embed

texts = [
    "Detention accrues at $65 per hour after 2 hours of free time.",
    "Drivers are paid waiting time once the free period expires.",
    "Demurrage applies to containers held at the marine terminal.",
    "The routing guide lists carriers in priority order per lane.",
    "I made a grilled cheese sandwich for lunch.",
]
V = np.array(embed(texts))
print("shape:", V.shape)
print("norms:", np.round(np.linalg.norm(V, axis=1), 4))
print("value range:", V.min().round(3), V.max().round(3))
PY
```

Answer in your notes:

- What is the dimensionality? What does one dimension "mean"? (Trick question — sit
  with why it's a trick.)
- Are the vectors unit-normalised? Check. **If they are, cosine similarity and dot
  product are the same operation** — and that fact is why half of vector DBs default to
  "inner product" and it confuses everyone.

### 1.2 Distance metrics

```
cosine(a,b)    = (a·b) / (|a||b|)        angle only, magnitude-blind
dot(a,b)       = a·b                      angle AND magnitude
euclidean(a,b) = |a-b|                    absolute position
```

For normalised vectors: `euclidean² = 2 - 2·cosine`. Derive it. It takes four lines and
it permanently fixes the "which metric should I pick?" confusion — for normalised
embeddings, **cosine and Euclidean produce identical rankings**. The choice only matters
when magnitude carries signal (some models encode "confidence" or length in magnitude).

Compute all three pairwise matrices for the 5 sentences above. Sentence 1 vs 2 should
be high (paraphrase), 1 vs 3 medium (related domain, different concept), 1 vs 5 low.

If 1 vs 3 comes out *higher* than 1 vs 2, that's your first real lesson: embeddings
capture **topical** similarity far more strongly than **propositional** similarity. This
is exactly why RAG retrieves the right document and the wrong paragraph.

### 1.3 Chunking is a retrieval decision, not a preprocessing detail

Chunk too small → the answer is split across chunks and no single chunk scores well.
Chunk too big → the embedding is an average of five topics and matches nothing sharply.

Strategies, with the trade-off you must be able to state out loud:

| Strategy | Good for | Breaks on |
|---|---|---|
| Fixed-size + overlap | Uniform prose | Tables, code, lists — splits mid-row |
| Recursive character | General default | Still blind to document semantics |
| Markdown/heading-aware | Structured docs like ours | Documents with no structure |
| Semantic (embedding-drift boundaries) | Long unstructured prose | Cost, and it's slow |
| Whole-document | Small corpora, long-context models | Cost per query, lost-in-the-middle |

Look at `data/corpus/02_detention_and_accessorials.md`. Where would a 500-character
fixed chunker cut it? Would the `$65/hour` figure survive with its condition ("after
2 hours free time") attached? **Go look.** This is the single most useful five minutes
of the day.

### 1.4 Why real indexes are approximate

Brute force is O(N·d) per query — fine at 10k vectors, fatal at 50M. HNSW builds a
navigable small-world graph with layered shortcuts: you enter at a sparse top layer,
greedily descend, and search a dense bottom layer locally.

The knobs and what they cost you:

- `M` — edges per node. Higher = better recall, more memory.
- `ef_construction` — build-time search width. Higher = better graph, slower build.
- `ef_search` — query-time width. Higher = better recall, slower query.

**You are trading recall for latency.** A client asking "why did it miss that document?"
may be asking about `ef_search`, not about your embeddings. Being able to say that is
FDE-grade knowledge. Today you measure it: your brute-force result is ground truth.

---

## Block 2 — Lab (2:15)

### 2.1 `src/fdekit/vectors.py` — from scratch, no vector DB (60 min)

```python
# Implement, with numpy only:
def l2_normalize(V: np.ndarray) -> np.ndarray: ...
def cosine_sim(q: np.ndarray, V: np.ndarray) -> np.ndarray: ...   # vectorised, no loops
def topk(q, V, k=5) -> list[tuple[int, float]]: ...

class SimpleVectorStore:
    """In-memory brute-force store. ~60 lines. Ground truth for the rest of the course."""
    def add(self, texts: list[str], metadata: list[dict]) -> None: ...
    def search(self, query: str, k: int = 5) -> list[SearchResult]: ...
    def save(self, path) / load(path)   # npz + json sidecar

# And three chunkers:
def chunk_fixed(text, size=500, overlap=50) -> list[str]: ...
def chunk_recursive(text, size=500, overlap=50) -> list[str]:
    """Split on \n\n, then \n, then '. ', then chars — recursively, largest separator first."""
def chunk_markdown(text) -> list[Chunk]:
    """Split on headings; carry the heading path into each chunk's text as a prefix."""
```

That last one — **prefixing the heading path into the chunk text before embedding** — is
a technique worth more than most of what's in the tutorials. A chunk that reads
`"Detention, Demurrage, and Accessorial Charges > Detention > Free time is 2 hours..."`
embeds far closer to the query "how much detention" than a bare paragraph does.

### 2.2 The chunking bake-off (40 min)

Index the corpus three times, once per chunker. Then run these 8 queries against each:

```
1. "How much is detention per hour?"                      -> doc 02
2. "What happens if I arrive 4 hours early at a grocery DC?" -> doc 03
3. "When does intermodal beat truckload?"                  -> doc 08
4. "What is routing guide depth and why does it matter?"   -> docs 04, 09
5. "Why did appointment times shift by an hour?"           -> doc 07
6. "What timezone problems exist in the TMS?"              -> docs 05, 07
7. "TONU"                                                  -> doc 02
8. "How is a carrier's monthly score calculated?"          -> doc 06
```

Record in `evals/day03_chunking_bakeoff.md`: for each (chunker × query), the top-3
chunks, whether the correct doc appeared, and at what rank. Compute
**Recall@3** and **MRR** per chunker.

Queries 6 and 7 are the interesting ones. Query 6 needs two documents — does any
chunker get both in top-3? Query 7 is a bare acronym — watch dense retrieval struggle
with rare tokens. That's your Day 14 motivation for hybrid search; note it now.

### 2.3 Now bring in Chroma, and check it (20 min)

Index the winning chunker's output into Chroma. Run the same 8 queries.

- Do the results match your brute-force ground truth exactly? If not, **which query
  differs and why?** (Approximation, or a different default metric, or normalisation.)
- Time both. At 10 docs, brute force will likely *win*. Say out loud why anyone uses
  an index anyway. That's the extrapolation muscle FDEs need.

---

## Block 3 — Teach-back #3 (0:30)

Record 8 min: **"Why your RAG returns the right document and the wrong paragraph."**
`teaching/recordings/day_03.mov`

Must include:
- The topical-vs-propositional similarity result from 1.2, with your actual numbers.
- A live chunk boundary that severs `$65/hour` from its condition.
- The heading-prefix fix, shown improving a real query's rank.

Do not say "embeddings capture semantic meaning" without immediately showing a case
where that phrase is misleading.

---

## Block 4 — Ship + retro (0:30)

```bash
pytest labs/ -q && ruff check src/ labs/ --fix
git add -A && git commit -m "Day 03: vectors from scratch, chunking bake-off, Chroma comparison" && git push
```

---

## Done when

- [ ] `SimpleVectorStore` returns correct top-k with zero Python loops in the hot path
- [ ] Three chunkers implemented; markdown chunker carries heading paths
- [ ] Bake-off table with Recall@3 and MRR for all three chunkers across 8 queries
- [ ] Chroma results reconciled against brute-force ground truth, discrepancies explained
- [ ] You can state the cosine/Euclidean equivalence for normalised vectors and prove it

---

## Trap list

- Forgetting to normalise, then wondering why dot product ranks long chunks higher.
- Embedding the query with a different model than the documents. Silent, catastrophic.
- Chunk overlap of 0 on prose. Chunk overlap of 50% on a big corpus (you just doubled cost).
- Comparing similarity scores *across different embedding models* as if they're on the same scale.
- Believing a similarity score of 0.82 is "good". It's meaningless without a distribution.
  Plot the score histogram for relevant vs. irrelevant pairs — that's how you pick a threshold.

---

## Stretch

Implement a toy HNSW: single layer, `M=8`, greedy search. Measure recall against your
brute-force ground truth as you vary `ef_search` from 4 to 64. Plot it. That plot is
one of the best slides you will ever put in front of a client who asks "is it accurate?"
