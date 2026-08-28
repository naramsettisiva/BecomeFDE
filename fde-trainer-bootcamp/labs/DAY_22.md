# Day 22 — The Trainer Craft: Designing Curriculum That Sticks

**Fri Sep 25, 2026** · Week 4 · Maps to: **the trainer role** · Backend: n/a · Est. cost: **$0–1**

> **Before you start — read `learn/DAY_22_LEARN.md` (1:15).**
> Failure-organised curriculum, four techniques, assessment. The lab below assumes it and does not re-explain it.


---

## Why today matters

You have been *practising* teaching for 21 days. Today you learn the craft deliberately.

There is a specific reason most technical training fails: it's organised around **topics**
(here is RAG, here is agents) instead of around **the failures a practitioner will hit**.
Topic-organised training produces students who can recite and cannot debug. Failure-organised
training produces students who recognise a problem when they meet it.

You have an unusual asset: a `LEARNING_LOG.md` containing 21 days of your own confusions,
recorded at the moment they happened, before you knew the answer. That file is worth more
than any curriculum template, because a trainer's biggest handicap is forgetting what it
felt like not to know. You wrote it down.

---

## Objectives

1. Mine your learning log into a failure-organised curriculum.
2. Learn and apply the four teaching techniques that separate good sessions from bad.
3. Build a complete, deliverable 60-minute lesson with materials.
4. Design the assessment — how you'd know a student actually learned it.

---

## Schedule (5:00)

| Block | Time | What |
|---|---|---|
| 0 | 0:45 | Mine the learning log |
| 1 | 1:15 | **Learn** — `learn/DAY_22_LEARN.md` |
| 2 | 2:00 | Build the 60-minute lesson, complete |
| 3 | 1:00 | Design the assessment + the full curriculum outline |

---

## Block 0 — Mine the learning log (0:45)

Read all 21 entries. Extract into `teaching/CURRICULUM_SOURCE.md`:

**1. Every confusion, verbatim.** Don't paraphrase — the raw phrasing is the value. Group
into clusters. You'll find 6–10 clusters and they are your curriculum's actual spine.

Likely clusters, based on what this course puts people through:
- "I thought embeddings understood meaning, not topic"
- "My eval looked fine and my system was broken"
- "I didn't know tool schemas cost tokens on every step"
- "I trusted the model's citation"
- "I set a threshold before I measured the noise"
- "I didn't know a document could contain instructions"

**2. Every trap-list item across all 21 labs.** You have ~120. These are your "common
errors" sections and your exam questions.

**3. Every moment something clicked.** What was the specific demonstration that did it?
The lost-in-the-middle experiment? The indirect injection? Those demos are your lesson
hooks — they're empirically validated on a sample size of one, which is one more than
most curriculum designers have.

**4. Every question you couldn't answer.** These are the questions students will ask you
live. Answer them now, in writing. That file becomes your FAQ, and having it means you'll
never be caught flat.

---

## Block 1 — Learn (1:15)

**Read `learn/DAY_22_LEARN.md` and work its examples on paper before continuing.**
Take the self-check at the end. Anything you miss goes on a flashcard and into tomorrow's
warm-up. The material below consolidates the module — it is not a substitute for it.

### 1.1 Failure-first design

Compare two lesson openings for the same content:

> **Topic-first:** "Today we'll cover retrieval-augmented generation. RAG has three
> components: an indexer, a retriever, and a generator..."

> **Failure-first:** "Here's a RAG system answering a question about detention charges.
> [shows confident, wrong answer] The retrieval worked. The model is fine. The answer is
> wrong. In the next hour you'll learn the four places this breaks and how to tell which
> one you're in."

The second creates a question the audience wants answered. Adults learn when they have an
open loop, not when they receive information. Every lesson you write from now on opens
with a failure.

**The structure that follows from this:**

```
1. FAILURE      Show it broken. Real, not contrived. 2-3 min.
2. QUESTION     Name what we don't yet understand. 1 min.
3. FRAME        The mental model — 3-5 elements, written down, referenced throughout. 5 min.
4. BUILD        Live, typed, incremental. Break it deliberately once. 20-25 min.
5. MEASURE      Show the number move. 5 min.
6. GENERALISE   Where else this applies. 5 min.
7. PRACTICE     They do it. 15 min.
8. CLOSE        One sentence they can repeat. One thing to try. 2 min.
```

### 1.2 The four techniques

**a. Predictive questioning.** Before you run the code, ask: *"What do you think happens
if I set k to 12?"* Take two answers. Then run it. Prediction before observation roughly
doubles retention, and it's free.

**b. Deliberate error.** Make a mistake on purpose, let it fail, then debug it live. This
teaches three things at once: the concept, the error message, and the debugging process.
It also models being wrong gracefully — which for many students is the more valuable lesson.

**c. The two-column mental model.** Keep a persistent visual (a whiteboard, a comment
block, a slide you return to). Refer to it by name repeatedly. "Remember, we're still in
clause two of the RAG contract — retrieval." Repetition of a named frame is what makes a
session cohere rather than feel like a list.

**d. Naming the confusion before they feel it.** *"This next part confused me for two hours.
The thing that will trip you is that the embedding for a question doesn't look like the
embedding for its answer. Watch."* Pre-naming a confusion converts a student's private
frustration into shared expectation. Your learning log is a list of these.

### 1.3 Pacing, and the two failure modes

**Too fast** is the default failure of an expert. Symptoms: no questions (they're lost, not
satisfied), typing sounds stop, chat goes quiet. Fix: a checkpoint every 10 minutes —
*"Everyone got output? Paste your top-1 score in chat."* A concrete artifact request is a
far better check than "any questions?", which always returns silence.

**Too slow** is the default failure of a nervous teacher. Symptoms: advanced students go
quiet, side conversations, people finishing your sentences. Fix: a parked "stretch" task
for the fast half so you can pace to the middle without losing the top.

Rule of thumb from your own recordings: **live typing takes 2.5× longer than you estimate.**
Time your Day 6 and Day 12 lessons against your planned durations and compute your personal
multiplier. Then plan with it.

---

## Block 2 — Build one complete 60-minute lesson (2:00)

Choose the topic where you have the strongest material and the strongest demos. Recommended:
**"Evals: why your AI system's score is lying to you"** — Module 05 territory, badly taught
everywhere, and you have unusually good artifacts from Days 5, 13, and 16.

Produce a full deliverable set in `teaching/lesson_evals/`:

**1. `LESSON_PLAN.md`** — minute-by-minute:

```
00:00  FAILURE. Two RAG systems side by side. System A scores 0.91, B scores 0.78.
       Show three real answers from each. B is obviously better to anyone reading.
       "Your eval said A. Your eyes say B. One of them is wrong. Which?"
00:03  QUESTION. What is a score actually measuring?
00:05  FRAME. The evaluation ladder — 4 rungs, written on screen, referenced all hour.
00:12  BUILD 1. Golden set generation, live. Generate 10 cases. Read them aloud.
       PREDICT: "How many of these do you think are actually good questions?"
       Review them together. Reject 3. Discuss why.
00:25  BUILD 2. Retrieval metrics from scratch. Recall@k and MRR in 10 lines.
       DELIBERATE ERROR: use MRR on the multi-hop case. It scores 1.0 and the
       system got half the answer. Let the room spot it.
00:38  BUILD 3. The judge. Score 5 answers. Then hand-label the same 5.
       Compute kappa live. It will be mediocre. Sit with that.
00:48  MEASURE. Tighten the rubric with one change. Re-run. Show kappa move.
00:53  GENERALISE. The noise floor rule. Why gates get disabled. The 5-run experiment.
00:57  PRACTICE (assigned). Take your own project. Build 20 cases. Measure your noise floor.
00:59  CLOSE. "A gate tighter than your noise floor gets disabled in two weeks,
       and then you have nothing."
```

**2. `SLIDES.md`** — 12 slides maximum. One idea each. No slide during live coding; the
editor is the slide.

**3. `starter/` and `solution/`** — working repos. Starter has the scaffolding and `TODO`s;
solution is complete. Test both from a **clean clone in a fresh venv**. This is the step
everyone skips and every cohort suffers for.

**4. `EXERCISES.md`** — three tiers so everyone has something:
- Core (everyone): build 20 cases, compute recall@5
- Stretch: implement nDCG, compare rankings to recall
- Challenge: measure your noise floor and set a threshold from it

**5. `FAQ.md`** — from your learning log's unanswered questions, plus:
- "Can't I just use RAGAS?" (You can. Here's what it computes and what it doesn't.)
- "How many cases do I need?" (Enough that your noise floor is smaller than the effect
  you care about. Here's how to check.)
- "My judge disagrees with me. Who's right?" (Read the disagreements. Usually the rubric.
  Sometimes you.)
- "How do I get real user questions before we have users?" (Personas, plus the client's
  existing support tickets and Slack history — the best golden sets are archaeological.)

**6. `INSTRUCTOR_NOTES.md`** — where it goes wrong when *you* teach it:
- The golden-set generation takes longer than you think — have 10 pre-generated as a fallback
- Someone will have no API key. Have the local path ready and tested
- κ will be embarrassing on the first run. That's the lesson, not a problem. Don't rescue it
- If the room is quiet at 00:25, do a paste-your-number checkpoint

---

## Block 3 — Assessment + full curriculum outline (1:00)

### 3.1 Assessment design (25 min)

How do you know they learned it? Not "did they enjoy it" — that measures your charisma.

| Level | Measures | Instrument |
|---|---|---|
| **Recall** | They remember the frame | Quick quiz: name the four rungs |
| **Application** | They can do it on new material | Build an eval for a corpus they haven't seen |
| **Diagnosis** | They can debug it | Given a broken eval, identify what's wrong. **This is the real test** |
| **Transfer** | They apply it unprompted | Their own project's eval, reviewed two weeks later |

Build the diagnosis instrument — it's the valuable one. Write **five broken evals**, each
with a different defect: a judge from the same model family, thresholds below the noise
floor, a golden set with no unanswerable cases, absolute scores confounded by verbosity, a
gate that silently skips on API error. Ask students to find the defect.

That exercise is genuinely excellent, and having built it is a strong argument for letting
you run the session.

### 3.2 Full curriculum outline (35 min)

`teaching/CURRICULUM.md` — your complete offering, structured as failures, not topics:

```
Module 1  "It gave a confident wrong answer"        → RAG contract, retrieval, citation
Module 2  "It works on my questions, not theirs"    → evals, golden sets, judges
Module 3  "It found the document, not the answer"   → chunking, hybrid, rerank, context
Module 4  "It forgot what I told it"                → memory types, context budget
Module 5  "It did the wrong thing with my tools"    → agent loop, authorisation, budgets
Module 6  "It's too slow and too expensive"         → caching, routing, cost model
Module 7  "It broke and I can't find out why"       → tracing, metrics, incident drill
Module 8  "Someone put instructions in my documents"→ injection, defence in depth
Module 9  "It only runs on my laptop"               → serving, deploy, handover
Module 10 "They can't run it without me"            → enablement, runbooks, eval ownership
```

For each: the opening failure demo, the frame, the build, the measurable outcome, and the
prerequisite. That's a complete 10-session programme, derived entirely from your own
recorded experience — and it covers the same ground as any published AI-engineering syllabus,
organised in a way that teaches better.

Write a one-paragraph pitch at the top: who it's for, what they'll be able to do, and why
failure-organised beats topic-organised. That paragraph is what you send when you ask to
teach.

---

## Done when

- [ ] Learning log mined into clusters, traps, click-moments, and unanswered questions
- [ ] One complete 60-minute lesson: plan, slides, starter, solution, exercises, FAQ, instructor notes
- [ ] Starter and solution both tested from a clean clone
- [ ] Five broken-eval diagnosis exercises written
- [ ] Full 10-module curriculum outline, failure-organised, with the pitch paragraph

---

## Trap list

- Organising by topic. Organise by failure.
- Slides during live coding.
- Untested starter repos. It will break for 30 people at once.
- "Any questions?" as a comprehension check. Ask for an artifact instead.
- Rescuing a demo that's failing usefully. Let it fail; that's the lesson.
- Assessing enjoyment instead of capability.
- Planning at your own typing speed. Use your measured 2.5× multiplier.
