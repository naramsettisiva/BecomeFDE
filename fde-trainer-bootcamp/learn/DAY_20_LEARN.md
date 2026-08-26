# Day 20 · Learn — Shipping under a deadline, and evaluating a document

**Read before `labs/DAY_20.md`. Budget 0:30.**

---

## 1. Where this sits

You have built every component this system needs. Today you assemble them into a product under a
fixed two-day clock.

Half of this module will feel like something you already know, because it is: 23 years of cutting
scope, protecting a date, and telling a stakeholder no in a way that keeps them on side. The AI
context changes none of that. Read §2.1–2.3 fast and confirm it matches instinct.

**The new material is §2.4 onward: evaluating a *document* rather than an answer.** Every eval
you have built scored a response against a known-correct answer. A quarterly carrier business
review has no correct answer. It has a correct *shape*, correct *numbers*, and — the part that
catches everyone — it must reach a **different conclusion** for a different carrier. That
property is invisible if you only test one carrier, and it is the failure that makes a capstone
look impressive and be worthless.

---

## 2. The mechanism

### 2.1 The vertical slice

**No component is done until the whole path runs, however badly.** Build a thin end-to-end thread
first; thicken it after.

```
0:00  Scaffold. One entrypoint that runs.
0:20  Hardcode a fake carrier review. It renders.  ← THE PATH EXISTS
0:40  Real data query (MCP → TMS tables)
1:00  Real retrieval + generation
1:30  Real output assembly — the actual document format
1:50  End to end on one real case. It will be bad. Good.
2:10  Commit.
```

The step people skip is 0:20, and its value has little to do with having a fallback demo.

**Hardcoding a fake output forces you to decide what the output IS.** Right now you have a
sentence — "a quarterly carrier business review" — hiding a dozen unmade decisions: how many
recommendations, detention exposure as a total or a per-event table, verdict before or after the
narrative, named shipments or not. Each is a scope decision. Make them at 0:20 or make them at 3pm
while debugging retrieval.

That is where scope creep actually lives. Not in someone asking for a feature — in an output format
never pinned down, so every hour you discover another thing the document "obviously" needs. Write
the fake document, look at it, and an open-ended build becomes fill-in-the-blanks.

You know this already: the design doc that starts from the customer-visible artifact converges; the
one that starts from the service topology does not. Same move, two-hour scale.

### 2.2 The NOT SHIPPING list

Two lists in `capstone/SCOPE.md`. `SHIPPING` — five items, hard cap. `NOT SHIPPING` — explicit,
named, with the tempting ones on it.

The second does the work, and the reason is temporal. **You write it while you are calm.** At 4pm
tomorrow you will be tired, the demo nearly working, and PDF export will feel like twenty minutes.
It is never twenty minutes — but that isn't the point. The point is that 4pm-tomorrow-you is not
the right person to make that call, and the list is a message from the version of you who was.

An item merely absent from SHIPPING is undecided, so you re-litigate it every spare hour. One
written on NOT SHIPPING is decided, and reopening it costs visible effort — the same mechanism as
a design doc's "alternatives considered" section.

### 2.3 The demo moment

One 30-second sequence. Everything on the shipping list must serve it.

> *"Ridgeline Freight's Q3 review is due Friday. Generate it."* → 40 seconds later: performance
> vs. contract, detention exposure, attributed root causes, cited policy references, three
> recommendations, each traceable to a source.

A scoping instrument, not a marketing exercise. Once written down, every scope question has a
mechanical answer: does this appear in those 30 seconds, or make what appears more credible? If
neither, it isn't shipping. A four-quarter trend chart is genuinely useful and does not appear.
Cut it.

---

### 2.4 Evaluating a document, not an answer

Today's output is ~1,200 words containing forty-odd factual claims, a verdict, and three
recommendations, with no reference document to diff against. So decompose "is this review good?"
into four classes with different costs and different authority.

| Class | How it runs | Cost | What it catches |
|---|---|---|---|
| **Structural** | Deterministic parse | Free | Missing sections, surviving placeholders, untagged numbers |
| **Factual** | Recompute from source, diff | Free | Wrong numbers |
| **Quality** | Calibrated LLM judge | Cents | Generic recommendations, wrong tone |
| **Adversarial** | Three subjects, compare conclusions | 3× a run | A system that templates instead of reasoning |

**Structural.** All sections present. No `TBD` or `[insert]` survived — check literally, because a
model short on retrieved context will emit a bracketed placeholder inside an otherwise polished
paragraph. Every numeric claim carries a provenance tag naming its query; every policy assertion a
citation. Costs nothing; run it forever.

**Factual.** One method only: **recompute every number independently from source and diff.** Not
"ask the model if it's right." Take the detention events, apply the policy in code — $65/hr after
2 hours free time, 15-minute increments rounded up, $650 cap per event — and compare against the
document's claim. Same for composite score, FTA, band assignment.

Why this outranks everything: **a document with a wrong number is worse than no document.** No
document costs a half-day of analyst time. A wrong detention total goes to the carrier, their
system disagrees, and you are in a dispute where your side was generated by a machine nobody now
trusts. And it *will* be found — a VP of Transportation reads the numbers first and spots a bad one
in about thirty seconds. Factual is 100% or it doesn't ship.

**Quality.** The Day 13 calibrated judge on one narrow question: are these recommendations
supported by the findings *in this document*, or would they fit any carrier? Keep the rubric
specific — "actionable" is usable only if it means naming a lane, event or threshold, what
changes, and by when.

### 2.5 The adversarial check: different conclusions, not different numbers

Build **three carriers with genuinely different profiles**:

| Profile | Shape | Correct conclusion |
|---|---|---|
| **Good** | FTA 94%, composite 91, Platinum, negligible detention | Continue, expand allocation |
| **Bad** | FTA 78% two consecutive quarters, composite 64, Bronze, heavy detention | Lane Review triggered, formal remediation |
| **Ambiguous** | Ridgeline Freight — FTA 83%, composite 78.5, Silver | Contested: below the 85% line this quarter but not last; detention concentrated in two facilities, not systemic |

Then verify the system reaches **different conclusions**, not merely different numbers.

A templating system will happily produce three documents with correct, different figures in every
slot and the *same* narrative arc: "performance is mixed, there are areas of strength and areas
for improvement, we recommend continued monitoring." Structurally perfect, factually perfect,
worthless. It reaches no conclusion, so it cannot reach a different one.

What you are testing: does the good performer's review recommend *expansion* while the bad one
recommends *remediation*? Does the bad one state "Lane Review is triggered" — a specific,
falsifiable, consequential claim? Does the ambiguous one say something honest about the ambiguity
instead of splitting the difference?

**This is invisible with one test carrier.** With Ridgeline alone every document looks plausible;
there is nothing to contrast it against. The failure lives in the diff between runs — so the
adversarial check is a *set*, not a case.

When it fails first time, the cause is almost always that your prompt describes the document's
*structure* and never states *judgement criteria*. Fix: give the writer explicit thresholds (FTA
below 85% for two consecutive quarters ⇒ Lane Review; composite below 70 ⇒ band downgrade) and
require a **stated verdict before the narrative**, so the prose must stay consistent with a
commitment already made.

### 2.6 Fix order when the eval fails

**1. Factual errors.** Non-negotiable, first. The cause is almost never the model — it is a join
duplicating detention events, a date boundary pulling a Q2 shipment into Q3, or 15-minute rounding
applied down instead of up. Look at the data path before the prompt.

**2. Missing citations.** An unverifiable claim in a document going to an external carrier is a
liability. Usually a chunk boundary severed the claim from its heading — the Day 3 problem, in
production.

**3. Generic recommendations.** Most common, most damaging, and the one that survives every other
check. Test: would this recommendation apply unchanged to any other carrier? If yes, the document
is worthless however good it looks.

The fix is mechanical: **summary statistics can only produce summary advice.** "$18,400 across 47
events" yields "reduce detention." Feed the three worst *specific* events — date, shipment ID,
facility, dwell, amount — and you get "three of the five worst detention events in Q3 occurred at
the Joliet DC on 06:00–09:00 appointments; moving those tenders to afternoon windows addresses
$4,100 of the $18,400." Specificity in, specificity out.

**4. Structural problems.** Last — cosmetic and cheap.

Re-run after each fix and log the delta. Don't batch; you lose attribution.

---

## 3. Worked example — on paper

A judgement exercise, not arithmetic. 9:00am Day 20, hard stop 6pm tomorrow. Eleven defensible
items:

```
 1. Carrier review document, end-to-end, one carrier/quarter
 2. HTML render with clean styling
 3. Detention exposure from raw events ($65/hr, 2hr free, 15-min
    increments rounded up, $650/event cap)
 4. Verified policy citations — every assertion quotes its source
 5. Web UI: carrier dropdown, progress bar, download button
 6. Three carrier fixtures (good / bad / ambiguous)
 7. Lane Review trigger detection (FTA < 85%, two consecutive quarters)
 8. Slack notification on completion
 9. Peer comparison within the same lane bucket
10. PDF export
11. Multi-quarter trend charts
```

**Q1.** Which single item, if it fails, kills the demo outright?

**Q2.** Two items look like features but are really the eval. Which, and why do they stay?

**Q3.** Which is cheapest to fake in twenty minutes, and what does faking it buy?

**Q4.** One item looks small and is a trap. Name it and its real cost.

**Q5.** Cut to five. Justify each survivor in one clause.

**Q6.** Difference between an item merely absent from SHIPPING and one written on NOT SHIPPING?

**Q7.** 4pm tomorrow, a supportive stakeholder asks for PDF export — "twenty minutes, right?"

<details>
<summary><b>Answers</b></summary>

**Q1.** Item 1. Everything else is an attribute of a document that must first exist.

**Q2.** Items 6 and 7. Item 6 is §2.5's adversarial set — without three subjects you cannot detect
a templating system — and it doubles as sample output a stranger can read without waiting 40
seconds. Item 7 is what makes those fixtures reach *different conclusions*: a falsifiable,
consequential verdict. Without it the reviews differ only in numbers.

**Q3.** Item 1 — a plausible Ridgeline review as a static string, rendered. Buys a decided output
format (every later hour becomes fill-in-the-blanks) and guarantees a demo if the day collapses.

**Q4.** Item 9. "Just another query" is wrong: you must define the peer set, normalise for lane mix
and volume, and decide what a fair comparison is — and it injects a new class of factual error into
a document whose factual score must be 100%. Runner-up: item 2; styling is unbounded.

**Q5.** Ship **1** (the demo *is* the document), **3** (the number a human can't compute quickly),
**4** (the trust mechanism; without it it's an LLM guess in a nice font), **6** (the eval, and the
samples), **7** (the verdict that makes conclusions differ). Cut 5, 8, 9, 10, 11; move 2 to SHOULD.
Note what went: the entire UI. The demo moment is a command and a document.

**Q6.** Absent means undecided, so it returns every spare hour. Listed means decided, and reopening
it requires visibly overturning your own call.

**Q7.** "Not for tomorrow's demo — it's on the not-shipping list. Output is markdown and renders in
the browser; if PDF is a real pilot requirement I'll scope it next week." You know this script. The
new part is that the written list makes this a *report of a prior decision* rather than a judgement
made under pressure — easier to say and easier to hear.

</details>

---

## 4. What people get wrong

**"Build the components properly, then integrate."**
Integration is where the unknowns are. Components built against an imagined interface get rebuilt.

**"The demo is a communication concern, so it comes last."**
It is a scoping instrument. Defined first it answers scope questions mechanically; defined last it
is a scramble to narrate whatever you built.

**"Evaluating a document is just evaluating a longer answer."**
A document has a shape to parse, numbers to recompute, quality to judge, and a conclusion that
must vary with the subject. Four mechanisms, not one.

**"If all my numbers are right, the document is good."**
It can be 100% factual and reach no conclusion — which passes every check except the adversarial
one.

**"Three test carriers is over-engineering for a two-day build."**
One carrier tells you the document looks plausible; it cannot tell you the system is reasoning.

**"Generic recommendations are a prompt problem."**
An *input* problem. Summary statistics in, summary advice out.

---

## 5. The trainer's angle

**The analogy that lands:** a house with plumbing roughed in to every room and no fixtures beats
one perfect marble bathroom and no water anywhere else. You can live in the first badly; you
cannot live in the second at all.

**The demo that makes it click:** two generated reviews side by side — good carrier, bad carrier
— from a system with correct numbers and no judgement criteria. The room reads both, notices the
numbers differ, then someone notices the *conclusion* is identical. The audience finds the
failure themselves, in a document that looked fine.

**The predictive question to ask first:** *"Structural, factual and quality checks all pass. Name
a way the document is still useless."* Let them guess before the side-by-side.

**The question a sharp student will ask:** *"Why not have an LLM judge score the whole document?"*

> Because the classes have different costs and different authority. Structural checks are free and
> run forever. Factual checks are the only ones with ground truth and the only ones that must be
> 100%, so you never want them mediated by a model that can be argued into agreeing. The judge is
> for the one property with no deterministic definition. Handing it everything makes your cheapest
> and most authoritative checks probabilistic, which is exactly backwards.

---

## 6. Self-check

1. Why is hardcoding a fake output at 0:20 the highest-value step of the morning?
2. What does the NOT SHIPPING list protect against that a short SHIPPING list does not?
3. What test does the demo moment let you apply to any proposed feature?
4. Name the four check classes and what each catches.
5. Why must factual be 100% rather than "high"?
6. Difference between three reviews with different numbers and three with different conclusions?
7. Why can't the adversarial failure be detected with one test carrier?
8. Good and bad carriers get the same narrative. Most likely cause, and the fix?
9. State the fix order after an eval failure, and why factual is first.
10. Why are generic recommendations an input problem rather than a prompt problem?

<details>
<summary><b>Answers</b></summary>

1. It forces the output format to be decided before three hours go into retrieval — an undecided
   output format is where scope creep hides. Also guarantees a demo exists.
2. Re-litigation. An absent item is undecided and returns; a listed one must be visibly overturned.
3. Does it appear in the 30 seconds, or make what appears more credible? If neither, cut.
4. Structural (missing sections, placeholders, untagged numbers); factual (wrong numbers, by
   independent recomputation and diff); quality (generic recommendations, tone); adversarial
   (same conclusion across different subjects).
5. A wrong number is worse than no document — it creates a carrier dispute, and any domain expert
   finds it in thirty seconds. No partial credit.
6. Different numbers proves the data path works. Different conclusions proves the system reasons.
   A template produces the first and never the second.
7. No contrast. One plausible document cannot reveal that the narrative would have been identical
   for a different subject; the failure lives in the diff.
8. The prompt describes structure, not judgement. Add explicit thresholds (FTA < 85% for two
   consecutive quarters ⇒ Lane Review) and require a stated verdict before the narrative.
9. Factual → citations → generic recommendations → structure. Factual first because a wrong number
   destroys the whole document's credibility; the rest is cosmetic beside it.
10. Summary statistics cannot yield specific advice. Feed the worst specific events — dates, IDs,
    facility, amounts — not a total.

</details>

**Scored below 7?** Re-read §2.4 and §2.5. The lab's Block 2 is built entirely on them, and they
are the only genuinely new material today.

---

## 7. Going deeper (optional)

- Your `LEARNING_LOG.md` from Day 13 — reuse the judge calibration numbers, don't re-derive them.
- Anthropic's published guidance on evaluating open-ended generation — the split into
  deterministic and model-judged checks is the same shape as §2.4.
- Anything you've read on "definition of done" in program management. It transfers almost
  unchanged; the only new clause is *conclusions must differ across subjects*.

---

**Now go to `labs/DAY_20.md`.** Block 0 is §2.2–2.3, Block 1 is §2.1, Block 2 is §2.4–2.5 (spend
your time on the three-carrier set), and Block 3 is §2.6 in order.
