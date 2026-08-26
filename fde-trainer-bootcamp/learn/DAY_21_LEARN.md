# Day 21 · Learn — Defensibility and the case study

**Read before `labs/DAY_21.md`. Budget 0:30.**

---

## 1. Where this sits

Yesterday you proved it works. Today you make it **defensible** — different properties, examined
by different people, at different moments.

You know the first half. You have shipped services into production at Amazon; blast radius, least
privilege and rollback are not new ideas. What is new is *which* of them a buyer of an AI system
probes first, and why some (per-route guardrail scoping, a trace_id in the document footer) exist
for reasons specific to generated output rather than to running code.

The second half is new territory: the **teardown question** and the **case study**. As a TPM you
wrote for people who already had the context. As an FDE you write for a buyer who does not, has
not decided, and is deciding partly on whether you seem like someone who tells them bad news
early.

---

## 2. The mechanism

### 2.1 What "defensible" means

Working means it produced a good document when you ran it. Defensible means you can answer, on the
spot, in front of someone hostile or merely careful:

- Where did this number come from? Show me.
- What happens when the model is wrong? When it's down?
- What does this cost per run, and what does the worst month look like?
- What can it *not* do?
- If we stop after the pilot, what does that cost us?

All five are answerable from artifacts, not from confidence — defensibility is a property of what
you built and wrote down, not of how well you present. And the demo answers none of them, which is
why the demo is the easy half.

### 2.2 Hardening as a checklist with reasons

Ritual hardening — enabling everything everywhere because a checklist says so — costs money, hides
which control is load-bearing, and leaves you unable to defend a choice you never made.

| Control | The reason, stated properly |
|---|---|
| **Guardrails scoped per route** | Guardrails bill per policy evaluated, so enabling the full set everywhere is a recurring monthly cost on paths carrying no risk. The internal analysis draft needs an injection check on indexed carrier documents; the external draft needs PII and tone. Different sets. |
| **`trace_id` in the document footer** | Six weeks out, a carrier disputes a detention figure. Without it you have a PDF and an argument. With it you pull the exact run, query result and retrieved policy revision, and either correct yourself in ten minutes or show your work. The difference between a system of record and a plausible essay. |
| **Cost cap → partial output with a banner** | Silent failure on a paid generation is the worst outcome: the user waits, gets nothing, retries, spends again. A document headed *"incomplete — budget exhausted"* is honest and salvageable. |
| **Least privilege** | The data agent needs read on four TMS tables. Nothing here needs write. Say that out loud in a review and watch the security conversation get shorter. |
| **Reserved concurrency** | Blast radius. A runaway generation loop is bounded by a number you set, not by your account limit. A containment control, not a performance one. |
| **Idempotency** | Same carrier, same quarter, same document unless `--force`. Prevents accidental spend, and means two people reading "the Q3 Ridgeline review" read the same text. |

Lead with the trace_id in a demo. People who have lived through a dispute recognise it instantly,
and it signals you thought past the demo into month four.

### 2.3 The teardown question

> *"If we don't proceed after the pilot, what does it cost us to stop, and how long does it take?"*

Almost nobody building an AI pilot can answer this. Almost every enterprise buyer wants to ask it,
and many won't, because asking sounds like they have already decided against you.

The counterintuitive part, and the most valuable thing in today's module: **naming the exit is a
way of getting to yes.** A pilot that can be cleanly stopped is easier to start. The buyer's real
fear is not that your system fails — it is that it half-succeeds, embeds itself in a workflow, and
becomes something they can neither remove nor justify. Every procurement process that has ever
slowed you down exists to manage that fear.

Answer it before it's asked. For the carrier review system the answer is short, *by design*:

> Read-only over the TMS via MCP; it writes files, never rows. Stopping means revoking one IAM
> role and deleting the vector index. No writes to reverse, no schema change, no migration.
> Analysts return to the manual process, which never stopped working. Two days, including handing
> over the eval harness so you can judge whatever replaces it.

Notice: **the decisions that make the teardown cheap are the same ones that make the system safe.**
Read-only access, no schema changes, output as files rather than records in someone else's system.
You did not choose them for this answer, but they are what makes it good — and had you built a
write path into the TMS, this is a paragraph you would dread writing.

You know the shape from launch reviews: rollback plan first, and nobody reads it as pessimism.
Same instinct, aimed at the commercial conversation instead of the deploy.

### 2.4 The case study as a professional artifact

Seven sections, and the order is the content.

| # | Section | Why it is *here* |
|---|---|---|
| 1 | **The problem — in their language** | The reader must recognise their own problem before spending attention on your solution. "A quarterly review takes an analyst half a day; 60 carriers is 30 analyst-days a quarter, and they arrive late." No architecture. |
| 2 | **The approach** | Eval-first: what a good review *is* — structural completeness, factual accuracy against source, verified citations, specific recommendations — defined before building. This separates you from someone who wired an API to a prompt. |
| 3 | **The architecture** | Now they care. Multi-agent split and why, MCP and why, verification as a separate layer and why. Three "why"s, not a parts list. |
| 4 | **The hard parts** | **The section that gets you hired.** Real ones, real resolutions. |
| 5 | **Results** | Baseline *and* final. A final number alone is unfalsifiable; a delta is evidence you measured. |
| 6 | **Limitations** | Do not skip. Its absence is the tell that the document is marketing rather than engineering, and readers who matter check for it specifically. |
| 7 | **Links** | Demo, repo, video. |

**On §4.** A hard part is a property of the *problem* a competent engineer would also have hit,
plus a non-obvious resolution. "Prompt engineering took iterations" is not one. "Two revisions of
the detention policy were indexed at once and retrieval returned contradictory free-time
thresholds depending on phrasing; fixed with effective-date metadata filtered to the revision in
force for the quarter" is. Specific, checkable, and it demonstrates what you are actually selling:
you find that class of bug before a client does.

**On §6.** What needs human review before anything reaches a carrier. What the system silently
cannot see. Limitations are a disclosure against your own interest, which is why they carry signal.

### 2.5 Why the writing outruns the code

**Written analysis with numbers travels further than code.** A hiring manager skims a repo — file
tree, README, maybe one file — and forms an impression in ninety seconds. The same person *reads*
a two-page memo that answers a question they have been arguing about internally, and forwards it.
Code is evidence for one reader who chooses to dig. A case study is an argument that propagates
without you in the room. This should be familiar: the six-page narrative outperformed the deck for
the same reason.

---

## 3. Worked example — on paper

A competent engineer hands you this outline. Diagnose and reorder.

```
CARRIER PERFORMANCE COPILOT — draft case study

1. Architecture (400w) — five agents, MCP tool layer, Bedrock + OpenSearch,
   system diagram
2. Tech stack (150w) — table of every service used
3. What it does (100w) — "generates quarterly carrier reviews automatically"
4. Results (80w) — "dramatically faster than manual review, high accuracy,
   works well across different carriers"
5. Challenges (100w) — "prompt engineering took several iterations;
   embeddings were tricky; reliable JSON was hard"
6. Future work (80w) — "add more carriers, fine-tune a model, build a UI"
7. Links
```

**Q1.** Section 1 leads. Which reader do you lose in the first paragraph, and why?

**Q2.** Make §4 defensible. Which three numbers does it need, and which must be labelled an
estimate?

**Q3.** "Challenges" vs. "the hard parts" — the difference? Rewrite one §5 entry as a real hard
part.

**Q4.** Why is "future work" not a substitute for a limitations section?

**Q5.** Reorder into the correct sequence. What happens to §2?

**Q6.** One sentence is missing from the very top. What must it contain?

**Q7.** A reviewer asks the teardown question. Which section should have pre-answered it, and what
is the answer here?

<details>
<summary><b>Answers</b></summary>

**Q1.** The person who owns the problem — the VP of Transportation, or the hiring manager deciding
whether this is worth thirty minutes. They do not have "five agents" as a problem; they have 30
analyst-days a quarter and reviews that arrive late. Architecture-first asks them to care about
your solution before they have recognised their problem, and only works on a reader who already
agreed the problem matters — not the reader you need.

**Q2.** (a) Baseline vs. final eval scorecard — structural, factual, quality, before and after.
(b) Time per review before and after, explicit that "40 seconds" is generation and human review
sits on top. (c) Cost per generation against the analyst hours displaced. The **estimate** is the
analyst-days-saved figure: it comes from an interview or an assumption, not a measurement. Label
it. The labelling is worth more than the number.

**Q3.** Challenges are you learning the tools — true of everyone, informative about nobody. Hard
parts are properties of the problem plus a non-obvious resolution. Rewrite: *"embeddings were
tricky"* → *"Two revisions of the detention policy were indexed at once, and retrieval returned
contradictory free-time thresholds depending on phrasing. Three of twelve detention figures were
computed against the superseded revision. Fixed with effective-date metadata and retrieval filtered
to the revision in force for the quarter."*

**Q4.** Future work is a promise; limitations are a disclosure. Future work is flattering, costs
nothing, and could be written by someone who never shipped. Limitations run against your interest,
which is why a reader treats them as signal — and they answer the buyer's actual question: *what
must a human check before this goes to a carrier?*

**Q5.** Problem → approach → architecture → hard parts → results → limitations → links. §2 is
deleted as a section; the two or three choices that mattered get one sentence each *inside*
architecture, with reasons. A stack list says what you touched, not what you decided.

**Q6.** The problem in their units plus the outcome: *"A quarterly carrier business review takes an
analyst half a day; across 60 contracted carriers that is 30 analyst-days a quarter, and they still
arrive late. This system produces a cited, number-verified draft in 40 seconds."*

**Q7.** Limitations, §6, or a short paragraph beside it. Read-only over the TMS via MCP, writes
files not rows; stopping is one IAM role revoked and the index deleted; no writes to reverse, no
schema change, no migration; analysts return to a manual process that never stopped; two days
including eval-harness handover. Short because the architecture made it short.

</details>

---

## 4. What people get wrong

**"Hardening is a checklist you complete."**
It is a set of decisions with costs. Per-policy billing makes "enable everything everywhere" a
recurring line item, and a control enabled without a reason is one you cannot defend when asked.

**"Tracing is for debugging."**
It is for *disputes*. The footer trace_id is an audit affordance for the carrier conversation six
weeks out — a different requirement from your own debugging.

**"Failing closed is always safest."**
On a paid generation, silence is the worst outcome — the user waits, gets nothing, retries, spends
again. A clearly bannered partial document is more honest and more useful.

**"Talking about stopping makes them less likely to start."**
Inverted. The fear is a half-successful pilot they cannot remove. A cheap, named exit removes the
reason to say no.

**"The case study is marketing, so it should be positive."**
The limitations section is the strongest credibility signal in it. Its absence is louder than its
content.

**"The code is the portfolio."**
A repo is skimmed; a memo with numbers is read and forwarded. Only one travels without you.

---

## 5. The trainer's angle

**The analogy that lands:** the trace_id is the BOL number. Nobody looks at it for months, then
there is a claim and it is the only thing that matters. Freight people get this immediately and
stop treating observability as an engineering luxury.

**The demo that makes it click:** generate a review, point at the footer, say "a carrier disputes
this detention figure in November." Pull the trace; show the query result and the exact policy
revision retrieved. Twenty seconds, and it reframes the system from "AI wrote this" to "this is
reproducible."

**The exercise for a room:** three minutes to write the teardown answer for their own project.
Most cannot, and discovering that is the lesson. Then ask which architectural decision would have
to change to make their answer shorter.

**The question a sharp student will ask:** *"Doesn't a limitations section hand an interviewer
ammunition?"*

> It hands them ammunition they were going to find anyway, on your terms. The alternative is that
> they find it themselves and then also wonder what else you left out. The asymmetry is large: a
> disclosed limitation costs you one point; an undisclosed one they discover costs you the
> credibility of the whole document.

---

## 6. Self-check

1. "Working" vs. "defensible"? Name three questions only the second answers.
2. Why is per-route guardrail scoping a cost decision, not just an architecture one?
3. What does the footer trace_id buy you that logs alone do not?
4. Why is a bannered partial document better than a clean failure on cost-cap breach?
5. What is reserved concurrency actually controlling here?
6. State the teardown question, and why buyers want to ask it but often don't.
7. Why does naming a cheap exit make a pilot easier to start?
8. Why does the case study lead with the problem rather than the architecture?
9. What separates a "hard part" from a "challenge"?
10. Why is future work not a substitute for limitations?

<details>
<summary><b>Answers</b></summary>

1. Working = it produced a good output when run. Defensible = you can answer, from artifacts: where
   did this number come from, what happens when the model is wrong or down, what does it cost per
   run, what can it not do, what does stopping cost.
2. Guardrails bill per policy evaluated, so the full set on every route is a recurring monthly cost
   on paths carrying no risk. Routes differ — injection on indexed carrier docs, PII and tone on
   the external draft.
3. Reproducibility of a *specific claim* for a third party. On a dispute you retrieve the exact
   run, query result and policy revision, rather than searching logs by timestamp.
4. Silence makes the user wait, get nothing, retry and spend again. A banner says exactly what
   happened and leaves salvageable output.
5. Blast radius — bounding a runaway loop by a number you chose rather than the account limit.
6. *"If we don't proceed after the pilot, what does it cost us to stop, and how long?"* They want
   to ask because the real fear is a half-successful pilot they cannot remove; they often don't,
   because asking sounds like they have decided against you.
7. It removes the downside of trying. The commitment shrinks from "adopt this" to "run this for a
   quarter" — easier to make and easier to defend internally.
8. The reader must recognise their own problem before spending attention on your solution.
   Architecture-first only works on a reader who already agreed the problem matters.
9. A hard part is a property of the problem a competent engineer would also hit, with a non-obvious
   resolution. A challenge is you learning the tools — true of everyone, informative about nobody.
10. Future work is a promise and flatters you. Limitations are a disclosure against your interest,
    which is why they carry signal — and they answer what a human must still check.

</details>

**Scored below 7?** Re-read §2.3 and §2.4. Blocks 2 and 4 of the lab are built directly on them.

---

## 7. Going deeper (optional)

- Amazon's six-page narrative practice, read as a document-design argument rather than a meeting
  ritual. §2.5 is the same claim.
- AWS Well-Architected, Security and Cost pillars — skim for the *reasons* behind controls you
  already apply reflexively; §2.2 is that habit applied to AI-specific controls.
- Two or three case studies from consultancies you respect. Check each for a limitations section.
  Most won't have one. Notice how you read them differently once you've looked.

---

**Now go to `labs/DAY_21.md`.** Block 2 is §2.2 item by item, Block 4 is §2.4 (sections in the
listed order; write §6 first if you're short on time), and §2.3 belongs in the case study whether
or not anyone asks.
