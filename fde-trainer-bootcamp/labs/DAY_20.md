# Day 20 — Capstone Build, Day 1: Skeleton to Working

**Wed Sep 23, 2026** · Week 4 · Maps to: **Module 07 — End-to-End Systems** · Backend: **all** · Est. cost: **$5–10**

> **Before you start — read `learn/DAY_20_LEARN.md` (0:30).**
> Vertical slice, scope control, evaluating a document. The lab below assumes it and does not re-explain it.


---

## Why today matters

Everything until now has been labs. Today it's a product. The difference is that a lab
ends when the code runs; a product ends when someone's workflow is genuinely shorter.

The discipline today is **ruthless scope control**. You have two days. The most common
capstone failure is a beautiful architecture with no working end-to-end path at 6pm on
day two. You will build the ugly complete path first and make it good second.

---

## Objectives

1. End-to-end path working by lunch — ugly, but complete, from input to delivered output.
2. Real evaluation set built from the workflow, not from the corpus.
3. Depth added only where the eval says it's needed.
4. Committed, deployed, and demoable by end of day — even if rough.

---

## Schedule (5:00)

| Block | Time | What |
|---|---|---|
| 0 | 0:20 | Plan lock |
| 1 | 0:30 | **Learn** — `learn/DAY_20_LEARN.md` |
| 2 | 1:40 | Vertical slice: end to end, ugly, complete |
| 3 | 1:00 | Eval set for the workflow + baseline |
| 4 | 1:00 | Depth where the eval demands it |
| 5 | 0:30 | Deploy + commit + tomorrow's list |

---

## Block 0 — Plan lock (0:20)

Re-read your `CAPSTONE_BRIEF.md`. Then cut it.

Write two lists in `capstone/SCOPE.md`:

```
SHIPPING (must work by 6pm tomorrow)
  1. ...
  2. ...
  3. ...          ← if this list is longer than 5 items, cut it to 5

NOT SHIPPING (explicitly, and I will not be tempted)
  - ...
  - ...
```

**The "not shipping" list is the one that saves you.** Write it now, while you're calm.
At 4pm tomorrow you will want to add a feature; the list is your promise to yourself.

Then define the **demo moment** — the single 30-second sequence you'll show. Everything
on the shipping list must serve it. Anything that doesn't, cut.

For the recommended capstone, the demo moment is:

> *"Ridgeline Freight's Q3 review is due Friday. Generate it."* → 40 seconds later a
> complete carrier business review appears: performance vs. contract, detention exposure,
> attributed root causes, cited policy references, and three recommendations — each
> traceable to a source. What used to be a half-day of an analyst's time.

That's the thing you're building. Everything else is optional.

---

## Block 1 — Learn (0:30)

**Read `learn/DAY_20_LEARN.md` and work its examples before continuing.**
Take the self-check at the end. This is a build day, so the module is short and deliberately practical — read it once, properly, then build.

---

## Block 2 — Vertical slice (1:40)

**Rule: no component is "done" until the whole path runs, however badly.**

Order of work:

```
0:00  Scaffold: repo structure, config, one entrypoint that runs
0:20  Hardcode a fake output. Confirm it renders. THE PATH EXISTS.
0:40  Replace fake data with a real data query (MCP → TMS tables)
1:00  Replace fake analysis with one real retrieval + generation
1:30  Real output assembly: the actual document/report format
1:50  Run end to end on ONE real case. It will be bad. Good.
2:10  Commit. You now have something to demo even if the day collapses.
```

That "hardcode a fake output at 0:20" step is the one people skip and the one that
guarantees you have a demo. It also forces you to decide what the output actually *is*
before you've spent three hours on retrieval — which is usually where the scope creep hides.

For the carrier review capstone, the vertical slice is:

```
input:  carrier="Ridgeline Freight", quarter="2026Q3"
  ↓ DataAgent (via MCP): scorecard, shipments, detention events, tender history
  ↓ PolicyAgent: retrieve relevant policy — thresholds, bands, dispute windows
  ↓ AnalystAgent: compute vs. contract, attribute causes, rank issues
  ↓ WriterAgent: assemble the review document
  ↓ Verifier: every number traced to a data query, every policy claim cited
output: capstone/output/ridgeline_2026Q3.md  (+ HTML render)
```

---

## Block 3 — The eval set (1:00)

**Crucial distinction:** you are no longer evaluating question-answering. You're evaluating
a *document*. That needs different metrics, and building them is the most FDE-shaped thing
you'll do today.

`capstone/evals/`:

**Structural checks** (free, deterministic, run every time):
- [ ] All required sections present
- [ ] Every numeric claim carries a data-query provenance tag
- [ ] Every policy assertion carries a verified citation
- [ ] No placeholder text ("TBD", "[insert]") survived
- [ ] Length within bounds

**Factual checks** (deterministic, against source data):
- [ ] Every number in the document matches the number the query returned. Recompute and diff.
- [ ] Band assignment matches the policy thresholds — recompute independently and compare.
- [ ] Date ranges correct; no data from outside the quarter.

**Quality checks** (LLM judge, calibrated per Day 13):
- Are the recommendations supported by the findings, or generic?
- Would a VP of Transportation find this actionable?
- Is the tone appropriate for an external carrier conversation?

**The adversarial check** (the one that matters most): build **three carriers with
different profiles** — a good performer, a bad performer, and a mixed one where the story
is genuinely ambiguous. A system that produces a plausible review for a good carrier and
the *same shape* of review for a bad one is broken. The reviews must differ in conclusion,
not just in numbers.

Run the baseline. Record the score. It will be poor. That's your starting line.

---

## Block 4 — Depth where the eval demands it (1:00)

Look at the failures. Fix in this order, and **only** these:

1. **Factual errors** — wrong numbers. Non-negotiable, fix first. Usually a data-join or
   date-range bug, not a model problem.
2. **Missing citations** — an unverifiable claim is a liability in a document that goes to
   an external carrier.
3. **Generic recommendations** — the most common and most damaging failure. If your
   recommendations would apply to any carrier, the document is worthless. Fix by giving
   the writer agent the *specific* worst events with their details, not summary statistics.
4. **Structural problems** — sections missing or misordered.

Re-run the eval after each fix. Log the delta. `capstone/evals/day20_progress.md`.

**Do not** add features. Do not improve the UI. Do not refactor. Look at your NOT SHIPPING
list if you feel the urge — that's what it's for.

---

## Block 5 — Deploy + commit (0:30)

- [ ] Deploy whatever works right now to your Day 17 target. A rough live version beats a
      perfect local one.
- [ ] Generate all three carrier reviews and commit the outputs — these are portfolio artifacts
- [ ] Write tomorrow's list, prioritised, in `capstone/TOMORROW.md`:
  ```
  MUST (demo breaks without it)
  SHOULD (demo is better with it)
  WON'T (moved to the not-shipping list)
  ```
- [ ] Commit and push

```bash
git add -A && git commit -m "Capstone day 1: end-to-end carrier review generation + eval harness" && git push
```

---

## Done when

- [ ] End-to-end path produces a real document from a real input
- [ ] Eval harness with structural, factual, and quality checks
- [ ] Three carrier profiles producing *materially different* reviews
- [ ] Baseline score recorded, at least three fixes applied with deltas logged
- [ ] Something deployed and reachable
- [ ] `TOMORROW.md` written and prioritised

---

## Trap list

- Building components in isolation. Vertical slice first, always.
- Perfecting retrieval before the output format exists.
- An eval that only checks the happy-path carrier.
- Adding a feature at 4pm. Check your NOT SHIPPING list.
- Not committing until the end of the day.
- Recommendations that would fit any carrier. This is the failure that makes a document
  look impressive and be useless — and the one a domain expert spots in ten seconds.

---

## A note on pace

If you're behind at 3pm, **cut, don't extend.** A finished small thing demos far better
than an unfinished large thing. The 40-second demo moment is what matters; everything
else is negotiable. Cutting scope deliberately, on schedule, is itself an FDE skill and
you should practise it here rather than on a client.
