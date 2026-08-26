# Day 05 · Learn — Measuring a system that has no right answer

**Read before `labs/DAY_05.md`. Budget 1:15. Pen and paper for §3 — there's real arithmetic and one result that should surprise you.**

---

## 1. Where this sits

Yesterday you built a pipeline with a dozen free parameters. Chunk size. Chunker strategy. k.
Reordering on or off. Refusal threshold. Two prompt rules you added because you saw a failure and
four you added because they seemed sensible. Every one has a defensible argument on both sides,
and right now you cannot tell which side is right.

That's the problem today solves. Every engagement reaches the moment where the client says "can
you make it better?" Without an instrument you're guessing — in public, in front of someone
paying for expertise. With one you can say *"the change moved faithfulness from 0.71 to 0.86 and
cost 12% more latency; here's the trade-off, you decide."* That sentence is most of the job.

Evals land in Week 1 deliberately: every lab after today is measurable, so the rest of the
bootcamp compounds instead of accumulating.

---

## 2. The mechanism

### 2.1 The ladder

Four rungs. You need all of them, and the order you build them in is the opposite of the order
clients ask for them.

| Rung | Measures | Cost | Trust |
|---|---|---|---|
| **1 · Unit / invariant** | Does the evidence quote exist in the chunk? Is the JSON valid? Did a refusal parse? | Free, instant, runs in CI | Total |
| **2 · Retrieval metrics** | Recall@k, MRR, nDCG against labelled relevance | Free after labelling | High — but it only measures retrieval |
| **3 · LLM-as-judge** | Faithfulness, relevance, completeness | ~$0.002/case | Medium, and it needs its own eval |
| **4 · Human / domain expert** | Is this actually right and useful? | Expensive, slow | Ground truth by definition |

The universal mistake is starting at rung 3 — the one that looks like AI — and never building
rung 1. Rung 1 is free, deterministic, catches the most embarrassing failures and runs on every
commit. **Build it first, always.**

The ladder also encodes this: each rung measures a different thing, and a good number on one
tells you nothing about the others. Recall@5 of 0.93 with faithfulness of 0.62 finds the right
document and then makes things up. Recall of 0.41 with faithfulness of 0.95 faithfully reports
the wrong chunk. Both look fine if you report one row.

### 2.2 The golden set is the product

Your metrics are exactly as good as the dataset they run on, and that dataset is the artefact
you'll still be using in month six.

**Composition matters more than size.** Sixty cases split 30 lookup / 15 synthesis / 10 condition
/ 5 absent tells you far more than three hundred lookups, because the four labels fail
differently:

- **lookup** — one fact, one chunk. "What's the TONU charge?" You'll be good at these and they'll
  dominate your aggregate.
- **synthesis** — needs two or more chunks. "If a carrier's FTA drops to 83% for two quarters,
  what happens, and how does that affect their scorecard band?" needs doc 01 *and* doc 06.
- **condition** — the number is only correct with its condition attached. For a 5-hour detention
  wait, $325 is wrong and $195 is right; only the free-time condition separates them.
- **absent** — not answerable from the corpus. The only way to measure refusal, which from Day 4
  §3 Q5 is often the cheapest fix available.

**The contamination problem, which nobody teaches.** Show a model a chunk and ask "write a
question this chunk answers," and the question inherits the chunk's vocabulary. "According to the
policy, what is the per-hour detention rate?" shares `detention`, `per hour` and `rate` with the
source, so your retriever finds it trivially. **You have measured lexical overlap and called it
recall.** Real users write "what do I get charged for sitting at the dock" — the
vocabulary-mismatch case from Day 3 that dense retrieval exists to solve, and the one your
synthetic set never tests.

The fix is the hand-review pass, and it is the actual lab today. Expect to reject or rewrite
about a quarter: leading questions ("According to the document, what is $65?"), ambiguous ones,
ones answerable from general knowledge, and ones that are the source sentence with a question
mark. **Write down the fraction you rejected** — that number is the most useful thing you'll ever
be able to tell a room about synthetic data.

### 2.3 Retrieval metrics, and what each one hides

Five metrics, about five lines of code each. Know them cold — you'll be asked to explain the
difference on a whiteboard.

**Recall@k** = (relevant in top k) / (total relevant). *Hides ranking completely* — rank 1 and
rank 5 score identically. Still the right headline metric, because (Day 4 §2.3) recall is the hard
ceiling on everything downstream.

**Precision@k** = (relevant in top k) / k. *Punishes you for a k you chose*, so it's comparable
only at identical k. Rarely what you want in RAG: you don't care that 3 of 5 chunks were noise if
the answer got through.

**MRR** = mean of 1 / (rank of the first relevant result). *Only ever sees the first hit.* On a
synthesis question needing two documents it scores 1.0 when the first is at rank 1, even if the
second never appeared. **MRR is structurally blind to the exact failure your synthesis bucket
has** — wrong headline metric here, fine one for a search box.

**nDCG@k** — discounted cumulative gain, normalised. The only one of the five handling *graded*
relevance (essential / helpful / noise) and rank position together:

```
DCG@k  = Σ (relᵢ / log₂(i + 1))       for i = 1..k, i is 1-indexed
IDCG@k = the same sum over the ideal ordering (grades sorted descending)
nDCG@k = DCG@k / IDCG@k
```

The discount is the whole idea: rank 1 divides by log₂(2) = 1 (no penalty), rank 2 by 1.585,
rank 5 by 2.585. Gain decays logarithmically because attention does. Normalising by the ideal
makes it comparable across queries with different numbers of relevant documents.

*One trap when comparing to a library:* two common gain formulations exist — linear `relᵢ` and
exponential `2^relᵢ − 1`. They give different numbers on the same ranking and defaults differ
between tools. Check which you're reading before comparing.

**Hit rate@k** = fraction of queries with at least one relevant doc in the top k.
Crude, throws away everything, and the one an executive will actually understand and repeat. Keep
it on the scorecard for exactly that reason.

### 2.4 Why the aggregate lies

You'll compute Recall@5 = 0.78 across sixty cases and feel fine. Segment it and find lookup at
0.93 and synthesis at 0.41.

This is a P50 latency that looks healthy while one shard is on fire, and you have the reflex
already: **never report a mean over a heterogeneous population.** The aggregate is a weighted
average of buckets that behave differently, so it moves when the *mix* moves even if the system
didn't. Your golden set is 25% synthesis by construction; if the client's real traffic is 50%
synthesis, your reported 0.78 is a fiction and the honest number is 0.67.

So: **segment every row of the scorecard**, and **ask the client for their question mix** — or
state your mix assumption on the slide. An unqualified aggregate is the easiest thing in your deck
for a sharp person to dismantle.

### 2.5 LLM-as-judge, and the four ways it lies

Rungs 1 and 2 can't tell you whether an answer is *faithful*. That needs judgement, and human
judgement doesn't scale to 600 evaluations a day. So you use a model, and inherit its biases.

**Self-preference.** Models rate their own outputs higher. Judge with a different model family
than the generator — local Llama generating, `gpt-4o-mini` or Claude judging. Not optional; "we
used the same model, it's fine" is the most common way an eval gets quietly invalidated.

**Position bias.** In pairwise comparison, whichever option is presented first wins more often —
substantially, and it persists in strong models. Fix: run both orderings and average, or call it a
tie unless both orderings agree.

**Verbosity bias.** Longer answers score higher, roughly independent of quality. Don't just "be
aware" of it — regress your judge scores against answer token count. If the correlation is strong,
your faithfulness metric is partly a length metric.

**Rubric drift.** "Rate this 1–10 for quality" produces noise with a mode at 8. Fix: binary or
three-point scales with written anchors for each level, and require the judge to quote its
evidence — which constrains the judgement to something checkable, exactly as it does in your
generator.

**And the technique that matters most: decompose into atomic claims before judging.** A
paragraph-level verdict is mush. Split into "detention is $65/hour", "free time is 2 hours",
"billed in 15-minute increments", "capped at $650" and judge each against the context. Now you
have a faithfulness *rate* — 3 of 4 supported — and you know exactly which claim was invented.

### 2.6 Evaluate the judge — and why raw agreement won't do it

The rule everybody skips: **your judge is a measurement instrument, so it needs calibration
against a standard.** Hand-label 25 cases yourself, blind, then compare.

The naive comparison is raw agreement — what fraction of the 25 you labelled the same. It is
almost useless, and §3 shows exactly why: a judge that says "supported" to everything scores 80%
agreement on a set that's 80% supported.

**Cohen's κ** corrects for agreement expected by chance:

```
κ = (p_o − p_e) / (1 − p_e)

p_o = observed agreement
p_e = agreement expected if both raters labelled independently at their own base rates
    = Σ over classes of  P(you say c) × P(judge says c)
```

κ = 1 is perfect, κ = 0 is exactly chance, negative is worse than chance.

The conventional bands come from Landis & Koch (1977): 0.21–0.40 fair, 0.41–0.60 moderate,
0.61–0.80 substantial, above 0.81 almost perfect. **Be honest that these are conventions from a
1977 biostatistics paper with no theoretical justification, and are widely criticised.** They're
the shared vocabulary, so use them and say where they came from. The working threshold here is
the lab's: **below 0.6, your judge is measuring something other than what you care about, and
every number downstream is decorative.**

One caveat to carry, because a statistically literate client will raise it: κ is depressed by
imbalanced prevalence — the "kappa paradox" (Feinstein & Cicchetti, 1990). When 90% of cases are
faithful, high agreement produces a low κ almost mechanically. So report κ **and** the per-class
recall on the class you care about: *of the answers I judged unfaithful, what fraction did the
judge catch?* That second number tells you whether the judge will find your failures, and it's
the one for the slide.

### 2.7 A/B discipline, and the noise floor nobody computes

Change exactly one thing. Re-run the *whole* scorecard, not the row you expect to move. Write two
sentences: what improved, what regressed, whether you'd ship it. **Almost every improvement costs
you something** — the reranker that lifts recall costs 200ms; the tighter refusal that kills wrong
answers kills nine correct ones too — and naming that cost separates an engineer from someone
selecting evidence.

Now the routinely-skipped, routinely-embarrassing part. **At 60 cases, most observed movements are
noise.** The standard error of a proportion is √(p(1−p)/n):

```
√(0.78 × 0.22 / 60) = √0.00286 = 0.053
```

**One standard error is 5.3 percentage points**, and a 95% interval is roughly ±10. So 0.78 → 0.82
is well inside the noise, and reporting it as an improvement is reporting a coin flip.

Two responses, in order of value. **Pair the comparison** — run both variants on *the same* 60
cases and look only at the cases that changed verdict. If 6 flipped wrong→right and 3
right→wrong, the argument is about 9 cases, not 60, and you can read all nine. That's McNemar's
test in spirit, and even without the p-value the paired design cuts variance sharply. Then **read
those discordant cases by hand**: nine hand-read failures teach you more than any p-value at this
scale. Significance testing is what you reach for at 600 cases.

The rule worth memorising: **at n = 60, treat anything under about 10 points as "go read the
cases," not as a result.**

---

## 3. Worked example — on paper

### Part A — retrieval metrics

> **Query** (synthesis): *"If a carrier's FTA drops to 83% for two quarters, what happens, and how
> does that affect their scorecard band?"* Truly relevant: **doc 01** (Lane Review below 85% for
> two consecutive quarters) and **doc 06** (scorecard bands).
>
> Your retriever returns, in order: **06, 04, 09, 01, 02**. Graded relevance: 06 → **3**,
> 01 → **3**, 04 → **1** (FTA appears in award logic, marginally useful), 09 → **0**, 02 → **0**.

**Q1.** Recall@5 and Recall@3.

**Q2.** Precision@5 and Precision@3.

**Q3.** MRR for this query. What does it claim about your system?

**Q4.** nDCG@5. Show DCG and IDCG. (Linear gain, `relᵢ / log₂(i+1)`; log₂3 = 1.585, log₂4 = 2,
log₂5 = 2.322.)

**Q5.** Which single metric goes in front of an executive, and which do you look at yourself?

### Part B — judge calibration

> You hand-label 25 answers `supported` / `unsupported`, blind. Against the judge:
>
> |  | judge: supported | judge: unsupported |
> |---|---|---|
> | **you: supported** | 18 | 2 |
> | **you: unsupported** | 3 | 2 |

**Q6.** Compute p_o, p_e, and κ. What band is that?

**Q7.** A lazy judge that returns `supported` for every case: what is its raw agreement on this
set, and what is its κ? What does that tell you about reporting raw agreement? And separately:
of the 5 answers you judged unsupported, how many did the real judge catch?

<details>
<summary><b>Answers — work them first, especially Q6 and Q7</b></summary>

**Q1.** Both relevant docs (06 at rank 1, 01 at rank 4) are in the top 5 → **Recall@5 = 1.00**.
Only 06 is in the top 3 → **Recall@3 = 0.50**.

**Q2.** **Precision@5 = 2/5 = 0.40.** **Precision@3 = 1/3 = 0.33.** Precision fell purely because
you chose k=5 — which is why it isn't comparable across systems at different k.

**Q3.** First relevant result is at rank 1, so **MRR = 1.00**. It claims perfection while Recall@3
says you found half the required evidence. **This is the case that exposes MRR**: on a
multi-document question, "the first hit was at rank 1" is not "the system found what it needed,"
and MRR cannot tell the difference.

**Q4.**
```
DCG@5  = 3/1 + 1/1.585 + 0/2 + 3/2.322 + 0/2.585
       = 3 + 0.631 + 0 + 1.292 + 0
       = 4.923

ideal ordering by grade: 3, 3, 1, 0, 0
IDCG@5 = 3/1 + 3/1.585 + 1/2 + 0 + 0
       = 3 + 1.893 + 0.5
       = 5.393

nDCG@5 = 4.923 / 5.393 = 0.913
```
**0.913** — high, and correctly so: you retrieved everything essential, with a useful doc at rank
4 instead of rank 2. nDCG is the only one of the five that captures "found both, but the second
was buried."

**Q5.** To the executive: **hit rate**, or Recall@5 if they'll take a fraction — it answers "did it
find the answer" in one number they can repeat in a meeting. To yourself: **Recall@k segmented by
difficulty**, because it's the ceiling on everything downstream and the segmentation is where the
finding lives. nDCG is the most informative and hardest to explain, which matters more than
technical people like to admit — a metric nobody trusts doesn't drive a decision.

**Q6.**
```
p_o = (18 + 2) / 25 = 0.80

your marginals:   supported 20/25 = 0.80   unsupported 5/25  = 0.20
judge marginals:  supported 21/25 = 0.84   unsupported 4/25  = 0.16

p_e = (0.80 × 0.84) + (0.20 × 0.16) = 0.672 + 0.032 = 0.704

κ = (0.80 − 0.704) / (1 − 0.704) = 0.096 / 0.296 = 0.324
```
**κ = 0.32 — "fair,"** below the 0.6 threshold. **This judge is not usable and every faithfulness
number it produced is decorative.** Note what happened: 80% agreement, which sounds like a good
judge, and κ = 0.32, which says most of that agreement was the base rate doing the work.

**Q7.** The all-supported judge agrees on your 20 `supported` cases and disagrees on your 5, so
raw agreement = **0.80** — *identical to the real judge*. Its κ: p_e = (0.80 × 1.0) + (0.20 × 0.0)
= 0.80, so κ = (0.80 − 0.80)/(1 − 0.80) = **0.00**, exactly chance.

**Raw agreement cannot distinguish a real judge from one that has learned to say yes.** That's the
entire reason κ exists, and it's a thirty-second demonstration worth keeping.

And the number that should actually change your behaviour: of the 5 answers you called
unsupported, the judge caught **2 — recall of 0.40 on the class you built it to find.** It misses
three unfaithful answers in five. Report that alongside κ, always; it's more actionable than
either headline number and a client understands it immediately.

</details>

---

## 4. What people get wrong

**"We have an eval, it scores 0.84."**
Over what population, segmented how, with what noise floor? At n = 60 the interval on 0.84 is
roughly ±9 points. An unqualified single number is a claim you can't defend.

**"The judge agreed with me 80% of the time, so it's good."**
§3 Q7 — a constant "yes" scores the same 80%. Compute κ, and report per-class recall next to it.

**"κ = 0.45 is reasonable agreement."**
It's "moderate" on a 1977 convention and below the working threshold for a metric you intend to
make decisions with. Tighten the rubric — anchors, forced evidence quotes, claim decomposition —
and re-measure. Iterating on a *rubric* rather than a prompt is a distinct skill.

**"Use the strongest model as judge."**
Use a *different* model from your generator. Strength doesn't remove self-preference; different
lineage does. If your generator is the strongest model you have, judge with the second strongest
from another family and note the limitation.

**"Synthetic golden sets are fine, the model wrote good questions."**
It wrote them in the source chunk's vocabulary, so your retriever solves them by lexical overlap
and your recall is inflated. The hand-review pass isn't optional cleanup; it's where the dataset
becomes a measurement.

**"Recall went from 0.78 to 0.83, the change worked."**
That's under one standard error at n = 60. Pair the comparison, find the flipped cases, read them.

**"RAGAS gives us faithfulness, we don't need to build this."**
RAGAS is fine and you should use it eventually. But it makes specific choices about claim
decomposition and judging that determine your number, and if you can't say what they are you
can't explain a result to a client.

**"We'll add the unanswerable cases later."**
Then you have no refusal metric — and from Day 4 §3, refusal is often the largest correctable
source of wrong answers in the system. Five cases. Write them today.

**"Run the eval when we're ready to show improvement."**
An eval you only run when you expect it to look good is a marketing asset. Run it on every change,
especially the ones that turn out badly.

---

## 5. The trainer's angle

**The analogy that lands:** the ladder is an observability stack, and Siva has built three of
them.

| Rung | What it is in a system you've run |
|---|---|
| 1 · Invariants | Unit tests and health checks. Free, deterministic, run on every commit |
| 2 · Retrieval metrics | SLIs. Objective, cheap, measure one layer only |
| 3 · LLM judge | Synthetic canaries. Approximate the user, need calibrating against reality |
| 4 · Human | Customer complaints. Ground truth, slow, expensive, arrives too late |

Nobody builds a monitoring stack starting from customer complaints, and nobody should build an
eval starting from an LLM judge. The analogy carries §2.4 for free too: **the aggregate hiding a
broken synthesis bucket is a healthy P50 hiding one bad shard.** Everyone in an infrastructure
room has been burned by that exact thing, and once they see it's the same shape they stop arguing
for a single headline number.

**The demo that makes it click:** put the 2×2 from §3 Part B on screen and ask the room whether
the judge is good. They'll say yes — 20 of 25. Compute κ live: 0.32. Then show that a judge saying
"supported" to everything scores the same 80% and κ = 0. The room's model of what "agreement"
means breaks and rebuilds in ninety seconds.

**Your second demo:** show Recall@5 = 0.78 on one slide. Next slide, the same number split by
difficulty — lookup 0.93, synthesis 0.41. Say nothing for three seconds. Then: *"Which of those
is your ops team actually going to ask?"*

**The question a sharp student will ask:** *"If the judge needs human labels to be trusted, and
we have human labels, why not just use the human labels?"* Have this:

> Different jobs. You label 25 cases once to *calibrate the instrument*, then the instrument runs
> 600 times a day at two-tenths of a cent each. It's the relationship a reference thermometer has
> with the thousand sensors in a warehouse — you don't measure the warehouse with the reference,
> you measure the sensors with it. Two things follow from taking that seriously. Calibration
> expires: re-measure κ whenever you change the rubric, the generator, or the judge model, because
> all three move the instrument. And the human set is never a *training* set — the moment you tune
> the judge to fit those 25 cases they stop being an independent standard and you need 25 new ones.

---

## 6. Self-check

Cover the answers.

1. Name the four rungs of the ladder and give one example metric from each.
2. Why build rung 1 first when clients ask for rung 3?
3. What are the four difficulty labels, and what does each one exist to expose?
4. Why do synthetic golden questions inflate recall? What's the fix?
5. Recall@5 and MRR both look good. Which failure can they both be hiding?
6. Write the DCG formula. What does the log discount represent, and why normalise?
7. Your aggregate Recall@5 is 0.78. Give two distinct reasons that number could mislead a client.
8. Name the four judge biases and one concrete fix for each.
9. Why decompose an answer into atomic claims before judging?
10. Write Cohen's κ. What is p_e?
11. Raw agreement is 0.80. Why is that not evidence the judge is good?
12. At n = 60 and p ≈ 0.78, what is the standard error? What's the practical rule that follows?

<details>
<summary><b>Answers</b></summary>

1. Unit/invariant (evidence-quote substring check); retrieval metrics (Recall@k); LLM-as-judge
   (faithfulness); human expert (is this actually right).
2. It's free, deterministic, runs in CI, and catches the most embarrassing failures. Rung 3 costs
   money, needs its own calibration, and can't tell you the JSON was malformed.
3. lookup (inflates your aggregate); synthesis (multi-chunk — where you fail); condition (the
   detention case); absent (the only way to measure refusal).
4. The question inherits the source chunk's vocabulary, so retrieval succeeds by lexical overlap
   rather than semantic match — the opposite of real user queries. Fix: hand review, rewrite in
   user language, record the rejection rate.
5. A multi-document question whose second required document was never retrieved. MRR sees only
   the first hit; Recall@k at a generous k gets carried by the easy half. Segment and check
   Recall@3.
6. DCG@k = Σ relᵢ/log₂(i+1). The discount models attention decaying with rank; normalising by the
   ideal ordering makes queries with different numbers of relevant docs comparable.
7. It's a weighted average over buckets that behave differently, so it moves with the *mix*; and
   at n = 60 its 95% interval is about ±10 points. Either alone invalidates the claim.
8. Self-preference → different model family. Position bias → both orders, averaged. Verbosity →
   regress score against token count and report it. Rubric drift → binary/3-point anchored scales
   plus a required evidence quote.
9. A paragraph verdict is mush you can't act on. Per-claim gives a faithfulness rate and names
   the invented claim.
10. κ = (p_o − p_e)/(1 − p_e). p_e is the agreement expected if both raters labelled independently
    at their own base rates — Σ over classes of P(you say c) × P(judge says c).
11. A judge that always answers the majority class scores the same 0.80 on an 80/20 set with
    κ = 0. Raw agreement mostly measures prevalence.
12. √(0.78 × 0.22 / 60) ≈ 0.053 — one SE is 5.3 points, a 95% interval roughly ±10. Rule: at
    n = 60, anything under ~10 points is "go read the discordant cases," not a result.

</details>

**Scored below 8?** Re-read §2.5 and §2.6. The judge and its calibration are where today's lab
spends its most expensive hour, and a judge you don't understand produces numbers you'll quote
for the rest of the course.

---

## 7. Going deeper (optional)

- *Cumulated Gain-Based Evaluation of IR Techniques* — Järvelin & Kekäläinen (2002). The nDCG
  paper; §4 has the reasoning behind the logarithmic discount.
- *The Measurement of Observer Agreement for Categorical Data* — Landis & Koch (1977). Source of
  the κ bands everyone quotes. Worth seeing how casually the thresholds were proposed.
- *High Agreement But Low Kappa* — Feinstein & Cicchetti (1990). The reason you report per-class
  recall next to κ.
- *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena* — Zheng et al. (2023). Judge-human
  agreement, plus position and verbosity bias with measured effect sizes.
- *Large Language Models are not Fair Evaluators* — Wang et al. (2023). Position bias and the
  swap-and-average fix.
- *RAGAS* — Es et al. (2023). Read **after** building your own judges, then read the source for
  `faithfulness` and check whether its claim decomposition matches what you assumed.

---

**Now go to `labs/DAY_05.md`.** The lab is built on §2.2 (the golden set and the hand-review
pass — that pass *is* the lab), §2.3 (you implement all five metrics from scratch), §2.5 (three
judges with claim decomposition), and §2.6 (measure κ, and don't stop at raw agreement).
