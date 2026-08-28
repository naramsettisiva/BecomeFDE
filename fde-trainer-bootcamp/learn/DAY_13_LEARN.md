# Day 13 · Learn — Evals at depth: manufacturing cases, calibrating the instrument, and gates that survive

**Read before `labs/DAY_13.md`. Budget 1:15. Pen and paper for §3 — the noise-floor and confidence-interval arithmetic are the day.**

---

## 1. Where this sits

Day 5 gave you an eval: forty hand-written cases, a judge, and a Cohen's κ you computed once. Day
12 measured the integrated system. Both were honest work, and both have the same three cracks.

Forty cases is too few — one case is 2.5 points, so any change smaller than "broke it badly" is
indistinguishable from noise. You wrote the cases yourself, so they're the questions you already
knew your system could answer. And every one is a grammatical sentence with correct terminology,
which is not how anyone at a freight desk types.

Today you fix all three, then do the thing that makes an eval suite an *asset* rather than a
script: find out how noisy it is, and set the gate below that. **This is the deliverable that
outlives you on an engagement.** The client's team will rewrite your retrieval code within six
months. They'll keep your eval suite for years, because it's the only thing telling them whether
the rewrite worked.

---

## 2. The mechanism

### 2.1 Why a hand-written golden set runs out

| Limit | Symptom | Fix |
|---|---|---|
| **Scale** | One case = 2.5 points; a 3-point "regression" is one case flipping | Synthetic generation |
| **Authorship bias** | You wrote questions your system answers; the misses are invisible | Generate from the *corpus*, not from memory |
| **Distribution** | Clean prose; real traffic is fragments and typos | Persona rewriting |

Synthetic generation is not really about volume — volume is a side effect. You generate for
**coverage of shapes you would not have thought to write**: a question needing two documents, a
question containing a false assumption, a question about a number that isn't in the corpus at all.

### 2.2 Generator 1 — extractive

Take a chunk, ask a model for a question answerable *only* by that chunk, record the chunk ID as
ground truth. Cheap, plentiful, ground truth free because you started from it.

They're also the weakest thing in your suite — they test lookup, the part that already works. Two
disciplines make them less useless.

**Forbid verbatim reuse of rare terms.** If the chunk says "demurrage" and the question says
"demurrage," you've built a lexical-match test. *"What's the free time before a container starts
racking up charges at the ramp?"* is a real test; *"What is the demurrage free time at inland
ramps?"* is a keyword lookup wearing a question mark.

**Record the answer span, not just the chunk ID.** "Chunk 04-b" gets you recall@k. "4 calendar
days" gets you answer correctness from a string assertion with no judge at all — the cheapest,
least noisy signal in the suite.

### 2.3 Generator 2 — multi-hop, and why the similarity band matters

Sample **two chunks from different documents**, hand both to the generator, ask for a question
that cannot be answered from either alone. Ground truth is now the *pair* of chunk IDs — a recall
metric that requires both, so a retriever returning one of two scores zero rather than half.

These are the valuable cases, and the ones a naive generator produces garbage for. The fix is a
sampling constraint: **pick pairs at moderate embedding similarity, roughly cosine 0.3–0.6 on your
corpus.** Both ends fail, in opposite ways:

| Pair similarity | What comes out | Why it's poison |
|---|---|---|
| **Too high** (>0.75) | Both chunks state the same fact | An extractive case in costume — answerable from either — and it **inflates** your synthesis score |
| **In band** (0.3–0.6) | Related topic, different facts | A real bridge exists: FTA threshold + scorecard weighting; detention rate + OTIF appointment window |
| **Too low** (<0.2) | An invented bridge | *"What is the demurrage rate during the scorecard appeal window?"* — unanswerable |

The last row is the expensive one. A nonsense case with a confident ground-truth answer doesn't
just waste a slot, it **penalises correct behaviour**: refusing is the right answer and your rubric
says the right answer is the fabricated one.

And the band is corpus-dependent. Day 3 §3 Q7 — real text vectors cluster in a narrow cone, so
unrelated pairs sit around 0.3–0.6 rather than at 0. On a corpus with tighter vocabulary your
unrelated floor might be 0.55, and 0.3–0.6 would be sampling pure noise. **Derive the band by
inspection on your own corpus**: ten pairs at each of three bands, read them, pick.

### 2.4 Generator 3 — adversarial, three kinds with three different correct behaviours

People get this wrong in a specific way: they assume adversarial means "the system should refuse."
One of the three requires the opposite.

**False premise.** The question embeds an assertion that contradicts the corpus.

> *"Since detention is billed from arrival with no free time, how much do we owe for a 3-hour
> wait?"*

Free time is 2 hours from the scheduled appointment, then $65/hour. The correct behaviour is **to
correct the premise and then answer**: there *is* 2 hours free, so a 3-hour wait is 1 chargeable
hour, $65. A refusal fails this case. Silently computing $195 from the user's framing is worse —
that's the model treating a user assertion as retrieved context, which is exactly what an LLM is
built to do and exactly what you don't want.

**Absent-fact.** The question asks for something the corpus does not contain.

> *"What's the detention rate for refrigerated trailers held over a weekend?"*

No reefer-specific rate exists anywhere in the corpus. The correct behaviour is to say so. These
cases produce your **refusal rate**, and refusal rate deserves a hard gate — a fabricated
plausible number under a client's letterhead is the failure that ends engagements.

**Near-miss.** Topic A phrased in the vocabulary of topic B.

> *"How many hours of free time before charges start at the ramp?"*

"Hours" and "free time" are detention vocabulary; "at the ramp" makes it demurrage, where the
answer is 4 calendar days. A **precision** test, and a direct descendant of Day 3 §2.4 — topical
similarity pulls you to the detention chunk and only propositional precision gets you to the right
one. Grade it twice: retrieved chunk must be the demurrage section, and the answer must not
contain `$65` or `2 hours`.

Two operational rules. **Write the pass condition per case, not per suite** — "must refuse," "must
correct the premise," "must not mention $65" are three different assertions and no single judge
prompt covers them. And **report the three kinds separately**: a system that refuses everything
scores 100% on absent-fact and 0% elsewhere, so the aggregate rewards cowardice.

### 2.5 Generator 4 — persona rewriting, and the gap it exposes

Rewrite a clean case in the voice of someone who actually asks it. Same ground truth. Keep a
pointer to the source case ID — **that pairing is what makes the drop attributable**, because the
only variable that changed is phrasing.

| Voice | The same question |
|---|---|
| **Clean (your Day 5 set)** | "Why did Ridgeline Freight's composite score place them in the Silver band this quarter on the Dallas–Chicago lane?" |
| **Dispatcher** | "why did ridgeline get dinged again on dal chi" |
| **Controller** | "need the backup on the ridgeline 78.5 — which component dragged it and is the FTA number restated or not" |
| **VP** | "Ridgeline is complaining. Are they actually underperforming or did we move the goalposts?" |

Each breaks specific machinery, not vibes:

1. **The lexical leg loses its terms.** "dal chi" is not "Dallas–Chicago"; "dinged" is not
   "composite score." Tomorrow's BM25 leg contributes nothing.
2. **The dense query gets shorter and noisier.** Six lowercase tokens carry far less signal than a
   twenty-word question. It still lands in the right neighbourhood — Day 3's point — but the
   neighbourhood is bigger.
3. **The router misclassifies.** Day 8's classifier was tuned on clean questions.
4. **The referent is missing.** "this quarter" is implicit; "the goalposts" refers to the
   telematics-denominator warning in the scorecard spec. Without session memory (Day 10) there is
   nothing to retrieve.

The VP question is the hardest and the most realistic: the right answer involves the scorecard
spec's own warning that a carrier's score falls when the shipper turns on tracking for a new lane
and the denominator moves. "Yes, Ridgeline's FTA is 83% against a 92% target" is not wrong, and it
is not the answer the VP needed.

**The clean-to-persona drop is the most honest number in your bootcamp**, and it's diagnostic
rather than just depressing. Segment the new failures: gold chunk outside top-k means retrieval
brittleness, which tomorrow mostly fixes; retrieval fine but answer wrong means a prompt or
context-assembly problem.

### 2.6 Generation hygiene

- **Dedupe by embedding similarity** at ~0.92 before review. Generators are repetitive.
- **Review every case, ~15 seconds each.** Accept / edit / reject; you'll reject 20–30%. **Log the
  rejection rate and the top three reasons** — that's a property of your generator prompt, and
  fixing the prompt is cheaper than reviewing more.
- **Judge from a different model family than the generator.** Day 5 §2.5: if one model wrote the
  question, wrote the reference answer, and grades the answer, you measured its self-consistency
  and called it accuracy.
- **A synthetic case is only as good as the chunk it came from.** If your chunker severed the $65
  from the 2-hour condition (Day 3 §2.6), the generator will happily produce a case with wrong
  ground truth.

### 2.7 Judge calibration as instrument calibration

A judge is a measurement instrument. Day 5 was a rough pass; this is the real loop — five steps,
one afternoon, once.

**1 · Build a labelled set, blind.** 50 answers spanning good and bad. Shuffle, strip every marker
of which system produced them, label in one sitting. Blind matters for the reason it always
matters: you rate your own change higher. The judge is not the only biased evaluator in the room.

Slip **five duplicate items** into the shuffle and check whether you labelled them the same way
twice. That's your **intra-rater agreement**, and it's the number nobody computes: *your own
self-consistency is the ceiling on the judge's κ against you.* If you contradicted yourself on two
of five duplicates, demanding κ > 0.7 is demanding the judge hold a standard you don't.

**2 · Measure.** Cohen's κ for categorical, Spearman ρ for graded, from Day 5:

```
κ = (p_o − p_e) / (1 − p_e)        p_e = Σ_classes P(you say c) × P(judge says c)
```

Report κ **and** per-class recall on the class you care about — of the answers you labelled
unfaithful, what fraction did the judge catch? Day 5 §2.6's kappa-paradox caveat still applies.

**3 · Diagnose every disagreement.** Exactly two explanations, and telling them apart is the skill:

| Cause | How to tell | Fix |
|---|---|---|
| **Rubric ambiguity** | Read the rubric aloud: *could a careful stranger reach the judge's verdict from this text?* If yes, the rubric permits both readings | Add an anchor and a boundary example |
| **Your own inconsistency** | Check your duplicate items and near-identical cases you labelled differently | Relabel — then write down the rule you were *actually* using and put **that** in the rubric |

The second happens more than people admit, and it's the more valuable finding: the implicit rule
you were unconsciously applying is usually the thing the rubric was missing.

**4 · Iterate the rubric, not the model.** The reflex when κ is low is a bigger judge model. Resist
it — a bigger model buys agreement with an *unspecified* standard you can't explain to a client,
the cost increase is permanent and per-case, the same failure returns on the next corpus, and the
rubric is the artifact you hand over while the model is a line in a config file.

The levers that actually move κ, in the order to try them:

| Lever | Why it works |
|---|---|
| **Written anchors per level** | Turns "supported" from a vibe into a test |
| **Require a verbatim evidence quote** | Constrains the judgement to something checkable — Day 4's citation trick applied to the judge |
| **Shrink the scale** | 5-point → 3-point usually raises κ a lot, because most disagreement is between adjacent levels |
| **Decision before vs. after reasoning** | Test both. Reasoning-first lets the judge talk itself into a verdict; decision-first commits then rationalises |
| **Split a compound criterion** | "Faithful *and* complete?" is two questions; the judge answers whichever is more salient |

**5 · Re-measure.** Target **κ > 0.7** for a judge you'd report to a client, and record the
progression with a note on what changed. A chart of κ versus rubric version is an unusual and very
persuasive teaching artifact — it shows evaluation as engineering rather than as a vendor's
defaults.

One caveat for the room: you calibrated against **yourself**, and you are not the domain expert.
If the client's SME would label differently, you have an instrument that reliably reproduces your
misunderstanding. Have the SME label 25 of the 50 and measure κ between you and them first.

### 2.8 Pairwise comparison, and position bias as a measurement

Absolute scores drift with rubric version, judge version, corpus phase. Pairwise is more stable
because it asks an easier question: not *how good is this* but *which of these two is better*,
which only requires detecting a difference.

It has one large defect, and the protocol turns the defect into a number. The judge is doing
next-token prediction over a prompt in which one answer physically appears first — there's a prior
over emitting "A" versus "B," plus primacy and recency effects. So:

> **Run both orders. If they agree, that's the verdict. If they disagree, it's a tie — and the
> disagreement rate IS your position-bias measurement.**

Report it. Above ~15% the rubric isn't discriminating and the position prior is what's left. Ties
are information too: a tournament that's 60% ties says your two systems are the same.

Two things pairwise does **not** fix. It doesn't remove **verbosity bias**, only make it catchable
by comparing mean answer length of winners and losers. And it doesn't create statistical power out
of nothing — §3 Q5, the most commonly ignored fact in this field. For aggregation, win rate is
fine for two systems; **Bradley–Terry** (1952) or Elo gives a rating with a confidence interval
across many.

### 2.9 Gates: three kinds, and the noise floor

| Check | Behaviour | Freight examples |
|---|---|---|
| **Hard gate** | Blocks merge | Citation verification < 0.90 · any schema violation · refusal rate on absent-fact cases < 0.95 |
| **Soft gate** | Warns, needs sign-off | Faithfulness down > 3 points · p95 latency up > 20% |
| **Alarm** | Reports, never blocks | Cost per query moved > 10% · answer-length distribution shifted |

Now the central lesson, and the sentence to close your teach-back with.

**Measure the noise floor first.** Run the suite five times with zero changes. That spread is your
noise floor. Any gate tighter than it fires on green pull requests.

The failure that follows is *social*, not technical, which is why engineers underestimate it. A
gate that fires on a no-op PR teaches the team that eval failures are noise. Within two weeks
someone adds `continue-on-error: true`, or reruns until it passes, or deletes the job — and then
you have nothing. Worse than nothing, because the workflow file still exists and everyone believes
they're covered.

Two levers, in order. **Reduce the noise:** temperature 0, fixed retrieval order with a
deterministic tie-break, a fixed sampling seed, N=3 with the median for judge metrics, and **pin
the model version** — a provider silently rolling a model underneath you is variance you can't fix
and can't detect except as a mysterious baseline shift. **Then set thresholds from measured σ:**
baseline − 2σ, with the σ values written into the workflow file as a comment so the next engineer
knows where the numbers came from.

Two rules that cost nothing. **A judge API error is a failure, not a skip** — a skipped case is a
silent pass. And **update the baseline in the same PR that changes behaviour**, or every
subsequent PR shows the same regression, everyone stops reading the table, and you reach a
disabled gate by a different route.

---

## 3. Worked example — on paper

> **Setup.** Fast suite: 60 cases. Faithfulness = fraction the judge scores `supported`. You run
> the suite **five times with no code changes** and get pass counts **52, 51, 54, 52, 51**.

**Q1.** Mean and sample standard deviation, as a fraction. A colleague proposes the gate
*"faithfulness must not drop more than 1 point below baseline."* What fraction of your five no-op
runs fails it?

**Q2.** Set the gate at baseline − 2σ instead — where does it sit? Citation verification came back
0.942 on all five runs. What kind of check should each of those two metrics be?

**Q3.** Switch judge metrics to **median of 3**. The standard error of a median of 3 samples from
a roughly normal distribution is about `1.16σ/√3`. Effective σ, new gate, and what it cost.

**Q4.** Judge calibration, 50 blind labels, rubric v1:

|  | judge: supported | judge: unsupported |
|---|---|---|
| **you: supported** | 33 | 5 |
| **you: unsupported** | 7 | 5 |

Compute p_o, p_e, κ. Rubric v3 gives **36 / 2 / 3 / 9** — κ again, plus per-class recall on
`unsupported` for both.

**Q5.** Tournament: 60 cases, v1 vs v2, both orders. The orders agree on 48 and disagree on 12;
of the 48 decisive, v2 wins 30. Position-bias rate and win rate. Then the 95% interval on that win
rate (`sd = √(0.25/n)`, ×1.96) — is "v2 is better" supported? How many decisive comparisons for a
±6-point interval?

**Q6.** Persona set: the same 60 cases rewritten, 41 pass versus 52 clean. Of the 11 new failures,
9 had the gold chunk outside top-5 and 2 retrieved correctly but answered wrong. Drop, diagnosis,
and which number goes in the client deck?

**Q7.** Economics. Generation $0.0034/case, judge $0.002/case. Fast suite 60 cases at N=3, 20
PRs/day, 22 working days. Nightly full suite 250 cases at N=3. Monthly cost of each.

<details>
<summary><b>Answers — do the arithmetic first, especially Q1 and Q5</b></summary>

**Q1.** Mean = 260/5 = **52 → 0.867**. Deviations 0, −1, +2, 0, −1 → squares sum to 6; sample
variance 6/4 = 1.5; sd = **1.225 cases = 0.0204**.

The proposed gate sits at 0.857. Runs 2 and 5 scored 0.850. **Two of five no-op runs fail — a 40%
flake rate on a PR that changed nothing.** That gate is disabled inside a fortnight, by someone
entirely correct to do so.

**Q2.** 2σ = 0.0408 → gate at **0.826**. Wide, and unsatisfying, which is the honest cost of a
noisy metric. Citation verification had σ = 0 — it's a deterministic substring check on
temperature-0 output — so **it earns a hard gate at 0.90**. Faithfulness is judge-derived and
noisy, so it's a **soft** gate. Different noise profiles, different treatment: that's the design.

**Q3.** Effective σ = 1.16 × 0.0204 / 1.732 = **0.0137**; 2σ = 0.0274 → gate moves to **0.839**,
about 1.3 points tighter. Cost: 3× runtime and 3× judge spend on every PR. A real decision, not a
default — see Q7.

**Q4.** v1: p_o = 38/50 = 0.76. Your marginals 0.76/0.24; judge 0.80/0.20.
p_e = (0.76)(0.80) + (0.24)(0.20) = 0.656. κ = 0.104/0.344 = **0.30 — "fair," unusable.**

v3: p_o = 45/50 = 0.90. Judge marginals 0.78/0.22. p_e = 0.5928 + 0.0528 = 0.6456.
κ = 0.2544/0.3544 = **0.72 — target met.**

Per-class recall on `unsupported`: v1 caught 5/12 = **42%**, v3 caught 9/12 = **75%**. That pair is
what you report, because it answers what a client actually asks: *will this judge find my
failures?*

**Q5.** Position bias = 12/60 = **20%** — above the 15% line, so the rubric isn't discriminating,
and that's a finding before any tournament result is. Win rate **30/48 = 62.5%** among decisive
comparisons (50% if ties count as half-losses). Report both, with n.

CI: sd = √(0.25/48) = 0.0722; ±1.96σ = **±14.2 points** → [48.3%, 76.7%]. **It crosses 50%. "v2 is
better" is not supported.** For ±6 points: 1.96√(0.25/n) = 0.06 → n ≈ **267 decisive comparisons.**
Which is why the lab targets 250 cases — the suite size isn't a round number someone liked, it's
roughly the smallest n at which your conclusions mean anything.

**Q6.** 41/60 = 0.683 versus 0.867 — a **drop of 18.4 points**. Nine of eleven failures are
retrieval misses, so this is phrasing brittleness in retrieval and tomorrow addresses most of it;
prompt engineering would address almost none of it. The deck gets **0.683** — it's the number that
matches the traffic they'll actually send. Reporting 0.867 isn't a lie, it's a measurement of a
population that doesn't exist.

**Q7.** $0.0054 per case per run. Fast suite: 60 × 3 × $0.0054 = **$0.97/PR** → 20 × 22 =
**$428/month**. Nightly full: 250 × 3 × $0.0054 = $4.05 → **$122/month**.

**The fast suite on every PR costs 3.5× what the full suite costs nightly.** That's the argument
for the split — hard gates only on a small suite at PR time, the expensive statistically-powered
judge-heavy suite once a day where a 20-minute runtime is free.

</details>

---

## 4. What people get wrong

**"Synthetic data means more data."**
It means coverage of shapes you wouldn't have written. Volume is a side effect and, unreviewed, a
liability.

**"An adversarial case passes if the system refuses."**
Only for absent-fact. False premise requires *correcting the premise and then answering*; a
refusal fails it.

**"Any two chunks make a multi-hop case."**
Too-similar pairs are extractive cases that inflate your synthesis score. Too-dissimilar pairs
have fabricated ground truth and punish correct refusals.

**"Low κ means I need a better judge model."**
It means your rubric is ambiguous or your labels are inconsistent. Iterate the rubric — free at
inference time, and it's the artifact you hand over.

**"κ of 0.7 means the judge is right."**
It means the judge agrees with *you* beyond chance. If you're wrong about the domain, you now have
a reliable instrument for reproducing your misunderstanding.

**"Raw agreement of 85% is fine."**
Day 5 §3 Q7: a judge that says `supported` to everything hits 80% raw agreement at κ = 0.00.

**"Position bias is a defect I should prompt away."**
It's a property of the instrument. The both-orders protocol converts it into a tie and a reported
number — what you do with every instrument error you can't eliminate.

**"We ran 40 comparisons and v2 won 60% — ship it."**
±15 points at that n. You measured nothing. Compute the interval before you make the claim.

**"Set the gate where the client wants quality to be."**
Set it below your measured noise floor, then work on reducing the noise. A deleted gate protects
nothing.

**"If the judge API errors, skip the case."**
That's a silent pass. Fail the run.

**"The baseline is sacred."**
It's a record of the last accepted state. Update it in the PR that changes behaviour.

---

## 5. The trainer's angle

**The analogy that lands, hardest with an ops room:** the noise floor is an alert threshold set
without looking at the metric's variance. Everyone in the room has been paged at 3am by a
threshold someone picked because it sounded strict, and everyone in the room has muted one. Same
mechanism, same social decay, different metric. Frame it that way and you never have to argue for
the five identical runs.

**The demo that makes it click:** run the identical suite twice, live, two numbers on screen side
by side. *Before* you run it, ask the room what threshold they'd have set — they'll say "no more
than a 2-point drop." Then show a 3.4-point spread with nothing changed. Twenty seconds, and it
beats any slide about determinism.

**The second demo:** persona rewriting, live, on the room's own question. Take a well-formed
question someone offers, retype it the way a dispatcher would — lowercase, abbreviated lane, no
domain terms — and re-run. The drop is visible and it's *theirs*.

**The predictive question before you run anything:** *"I'm going to run this identical suite twice.
How different will the numbers be?"* Almost everyone guesses zero, or "a rounding error."

**The question a sharp student will ask:** *"If the judge only has to agree with you, and you're
not a freight expert, what have you actually calibrated?"* Have this ready:

> Agreement with a **stated standard** — which is the rubric, not me. That's exactly why you
> iterate the rubric and not the model: the rubric is a document a domain expert can read and
> argue with; the model is a config line nobody can audit. Calibration makes your standard
> explicit and reproducible. It does not make it correct. The correctness step is separate and
> most teams skip it: have the client's SME label 25 of your 50 blind and measure κ between you
> and them *before* you measure κ between you and the judge. If that number is low, stop — you're
> about to build a very reliable instrument for measuring the wrong thing.

**And the framework question:** *"Why not just use RAGAS?"* Use it as a starting rubric, then
measure its κ against your labels on your corpus. It's a set of sensible defaults nobody
calibrated for freight accessorials, and the defaults are the part that has to change. A framework
gives you the loop; it can't give you the anchors.

---

## 6. Self-check

Cover the answers.

1. Name the three limits of a hand-written golden set and the fix for each.
2. Why is the multi-hop similarity band bounded on *both* sides? What goes wrong at each end?
3. State the three adversarial kinds and the correct behaviour for each.
4. Why must adversarial results be reported per-kind rather than aggregated?
5. Name three mechanisms by which persona rewriting breaks a working pipeline.
6. Why do you keep the source case ID on a persona-rewritten case?
7. What are the two possible causes of a judge/human disagreement, and how do you tell them apart?
8. Why iterate the rubric rather than the judge model? Give two reasons.
9. What is intra-rater agreement, and what does it bound?
10. Describe the both-orders pairwise protocol. What does the disagreement rate measure?
11. You measure a 62% win rate over 48 comparisons. What can you claim?
12. What is a noise floor, how do you measure it, and what happens to a gate tighter than it?

<details>
<summary><b>Answers</b></summary>

1. Scale → synthetic generation. Authorship bias → generate from the corpus. Distribution →
   persona rewriting.
2. Too similar: both chunks state the same fact, so it's an extractive case that inflates the
   synthesis score. Too dissimilar: no real bridge, the generator invents one, and the fabricated
   ground truth penalises a correct refusal.
3. False premise → **correct the premise, then answer**. Absent-fact → refuse. Near-miss → answer
   the right topic precisely without leaking the confusable one's numbers.
4. Opposite pass conditions. A system that refuses everything scores 100% on absent-fact and 0%
   elsewhere; the aggregate rewards it.
5. Lexical terms vanish so BM25 contributes nothing; the query gets short and noisy so the dense
   neighbourhood widens; the router was tuned on clean phrasing; implicit referents leave nothing
   to retrieve without session memory. Any three.
6. So the comparison is paired — same fact, only phrasing changed — which makes the drop
   attributable to phrasing rather than to a different sample.
7. Rubric ambiguity (a careful stranger could reach the judge's verdict from the rubric text) or
   your own inconsistency (check duplicates and near-identical cases). Fix the rubric in the
   first; relabel *and* write the implicit rule into the rubric in the second.
8. Any two: a bigger model buys agreement with an unspecified standard you can't explain; the cost
   is permanent and per-case; the failure recurs on the next corpus; the rubric is the auditable
   artifact you hand over.
9. Your own label-to-label consistency, measured with duplicate items hidden in the blind set. It
   is the ceiling on the judge's κ against you.
10. Run each comparison in both orders; agreement is the verdict, disagreement is a tie. The
    disagreement rate is your position-bias measurement; above ~15% the rubric isn't
    discriminating.
11. Very little. sd = √(0.25/48) = 0.072 → ±14 points at 95%, an interval that crosses 50%. You'd
    need ~270 decisive comparisons for a ±6-point claim.
12. The run-to-run spread with no changes; measure it over five identical runs and take σ per
    metric. A tighter gate fires on green PRs, gets disabled within two weeks, and then you have
    nothing.

</details>

**Scored below 9?** Re-read §2.4 and §2.9. The lab's two hardest deliverables — the adversarial
generator with per-case pass conditions, and a CI gate whose thresholds come from measured σ — are
exactly those sections, and the lab will not re-explain either.

---

## 7. Going deeper

<!--reading:13-->

### If you read one thing this week

**[Using LLM-as-a-Judge For Evaluation: A Complete Guide](https://hamel.dev/blog/posts/llm-judge/)** — Hamel Husain · essay · ~45 min

The 'critique shadowing' loop is judge calibration done properly — a domain expert grades a sample, you measure agreement, you fix the prompt, you re-measure — and the insistence on binary pass/fail with a written critique is the single change that most improves a judge you already have.

### Then, in the order I'd take them

- **[Who Validates the Validators? Aligning LLM-Assisted Evaluation of LLM Outputs with Human Preferences](https://arxiv.org/abs/2404.12272)** — Shreya Shankar, J.D. Zamfirescu-Pereira, Björn Hartmann, Aditya G. Parameswaran & Ian Arawjo · paper · ~40 min  
  Read the sections on criteria drift and on the EvalGen interface — the finding that people only discover their real grading criteria by grading outputs is why §2.6's calibration set has to be built before the rubric is frozen, not after.
- **[Interrater reliability: the kappa statistic](https://biochemia-medica.com/en/journal/22/3/10.11613/BM.2012.031/fullArticle)** — Mary L. McHugh · paper · ~25 min  
  Six free pages that tell you what Cohen's kappa is actually correcting for, how to compute it, and — the part that matters in a client review — why the conventional 'substantial agreement above 0.6' bands are looser than they should be for anything consequential.
- **[Testset Generation (Ragas)](https://docs.ragas.io/en/stable/concepts/test_data_generation/)** — Ragas maintainers (Exploding Gradients) · docs · ~25 min  
  A working implementation of §2.2–2.3's generators, including the knowledge-graph approach to sampling chunk pairs — read it as a concrete alternative to the similarity-band heuristic, and note where it does and doesn't guard against unanswerable multi-hop cases.
- **[Task-Specific LLM Evals that Do & Don't Work](https://eugeneyan.com/writing/evals/)** — Eugene Yan · essay · ~40 min  
  A survey of which metrics survive contact with a real task and which quietly don't, with a strong section on classification metrics — the reason it belongs today is that regression gates need a metric whose noise floor you can measure, and most of the popular ones fail that test.

<!--/reading-->

### Also mentioned in this module

- *A Coefficient of Agreement for Nominal Scales* — Cohen, 1960. Four pages; the chance-correction
  argument is worth the original.
- *The Measurement of Observer Agreement for Categorical Data* — Landis & Koch, 1977. Source of
  the "fair / moderate / substantial" bands everyone quotes without attribution. They're
  conventions, not laws — say so when you teach them.
- *High Agreement But Low Kappa* — Feinstein & Cicchetti, 1990. The prevalence paradox from Day 5
  §2.6, and why you report per-class recall alongside κ.
- *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena* — Zheng et al., 2023. Position,
  verbosity and self-enhancement bias, measured rather than asserted. The empirical basis for §2.8.
- *Beyond Accuracy: Behavioral Testing of NLP Models with CheckList* — Ribeiro et al., ACL 2020.
  Pre-dates LLMs and is still the clearest framing of adversarial test generation; its minimum-
  functionality, invariance and directional-expectation tests map onto §2.4.
- *Rank Analysis of Incomplete Block Designs* — Bradley & Terry, 1952. Skim for the shape, use a
  library.
- On reporting confidence intervals for eval results as a matter of course, Evan Miller's 2024
  write-up on adding error bars to evals is the one I'd point at. Read alongside §3 Q5.

---

**Now go to `labs/DAY_13.md`.** The lab builds directly on §2.2–§2.5 (the four generators, the
similarity band, the three adversarial kinds), §2.7 (three rubric versions with κ for each), §2.8
(the both-orders tournament and its position-bias rate), and §2.9 (five identical runs, σ, and a
gate that blocks a deliberately regressed PR).
