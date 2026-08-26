# Day 13 — Evals at Depth: Synthetic Data, Judges, and Regression Gates

**Tue Sep 8, 2026** · Week 3 · Maps to: **Module 05 — Evals** · Backend: **local** + `[PAID]` · Est. cost: **$4–8**

> **Before you start — read `learn/DAY_13_LEARN.md` (1:15).**
> Synthetic eval data, judge calibration, the noise floor. The lab below assumes it and does not re-explain it.


---

## Why today matters

**FDE lens.** Week 1 gave you an eval. Today you build an eval *system*: synthetic data
generation at scale, a calibrated judge, adversarial cases, and a CI gate that blocks a
bad change. This is the deliverable that survives after you leave an engagement. Code
rots; a good eval suite is what lets the client's own team keep shipping.

**Trainer lens.** Evals are on every syllabus and taught badly on most — usually as a tour of
RAGAS. If you can teach them properly, you become the person asked to run that session,
wherever you are. It's the single most under-served topic in AI education right now.

---

## Objectives

1. Generate synthetic eval data at scale, with controlled difficulty and adversarial cases.
2. Build a judge you have *calibrated* and can defend, including agreement statistics.
3. Implement pairwise comparison with position-bias control.
4. Wire a regression gate into CI that actually blocks a merge.

---

## Schedule (5:00)

| Block | Time | What |
|---|---|---|
| 0 | 0:30 | Warm-up |
| 1 | 1:15 | **Learn** — `learn/DAY_13_LEARN.md` |
| 2 | 2:45 | Lab: generator → judge → pairwise → CI gate |
| 3 | 0:30 | Teach-back #13 |

---

## Block 0 — Warm-up (0:30)

1. Where did integration regress your system, and why?
2. p95 cost per query — and which node dominates it?
3. What fraction of requests hit a budget limit?
4. Rebuild the trace for one query from memory: which nodes fire, in what order?

---

## Block 1 — Learn (1:15)

**Read `learn/DAY_13_LEARN.md` and work its examples on paper before continuing.**
Take the self-check at the end. Anything you miss goes on a flashcard and into tomorrow's
warm-up. The material below consolidates the module — it is not a substitute for it.

### 1.1 Synthetic eval data — the four generators

| Generator | Method | Produces |
|---|---|---|
| **Extractive** | From a chunk, ask for a question answerable only by it | Lookup cases. Easy, plentiful, weak |
| **Multi-hop** | Sample 2 chunks from *different* docs, ask for a question needing both | Synthesis cases. The valuable ones |
| **Adversarial** | Perturb a good question: negate it, add a false premise, ask for a number that isn't there | Refusal + robustness cases |
| **Persona** | Rewrite questions in the voice of a dispatcher, a controller, a VP | Realistic phrasing. Exposes the gap between clean questions and real ones |

The persona generator is underrated. Your Day 5 golden set is full of well-formed
questions. Real users type "why did ridgeline get dinged again on dal chi". Generate 20
of those and re-run your scorecard. **The drop is the most honest number in your
bootcamp.**

Three adversarial types you must include:
- **False premise**: "Since detention is billed from arrival with no free time, how much
  for a 3-hour wait?" — the correct behaviour is to *correct the premise*, not answer it.
- **Absent-fact**: asks for a number the corpus doesn't contain. Must refuse.
- **Near-miss**: asks about demurrage using detention vocabulary. Tests precision.

### 1.2 Judge calibration, properly

You did a rough version on Day 5. Today, the real method:

1. **Build a labelled set.** 50 answers, spanning good/bad, labelled by you, blind
   (shuffle, hide which system produced them).
2. **Measure agreement.** Cohen's κ for categorical, Spearman ρ for graded.
3. **Diagnose disagreements.** Read every case where you and the judge differ. There are
   only two explanations, and telling them apart is the skill: either the rubric is
   ambiguous (fix the rubric) or *you* were inconsistent (fix your labels — this happens
   more than people admit).
4. **Iterate the rubric**, not the model. Add anchors. Require evidence quotes. Force a
   decision before the explanation, or after — test both, they behave differently.
5. **Re-measure.** Target κ > 0.7 for a judge you'd report to a client.

Record the κ progression across rubric versions. A chart of "κ vs. rubric version" is an
unusual and very persuasive teaching artifact.

### 1.3 Regression gates

Three kinds of check, and they need different treatment:

| Check | Behaviour | Example |
|---|---|---|
| **Hard gate** | Blocks merge | Citation verification rate < 0.90; any schema violation; refusal rate on absent cases < 0.95 |
| **Soft gate** | Warns, needs sign-off | Faithfulness drops > 3 points; p95 latency up > 20% |
| **Alarm** | Reports, never blocks | Cost per query changed > 10%; answer length distribution shifted |

Non-determinism means a gate on a noisy metric will flake and get disabled within two
weeks — and a disabled gate is worse than no gate. So:

- **Fix the seed where you can** (temperature 0, fixed retrieval order).
- **Run N=3 and use the median** for judge metrics.
- **Set thresholds from measured variance**, not from wishes. Run your suite 5 times
  with no changes; the spread *is* your noise floor. A gate tighter than the noise floor
  is a flake generator.

That last point is the most useful thing in today's lab. Almost nobody does it.

---

## Block 2 — Lab (2:45)

### 2.1 Synthetic data pipeline (60 min)

`src/fdekit/evalgen.py`:

```python
def gen_extractive(chunks, n_per_chunk=2) -> list[Case]: ...
def gen_multihop(chunks, n=40) -> list[Case]:
    """Sample chunk pairs from DIFFERENT documents with moderate embedding
    similarity — too similar and the question is trivial, too dissimilar and
    it's nonsense. Target cosine 0.3-0.6."""
def gen_adversarial(cases, kinds=("false_premise","absent","near_miss")) -> list[Case]: ...
def gen_persona(cases, personas=("dispatcher","controller","vp")) -> list[Case]: ...

def dedupe(cases, threshold=0.92) -> list[Case]:   # embedding similarity
def review_queue(cases) -> None:                    # CLI for fast human accept/edit/reject
```

That chunk-pair similarity band (0.3–0.6) for multi-hop generation is the kind of detail
that makes synthetic data useful instead of noise. Derive your own band by inspection —
generate 10 pairs at each of three bands and see which produce good questions.

Target: **250 cases**. Then run the review CLI. Budget 30 of your 60 minutes for review;
aim for ~15 seconds per case. You'll reject 20–30%. Log the rejection rate and the top
three rejection reasons — that's teaching material.

### 2.2 The judge, calibrated (60 min)

`src/fdekit/judge.py`, v2:

```python
@dataclass
class Rubric:
    version: str
    criterion: str
    anchors: dict[str, str]        # {"supported": "every claim traceable...", ...}
    require_evidence: bool = True
    decision_first: bool = False   # test both orderings

class Judge:
    def __init__(self, rubric: Rubric, model: str, n_samples: int = 1): ...
    def score(self, case, answer) -> Verdict: ...
    def calibrate(self, labelled: list[tuple[Case, Answer, Label]]) -> Calibration:
        """Returns kappa, per-class confusion, and the disagreement cases."""
```

Do the full loop: label 50 blind → measure → read disagreements → revise rubric → measure
again. Do at least **three rubric versions**. Record all three κ values in
`evals/day13_judge_calibration.md` with what changed between them.

Non-negotiable: judge with a different model family than the generator. Local Llama
generates, `gpt-4o-mini` or Claude judges.

### 2.3 Pairwise comparison (40 min)

Absolute scores drift between runs. Pairwise is more stable and it's how you'll answer
"is v2 better than v1?"

```python
def pairwise(case, answer_a, answer_b, judge) -> Literal["A","B","tie"]:
    """Run BOTH orders. If they disagree, it's a tie — that disagreement rate
    IS your position-bias measurement. Report it."""

def tournament(strategies, cases, judge) -> pd.DataFrame:
    """Round-robin. Report win rate and a Bradley-Terry or Elo-style rating."""
```

Run a tournament across your Day 8 strategies. Compare the ranking to the absolute-score
ranking from Day 8. **If they disagree, that's a finding** — investigate before you trust
either. Usually it's verbosity bias in the absolute scores.

Also report your position-bias rate (the fraction where order flipped the verdict). If
it's above 15%, your rubric is too vague.

### 2.4 CI gate (40 min)

`.github/workflows/eval.yml` + `scripts/run_evals.py`:

```yaml
on: [pull_request]
jobs:
  eval:
    steps:
      - run: python scripts/run_evals.py --suite fast --gate
      # fast suite: 60 cases, ~3 min, hard gates only
      # nightly: full 250 cases + judge + tournament
```

`run_evals.py` must:
- run the suite, N=3, median for judge metrics
- compare against `evals/baseline.json`
- exit non-zero on any hard-gate breach
- write a **markdown summary to the PR comment** — a table of metric / baseline / current
  / delta / status
- never silently pass because the judge errored (a failed judge call is a failure, not a skip)

**Establish your noise floor first.** Run the suite 5 times with zero changes, compute the
standard deviation of each metric, and set thresholds at baseline − 2σ. Write those σ
values in the workflow file as a comment so the next engineer knows where the numbers
came from.

Then prove it works: make a deliberate regression (drop k from 5 to 1), open a PR,
watch it fail. Screenshot it. **That screenshot goes in your portfolio.**

---

## Block 3 — Teach-back #13 (0:30)

Record 12 min: **"Your eval flakes because you set the threshold before measuring the noise."**
`teaching/recordings/day_13.mov`

Show: your 5-run noise floor, your κ progression across rubric versions, your
position-bias rate, and the CI gate blocking a real PR. Close with the sentence that
lands: *"A gate tighter than your noise floor gets disabled in two weeks, and then you
have nothing."*

---

## Done when

- [ ] 250 generated cases, human-reviewed, rejection rate logged with reasons
- [ ] Adversarial cases across all three kinds; persona-rewritten cases and the score drop measured
- [ ] Three rubric versions with κ measured for each; final κ > 0.7
- [ ] Pairwise tournament run; position-bias rate reported
- [ ] Noise floor established over 5 identical runs; thresholds set from σ
- [ ] CI gate blocking a deliberately regressed PR, screenshotted

---

## Trap list

- Generating 1,000 cases and reviewing none.
- Judge and generator from the same family.
- Thresholds set from hope. Measure the noise first.
- Absolute scores as the only signal — verbosity bias will fool you.
- A gate that skips when the judge API errors. That's a silent pass.
- Never updating the baseline, so every PR shows a regression and everyone stops reading.

---

## Stretch

Add **eval-driven prompt optimisation**: for the worst-performing 20 cases, have a model
propose system-prompt amendments; test each against the *full* suite; accept only ones
that improve the target metric without regressing others. Log which amendments survive.
This is DSPy's core idea, hand-rolled — and having built it yourself means you can
explain DSPy in three sentences instead of a session.
