# Day 14 · Learn — Advanced retrieval: lexical, fusion, reranking, and the duplicate nobody warns you about

**Read before `labs/DAY_14.md`. Budget 1:15.** Pen and paper for §3 — the BM25 and RRF arithmetic is the day.

---

## 1. Where this sits

Day 3 left you with a table of things dense retrieval cannot do — acronyms, exact IDs, negation,
numeric constraints — and a promise that the fixes were Day 14. Day 13 gave you a suite that can
detect whether a fix worked.

Today you collect. Four techniques, each cheap and well-understood: lexical retrieval alongside dense,
rank fusion to combine them, a cross-encoder to reorder the shortlist, index-time chunk augmentation.

And then a fifth thing, which is not a technique but a corpus property: **two revisions of the same
policy, carrying different numbers, both scoring beautifully.** Recall@5 says you found the answer.
You found two answers. The model picks one, or averages them, and a client's controller finds out
before you do. That problem separates an FDE from someone who has read a RAG tutorial, because almost
no tutorial covers it and almost every enterprise corpus has it.

---

## 2. The mechanism

### 2.1 The failure taxonomy, and which tool fixes which

| Failure | Why dense fails | Corpus example | Fix |
|---|---|---|---|
| **Rare tokens / acronyms** | Under-represented in training; the vector is near-arbitrary | `TONU`, `EDI 214` | **BM25** |
| **Exact identifiers** | Embeddings never do exact match | `SHP-202608-0041729` | **BM25**, if your tokeniser keeps it intact |
| **Negation** | "not X" is one token from "X"; the geometry barely moves | "lanes where intermodal is *not* suitable" | **Neither** |
| **Numeric constraints** | No magnitude reasoning in the geometry | "carriers scoring below 70" | **Metadata filter** |
| **Vocabulary mismatch** | — the one dense *fixes* | "sitting at the dock" → detention | Dense |

Read the fix column as three groups.

**Rows 1–2 are lexical problems and BM25 solves them outright.** A rare string either appears in the
chunk or it doesn't — that's set membership, and set membership is not a question you should be
answering with cosine similarity.

**Rows 3–4 are not retrieval problems at all.** "Which carriers scored below 70" is a `SELECT` with a
`WHERE` clause. No embedding quality gets you there, because the question is about magnitude and your
index encodes direction. A metadata filter alongside the vector search — `band = 'Bronze'`,
`effective_date >= '2026-07-01'` — hands the comparison to something that can compare. **Saying
"retrieval is the wrong tool for this query" in a design review is part of the job.** Negation is the
honest gap: BM25 drops "not" as a stopword, query rewriting and reranking help unreliably, and you
should name the limit rather than claim a fix.

**Row 5 is why you keep dense at all.** A dispatcher typing "what do we get charged for sitting at the
dock" shares zero terms with the detention policy. BM25 scores it zero.

### 2.2 BM25, explained plainly

BM25 is a scoring function from the 1990s that has stubbornly refused to be beaten. It is built from
two ideas.

**Idea one: term frequency saturates.** A chunk mentioning "detention" three times is more about
detention than one mentioning it once. A chunk mentioning it thirty times is not thirty times more
about detention — it's the accessorials policy, same as the one that said it three times. So tf should
rise fast and then flatten:

```
                 tf · (k₁ + 1)
tf_component  =  ─────────────         k₁ ≈ 1.2
                   tf + K
```

As `tf → ∞` this approaches `k₁ + 1 = 2.2` and stops. The first occurrence buys most of what you'll
get; the tenth buys almost nothing. §3 Q2 has the exact curve, and it flattens harder than people
expect.

`K` carries length normalisation:

```
K = k₁ · (1 − b + b · |d| / avgdl)         b ≈ 0.75
```

A long chunk gets a bigger `K`, dividing its tf contribution down — the same argument as Day 3's
preference for cosine over raw dot product. **A document should not rank higher for being long enough
to contain the word by accident.**

**Idea two: rare terms carry more signal.** If a term appears in 1,400 of 2,000 chunks, its presence
tells you nothing about which chunk you want. If it appears in 3, it tells you everything.

```
IDF(t) = ln( (N − df + 0.5) / (df + 0.5) + 1 )
```

The `+0.5`s are smoothing; the outer `+1` keeps IDF non-negative for near-universal terms.

Full BM25 sums the two over query terms:

```
score(q, d) = Σ_{t ∈ q}  IDF(t) · tf(t,d)·(k₁+1) / ( tf(t,d) + K )
```

No training, no embeddings, no GPU. A bag of counts and two hyperparameters nobody has needed to
change in twenty years.

### 2.3 Why that shape wins exactly where dense fails

`TONU` appears in 3 chunks out of 2,000; its IDF is about **6.35**. "Carrier" appears in 1,400; its
IDF is about **0.36** — a factor of eighteen. One occurrence of `TONU` outweighs six of "carrier" by
more than ten to one, because saturation caps what repetition buys while IDF has no such cap.

**That is the precise mechanism behind hybrid's win on acronyms.** Not that BM25 is vaguely "better at
keywords" — the scoring function is explicitly weighted toward terms that discriminate, and rare terms
discriminate. The embedding model has the opposite problem with the same input: a token it saw a
handful of times in training has a vector shaped mostly by whatever it co-occurred with, and no
dimension count fixes an undertrained token.

**One detail quietly destroys the whole advantage: tokenisation.** If your tokeniser splits
`SHP-202608-0041729` into `shp` / `202608` / `0041729`, you have converted the corpus's most
discriminative string into three common fragments. `shp` now appears in every shipment reference and
its IDF collapses. Check this — it's the most common way a hybrid retriever gets built and then fails
on exactly the queries it was added for.

### 2.4 Fusion: why ranks, and never scores

Two ranked lists, one needed. The obvious move — blend the scores — is wrong, and you'll have to
defend why.

| | Range | Stability |
|---|---|---|
| **Cosine** | Bounded [−1, 1], in practice a narrow band | Stable per model |
| **BM25** | **Unbounded above**, scale set by IDF | **Changes when the corpus changes** |

A BM25 score of 8.3 is not "high." It's a sum whose scale is set by how rare the query terms are *in
this corpus at this moment*. Index two hundred documents mentioning `TONU` and every BM25 score
involving it drops, with no change in relevance.

So to blend, you must normalise — and every normalisation has the same defect:

- **Min-max or z-score over the returned list** — both are defined by *this query's* results, so the
  scale is redefined per query. A query with one great hit and one with fifty mediocre ones both
  produce 1.0 at the top.
- **A fixed divisor calibrated offline** — works until you re-index, then it's silently wrong. Silently
  wrong after a re-index is the worst failure class there is, because nothing errors.

**Reciprocal Rank Fusion sidesteps all of it by discarding scores and keeping ranks.**

```
RRF(d) = Σ_{retrievers i}  1 / (k + rank_i(d))          k = 60
```

Rank 1 is rank 1 whether the score was 8.3 or 0.83. Nothing to normalise, nothing to recalibrate when
the corpus grows. Four lines of code, one parameter nobody tunes.

State the cost too: **RRF throws away margin.** If A scored 8.3 and B scored 0.4, RRF only knows A came
first. When one retriever is confident and the other is guessing, they get equal say. In practice that
loss is smaller than the loss from a normalisation that breaks. If one leg deserves more weight on your
corpus, weight the whole leg — `w_i / (k + rank_i(d))` — rather than reintroducing scores.

### 2.5 What the k = 60 damping does

`k` controls **how much more a rank-1 hit is worth than a rank-10 hit.**

| | Weight at rank 1 | Weight at rank 10 | Ratio |
|---|---|---|---|
| `k = 0` | 1.000 | 0.100 | **10.0×** |
| `k = 1` | 0.500 | 0.091 | **5.5×** |
| `k = 60` | 0.0164 | 0.0143 | **1.15×** |

At `k = 0`, being first in one list is worth ten times being tenth, so **one confident retriever
dictates the fused order** and the other leg is decoration. At `k = 60` the top twenty ranks are nearly
flat, so what dominates the sum is **appearing in both lists at all.**

Have the sentence ready: *`k` trades single-retriever confidence against cross-retriever agreement,
and 60 sits far toward agreement.* A document at rank 3 in both lists beats one at rank 1 in one and
rank 50 in the other — §3 Q4 and Q5, and once you've done that arithmetic the parameter stops being
magic. Whether 60 is optimal for your corpus is an empirical question almost nobody asks; RRF is
insensitive enough over 10–100 that tuning rarely repays an afternoon. Say that rather than claiming
60 is principled — it comes from the original paper's experiments, not from a derivation.

### 2.6 Bi-encoder vs cross-encoder: the precompute question

Everything from Day 3 is a **bi-encoder**. The query goes through the model alone. Each document went
through the model alone, at index time. Then you compare vectors.

```
bi-encoder:     encode(query) ──┐
                                ├─→ cosine → score     (doc side precomputed)
                encode(doc)   ──┘
```

Query and document **never meet inside the model.** The document's vector was computed before your
query existed — that's why it's fast, and exactly why it's approximate. It had to be compressed into
1024 numbers without knowing what would be asked of it.

A **cross-encoder** concatenates them and runs one forward pass over the pair:

```
cross-encoder:  [CLS] query [SEP] document [SEP] ──→ transformer ──→ relevance score
                       └──── full attention across both ────┘
```

Every query token attends to every document token. The model can see that "2 hours" is the free-time
condition attached to the "$65 per hour" being asked about; it can see the document says *not*
suitable. **That joint attention is the entire accuracy advantage**, and it addresses Day 3's
topical-vs-propositional gap directly: the cross-encoder scores the claim, not the neighbourhood.

And it is exactly why the result **cannot be precomputed.** The score is a function of the pair —
there is no per-document artifact to store, because the document's representation depends on the
query. You cannot index it, cache it across queries, or put it in an HNSW graph.

### 2.7 Retrieve 50, rerank to 5

```
query ──→ bi-encoder + BM25 → RRF → top 50      fast, approximate, wide net
      ──→ cross-encoder scores all 50 → top 5   slow, accurate, narrow
      ──→ generate
```

The bi-encoder's job is no longer to be right. **It is to be cheap and to not lose the answer** — get
the gold chunk somewhere into fifty candidates. The cross-encoder's job is to be right about fifty
things.

Run the numbers and the design becomes inevitable. At 3.6ms per pair on a small local cross-encoder,
50 candidates cost **180ms**; all 2,000 chunks cost **7.2 seconds**; a realistic enterprise 200,000
chunks costs **twelve minutes per query.** Meanwhile the bi-encoder's query cost barely moves from
2,000 to 200,000, because HNSW search is roughly logarithmic. The split isn't an optimisation; it's
the only thing that runs.

Two failure modes to name before you meet them. **Reranking too few candidates** — retrieve 5 and
rerank 5 and you've spent the latency for nothing; if the gold chunk was at rank 12 it isn't in the
room. The value is entirely in the width of the net. **Trusting the absolute score** — cross-encoder
outputs are logits from a model trained on someone else's relevance distribution, usually MS MARCO. A
0.7 doesn't mean 70% relevant; calibrate on your own pairs or use it only for ordering.

### 2.8 Contextual retrieval

Day 3 §2.7 gave you heading-path prefixing: prepend the structural path so `Detention, Demurrage and
Accessorial Charges > Demurrage >` rides along and disambiguates the chunk from detention. Free, no
model call, several points of recall.

**Contextual retrieval is the general form, with the prefix written by a model instead of copied from
the heading.** At index time, hand a small model the parent document and the chunk, and ask for one or
two sentences situating it:

```
Raw chunk:
  "This applies only during declared weather emergencies and suspends
   measurement for the duration plus 48 hours."

Contextualised:
  "This chunk is from the Carrier Tender Acceptance Policy, Revision 7,
   Exceptions section, covering force majeure suspension of tender
   acceptance measurement. This applies only during declared weather..."
```

The raw chunk is unretrievable by any query a human would write — it has no subject. The
contextualised version embeds near "when does tender acceptance stop being measured," and — the part
people miss — it now contains the *lexical* terms `tender acceptance`, `force majeure`, `Revision 7`,
so **the BM25 leg gets stronger too.** Contextual augmentation improves both retrievers at once, which
is why it stacks on hybrid rather than overlapping with it.

Three properties to hold onto:

**Index-time only.** One small-model call per chunk, once. Contextualising at query time gives you the
latency of an LLM call in front of every retrieval and none of the benefit.

**Prompt caching makes it cheap.** All ten chunks from a document share the same parent in the prompt.
Put the parent *first and unchanged*, the chunk last, and nine of ten calls read a cached prefix at
roughly a tenth the input price. §3 Q7 does the arithmetic; a 200-document corpus costs under a dollar.

**The honest comparison is against the free approximation, not against nothing.** On a well-structured
markdown corpus like this one, the heading path already carries most of the disambiguating signal; on
scanned PDFs with no structure, contextual retrieval is the only version available and the gap is
large. Measure the delta — it's what justifies the index-time spend to a client. Anthropic's 2024
write-up reports roughly a third fewer failed retrievals, and two-thirds fewer with reranking added;
treat those as the shape of the result, not numbers you'll reproduce.

### 2.9 The near-duplicate problem

Everything above makes retrieval find more. This one is about retrieval finding **too much of the
right thing.**

Your corpus has `01_tender_acceptance_policy.md` — Revision 7. Real document stores also contain
Revision 6, Revision 5, a regional addendum modifying Revision 6 for Canada, and a deck from the 2025
carrier summit quoting Revision 5. Nobody deleted anything, because deleting things in an enterprise
requires a person to take responsibility for deleting them.

Now: *"What FTA do primary carriers need to maintain?"*

Revision 7 says **92%**, Lane Review below **85%** for two consecutive quarters. Revision 6 says 90%
and 82%. Both are genuine policy documents, both topically perfect, both lexically perfect. **Every
technique in this module ranks them both at the top, and the reranker does it with more confidence.**

Then the model picks one arbitrarily — usually whichever appeared first, a function of your sort
stability rather than of correctness; or blends them into *"FTA of 90–92%,"* which is not a policy that
exists; or reports both in a tone implying they don't conflict.

**Your retrieval metrics all look fine.** Recall@5 is 1.0, nDCG is excellent, and yesterday's eval
suite passes — you wrote ground truth from the current revision and the current revision *was*
retrieved. The failure sits downstream of every number on your ablation table, which is why it
survives to production.

**Three fixes.**

| Fix | How | Cost | When it's right |
|---|---|---|---|
| **1 · Metadata filter** | Index `effective_date` / `status`; filter to current at query time | Needs metadata you can trust | You control ingestion, or the source has real lifecycle fields |
| **2 · Index-time dedupe** | Cluster near-identical chunks, keep the newest | Loses history — "what did the policy say in Q1?" becomes unanswerable | Superseded versions have no business value |
| **3 · Surface the conflict** | Detect that retrieved chunks disagree, make the model say so | Hardest; needs detection *and* prompt support | Almost always, and it wins the room |

Fix 1 is the default answer and it fails on contact with reality more often than you'd like, because
the metadata is wrong. "Tender Acceptance Policy FINAL v2 (revised).docx" with a `last_modified` of
last Tuesday — because someone opened it to fix a typo — beats the actual current revision on any
recency filter you write. **File modification time is not policy effective date.** Extract the
effective date from the document text and treat disagreement between the two as a data-quality finding
to hand back; that finding is often worth more to the client than your retriever. Fix 2 is legitimate
if you're explicit about what you're discarding — a controller reconstructing a disputed March invoice
needs the policy as it stood in March.

**Fix 3 is the right answer.** After reranking, before generation: group surviving chunks by document
family (same title, same section path, different revision); within a group, extract comparable values
— numbers with units, percentages, dates — and check whether they differ; if they do, **don't pick.**
Pass them all through with effective dates attached and an explicit instruction to state the current
value, name the superseded one, and say which is which.

> *"Revision 7, effective 1 July 2026, requires FTA ≥ 92% per lane per quarter. Revision 6
> (superseded) set this at 90%. If you're looking at a Q1 scorecard, 90% applied then."*

More useful than the correct-but-silent answer, and dramatically more trustworthy, because it shows
the system knows what it doesn't know.

One caution: conflict detection has a false-positive mode. Detention says $65/hr and demurrage says
$150/day; a naive "these numbers differ" check fires on chunks that aren't in conflict, just about
different things. Scope the comparison to chunks that are near-duplicates *of each other* — high
content similarity, same section heading.

### 2.10 The order to apply these, and when to stop

| Technique | Recall gain | Latency | Index cost | Ship when |
|---|---|---|---|---|
| **BM25 hybrid + RRF** | Large on IDs/acronyms | +10–20ms | None | Always — free, covers dense's worst failures |
| **Cross-encoder rerank** | Largest single jump | +150–250ms | None | Unless under a hard sub-100ms budget |
| **Contextual chunks** | Moderate; large if unstructured | None at query time | One call per chunk | Corpus is stable and poorly structured |
| **Metadata pre-filter** | Moderate — **and cuts latency** | **Negative** | Ingestion work | Metadata is trustworthy |

The metadata row is the one to call out in a review: quality *and* speed, because pre-filtering shrinks
the candidate set before the expensive reranking stage.

**Stop when the remaining failures aren't retrieval failures.** Segment your misses: gold chunk in the
top 50 but the answer still wrong means more retrieval technique buys nothing — that's prompt, context
assembly, or chunking. It's what stops you spending a week on ColBERT when your real problem is the
$65 severed from the 2-hour condition back on Day 3.

---

## 3. Worked example — on paper

> **Setup.** **N = 2,000 chunks**, **avgdl = 100 tokens**, `k₁ = 1.2`, `b = 0.75`.
> `TONU` appears in **df = 3** chunks; `carrier` in **df = 1,400**.

**Q1.** Compute `IDF(TONU)` and `IDF(carrier)` from
`IDF(t) = ln((N − df + 0.5)/(df + 0.5) + 1)`. Ratio?

**Q2.** A chunk has `|d| = 120`. Compute `K`, then `tf·(k₁+1)/(tf + K)` for `tf` = 1, 2, 3, 10, 11. How
much does the 2nd occurrence add? The 11th? Ceiling as `tf → ∞`?

**Q3.** Chunk A (the TONU section) contains `TONU` twice; chunk B contains `carrier` six times and no
`TONU`. Both 120 tokens. Score each for the query `TONU`, and say in one sentence why this is the
mechanism behind hybrid's win on acronyms.

**Q4.** Query *"What FTA do primary carriers need to maintain?"* returns:

| Doc | Dense rank | BM25 rank |
|---|---|---|
| **A** | 1 | 50 |
| **B** | 3 | 3 |
| **C** | 2 | 8 |

Compute RRF at `k = 60` and rank them.

**Q5.** Recompute at `k = 1`. What changed, and why? Then give the rank-1 : rank-10 weight ratio at
each `k`, and say in one sentence what `k` trades.

**Q6.** A cross-encoder scores one pair in **3.6ms**. (a) Time to score the whole 2,000-chunk corpus for
one query? At 200,000? (b) Time to rerank 50, and what it does to a 42ms dense-only p50? (c) Why can't
you precompute cross-encoder scores the way you precomputed document embeddings?

**Q7. (a)** Top-5 for the FTA query: rev-7, rev-6, rev-7, glossary, rev-5. Ground truth is the rev-7
chunk. Recall@5? What fraction of the context carries a superseded number? What does that say about
recall@5 as your only gate?

**(b)** Contextual augmentation: **200 documents**, **10 chunks each**, parent doc **1,500 tokens**,
chunk + instruction **200 tokens**, output **120 tokens**. Input **$0.25/M**, cached-read **$0.03/M**,
output **$1.25/M**. Total with no prompt caching, and with the parent document as a cached prefix?

<details>
<summary><b>Answers — do Q2, Q4 and Q5 by hand; those three are the day</b></summary>

**Q1.** `IDF(TONU) = ln(1997.5/3.5 + 1) = ln(571.71) = ` **6.35**.
`IDF(carrier) = ln(600.5/1400.5 + 1) = ln(1.4288) = ` **0.357**. Ratio ≈ **17.8×**.

**Q2.** `K = 1.2 · (0.25 + 0.75 × 1.2) = 1.2 × 1.15 = ` **1.38**

| tf | `tf·2.2/(tf+1.38)` | gain over previous |
|---|---|---|
| 1 | 0.924 | — |
| 2 | 1.302 | **+0.377** |
| 3 | 1.507 | +0.205 |
| 10 | 1.933 | — |
| 11 | 1.955 | **+0.022** |

The 2nd occurrence adds 0.377, the 11th adds 0.022 — **17× less.** Ceiling is `k₁ + 1 = ` **2.2**, and
tf=11 is already at 89% of it. Saturation isn't a gentle rolloff; it's essentially done by the fifth
occurrence.

**Q3.** A: `6.35 × 1.302 = ` **8.27**. B: **0** — it doesn't contain the term. Even if B also contained
`TONU` once, `6.35 × 0.924 = 5.87`, still well below A; and B's six `carrier` occurrences contribute
`0.357 × 1.789 = 0.64` — **less than a tenth** of what a single `TONU` contributes.

One sentence: BM25 concentrates score on terms that discriminate between documents, and a rare acronym
is the most discriminative thing in the corpus — which is exactly the token an embedding model saw
least in training and represents worst.

**Q4.** A: `1/61 + 1/110 = ` **0.02548**. B: `1/63 + 1/63 = ` **0.03175**. C: `1/62 + 1/68 = `
**0.03084**. Order **B > C > A.** The document at rank 3 in *both* lists beats the one at rank 1 in
one and rank 50 in the other — agreement across independent retrievers is stronger evidence than one
retriever's confidence.

**Q5.** A: `0.5 + 0.0196 = ` **0.5196**. B: `0.25 + 0.25 = ` **0.500**. C: `0.333 + 0.111 = ` **0.4444**.
Order flips to **A > B > C**: at `k = 1`, being rank 1 in one list is worth so much that rank 50 in the
other barely registers.

Ratios rank-1 : rank-10 — `k=1`: `(1/2)/(1/11) = ` **5.5×**; `k=60`: `(1/61)/(1/70) = ` **1.15×**.

`k` trades **single-retriever confidence against cross-retriever agreement.** Small `k` lets one
confident retriever dictate; large `k` flattens the top of each list so what matters is showing up in
both — which is what you want when your two retrievers fail in *different* ways.

**Q6.** (a) 2,000 × 3.6ms = **7.2s** per query; 200,000 × 3.6ms = **720s ≈ 12 minutes**. Not a system.
(b) 50 × 3.6ms = **180ms**, taking p50 from 42ms to roughly **222ms** — a 5× latency increase for what
is usually the biggest quality jump on the table. State it as that trade, not as "reranking is slow."
(c) The score is a function of the *pair*: the document's internal representation depends on the query
it attends to, so there's no per-document artifact to store. That is also the source of the accuracy —
Day 3's topical/propositional gap closes because the tokens attend to each other.

**Q7. (a)** Recall@5 = **1.0**. But **2 of 5** chunks — 40% of the context — carry a superseded FTA
threshold, one of them at rank 2.

**Recall@5 cannot detect this failure class at all.** It's a set-membership metric and the problem is
contradiction among members. A gate built on recall@5 passes a system that confidently tells a
controller the threshold is 90%. Conflict detection needs its own metric — which is what
`evals/day14_conflict_handling.md` is for.

**(b)** 2,000 chunks.
*No caching:* input `2,000 × 1,700 = 3.4M` → **$0.85**; output `2,000 × 120 = 240K` → **$0.30**;
total ≈ **$1.15**.
*With caching*, parent first and unchanged, 1 of 10 calls per doc pays full price for it: full input
`200 × (1,500 + 2,000) = 700K` → **$0.175**; cached `200 × 13,500 = 2.7M` at $0.03/M → **$0.081**;
output **$0.30**; total ≈ **$0.56**.

Two takeaways. **The absolute number is trivial** — under a dollar for the whole corpus, about $56 at
200,000 chunks. Contextual retrieval isn't expensive; it just *feels* expensive because it's a model
call per chunk. And **the saving came entirely from prompt ordering** — same tokens, same model, same
output, reordered so the stable part comes first. That's tomorrow's §2 in one line.

</details>

---

## 4. What people get wrong

**"Just normalise the BM25 scores and blend."**
Every normalisation is defined relative to something that moves — this query's top hit, this list's
distribution, or last month's corpus. Ranks are scale-free by construction.

**"The reranker replaces the retriever."**
It reorders what it's handed. First-stage recall is the ceiling on the whole pipeline — and reranking
5 candidates pays the latency for nothing.

**"Cross-encoders are just better, use them everywhere."**
They can't be precomputed. 200,000 chunks per query is twelve minutes. Two stages isn't a compromise,
it's the only shape that runs.

**"Contextual retrieval is expensive, and it only helps the dense leg."**
Sub-dollar for 200 documents, index-time, one-off — the expensive mistake would be doing it per query.
And it adds real terms to the chunk text, so BM25 gets stronger too; that's why it stacks on hybrid.

**"Our tokeniser is fine."**
Check that `SHP-202608-0041729` survives intact. If it splits you've destroyed BM25's advantage on
exactly the queries you added it for, and the aggregate metric will barely move so you won't notice.

**"Recall@5 of 0.93 means retrieval is solved."**
Recall is set membership. It says nothing about two retrieved chunks contradicting each other, which
is the failure that reaches the client.

**"Near-duplicates are the client's data-hygiene problem — and anyway, just filter to the newest."**
It's theirs *and* yours, because your system is the thing that will state the wrong number. And file
modification time is not policy effective date: someone opened Revision 5 last Tuesday to fix a typo.
Extract the date from the text.

**"These techniques are worth 10–20 points — I measured it on ten documents."**
At N=10 everything wins, because the answer lands in the top 5 by accident. Every comparison here
needs a corpus big enough for the retriever to be able to fail.

---

## 5. The trainer's angle

**The analogy that lands:** retrieve-then-rerank is a **bloom filter in front of an expensive lookup.**
The first stage is cheap, approximate, and tuned so it must never produce a false negative — losing the
gold chunk is unrecoverable. The second is expensive, exact, and only sees what survived. Every SRE in
the room has built this; they've just never seen it applied to text, and once they have the frame,
"why not rerank everything?" answers itself.

For RRF: **it's quorum, not weighted voting.** Two independent signals failing in uncorrelated ways,
and you count agreement rather than trust either one's confidence, because their confidence scales
aren't comparable and never will be. That framing gets a nod where "reciprocal rank fusion" gets a
blank stare.

**The demo that makes it click:** two queries side by side, live.

```
"what do we get charged for sitting at the dock"    BM25: nothing.  Dense: the detention section.
"TONU"                                              BM25: exact hit. Dense: three random accessorials.
```

Each retriever fails completely on the other's query. Show them failing *before* you show the fusion.
Ninety seconds, and nobody will ask again why you need both.

**The second demo, and it wins the day:** the near-duplicate. Ask *"What FTA do primary carriers need
to maintain?"* against a corpus holding Revisions 6 and 7. Show the model answering "90–92%." Let it
sit. Then turn on conflict surfacing and show *"Revision 7 (current, effective 1 July 2026) requires
92%; Revision 6 set it at 90%."* Experienced enterprise people react to that harder than to any recall
number, because someone in the room has sat in the meeting where two teams worked from different
revisions of the same document.

**The predictive question before you run anything:** *"Document A is rank 1 in one list and rank 50 in
the other. Document B is rank 3 in both. Which wins under RRF?"* Take a show of hands first. Most rooms
say A. The §3 Q4 arithmetic takes thirty seconds on a whiteboard and permanently fixes the intuition.

**The question a sharp student will ask:** *"We already have Elasticsearch. Do we need a vector
database at all?"*

> Sometimes genuinely not — and be willing to say so, because it's a real cost line and "no" builds
> more trust than "yes." Decide it rather than argue it: run your eval suite three ways — BM25 only,
> dense only, hybrid — and segment by query type. If the traffic is mostly identifiers, part numbers
> and error codes, as a lot of enterprise search is, BM25 alone may get within a couple of points of
> hybrid and the vector database is operational cost you don't need. If it's people describing
> problems in their own words, dense earns its keep on the first query. And modern Elasticsearch and
> OpenSearch both ship dense vector fields, so the real question is usually "do we need a *second*
> system." The answer is a table with your numbers in it, not an architectural preference — and
> almost nobody can produce that table.

**The second question, from whoever's paying:** *"Which of these do we skip?"* Have §2.10's order
ready — and note that metadata filtering depends on whether their metadata is trustworthy, which is a
question about their ingestion pipeline rather than about retrieval.

---

## 6. Self-check

Cover the answers.

1. Which two failure classes does BM25 fix outright, and which two does it not touch?
2. What's the correct tool for "which carriers scored below 70," and why isn't it retrieval?
3. Explain term-frequency saturation. What's the ceiling, and where does the curve flatten?
4. What does IDF do, and why does it make BM25 strong on rare acronyms?
5. Why can't you blend BM25 and cosine scores? Name two normalisations and how each breaks.
6. Write the RRF formula. What does it discard, what does it gain, and what does `k` control?
7. Bi-encoder vs cross-encoder, in one sentence about where the query and document meet.
8. Why can't cross-encoder scores be precomputed, and what architecture does that force?
9. What is contextual retrieval, when does it run, and why does it help the lexical leg too?
10. Describe the near-duplicate failure. Why don't your retrieval metrics catch it?
11. Name the three fixes, and one specific way the easiest of them fails in practice.
12. What breaks if your tokeniser splits `SHP-202608-0041729`, and why won't the aggregate tell you?

<details>
<summary><b>Answers</b></summary>

1. Fixes rare tokens/acronyms and exact identifiers. Doesn't touch negation or numeric constraints —
   those need query rewriting or metadata/structured filtering.
2. A metadata filter or structured query. Retrieval indexes direction in embedding space or term
   overlap; neither can evaluate "less than 70."
3. `tf(k₁+1)/(tf+K)` rises steeply then flattens. Ceiling `k₁+1 ≈ 2.2`; it's ~90% of the way there by
   the tenth occurrence, and the 11th adds about 6% of what the 2nd added.
4. Weights a term by rarity across the corpus, so discriminating terms dominate. A rare acronym has
   very high IDF — and it's precisely the token an embedding model represents worst.
5. BM25 is unbounded and its scale depends on corpus statistics that change on re-index; cosine is
   bounded. Min-max redefines the scale per query (the top hit is always 1.0); a fixed offline divisor
   is silently wrong after any re-index.
6. `RRF(d) = Σᵢ 1/(k + rankᵢ(d))`. It discards margin — how much better the top hit was — and gains
   scale-freedom, so nothing needs normalising when the corpus changes. `k` sets how much more a top
   rank is worth than a lower one: at `k=1` rank 1 is 5.5× rank 10, so one confident retriever dictates
   the order; at `k=60` it's 1.15×, so appearing in both lists dominates.
7. Bi-encoder: encoded separately, never meet inside the model — only the vectors are compared.
   Cross-encoder: concatenated and run through together, full attention across both.
8. The score is a function of the pair, so the document has no query-independent representation to
   store. That forces two stages: cheap wide retrieval, then expensive narrow reranking — and it's why
   reranking 5 candidates wastes the latency, since the value is the width of the first-stage net.
9. A model-written one-or-two-sentence prefix situating each chunk in its parent document, generated
   at index time only. It injects real domain terms into the chunk text, so BM25 matches on them as
   well as the embedding moving.
10. Two revisions with different numbers both rank at the top; the model picks one arbitrarily, blends
    them, or reports both without flagging the conflict. Recall and nDCG are membership and ordering
    metrics — the gold chunk *was* retrieved, so they read as perfect.
11. Metadata filter on effective date/status; index-time dedupe keeping the newest; surfacing the
    conflict. The metadata filter fails when file modification time proxies for policy effective date —
    someone opens an old revision to fix a typo and it becomes the "newest."
12. `shp`, `202608` and `0041729` are far more common than the intact ID, so IDF collapses and BM25
    loses its advantage on exactly the identifier queries you added it for. The aggregate barely moves
    because ID queries are a small slice — you only see it if you segment by query type.

</details>

**Scored below 9?** Re-read §2.4–§2.5 and §2.9. The lab's two hardest deliverables — an RRF
implementation you can defend in a design review, and conflict surfacing over deliberately planted
near-duplicates — are exactly those sections, and the lab will not re-explain either.

---

## 7. Going deeper

<!--reading:14-->

### If you read one thing this week

**[Practical BM25 — Part 2: The BM25 Algorithm and its Variables](https://www.elastic.co/blog/practical-bm25-part-2-the-bm25-algorithm-and-its-variables)** — Shane Connelly (Elastic) · essay · ~30 min

Walks §2.2's formula one variable at a time against a toy index you can picture — set k1 to 0 and watch term frequency stop mattering, change b and watch length normalisation move — which fixes the saturation and IDF intuitions in half an hour.

### Then, in the order I'd take them

- **[The Probabilistic Relevance Framework: BM25 and Beyond](https://www.staff.city.ac.uk/~sbrp622/papers/foundations_bm25_review.pdf)** — Stephen Robertson & Hugo Zaragoza · paper · ~1h  
  The primary source, by BM25's own authors — read §3 (the derivation of the term-frequency and document-length components) and stop there; the rest is a research monograph and you don't need it to defend the scoring function in a design review.
- **[Retrieve & Re-Rank](https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html)** — Nils Reimers et al. (Sentence Transformers) · docs · ~20 min  
  The clearest short statement of §2.5's bi-encoder / cross-encoder split — one encodes query and document independently so you can pre-index, the other reads them together and can't — plus working code for the two-stage pipeline.
- **[Passage Re-ranking with BERT](https://arxiv.org/abs/1901.04085)** — Rodrigo Nogueira & Kyunghyun Cho · paper · ~20 min  
  Four pages, and the paper that established the retrieve-then-rerank pattern everyone now ships — worth reading for the size of the gain over BM25 alone, which is the number that justifies the reranker's latency budget in §2.5.
- **[The Use of MMR, Diversity-Based Reranking for Reordering Documents and Producing Summaries](https://www.cs.cmu.edu/~jgc/publication/The_Use_MMR_Diversity_Based_LTMIR_1998.pdf)** — Jaime Carbonell & Jade Goldstein · paper · ~25 min  
  The 1998 original of the near-duplicate fix in §2.7 — a single λ trading relevance against novelty — and it is the same crowding-out mechanism as Day 10's semantic-memory decay, so reading it once buys you both.

<!--/reading-->

### Also mentioned in this module

- *Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods* — Cormack,
  Clarke & Buettcher, SIGIR 2009. Short, and the source of the `k = 60` default.
- *BEIR* — Thakur et al., NeurIPS 2021. The empirical case that BM25 remains a startlingly strong
  baseline out-of-domain. Ammunition when someone wants to delete the lexical leg.
- *ColBERT* — Khattab & Zaharia, SIGIR 2020. The middle ground: per-token vectors, late interaction,
  precomputable. Today's stretch goal.
- *Introducing Contextual Retrieval* — Anthropic engineering blog, 2024. §2.8 with measured gains and a
  worked prompt-caching cost model.

---

**Now go to `labs/DAY_14.md`.** The lab builds directly on §2.2–§2.3 (BM25 and the tokenisation trap),
§2.4–§2.5 (RRF and the `k` derivation from §3), §2.6–§2.7 (the retrieve-50-rerank-5 ablation row and
its latency cost), §2.8 (contextual chunks measured against Day 3's free heading-path approximation),
and §2.9 — which is the whole of block 2.3 and the demo you'll close your teach-back with.
