# Day 05 — Evals: Making "It Seems Better" Into a Number

**Wed Sep 2, 2026** · Week 1 · Maps to: **Module 05 — Evals** · Backend: **local** + `[PAID]` judge · Est. cost: **$1–3**

> **Before you start — read `learn/DAY_05_LEARN.md` (1:15).**
> The eval ladder, retrieval metrics, judge bias, Cohen's kappa. The lab below assumes it and does not re-explain it.


---

## Why today matters

**FDE lens.** This is the day you stop being a person who builds demos and start being a
person who ships systems. Every engagement reaches a moment where the client says "can
you make it better?" Without an eval you are guessing, and worse, you're guessing in
public. With an eval you can say "the change moved faithfulness from 0.71 to 0.86 and
cost 12% more latency; here's the trade-off, you decide." That sentence is the whole job.

**Trainer lens.** Evals are the least-taught and most-needed part of the curriculum.
Most courses show RAGAS for ten minutes. You're going to build the harness by hand
first so you can teach *why* each metric exists and where each one lies to you.

You're doing evals in Week 1 on purpose. Every lab after today is measurable, so the rest of
the bootcamp compounds instead of accumulating.

---

## Objectives

1. Generate a synthetic golden dataset from your corpus, then correct it by hand.
2. Compute retrieval metrics (Recall@k, MRR, nDCG) from scratch and say what each misses.
3. Build an LLM-as-judge for faithfulness and answer relevance — and then **evaluate the judge**.
4. Produce a scorecard that fits on one screen and that a non-engineer can read.

---

## Schedule (5:00)

| Block | Time | What |
|---|---|---|
| 0 | 0:30 | Warm-up |
| 1 | 1:15 | **Learn** — `learn/DAY_05_LEARN.md` |
| 2 | 2:45 | Lab: golden set → metrics → judge → scorecard → first A/B |
| 3 | 0:30 | Teach-back #5 |

---

## Block 0 — Warm-up (0:30)

<!--cards-->
> **Cards first — 5 minutes.** Open **Warm-up drill** in the sidebar of `fde-bootcamp.html`.
> It deals you every card that is due from the days you have finished, hardest box first, and
> it is capped at 20 so it stays a drill. Cards you miss come back tomorrow; cards you know
> go 1 → 2 → 4 → 8 → 16 days out. Then do the recall below, closed book.
<!--/cards-->


Closed book: state the four clauses of the RAG contract and, for each, the experiment
that tells you it's the one that's broken.

Then re-run Break 3 from yesterday. Still reproducible?

---

## Block 1 — Learn (1:15)

**Read `learn/DAY_05_LEARN.md` and work its examples on paper before continuing.**
Take the self-check at the end. Anything you miss goes on a flashcard and into tomorrow's
warm-up. The material below consolidates the module — it is not a substitute for it.

### 1.1 The evaluation ladder

You need all four rungs. Clients will ask for the top one first; you build bottom-up.

| Rung | Measures | Cost | Trust |
|---|---|---|---|
| **1. Unit / invariant** | Does the evidence quote exist in the chunk? Is the JSON valid? | Free, instant | Total |
| **2. Retrieval metrics** | Recall@k, MRR, nDCG against labelled relevance | Free after labelling | High, but only measures retrieval |
| **3. LLM-as-judge** | Faithfulness, relevance, completeness | ~$0.002/case | Medium — needs its own eval |
| **4. Human / domain expert** | Is this actually right and useful? | Expensive, slow | Ground truth |

The mistake everyone makes is starting at rung 3 and never building rung 1. Rung 1 is
free, runs in CI, and catches the most embarrassing failures. Build it first, always.

### 1.2 Retrieval metrics, and what each hides

Implement these yourself today — they're five lines each and knowing them cold is
non-negotiable for teaching:

- **Recall@k** = (relevant docs in top k) / (total relevant). *Hides ranking entirely* —
  rank 1 and rank 5 score the same.
- **Precision@k** = (relevant in top k) / k. *Punishes you for k you chose*, so it's
  only comparable at fixed k.
- **MRR** = mean of 1/rank-of-first-relevant. *Only sees the first hit* — useless for
  multi-hop questions where you need two documents.
- **nDCG@k** = discounted gain, normalised. Handles graded relevance and rank. *Hardest
  to explain to a client*, which matters more than people admit.
- **Hit rate** = fraction of queries with ≥1 relevant in top k. Crude, but the one
  executives actually understand.

Your multi-hop query from yesterday (FTA + scorecard bands) is the case that exposes
MRR. Use it as the teaching example.

### 1.3 The judge problem

An LLM judge is a model evaluating a model. Four ways it lies to you:

1. **Self-preference** — a model rates its own output higher. Judge with a *different*
   model family than the generator. If your generator is local Llama, judge with
   `gpt-4o-mini` or Claude.
2. **Position bias** — in pairwise comparison, the first option wins more often. Fix:
   run both orders, average.
3. **Verbosity bias** — longer answers score higher regardless of quality. Fix: include
   length in your analysis; check whether score correlates with token count. It will.
4. **Rubric drift** — vague rubrics ("rate 1–10 for quality") produce noise. Fix: binary
   or 3-point scales with explicit anchors, and require the judge to quote evidence.

And the rule people skip: **evaluate your judge.** Label 25 cases yourself. Compute
judge-vs-you agreement (Cohen's κ). If κ < 0.6, your judge is measuring something other
than what you care about and every number downstream is decorative.

---

## Block 2 — Lab (2:45)

### 2.1 Generate the golden set (45 min)

`labs/day05/make_goldenset.py`:

```python
# For each chunk in the corpus:
#   ask the model to produce 2 questions answerable ONLY from that chunk,
#   plus the exact answer span, plus a difficulty label:
#     - "lookup"    single fact, one chunk
#     - "synthesis" needs 2+ chunks
#     - "condition" the number is only correct with its condition attached
#     - "absent"    NOT answerable from the corpus (you write these by hand)
# Output: evals/goldenset_v1.jsonl
#   {"id","question","expected_answer","relevant_doc_ids":[...],"difficulty"}
```

Target: **60 cases** — 30 lookup, 15 synthesis, 10 condition, 5 absent.

Then spend **20 minutes reviewing them by hand.** You will find that maybe a quarter are
bad: ambiguous, trivially leading ("According to the document, what is $65?"), or
answerable from general knowledge. Delete or fix them.

**This manual pass is the lab.** Synthetic golden sets are how you get to 60 cases in an
hour; hand-review is how they become worth anything. Every course that skips this
produces students who trust bad numbers. Write down what fraction you rejected — that
number goes in your Day 22 lesson.

The 5 "absent" cases are load-bearing: they're the only way to measure whether your
refusal path works. A system that scores 0.95 faithfulness and never refuses is not
a good system; it's an untested one.

### 2.2 Metrics from scratch (40 min)

`src/fdekit/evals.py`:

```python
def recall_at_k(retrieved_ids, relevant_ids, k) -> float: ...
def precision_at_k(...) -> float: ...
def mrr(...) -> float: ...
def ndcg_at_k(retrieved_ids, relevance_grades, k) -> float: ...
def hit_rate(...) -> float: ...

def evaluate_retrieval(pipeline, goldenset, ks=(1,3,5,10)) -> pd.DataFrame:
    """One row per query, one column per metric. Group by difficulty."""
```

Run it. Look at the breakdown **by difficulty**. Your aggregate number will look fine and
your `synthesis` bucket will be terrible. That gap is the most important finding of the
day — and the reason Week 2 exists.

### 2.3 LLM-as-judge `[PAID]` (50 min)

`src/fdekit/judge.py` — three judges, each with a tight rubric:

```python
def judge_faithfulness(question, answer, context) -> Verdict:
    """Is every claim in the answer supported by the context?
    Return: {"verdict": "supported"|"partially"|"unsupported",
             "unsupported_claims": [...], "reasoning": "..."}
    Decompose the answer into atomic claims first, judge each. Aggregate."""

def judge_relevance(question, answer) -> Verdict:
    """Does the answer address the question asked? 3-point anchored scale."""

def judge_completeness(question, answer, expected_answer) -> Verdict:
    """Does it contain the expected facts? Which are missing?"""
```

Claim decomposition matters: judging a whole paragraph gives you mush. Judging
"detention is $65/hour" and "free time is 2 hours" and "billed in 15-min increments"
separately gives you a faithfulness *rate* and tells you exactly which claim was invented.

**Then evaluate the judge (20 min of the 50).** Hand-label 25 answers yourself,
blind. Compute agreement:

```python
from sklearn.metrics import cohen_kappa_score
print(cohen_kappa_score(my_labels, judge_labels))
```

Record κ in `evals/day05_judge_calibration.md`. If it's low, tighten the rubric — add
anchors, force evidence quotes — and re-measure. Iterating on a *rubric* rather than a
prompt is a distinct skill and a great 10-minute teaching segment.

### 2.4 Scorecard + your first honest A/B (30 min)

`labs/day05/scorecard.py` → prints and writes `evals/scorecard_YYYYMMDD.md`:

```
RAG v1 — 60 cases — 2026-08-29
                          overall   lookup  synthesis  condition  absent
Recall@5                    0.78     0.93      0.41      0.80       —
MRR                         0.71     0.88      0.34      0.72       —
Faithfulness (judge)        0.84     0.91      0.62      0.71       —
Citation verified           0.79     0.88      0.55      0.68       —
Refusal correct               —        —         —         —       0.40
Mean latency                1.9 s
Cost / query              $0.0011
```

Now run **one** A/B. Change exactly one thing — k from 5 to 3, or fixed chunker to
markdown chunker — and re-run the whole scorecard. Write two sentences: what moved,
what regressed, and whether you'd ship it.

That "what regressed" half is what separates an engineer from someone reporting
selectively. Almost every improvement costs you something. Find the cost.

---

## Block 3 — Teach-back #5 (0:30)

Record 10 min: **"Your eval is lying to you: three ways."**
`teaching/recordings/day_05.mov`

Cover, with your own numbers:
1. The aggregate score that hides a broken bucket (your synthesis row).
2. The judge that agrees with itself and not with you (your κ).
3. The golden set that measures reading comprehension instead of retrieval (your
   rejected-question rate from 2.1).

End with the one-screen scorecard and this line: *"If you can't show me this, you don't
know whether your change helped."*

---

## Done when

- [ ] `evals/goldenset_v1.jsonl` — 60 hand-reviewed cases across 4 difficulty labels
- [ ] All five retrieval metrics implemented from scratch and unit-tested
- [ ] Three judges running with claim decomposition
- [ ] Cohen's κ measured and recorded for your judge
- [ ] One scorecard committed, one A/B run with regressions named

---

## Trap list

- Reporting only the aggregate. Always segment.
- Judging with the same model that generated. Guaranteed self-preference.
- A golden set with no unanswerable cases. You have no refusal metric.
- Changing two things and attributing the improvement to the one you liked.
- Treating κ = 0.4 as "reasonable agreement." It isn't.
- Running the eval only when you expect it to look good.

---

## Stretch

Wire up **RAGAS** on the same golden set and compare its faithfulness score to yours.
Where they disagree, read RAGAS's source for that metric. Knowing what a popular library
actually computes — and being able to say "it decomposes claims differently than you'd
expect" — is exactly the depth that makes a trainer credible.
