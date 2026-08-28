# Day 08 — Agentic RAG: Routing, Decomposition, and Self-Correction

**Mon Sep 7, 2026** · Week 2 · Maps to: **Module 02 — Agentic RAG** · Backend: **local** + `[PAID]` · Est. cost: **$2–4**

> **Before you start — read `learn/DAY_08_LEARN.md` (1:15).**
> The four agentic-RAG patterns and what each costs. The lab below assumes it and does not re-explain it.


---

## Why today matters

**FDE lens.** Today you fix the number that has been bothering you since Day 5: your
`synthesis` bucket at 0.41. Naive RAG does one retrieval per question. Real questions
need two, or a rewritten query, or a check that the retrieved context is actually
relevant before generating. Being able to walk a client from "our RAG gets 60% of
questions right" to a measured 85% in a week is the single most sellable skill in this
entire bootcamp.

**Trainer lens.** This is where students confuse "agentic RAG" with "an agent that has a
search tool." They're different, and the difference matters. Today you build four
distinct patterns and measure each, so you can teach them as a menu with costs attached
rather than a buzzword.

---

## Objectives

1. Implement four agentic-RAG patterns: **routing**, **query rewriting**, **decomposition**, **corrective/self-RAG**.
2. Measure each against your Day 5 golden set — improvement *and* cost.
3. Build a LangGraph state machine with conditional edges and explain when a graph beats a loop.
4. Produce an honest recommendation: which pattern for which question type, at what price.

---

## Schedule (5:00)

| Block | Time | What |
|---|---|---|
| 0 | 0:30 | Warm-up |
| 1 | 1:15 | **Learn** — `learn/DAY_08_LEARN.md` |
| 2 | 2:30 | Lab: build all four, measure all four |
| 3 | 0:30 | Teach-back #8 |
| 4 | 0:15 | Ship |

---

## Block 0 — Warm-up (0:30)

<!--cards-->
> **Cards first — 5 minutes.** Open **Warm-up drill** in the sidebar of `fde-bootcamp.html`.
> It deals you every card that is due from the days you have finished, hardest box first, and
> it is capped at 20 so it stays a drill. Cards you miss come back tomorrow; cards you know
> go 1 → 2 → 4 → 8 → 16 days out. Then do the recall below, closed book.
<!--/cards-->


1. Write the agent loop from memory. Five steps.
2. What does the OpenAI wire format do with `arguments` that Anthropic doesn't?
3. Three situations where you'd talk a client *out* of an agent.
4. Re-run yesterday's agent on a task with `max_cost_usd=0.02`. Correct `stop_reason`?

---

## Block 1 — Learn (1:15)

**Read `learn/DAY_08_LEARN.md` and work its examples on paper before continuing.**
Take the self-check at the end. Anything you miss goes on a flashcard and into tomorrow's
warm-up. The material below consolidates the module — it is not a substitute for it.

### Pattern A — Routing

A cheap classifier decides *where* the question goes before any retrieval happens.

```
question → router → { policy_corpus | shipment_db | calculator | refuse | web }
```

Why it matters: your corpus has policy documents. "What's shipment SHP-202608-0041729's
status?" should never touch the vector store. Routing avoids retrieving irrelevant
context, which is the cheapest quality win available.

Implementation choice, in order of preference:
1. **Structured classification** with a small model — fast, cheap, testable.
2. **Embedding similarity to route descriptions** — free, no LLM call, surprisingly good.
3. **Tool-calling agent choosing** — most flexible, most expensive, hardest to test.

Most teams jump to 3. Try 2 first and measure — you will often find it's within a few
points of 3 at zero marginal cost. That measurement is a great teaching moment.

### Pattern B — Query rewriting / expansion

The user's question is rarely the best search query.

- **Rewrite**: "how much do I get charged for sitting at the dock" → "detention charges free time hourly rate"
- **HyDE** (Hypothetical Document Embeddings): generate a fake *answer*, embed that, search
  with it. Answers look like documents; questions don't. Often a large win.
- **Multi-query**: generate 3 paraphrases, retrieve for each, reciprocal-rank-fuse the results.
- **Step-back**: ask a more general question first to get framing context, then the specific one.

Cost: 1 extra small-model call. Benefit on your `condition` and `lookup` buckets: measure it.

### Pattern C — Decomposition

For multi-hop questions. This is the fix for your 0.41.

```
"If a carrier's FTA drops to 83% for two quarters, what happens and how does that
 affect their scorecard band?"
    ↓ decompose
 [1] "What happens when FTA falls below 85% for two consecutive quarters?"   → doc 01
 [2] "How is the composite scorecard score calculated and what are the bands?" → doc 06
    ↓ retrieve each independently, then synthesise
```

Key design decision: **parallel or sequential?** Parallel when sub-questions are
independent (faster, cheaper). Sequential when sub-question 2 depends on the answer to 1
("which carrier has the worst FTA, and what's their detention exposure?" — you can't
write query 2 until you know the carrier). Detect which case you're in; don't hardcode.

### Pattern D — Corrective / Self-RAG

Add a grading step between retrieval and generation:

```
retrieve → grade each chunk (relevant? yes/no) → 
   if enough relevant  : generate
   if some relevant    : generate with only those
   if none relevant    : rewrite query and retry (once)
   if still none       : refuse
after generation       : grade the answer for groundedness → regenerate once if unsupported
```

This is the pattern that most directly buys you the *refusal* behaviour clients trust.
It also roughly doubles your cost per query. Both facts go in your recommendation.

---

## Block 2 — Lab (2:30)

### 2.1 Build the four patterns (100 min)

`src/fdekit/agentic_rag.py`. Each pattern is a class with the same interface so you can
swap and measure:

```python
class Strategy(Protocol):
    name: str
    def answer(self, question: str) -> Answer: ...

class NaiveRag(Strategy): ...          # your Day 4 baseline
class RoutedRag(Strategy): ...         # A
class RewriteRag(Strategy): ...        # B — implement HyDE and multi-query
class DecomposedRag(Strategy): ...     # C — with dependency detection
class CorrectiveRag(Strategy): ...     # D
class FullStack(Strategy): ...         # route → rewrite → decompose → grade → generate
```

Suggested pacing: 20 min each for A/B/C/D, 20 min for FullStack.

For the router, implement **both** the embedding approach and the LLM-classifier approach
so you can report the difference. It's a 15-minute add and it makes your teach-back real.

### 2.2 The bake-off (50 min)

Run all six strategies against your 60-case golden set. Produce
`evals/day08_strategy_bakeoff.md`:

```
                    Naive  Routed  Rewrite  Decomp  Corrective  FullStack
Recall@5 overall     0.78    0.79    0.86     0.88      0.83       0.91
  · lookup           0.93    0.94    0.95     0.93      0.94       0.95
  · synthesis        0.41    0.42    0.55     0.87      0.58       0.89
  · condition        0.80    0.81    0.88     0.83      0.90       0.92
Faithfulness         0.84    0.85    0.86     0.85      0.94       0.94
Refusal correct      0.40    0.80    0.40     0.40      1.00       1.00
LLM calls / query     1.0     2.0     2.0      3.4       3.1        5.2
Latency p50           1.9s    2.4s    3.1s     4.8s      4.4s       7.9s
Cost / query        $0.0011 $0.0013 $0.0019  $0.0034   $0.0031    $0.0058
```

(Illustrative shape — your numbers will differ. The **shape** is what you're learning:
every quality gain has a latency and cost column next to it.)

### 2.3 LangGraph state machine (15 min)

Rebuild `CorrectiveRag` as a LangGraph graph with conditional edges:

```
        ┌──────────┐
        │ retrieve │
        └────┬─────┘
             ▼
        ┌──────────┐   none relevant   ┌─────────┐
        │  grade   ├──────────────────►│ rewrite │──┐
        └────┬─────┘                   └─────────┘  │
             │ relevant                    ▲        │
             ▼                             └────────┘ (max 1 retry)
        ┌──────────┐    ungrounded    ┌──────────────┐
        │ generate ├─────────────────►│  regenerate  │
        └────┬─────┘                  └──────────────┘
             ▼
           answer / refuse
```

Now answer, in writing: **what did the graph give you that the loop didn't?** The honest
answer is usually: explicit state, checkpointing, resumability, and a picture you can
show a client. Not intelligence. Say that clearly and you'll be one of the few people
in the room who understands what they bought.

---

## Block 3 — Teach-back #8 (0:30)

Record 10 min: **"Agentic RAG is four patterns, and three of them cost you latency."**
`teaching/recordings/day_08.mov`

Lead with your bake-off table. Walk one row — the synthesis row — from 0.41 to 0.89 and
name exactly which pattern did it. Then show the latency row and ask the audience the
question a client will ask: *"is 8 seconds acceptable for your users?"*

Teaching a trade-off honestly is harder than teaching a technique. This is the rep.

---

## Block 4 — Ship (0:15)

```bash
git add -A && git commit -m "Day 08: four agentic RAG patterns, measured bake-off, LangGraph state machine" && git push
```

---

## Done when

- [ ] Six strategies implemented behind one interface
- [ ] Full bake-off table with quality, latency, calls, and cost per strategy, segmented by difficulty
- [ ] Synthesis bucket materially improved — name the pattern responsible
- [ ] Router implemented both ways with the difference measured
- [ ] LangGraph version working, with a written answer to "what did the graph buy me?"
- [ ] A one-paragraph recommendation: which pattern you'd ship, for which question mix, and why

---

## Trap list

- Stacking all four patterns by default. You just made a 1-second system take 8 seconds
  to fix a bucket that's 12% of traffic. Route by question type instead.
- Rewriting the query and then evaluating retrieval against the *original* question's
  labels. Your golden set labels documents, not queries — make sure that holds.
- Decomposing questions that don't need it. Detect, don't always.
- A grader that grades everything "relevant." Check its distribution — if it says yes
  95% of the time, it's not grading, it's agreeing.
- Reporting only the strategy that won.

---

## Stretch

Implement **adaptive routing**: a cheap classifier predicts the question's difficulty
class and sends it to the cheapest strategy that handles that class. Measure the blended
cost and latency against always-FullStack. If you can show "94% of FullStack's quality
at 40% of the cost," that is a genuinely excellent slide and a genuinely excellent
consulting recommendation.
