# Day 06 — Week 1 Capstone: Ship It, Demo It, Teach It

**Mon Aug 31, 2026** · Week 1 · Maps to: **Module 07 — End-to-End Systems** · Backend: **local** + `[PAID]` · Est. cost: **$1–2**

> **Before you start — read `learn/DAY_06_LEARN.md` (0:45).**
> Week 1 synthesis; how demos and lessons are structured. The lab below assumes it and does not re-explain it.


---

## Why today matters

**FDE lens.** A working pipeline in a terminal is worth nothing to a client. The
transition from `python ask.py` to something a non-engineer can click is where 90% of
prototypes die, and it's where FDEs earn their title — *forward deployed* means the
thing runs where the user is. Today you cross that line for the first time.

**Trainer lens.** Today you produce your first full teaching asset: a 20-minute lesson
with a working demo, delivered on camera, with a deliberate failure and recovery. This
is the format of every conference talk and every cohort session you will ever run.

---

## Objectives

1. Ship a UI on top of RAG v1 that shows retrieval, citations, and cost — not just answers.
2. Write a demo script you can perform in 6 minutes without notes.
3. Record a 20-minute lesson: concept → live build → failure → fix → summary.
4. Write the Week 1 retrospective that shapes Week 2.

---

## Schedule (5:00)

| Block | Time | What |
|---|---|---|
| 0 | 0:30 | Warm-up: Week 1 recall, closed book |
| 1 | 0:45 | **Learn** — `learn/DAY_06_LEARN.md` |
| 2 | 1:15 | Build: Chainlit UI with transparency panel |
| 3 | 0:45 | Demo script + rehearsal |
| 4 | 1:15 | Teach-back #6 — the full 20-minute lesson |
| 5 | 0:30 | Week 1 retro + Week 2 prep |

---

## Block 0 — Warm-up: Week 1 recall (0:30)

Closed book, 20 questions. Write answers in `notebooks/day06_recall.md`, then check.
Anything you miss goes on a flashcard and gets reviewed every morning of Week 2.

1. Four layers of the stack; what changes when you swap each.
2. Three levels of structured output; failure mode of each.
3. Why retry a 429 but not a 400.
4. Cosine vs. Euclidean for normalised vectors.
5. Why does chunking sever conditions from numbers, and what's the fix?
6. What does the heading-path prefix do to retrieval quality, and why?
7. The four clauses of the RAG contract.
8. What is lost-in-the-middle and how do you mitigate it in prompt assembly?
9. Bronze / Silver / Gold citations.
10. Why is `INSUFFICIENT_CONTEXT` better than "say if you don't know"?
11. Recall@k vs. MRR — which one hides multi-hop failure and why?
12. nDCG — what does the discount do?
13. Three biases of an LLM judge and the fix for each.
14. What is Cohen's κ and what threshold makes a judge usable?
15. Why must a golden set contain unanswerable questions?
16. Your synthesis-bucket score vs. lookup-bucket score. Why the gap?
17. `M`, `ef_construction`, `ef_search`.
18. Input cost of 40k queries × 6k tokens on `gpt-4o-mini`.
19. Name the LLM failure mode that raises no exception.
20. What single change would most improve your current pipeline, and how would you prove it?

---

## Block 1 — Learn (0:45)

**Read `learn/DAY_06_LEARN.md` and work its examples before continuing.**
Take the self-check at the end. This is a build day, so the module is short and deliberately practical — read it once, properly, then build.

---

## Block 2 — Build the UI (1:15)

`capstone/week1/app.py` using **Chainlit** (async-native, streaming, easy custom panes).

Requirements — the UI must expose the machinery, not hide it:

```
┌─────────────────────────────────────────────────────────┐
│  Freight Ops Assistant                        [local ▾] │
├─────────────────────────────────────────────────────────┤
│  How much detention for a 5-hour wait?                  │
│                                                          │
│  Detention accrues at $65/hour after 2 hours of free    │
│  time, billed in 15-minute increments [02]. A 5-hour    │
│  wait yields 3 billable hours = $195, subject to the    │
│  $650 per-event cap [02].                                │
│                                                          │
│  ✓ [02] "Detention accrues at $65 per hour"   verified  │
│  ✓ [02] "capped at $650 per event"            verified  │
├─────────────────────────────────────────────────────────┤
│  ▸ Retrieved chunks (5)          ▸ Prompt   ▸ Cost      │
│    02 §Detention          0.847                          │
│    02 §Demurrage          0.712                          │
│    06 §Composite score    0.498  ← not used             │
│                                          1.8s · $0.0011  │
└─────────────────────────────────────────────────────────┘
```

Must-haves:

- [ ] Streaming answer tokens
- [ ] Inline citations, colour-coded **verified** (substring check passed) vs **unverified**
- [ ] Collapsible panel: retrieved chunks with scores and heading paths
- [ ] Collapsible panel: the exact assembled prompt (this is the transparency that wins client trust)
- [ ] Backend switcher: local ↔ hosted, live
- [ ] Running session cost, in dollars, visible at all times
- [ ] Graceful refusal display when `INSUFFICIENT_CONTEXT` fires

```bash
chainlit run capstone/week1/app.py -w
```

**The transparency panel is the differentiator.** Everyone demos a chat box. Almost
nobody shows the retrieved chunks and the assembled prompt live. Doing so does two
things: it makes the client trust you, and it makes the system *teachable* — you can
point at the screen and say "see, the right chunk was retrieved at rank 3 but the
model ignored it." Keep this pattern for the rest of your career.

---

## Block 3 — Demo script (0:45)

Write `portfolio/demo_script_week1.md`. Structure — 6 minutes, timed:

| Time | Beat | Purpose |
|---|---|---|
| 0:00–0:30 | **The problem, in their language.** "Your ops team gets 200 questions a week about accessorial policy. Each one is a Slack message and a 20-minute interruption." | Never open with the technology |
| 0:30–1:30 | **The happy path.** One question, streamed answer, verified citations. | Establish it works |
| 1:30–2:30 | **The transparency.** Open the panels. Show retrieval, show the prompt. | Establish it's not magic |
| 2:30–3:30 | **The refusal.** Ask something outside the corpus. It declines. | This is the trust moment. Most demos skip it. |
| 3:30–4:30 | **The honest limitation.** Ask your multi-hop question. Watch it underperform. Say so. Say what fixes it. | Credibility. Clients have seen ten demos; you're the first who named a weakness |
| 4:30–5:30 | **The numbers.** Scorecard + cost per query + monthly projection. | This is what gets funded |
| 5:30–6:00 | **The ask.** What you'd need to take it further. | Every demo ends with a next step |

Rehearse it **three times, timed, out loud**. Third run without notes. Yes, alone in a
room. This feels ridiculous and it is the single highest-return 30 minutes in Week 1 —
you cannot discover that beat 5 takes 90 seconds instead of 60 by reading it silently.

---

## Block 4 — Teach-back #6: your first full lesson (1:15)

Record **20 minutes**: *"Build a RAG system you can actually defend."*
Save `teaching/recordings/day_06_lesson.mov` and the outline in `teaching/lesson_01_rag.md`.

Required structure — this is the shape of every good technical lesson:

1. **Hook (2 min).** A wrong answer from a plausible-looking RAG system. Ask the room:
   why? Take no answers — plant the question.
2. **Frame (3 min).** The four-clause contract. Written down, referenced throughout.
3. **Live build (8 min).** Retrieve → assemble → generate. Type it. Do not paste.
4. **Deliberate failure (3 min).** Break clause 2 (retrieval misses). Show the confident
   wrong answer. Diagnose it on screen.
5. **Fix + measure (3 min).** Apply the fix, re-run the eval, show the number move.
6. **Close (1 min).** One sentence they can repeat. One thing to try tonight.

Rules for the recording:
- **Type live.** Pasting teaches nothing about pace and it hides the errors students hit.
- **Keep your typos in.** Recovering from a typo on camera is a teaching moment; editing
  it out is a missed one.
- Say "I don't know" if you hit something you don't know, then note it. That's the
  single most trust-building thing an instructor does.

Then watch it back at 1.0x — all 20 minutes, no skipping. Grade against:

| Dimension | 1–5 |
|---|---|
| Did the hook create a real question? | |
| Was the frame referenced at least 3 times? | |
| Live-build pace — could someone follow along typing? | |
| Was the failure genuinely surprising? | |
| Did the number actually move, visibly? | |
| Filler words per minute (count them) | |
| Did you explain *why* before *how*? | |

---

## Block 5 — Week 1 retro (0:30)

Write `LEARNING_LOG.md` → "Week 1 Retrospective":

1. **Scorecard delta.** Your best numbers today vs. the first run on Day 5.
2. **The biggest surprise.** One thing you believed on Aug 25 that's now wrong.
3. **The weakest bucket.** Which difficulty class fails, and your hypothesis why.
4. **Teaching self-assessment.** Across 6 recordings, what's your recurring flaw?
   (Common ones: burying the lead, narrating keystrokes, apologising for the material,
   speeding up when nervous.) Pick **one** to fix in Week 2 and write it at the top of
   every remaining lab file.
5. **Time honesty.** Actual hours vs. 5/day. If you're consistently over, we cut scope
   in Week 2 — tell me. Grinding to 7 hours a day for three more weeks does not work.

Then commit and push:

```bash
git add -A && git commit -m "Week 1 capstone: Chainlit RAG app, demo script, first full lesson" && git push
```

---

## Done when

- [ ] Chainlit app runs, streams, cites, shows chunks + prompt + cost, and refuses correctly
- [ ] Demo script written and rehearsed three times, third time from memory, under 6:30
- [ ] 20-minute lesson recorded, watched back in full, graded on all seven dimensions
- [ ] Week 1 retro written with a named teaching flaw to fix
- [ ] Everything pushed to GitHub

---

## Week 1 is done. What you now have

A RAG system you built from the vector math up, an eval harness with a calibrated judge,
a UI that shows its own reasoning, a demo you can perform cold, and six recordings of
yourself getting better at explaining it.

**Week 2 is agents.** The thing that made your synthesis bucket score 0.41 today gets
fixed on Days 8–9. Read `labs/DAY_07.md` tonight — 10 minutes, just the concept section,
so tomorrow starts warm.
