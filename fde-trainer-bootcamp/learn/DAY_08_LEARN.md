# Day 08 · Learn — Agentic RAG: routing, rewriting, decomposition, correction

**Read before `labs/DAY_08.md`. Budget 1:15. Pen and paper for §3 — the fusion arithmetic and the blended-cost arithmetic are both the point.**

---

## 1. Where this sits

Day 5 gave you a number you haven't been able to stop thinking about: your `synthesis` bucket
scores **0.41**. Lookups are fine, conditional questions are decent, and anything requiring two
facts from two documents falls over. Day 7 gave you a loop that can take more than one action.

Today is those two facts meeting. Naive RAG issues **one** retrieval per question, and that is a
structural limit, not a tuning problem — no chunk size, no `k`, no reranker fixes a question whose
answer lives in two places the query vector can't reach at once.

The trap you're being inoculated against: "agentic RAG" is not "an agent with a search tool."
That's one implementation of one of four patterns, and usually the least testable one. Today you
learn the four as a **menu with prices attached** — because every one of them buys recall with
latency and dollars, and the client conversation is always about the exchange rate.

---

## 2. The mechanism

### 2.1 Why one retrieval can't answer a two-hop question

Three distinct failure shapes hide under "multi-hop." Naming them separately is what lets you pick
a pattern instead of stacking all four.

**Shape A — two neighbourhoods, one query vector.** *"Ridgeline Freight's FTA is 83% for two
straight quarters — what happens, and what does that do to their scorecard band?"* The answer needs
document 01 (Lane Review below 85% for two consecutive quarters) and document 06 (the 70–79 Silver
band). Day 3's geometry says exactly what happens: the question's embedding is a *single* point
sitting between two clusters, cleanly inside neither. With `k=5` you get four chunks from whichever
cluster it drifted toward and one weak straggler from the other, and the generator answers half the
question confidently.

**Shape B — the bridging entity is unstated.** *"Which carrier has the worst FTA on DAL→CHI, and
what's their detention exposure this quarter?"* You cannot *write* query two until query one
answers — the carrier name is the join key and it isn't in the question. Retrieval breadth doesn't
help; this needs sequencing.

**Shape C — the question isn't shaped like a document.** *"What do I get charged for sitting at the
dock?"* Questions are short, interrogative, and use user vocabulary; documents are declarative and
use policy vocabulary, so they occupy different regions of the space. Day 3's vocabulary-mismatch
case, fixed by changing the *query* rather than the retrieval.

Each shape maps to a pattern: A → decomposition or multi-query, B → sequential decomposition,
C → rewriting/HyDE. And a fourth pattern, correction, exists because all three can still fail and
you'd rather refuse than fabricate.

### 2.2 Pattern A — Routing

A cheap decision about *where* the question goes, before any retrieval happens.

```
question → router → { policy_corpus | shipment_db | calculator | web | refuse }
```

The win people underrate: routing is mostly a **refusal** mechanism. "What's SHP-202608-0041729's
status?" should never touch the vector store — if it does you retrieve the detention policy, which
is topically adjacent and useless, and the generator answers from it anyway. In the lab's
illustrative bake-off, routing moves `refusal correct` from 0.40 to 0.80 while barely touching
recall. That's the shape of the win.

Three implementations, in ascending cost:

| Implementation | Cost/query | Latency | Testability | Fails when |
|---|---|---|---|---|
| **Embedding similarity to route descriptions** | ~$0 (1 embedding) | ~10 ms | Excellent — it's a classifier | Routes are semantically close; question uses novel vocabulary |
| **Small-model structured classifier** | 1 cheap call | ~200 ms | Excellent — confusion matrix | Genuinely ambiguous questions; prompt drift |
| **Tool-choosing agent** | 1+ full calls | 1–2 s | Poor — it's a loop | Hard to constrain, hard to unit-test |

Most teams jump straight to the third. **Try the first and measure** — it's routinely within a few
points at zero marginal cost, and it's just Day 3 machinery: write a paragraph describing each
route, embed those once, embed the question, take the nearest.

Two implementation notes. Use a **score margin**, not a bare argmax — top two routes within ~0.03
means the question is ambiguous and should fall back to the classifier or a broad route. And
**measure routing as a classification problem**: confusion matrix, per-class precision and recall.
Recall@5 tells you nothing about a router.

### 2.3 Pattern B — Query rewriting

The user's question is rarely the best search query. Four variants, and they are not
interchangeable:

| Variant | What it does | Extra calls | Best for |
|---|---|---|---|
| **Rewrite** | "what do I get charged for sitting at the dock" → "detention charges free time hourly rate" | 1 small | Shape C, vocabulary gap |
| **HyDE** | Generate a fake *answer*, embed that, search with it | 1 | Shape C, hard |
| **Multi-query** | Generate 3 paraphrases, retrieve each, fuse | 1 + 3 retrievals | Shape A, cheaply |
| **Step-back** | Ask a more general question first for framing, then the specific one | 1 + 2 retrievals | Questions needing definitional context |

**HyDE deserves the mechanism, because everyone misunderstands why it works.** You ask a small
model to hallucinate a plausible policy paragraph answering the question — "Detention accrues at a
per-hour rate after a free-time window at both origin and destination…" — then embed *that* and
search with it. It works because a hypothetical answer is *document-shaped*: declarative,
policy-voiced, the right length. You've moved the query from question-space into document-space,
which is precisely Shape C.

The critical property: **you throw the generated text away.** Only the vector is used, so a factual
error in the hypothesis is usually harmless — invent "$80 per hour" and the vector still lands in
the detention neighbourhood, and retrieval returns the real $65 rule. HyDE fails on wrong *domain*
(a demurrage paragraph for a detention question), not on wrong numbers. Say that out loud in a
teach-back: "but it might hallucinate" is the first objection you'll get.

**Step-back** (Zheng et al., 2023) is the one people skip. For *"can Ridgeline stay primary on
DAL→CHI at 83% FTA?"*, step back to *"how is primary carrier status determined?"*, retrieve that,
then answer the specific question with the framing in context. Cheap, and it fixes questions that
presuppose a rule the retriever never surfaces.

### 2.4 Reciprocal rank fusion, and why ranks beat scores

Multi-query gives you three ranked lists. Something has to merge them.

The obvious move is to sum the similarity scores. **Don't.** Day 3 told you why: a score of 0.82
means nothing on its own, and scores aren't comparable across retrievers or even across queries
against the same retriever. Sum them and whichever list has the widest numeric range dominates for
reasons unrelated to relevance — catastrophically so the moment one list is BM25 (Day 14), whose
raw scores run 1–20 against cosine's 0.4–0.8.

**Reciprocal rank fusion** (Cormack, Clarke & Buettcher, SIGIR 2009) throws the scores away and
uses only positions:

```
RRF(d) = Σ over lists i  of  1 / (k + rank_i(d))          k = 60 by convention
```

Two properties do the work.

**Scale-free.** A rank is a rank whether it came from cosine, BM25, or a cross-encoder. Nothing
needs normalising, and there's nothing to tune per corpus.

**The `k=60` damping makes consensus beat a single strong hit.** With k=60, rank 1 contributes
1/61 = 0.0164 and rank 3 contributes 1/63 = 0.0159 — a difference of 3%. So a document that placed
third in all three lists (0.0476) comfortably beats one that placed first in exactly one (0.0164).
That is the behaviour you want from a fusion step: *agreement across independent views is stronger
evidence than one confident view.* Lower k sharpens toward top-rank dominance; higher k flattens
further. Sensitivity is genuinely low, and tuning k is a poor use of your afternoon.

Be honest about what RRF does **not** do: it fixes the *scale* problem, not the *quality* problem.
If a retriever reliably loves the glossary, RRF still ranks the glossary highly — it just won't let
it win by an accident of numeric range. Fixing that needs a better retriever or Pattern D. You'll
see exactly this in §3.

The alternative to be able to argue against: min-max normalise each list, then sum. Defensible and
used in production; its weakness is that min-max is hostage to a single top score — a list whose
best result is barely relevant still gets it scaled to 1.0. **The field uses both.** RRF is the
default because it needs no per-corpus tuning and degrades gracefully.

### 2.5 Pattern C — Decomposition, and the dependency question

For Shape A and Shape B. A planner model emits sub-questions; you retrieve for each; you synthesise.

```
"If a carrier's FTA drops to 83% for two quarters, what happens and how does
 that affect their scorecard band?"
   ↓ plan
 [1] "What happens when FTA falls below 85% for two consecutive quarters?"   → doc 01
 [2] "How is the composite scorecard calculated and what are the bands?"     → doc 06
   ↓ retrieve each independently, then synthesise
```

The design decision that separates a working decomposer from a demo is **parallel or sequential**,
and the way to get it right is to stop treating it as logic and make it a schema field:

```python
class SubQuestion(BaseModel):
    id: int
    question: str
    depends_on: list[int]   # ids whose answers this question needs
```

Now you have a DAG, and you know what to do with one: topological sort, run each level concurrently
with `asyncio.gather` and the Day 2 semaphore, feed resolved answers forward into the next level's
prompt. Shape A gives `depends_on: []` everywhere and runs in one wave; Shape B gives
`[2] depends_on [1]` and runs in two. **Detect, don't hardcode** — the planner knows, and a typed
field is far more reliable than asking in prose.

Guard against **over-decomposition**. A single-hop lookup split into three sub-questions costs 3×
and often scores *worse*: three narrow retrievals return three overlapping chunk sets and the
synthesiser now has a reconciliation problem it didn't have. Gate it — let the planner return a
one-item plan and short-circuit to naive RAG, or route on question type first. "Decompose
everything" is the most common way this pattern loses money.

### 2.6 Pattern D — Corrective / self-RAG

Insert grading between retrieval and generation, and again after it.

```
retrieve → grade each chunk (relevant? yes/no)
   enough relevant → generate
   some relevant   → generate using only those
   none relevant   → rewrite the query, retry (once)
   still none      → refuse
generate → grade the answer for groundedness → regenerate once if unsupported
```

The pre-generation grader is a cheap binary classifier per chunk — batch all `k` into one call. The
post-generation grader is your Day 5 faithfulness judge, moved from the eval harness into the
request path: same rubric, same known Cohen's κ, now running online.

**This is the pattern that buys refusal**, the behaviour enterprise clients actually trust. A
system that says "the policy corpus doesn't cover spot reefer rates" is worth more than one that's
3 points better on recall and invents an answer for out-of-scope questions.

Two honest caveats. **Grader calibration is the whole game** — a grader saying "relevant" 95% of
the time is agreeing, not grading, and you've paid for a step that changes nothing. Check the
yes-rate on your golden set, and fix it with a rubric carrying an explicit negative example and a
definition of relevance tied to *answering the question* rather than *being about the topic*, which
is Day 3's topical-vs-propositional distinction turning up a fourth time.

And **the names**. CRAG (Yan et al., 2024) uses an external retrieval evaluator with a web-search
fallback; Self-RAG (Asai et al., 2023) trains reflection tokens *into the model*. Almost nothing in
production is either — it's a grading loop around a stock model, which is fine and works. Say
"corrective grading loop" and cite what inspired it. Claiming you implemented Self-RAG when you
trained nothing is the kind of thing a sharp client notices.

### 2.7 The ledger: what each pattern costs

| Pattern | LLM calls/query | Added latency | Fixes | Typical bucket moved |
|---|---|---|---|---|
| Naive | 1.0 | — | — | baseline |
| Routing (embedding) | 1.0 | +10 ms | wrong-corpus retrieval | refusal |
| Routing (classifier) | 2.0 | +0.3 s | same, more robust | refusal |
| Rewrite / HyDE | 2.0 | +0.8 s | Shape C | condition, lookup |
| Multi-query + RRF | 2.0 + 3 retrievals | +1.0 s | Shape A, cheaply | synthesis (partly) |
| Decomposition | 1 + n + 1 | +2 to +4 s | Shapes A and B | **synthesis** |
| Corrective | ~2× naive | +2 s | ungrounded answers | faithfulness, refusal |

The composition point people miss: **patterns multiply, they don't add.** Decomposition into 3
sub-questions with corrective grading on each is 3 × 2 = 6 gradings plus a plan plus a synthesis.
That's how you get the lab's FullStack at 5.2 calls and 7.9 s p50. Stacking everything by default
is how a 1-second system becomes an 8-second system to fix a bucket that is 12% of traffic.

### 2.8 When a state graph beats a loop

You'll rebuild the corrective pattern as a LangGraph state machine. Be precise about what that
purchase gets you, because it's the question a client will ask.

| A loop gives you | A graph adds |
|---|---|
| Control flow you can read | **Explicit state** — a typed object, not variables scattered in a closure |
| A step trace | **Checkpointing** — persist state at each node |
| Restart from the beginning | **Resumability** — restart from the failed node, not the start |
| An if-statement | **Conditional edges** you can draw, diff, and show a client |
| | **Human-in-the-loop** — interrupt at a node, wait for approval, resume |

**Not intelligence.** The graph does not make better retrieval decisions than your `if` statement.
Say that out loud in the teach-back and you'll be one of very few people in the room who understands
what they bought.

You know this trade: Step Functions versus a Python script. Reach for the state machine when a run
is long or expensive enough that restarting from zero is unacceptable, when a human approves
something mid-flow, or when the topology is itself the artefact you need to show someone. For a
4-second, 5-call, fully automatic request path, a loop is correct and the graph is overhead. Both
answers are defensible; only one is defensible *with a reason*, and that's what the client pays for.

---

## 3. Worked example — on paper

### Part 1 — Fusion

Two ranked lists for *"Ridgeline FTA 83% two quarters — consequences and scorecard band?"*

```
Dense (rewritten query, cosine)      BM25 (original question, raw scores)
1. D01  0.74                          1. D10  18.2
2. D06  0.69                          2. D04  11.6
3. D10  0.61                          3. D01   9.4
4. D04  0.55                          4. D02   6.1
```

D01 = tender acceptance policy, D06 = carrier scorecard spec, D10 = glossary, D04 = lane bidding,
D02 = detention. The correct answer needs **D01 and D06**.

**Q1.** Rank all five documents by **raw score sum**. Which two come out on top?

**Q2.** Rank them by **RRF with k = 60**. Show the arithmetic for D01 and D10.

**Q3.** What did RRF fix, and what did it *not* fix? What would you reach for next?

### Part 2 — Blended cost

Your 60-case golden set: **30 lookup, 18 condition, 12 synthesis.** From the bake-off:

| Strategy | recall — lookup | condition | synthesis | calls/query | p50 |
|---|---|---|---|---|---|
| Naive | 0.93 | 0.80 | 0.41 | 1.0 | 1.9 s |
| Corrective | 0.94 | 0.90 | 0.58 | 3.1 | 4.4 s |
| Decomposed | 0.93 | 0.83 | 0.87 | 3.4 | 4.8 s |
| FullStack | 0.95 | 0.92 | 0.89 | 5.2 | 7.9 s |

FullStack's overall recall is **0.91**.

**Q4.** Adaptive routing sends lookup → Naive, condition → Corrective, synthesis → Decomposed.
Blended calls per query? As a fraction of always-FullStack?

**Q5.** Blended recall, assuming a perfect router. Compare to FullStack's 0.91.

**Q6.** Blended p50 latency by the same weighting. Then say why that number is not actually the
system's median latency.

**Q7.** The router is 90% accurate, and its errors send synthesis questions to Naive. Recompute
blended recall. How many points did router error cost you?

<details>
<summary><b>Answers — do the arithmetic first</b></summary>

**Q1.** D10 = 0.61 + 18.2 = **18.81** · D04 = 0.55 + 11.6 = **12.15** · D01 = 0.74 + 9.4 =
**10.14** · D02 = **6.1** · D06 = **0.69**.
Ranking: **D10 > D04 > D01 > D02 > D06.** The glossary wins and the scorecard spec comes *last* —
purely because BM25's numbers are twenty times larger than cosine's. Neither answer document is in
the top two. This is what "just sum the scores" does to you.

**Q2.** D01 = 1/(60+1) + 1/(60+3) = 0.016393 + 0.015873 = **0.032266**
D10 = 1/(60+3) + 1/(60+1) = 0.015873 + 0.016393 = **0.032266**
D04 = 1/64 + 1/62 = 0.015625 + 0.016129 = **0.031754** · D06 = 1/62 = **0.016129** ·
D02 = 1/64 = **0.015625**
Ranking: **D01 = D10 > D04 > D06 > D02.**

**Q3.** RRF fixed the **scale** problem: D01 climbed from 3rd to 1st-equal, and D06 climbed above
D02. Nothing about numeric range decides anything now.
It did **not** fix the retrieval quality problem: BM25 still loves the glossary, so D10 still ties
for first, and D06 — which you need — is still only 4th. Fusion cannot manufacture relevance that
neither retriever found. Next move: Pattern D, a relevance grader that drops D10 before generation;
or Pattern C, decomposing so that "what are the scorecard bands?" is its own query and pulls D06
to rank 1 in a list of its own.

**Q4.** (30×1.0 + 18×3.1 + 12×3.4) / 60 = (30 + 55.8 + 40.8)/60 = 126.6/60 = **2.11 calls/query**.
Against FullStack's 5.2 that's **40.6%**.

**Q5.** (30×0.93 + 18×0.90 + 12×0.87)/60 = (27.9 + 16.2 + 10.44)/60 = 54.54/60 = **0.909**.
FullStack is 0.910. **Statistically indistinguishable quality at 41% of the calls** — that's the
slide, and you derived it on paper before writing any code.

**Q6.** (30×1.9 + 18×4.4 + 12×4.8)/60 = **3.23 s** — which is the *mean of the per-bucket p50s*, a
different quantity from the system's p50. **The median of a mixture is not the weighted mean of the
medians.** Half your traffic is lookups at ~1.9 s, so the true p50 sits near the top of the lookup
distribution, well under 3.23 s. Measure the p50 and p95 of the mixture; never derive a percentile
by averaging percentiles.

**Q7.** Synthesis expected recall = 0.9(0.87) + 0.1(0.41) = 0.783 + 0.041 = **0.824**.
Blended = (27.9 + 16.2 + 12×0.824)/60 = (27.9 + 16.2 + 9.888)/60 = 53.988/60 = **0.900**.
Router error cost **0.9 points** — about one point of recall for 10 points of router accuracy. Which
tells you where to spend your next hour: a 95%-accurate router is worth more than any tuning of the
strategies it routes to, and it's the cheapest thing in the system to improve.

</details>

---

## 4. What people get wrong

**"Agentic RAG means an agent with a search tool."**
That's one implementation of one pattern, and the hardest to test. Three of the four patterns
aren't loops at all — routing and rewriting are single extra calls in a fixed pipeline.

**"Stack all four and you get the best system."**
You get 5.2 calls and 7.9 s p50 to fix a bucket that's 12% of traffic. §3 Q4–Q5: routing to the
cheapest sufficient strategy gets 99.9% of the quality for 41% of the calls.

**"HyDE works because the hypothetical answer is accurate."**
You throw the text away and keep only the vector. It works because a hypothetical answer is
*document-shaped*. It fails on wrong domain, not wrong numbers.

**"Decomposition always helps multi-hop."**
It helps Shapes A and B and hurts single-hop, where three overlapping retrievals give the
synthesiser a reconciliation problem it didn't have. Detect, don't always.

**"Summing similarity scores is a reasonable fusion."**
§3 Q1. The glossary wins and the answer document comes last, decided entirely by numeric range.

**"The relevance grader is objective."**
It's a model with a rubric. Check its yes-rate — 95% yes means it's agreeing, not grading.

**"Rewriting improved retrieval, so evaluate against the rewritten query."**
No. Your golden set labels *documents* for the *original* question. Evaluate against those labels
or you're measuring whether the rewriter agrees with itself.

**"Recall@5 went up, so the answers got better."**
Different axes. The corrective pattern moves faithfulness and refusal correctness hard while barely
touching recall — that's the whole point of it, and a recall-only report hides it.

**"The state graph made the system smarter."**
It made the state explicit, checkpointed, and resumable. Retrieval decisions are identical.

---

## 5. The trainer's angle

**The analogy that lands, and it's exact:** naive RAG is a full table scan against one index.
Agentic RAG is a **query planner**. Routing is content-based routing at L7 — inspect the request,
pick the backend. Decomposition is a join plan, and the parallel-vs-sequential question is precisely
the difference between a hash join you can parallelise and a nested-loop join where the inner query
needs a row from the outer. Corrective RAG is a validation stage that can abort the plan. And RRF is
ranked-choice voting: you throw away the margin of victory and keep only the ordering, because
margins from different electorates aren't comparable.

**The demo that makes it click:** run the Ridgeline question through Naive and through Decomposed,
and put the **retrieved chunk IDs** side by side — not the answers. Naive returns four chunks from
document 01 and one glossary straggler. Decomposed returns two from 01 and two from 06. The room
sees that the generator was never the problem; it was never given document 06. Then show the latency
column and let the trade-off land while they're still convinced.

**The predictive question:** before the bake-off, ask *"which pattern fixes the synthesis bucket,
and what do you think it costs?"* Most rooms guess corrective RAG, because grading feels like
rigour. It's decomposition by a mile, and corrective barely moves recall at all — it moves
faithfulness. That surprise teaches the "different axes" point better than any explanation.

**The question a sharp student will ask:** *"If decomposition takes synthesis from 0.41 to 0.87, why
would I ever not decompose?"*

> Because it's 3.4 calls and 4.8 seconds against 1.0 and 1.9, and 50% of your traffic is lookups
> that decomposition makes slightly *worse* — three narrow retrievals overlap and the synthesiser
> has to reconcile them. Do the arithmetic: routing each question to the cheapest strategy that
> handles it gives you 0.909 against FullStack's 0.910 at 41% of the calls. So the real answer is
> that decomposition is the right tool for 20% of your questions and the wrong tool for the rest,
> and the highest-value component in the system turns out to be the cheap thing that decides which
> is which. That's also where to spend your next hour: ten points of router accuracy is worth about
> a point of blended recall, and a router is far cheaper to improve than a retriever.

---

## 6. Self-check

Cover the answers.

1. Name the three shapes of multi-hop failure and the pattern each one calls for.
2. Why does a single query vector do badly on a two-document question? Answer in Day 3's terms.
3. Three routing implementations, ascending cost. Which do most teams reach for first, and which
   should they try first?
4. How do you evaluate a router? Why isn't recall@5 the right metric?
5. Why does HyDE work? What is thrown away, and what failure mode remains?
6. What is step-back prompting for?
7. Write the RRF formula. Why ranks and not scores?
8. What does k=60 do, and what happens to a document ranked 3rd in three lists versus 1st in one?
9. What does RRF *not* fix?
10. How do you decide parallel vs. sequential decomposition without hardcoding it?
11. What's the tell that your relevance grader isn't working, and how do you fix it?
12. Name three things a state graph gives you over a loop, and one thing it does not.

<details>
<summary><b>Answers</b></summary>

1. A: two neighbourhoods, one query vector → decomposition or multi-query. B: unstated bridging
   entity → *sequential* decomposition. C: question isn't document-shaped → rewriting / HyDE.
2. The embedding is a single point. A question spanning two topics lands between two clusters and
   near neither; `k` slots get spent mostly in one. Topical proximity, not propositional match.
3. Embedding similarity to route descriptions (~free) → small-model classifier (1 cheap call) →
   tool-choosing agent (1+ full calls). Most reach for the agent; try the embedding router first
   and measure the gap.
4. As a classification problem — confusion matrix, per-class precision and recall. Recall@5
   measures the retriever downstream of the router, not the routing decision.
5. A hypothetical answer is document-shaped, so its vector sits in document-space rather than
   question-space. The generated text is discarded; only the vector is used, so wrong numbers are
   harmless. It fails when the hypothesis is in the wrong domain.
6. Retrieving general framing context for questions that presuppose a rule the retriever wouldn't
   otherwise surface.
7. `RRF(d) = Σᵢ 1/(k + rankᵢ(d))`. Ranks because scores are uncalibrated and incomparable across
   retrievers and queries; summing them lets the widest numeric range win.
8. It damps the top-rank advantage — 1/61 vs 1/63 is a 3% difference. Third in three lists
   (0.0476) beats first in one (0.0164): consensus beats a single confident hit.
9. Retrieval quality. If a retriever reliably surfaces the wrong document, RRF still ranks it
   highly — it just stops it winning by scale accident. Grade or decompose instead.
10. Have the planner emit `depends_on: list[int]` as a typed field. That gives you a DAG:
    topological sort, `asyncio.gather` per level, feed answers forward.
11. It says "relevant" ~95% of the time — it's agreeing, not grading. Fix the rubric with an
    explicit negative example and define relevance as *answers the question*, not *is about the
    topic*.
12. Explicit typed state, checkpointing, resumability from the failed node, drawable conditional
    edges, human-in-the-loop interrupts (any three). It does **not** make retrieval decisions any
    better.

</details>

**Scored below 9?** Re-read §2.4 and §2.5. The lab's `RewriteRag` fusion and `DecomposedRag`
dependency detection are exactly those two, and the bake-off is meaningless if the fusion is wrong.

---

## 7. Going deeper (optional)

- *Precise Zero-Shot Dense Retrieval without Relevance Labels* — Gao, Ma, Lin & Callan, 2022. The
  HyDE paper. Short, and §3's argument is the one in §2.3 above.
- *Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods* — Cormack,
  Clarke & Buettcher, SIGIR 2009. Two pages, and where k=60 comes from.
- *Self-RAG: Learning to Retrieve, Generate and Critique through Self-Reflection* — Asai et al.,
  2023. Note what's actually trained — reflection tokens — versus what people ship.
- *Corrective Retrieval Augmented Generation* — Yan et al., 2024. The retrieval evaluator and the
  web-search fallback.
- *Take a Step Back: Evoking Reasoning via Abstraction in Large Language Models* — Zheng et al.,
  2023.
- *Adaptive-RAG: Learning to Adapt Retrieval-Augmented LLMs through Question Complexity* — Jeong
  et al., NAACL 2024. This is §3 Part 2 as a paper, and it's the lab's stretch goal.
- *Interleaving Retrieval with Chain-of-Thought Reasoning* (IRCoT) — Trivedi et al., 2022, and
  *HotpotQA* — Yang et al., 2018, if you want the multi-hop benchmark lineage.

---

**Now go to `labs/DAY_08.md`.** The lab builds on §2.2 (you implement the router *both* ways and
report the gap), §2.3 (HyDE and multi-query), §2.4 (your fusion function — get this right first),
§2.5 (`depends_on` dependency detection), §2.6 (the grading loop, and check your grader's yes-rate),
and §2.8 (the written answer to "what did the graph buy me?").
