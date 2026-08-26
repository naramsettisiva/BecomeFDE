# Day 14 — Advanced Retrieval: Hybrid, Rerank, and Context Engineering

**Wed Sep 9, 2026** · Week 3 · Maps to: **Module 06 — Advanced Retrieval & Skills** · Backend: **local** + `[PAID]` · Est. cost: **$2–4**

> **Before you start — read `learn/DAY_14_LEARN.md` (1:15).**
> BM25, RRF, cross-encoders, near-duplicates. The lab below assumes it and does not re-explain it.


---

## Why today matters

**FDE lens.** Retrieval is the highest-leverage place to spend engineering time, and the
techniques today are cheap, well-understood, and reliably worth 10–20 points of recall.
When a client says "it doesn't find our stuff," this is the day's worth of work that
fixes it. Knowing the *order* to apply them in — and when to stop — is what you're paid for.

**Trainer lens.** This is a satisfying session to teach because every technique produces
a visible number change. Build the demos so each one moves a metric on screen.

---

## Objectives

1. Implement BM25 + dense hybrid with Reciprocal Rank Fusion, and explain why RRF beats score blending.
2. Add a cross-encoder reranker and quantify the recall/latency trade.
3. Implement contextual retrieval (chunk augmentation) and measure it.
4. Scale the corpus 20× and see which techniques still hold up.

---

## Schedule (5:00)

| Block | Time | What |
|---|---|---|
| 0 | 0:30 | Warm-up |
| 1 | 1:15 | **Learn** — `learn/DAY_14_LEARN.md` |
| 2 | 2:45 | Lab: build five techniques, measure each, scale the corpus |
| 3 | 0:30 | Teach-back #14 |

---

## Block 0 — Warm-up (0:30)

1. Your noise floor: which metric was noisiest, and what σ did you measure?
2. Final judge κ, and what rubric change moved it most?
3. Position-bias rate in your tournament?
4. How much did persona-rewriting drop your score? Why does that number matter more than
   the clean-question score?

---

## Block 1 — Learn (1:15)

**Read `learn/DAY_14_LEARN.md` and work its examples on paper before continuing.**
Take the self-check at the end. Anything you miss goes on a flashcard and into tomorrow's
warm-up. The material below consolidates the module — it is not a substitute for it.

### 1.1 Why dense retrieval fails, precisely

You saw it on Day 3 with the query `TONU`. The failure modes:

| Failure | Why | Example from your corpus |
|---|---|---|
| **Rare tokens / acronyms** | Under-represented in training; the embedding is near-random | `TONU`, `INC-4471`, `EDI 214` |
| **Exact identifiers** | Embeddings don't do exact match | `SHP-202608-0041729` |
| **Negation** | "not X" embeds close to "X" | "lanes where intermodal is *not* suitable" |
| **Numeric constraints** | No magnitude reasoning | "carriers scoring below 70" |
| **Domain jargon vs. plain language** | Vocabulary mismatch | "sitting at the dock" vs. "detention" |

BM25 fixes rows 1 and 2 outright. Query rewriting (Day 8) helps row 5. Rows 3 and 4 need
metadata filtering or structured queries — **retrieval is not always the right tool**, and
saying so is part of the job.

### 1.2 Fusion: why RRF and not score blending

BM25 scores are unbounded and corpus-dependent. Cosine scores are in [-1,1]. Blending them
requires normalisation that breaks whenever the corpus changes.

**Reciprocal Rank Fusion** uses only *ranks*:

```
RRF(d) = Σ_over_retrievers 1 / (k + rank_i(d))       k ≈ 60
```

Scale-free, needs no tuning, robust, and it's four lines of code. The `k=60` damps the
influence of top ranks so a document that's rank-3 in both lists can beat one that's
rank-1 in one and rank-50 in the other — which is usually what you want.

Derive why by hand for a small example. It takes five minutes and makes the parameter
intuitive instead of magic.

### 1.3 Reranking

Bi-encoder (your embeddings): encodes query and doc *separately*, compares vectors. Fast,
pre-computable, approximate.

Cross-encoder (reranker): encodes query and doc *together*, full attention across both.
Much more accurate, cannot be precomputed, must run per candidate at query time.

So the standard architecture:

```
query → retrieve 50 candidates (fast, approximate)
      → rerank to top 5 (slow, accurate)
      → generate
```

Costs: latency (~50–200ms for 50 candidates with a small cross-encoder locally, more for
an API reranker) and, if hosted, money. Benefit is typically the largest single quality
jump available. Measure both today.

### 1.4 Contextual retrieval

The Day 3 problem: a chunk reading "This applies only during declared weather emergencies"
is meaningless alone. The fix: prepend generated context to each chunk *before* embedding.

```
Original chunk: "Free time is 4 calendar days at inland ramps..."
Contextualised: "This chunk is from the Detention, Demurrage and Accessorial
Charges policy, section on Demurrage for intermodal containers at ramps and
terminals. Free time is 4 calendar days at inland ramps..."
```

Cost: one small-model call per chunk **at index time only** — so it's a one-off, and it's
cheap with prompt caching over the parent document. Reported gains are large. Your
heading-path prefix from Day 3 was a free approximation of this; today you do the real
version and measure the delta between them.

---

## Block 2 — Lab (2:45)

### 2.1 Scale the corpus first (30 min)

10 documents is too small to distinguish these techniques — everything wins at N=10.

`scripts/expand_corpus.py`: grow to **~200 documents / ~2,000 chunks** by:
- generating realistic variants (regional policy addenda, carrier-specific exhibits,
  monthly scorecards, 12 more incident postmortems, meeting notes, an FAQ)
- adding deliberate **near-duplicates** (revision 6 and revision 7 of the same policy,
  differing in two numbers) — this is the single most realistic thing you can add, and it
  breaks naive retrieval in exactly the way real corpora do
- adding documents that contain *contradictory* information across revisions

Re-run your Day 13 golden set against the bigger corpus **before** adding any new
technique. Your scores will drop. **That drop is the lesson**: technique comparisons at
toy scale are worthless. Record the before/after.

### 2.2 Build five techniques, measure each (90 min)

Add to `src/fdekit/retrieval.py`, and after each one, run the scorecard:

```python
class BM25Retriever: ...              # rank_bm25; tokenise carefully — keep IDs intact
def rrf_fuse(rankings: list[list[str]], k: int = 60) -> list[str]: ...
class HybridRetriever: ...            # dense + BM25 → RRF
class CrossEncoderReranker: ...       # sentence-transformers, ms-marco-MiniLM-L-6-v2
def contextualise_chunks(chunks, parent_docs) -> list[Chunk]: ...   # index-time
class ParentDocumentRetriever: ...    # search small chunks, return the parent section
class MetadataFilteredRetriever: ...  # pre-filter by doc_type, effective_date, region
```

Build the ablation table as you go — `evals/day14_retrieval_ablation.md`:

```
                                Recall@5  MRR   nDCG@5  p50 latency  index cost
dense only (baseline)             0.61    0.52   0.55      42ms        $0.04
+ BM25 hybrid (RRF)               0.74    0.63   0.68      58ms        $0.04
+ cross-encoder rerank            0.86    0.79   0.83     210ms        $0.04
+ contextual chunks               0.91    0.84   0.88     215ms        $0.61
+ parent-document return          0.91    0.84   0.90     220ms        $0.61
+ metadata pre-filter             0.93    0.88   0.91     180ms        $0.61
```

Note the last row: **latency went down** because pre-filtering shrinks the candidate set
before reranking. Finding a technique that improves quality *and* latency is rare and
worth calling out.

Also segment by query type. Hybrid should crush the acronym/ID queries specifically —
show that isolated, not just in the aggregate.

### 2.3 The near-duplicate problem (30 min)

Your expanded corpus has revision 6 and revision 7 of the tender acceptance policy with
different FTA thresholds. Ask: *"What FTA do primary carriers need to maintain?"*

Watch your retriever return chunks from both revisions, and watch the model either pick
one arbitrarily or blend them into a wrong answer. This is **the** most common real-world
RAG failure in enterprises and almost no tutorial covers it.

Fix it three ways and measure each:
1. **Metadata filter** on `effective_date` / `status=current`. Simple, requires clean metadata.
2. **Deduplication at index time** by content similarity, keeping the newest. Loses history.
3. **Surface the conflict**: detect that retrieved chunks disagree and have the model say
   *"Revision 6 said 90%; revision 7 (current) says 92%."* Hardest, and the best answer.

Option 3 is a genuinely impressive demo. Build it. `evals/day14_conflict_handling.md`.

### 2.4 Pick your production config (30 min)

You now have six techniques and a latency budget. Write a short decision memo:

- Which techniques ship, in what order, and why.
- Which one you'd skip and what it would cost you.
- Where the latency budget goes.
- What the index-time cost is at 200 docs, and at 200,000.

Half a page. This is the artifact an FDE actually delivers — not the code, the reasoned
recommendation with numbers behind it.

---

## Block 3 — Teach-back #14 (0:30)

Record 12 min: **"Retrieval ablation: what each technique buys, and what it costs."**
`teaching/recordings/day_14.mov`

Walk the ablation table row by row. For each: the failure it fixes, a live example of
that failure, and the latency column. Then the near-duplicate demo, because it's the one
that makes experienced people in the room nod — they've all been burned by it.

Close on the corpus-scale point: *"Every number I just showed you would have been
meaningless at ten documents."*

---

## Done when

- [ ] Corpus expanded to ~200 docs with deliberate near-duplicates and contradictions
- [ ] Before/after scores at 10 docs vs. 200 docs recorded
- [ ] All six retrieval techniques implemented
- [ ] Full ablation table: quality, latency, and index cost per technique
- [ ] Segmented results showing hybrid's specific win on acronyms/IDs
- [ ] Near-duplicate conflict handled all three ways, with conflict-surfacing working
- [ ] Half-page production-config decision memo

---

## Trap list

- Benchmarking retrieval on a 10-document corpus. Everything wins; nothing is learned.
- Blending BM25 and cosine scores directly. Use ranks.
- Reranking 5 candidates. Retrieve 50, rerank to 5 — the point is the wide net.
- Contextualising chunks at query time. It's an index-time operation.
- Ignoring near-duplicates until a client finds them.
- A tokeniser that splits `SHP-202608-0041729` into pieces, destroying BM25's advantage
  on exactly the queries it should win. Check your tokenisation.

---

## Stretch

Implement **ColBERT-style late interaction** (or use `RAGatouille`) and add it as a row in
the ablation. Then answer the question a client will ask: *"we already have Elasticsearch —
do we need a vector database at all?"* With today's ablation you can answer it with
numbers instead of opinion, which almost nobody can.
