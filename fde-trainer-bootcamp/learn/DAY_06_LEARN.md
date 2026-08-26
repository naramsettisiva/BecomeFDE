# Day 06 · Learn — Week 1 as one system, and the architecture of a demo

**Read before `labs/DAY_06.md`. Budget 0:45 — this is a capstone day, so the module is short and the build is long.**

---

## 1. Where this sits

There is no new mechanism today. Days 1 through 5 gave you a language model, a typed call, an
embedding space, a retriever, an assembled prompt, a verifiable citation, and an instrument to
measure the whole thing. That's a system.

The problem today solves is that **the system has an audience of one.** It runs in your terminal,
takes arguments you remember, and outputs a wall of text that means something because you built
it. To a client that's worth nothing. To a room of students it's worth less than nothing, because
watching someone else's expertise scroll past is how people learn that a topic isn't for them.

So today's skill is delivery architecture: how a demo is structured so it makes an argument, and
how a lesson is structured so it transfers. Both have a shape, and the shape is not personal
style. Get it wrong and a working system reads as a toy.

---

## 2. The mechanism

### 2.1 Week 1 as one causal chain

Before you can teach it you need to hold it as one object. Here is the whole week as a chain,
with the diagnostic for each link — which is also the order you debug in:

| Link | The decision | How it fails | The one-line diagnostic |
|---|---|---|---|
| Tokenisation | none — it's imposed on you | Rare IDs cost 11× | Count tokens, don't estimate |
| Chunking | size, strategy, overlap | Severs a condition from its number | Read the chunk that contains `$65` — is `2 hours` in it? |
| Embedding | model, dimensionality | Topical match beats propositional | Score a paraphrase against a topical neighbour |
| Indexing | brute force vs. HNSW | Approximation misses a true neighbour | Compare against exhaustive search |
| Retrieval | k, hybrid, filters | Right document, wrong paragraph | Paste the correct chunk in — does the answer fix? |
| Assembly | order, delimiters, refusal instruction | Correct chunk present and unused | Reorder the same chunks — does the answer change? |
| Generation | model, temperature | Confident, well-formed, wrong | Does it refuse when it should? |
| Verification | Gold citation | Quote verifies but doesn't support | Is every stated number inside a verified quote? |
| Measurement | golden set, metrics, judge | Aggregate hides a broken bucket | Segment by difficulty; compute κ |

Read down that table once and you have the spine of every conversation you'll ever have about a
RAG system. **Its most valuable property is that it's ordered**: retrieval failures are cheaper to
diagnose than generation failures, and both are cheaper than chunking failures, so you check in
that order and rarely go past step five.

### 2.2 A demo is an argument, not a feature tour

The instinct is to show what the system can do. Resist it. **A demo is one argument made to three
audiences at once**, and every beat exists to move one of them:

| Audience | The question in their head | The beat that answers it |
|---|---|---|
| The ops user | "Would this actually answer my questions?" | The happy path, in their vocabulary |
| The engineering lead | "Is this a wrapper around a chatbot, or a system?" | The transparency panel |
| The budget holder | "What does it cost and what does it replace?" | The numbers |

Serve only the first and you get "nice demo" with no follow-up. Serve only the second and the ops
people disengage in ninety seconds. The order matters too: the ops user's question goes first,
because until the thing visibly works nobody cares how it works.

### 2.3 The seven beats, and why each is there

Six minutes, timed:

| Time | Beat | Why it exists — and what breaks without it |
|---|---|---|
| 0:00–0:30 | **The problem, in their language** | Opening with technology makes it your project, not their problem. "Your ops team gets 200 questions a week about accessorial policy; each one is a Slack message and a 20-minute interruption." |
| 0:30–1:30 | **The happy path** | Establishes it works at all. Everything after this is conditional on it |
| 1:30–2:30 | **The transparency** | Open the retrieved-chunks and assembled-prompt panels. This is what makes it a system rather than magic |
| 2:30–3:30 | **The refusal** | Ask something outside the corpus. It declines. **This is the trust moment and almost every demo skips it** |
| 3:30–4:30 | **The honest limitation** | Run your multi-hop question. Watch it underperform. Say so, and say what fixes it |
| 4:30–5:30 | **The numbers** | Scorecard, cost per query, monthly projection |
| 5:30–6:00 | **The ask** | Every demo ends with a next step, or it ends with nothing |

The two load-bearing beats are 4 and 5, and they're the two that feel most dangerous.

**Beat 4 — the refusal.** Everyone your client has met demoed a system that answers; nobody demoed
one that declines. The moment yours says `INSUFFICIENT_CONTEXT` to a question about drone
delivery, the room's model of it shifts from "confident text generator" to "thing with a known
boundary." That shift is what makes them willing to put it in front of carriers.

**Beat 5 — the named limitation.** Counter-intuitive enough to argue: you deliberately show your
system doing badly. The reason is that your client has seen ten flawless demos this quarter and
knows from experience that flawless demos become disappointing pilots. **You are the first person
to name a weakness before they find it**, so when you say the other parts work, they believe you.
Naming the fix — "that's query decomposition, known technique, here's what it takes" — converts
the weakness into evidence of competence.

### 2.4 Engineering the demo so it survives contact

Rule: **never demo anything you have not reproduced three times in a row.**

Four things break demos, in order of frequency:

**Dead air.** A 1.9-second wait is nothing at your desk and an eternity in front of twelve people.
Stream, so time-to-first-token is ~0.4s and something is visibly happening — and plan the sentence
you say while it generates rather than improvising it.

**Cold start.** Day 4's trap list says don't ingest on every query; in a demo it's fatal, and §3
Q4 has the arithmetic. Warm the index, run one throwaway query, confirm the panels populated
before anyone is watching.

**Non-determinism.** Temperature 0 (Day 1: consistent, not identical), fixed k, fixed seed where
your stack has one, and a terminal capture of the working run you can cut to without apologising.

**The question that derails.** Someone asks about a document that isn't in the corpus, or an edge
case you never tested. The move is the same one that works in a lesson: answer what you know, say
plainly what you don't, and write it down on screen where they can watch you write it. "I don't
know, good question, I'm noting it" costs nothing and buys more credibility than a confident guess
that unravels in week three.

### 2.5 Lesson architecture — the six-part shape

A demo makes an argument. A lesson transfers a capability, and it has a different shape:

**1 · Hook (2 min).** Show a wrong answer from a plausible-looking system and ask the room why.
Take no answers — the point isn't the discussion, it's that an unanswered question creates a
retrieval cue. Material landing on an open question is retained substantially better than the same
material delivered cold, and it works even when the guesses are wrong (Richland, Kornell & Kao,
2009). The cheapest technique in teaching, and the one most often skipped because it feels like
stalling.

**2 · Frame (3 min).** The four-clause contract, written down and left on screen. A frame is a
filing system: each new fact attaches to a clause instead of becoming a separate item in working
memory. **Reference it out loud at least three times** or it decays into a slide nobody used.

**3 · Live build (8 min).** Type it, don't paste. Pasting hides the pace, hides the errors students
will hit, and removes every natural pause where a question can land. §3 Q2 tells you how much code
fits in eight minutes, and it's less than you think — so pre-stage everything except the part you
want them watching.

**4 · Deliberate failure (3 min).** Break clause 2. Show the confident wrong answer. This is what
they'll remember in six weeks, because a violated expectation is what makes a memory durable.

**5 · Fix and measure (3 min).** Apply the fix, re-run the eval, **show the number move on
screen** — a before value and an after value, not "this should improve things." This beat is what
separates a lesson from a talk, and it's only possible because you built Day 5.

**6 · Close (1 min).** One sentence they can repeat to a colleague. One thing to try tonight.

### 2.6 The mechanics that separate good from bad

**Pace is arithmetic, not feel.** §3 Q1 works it out: a 20-minute lesson is roughly 2,500 spoken
words, of which hook, frame and close consume about 850. That leaves about four ideas explained
properly. If your outline has nine you will speed up, and speeding up is the most common failure
on a recording.

**Prediction before observation.** Before running anything, ask the room what will happen and take
two guesses. Thirty seconds, and it roughly doubles retention — the observation now resolves a
commitment instead of arriving as one more fact.

**Keep your typos.** Recovering from one on camera teaches debugging and pace. Editing it out
teaches that the instructor doesn't make mistakes, which is false and demoralising.

**One idea per screen.** The transparency panel exists for the same reason: don't say "the model
attended to the wrong chunk," point at rank 3 and say "that one."

### 2.7 Demo, lesson, workshop — three formats, three success measures

| | Demo | Lesson | Workshop |
|---|---|---|---|
| **Goal** | A decision | A capability | A working artefact |
| **Length** | 5–10 min | 20–60 min | 2–8 hours |
| **Who talks** | You | You, mostly | Them, mostly |
| **Success measure** | They ask a next-step question | They can explain it to someone else | Their code runs |
| **First thing to cut when short** | The feature tour | The third example | Your own talking |
| **Fatal error** | No refusal beat | No measured fix | Not enough time to fail and recover |

The last row matters most. **A workshop where nobody's code breaks has taught nothing** — debugging
is the skill, and you removed the only chance to practise it. Budget for failure explicitly: if
the exercise takes 20 minutes when it works, schedule 45.

### 2.8 Rehearsal is instrumentation, and your rubric is a judge

Rehearse three times, timed, out loud, alone — the third from memory. This feels ridiculous and
it's the highest-return thirty minutes in Week 1, for a reason you'll recognise from Day 5:
**you cannot measure a beat's duration by reading it silently.** Beat 5 takes 90 seconds and you
budgeted 60; there's no way to discover that except by running it.

Then watch the recording back at 1.0x, all of it, and grade against the lab's seven dimensions.
That rubric is a judge scored by you, so every caveat from Day 5 §2.5 applies — including
self-preference, which is severe when judge and generator are the same person. Two mitigations:
anchor each dimension with a written description of a 3 versus a 5, and count something objective
(filler words per minute) so at least one row can't be argued with.

---

## 3. Worked example — on paper

**Q1.** A 20-minute lesson: 12 min of explanation at ~140 wpm, 8 min of live build at ~100 wpm.
Total word budget? Hook + frame + close consume ~850. At ~400 words per idea-with-example, how
many new ideas fit?

**Q2.** Live build is 8 minutes and typing-while-narrating runs 2–3 lines/min. How many lines?
`rag.py` is 200 — what follows?

**Q3.** Seven demo beats budgeted at 6:00. In rehearsal beat 5 runs 90 s instead of 60. Where do
the 30 seconds come from?

**Q4.** Six queries at 1.9 s mean; cold index ingestion takes 40 s; beat 2 is a 60-second slot.
What happens if you don't pre-warm, and what's the fix?

**Q5.** Cost slide: 200 questions/week at $0.0011 per query; an ops interruption is 20 minutes at
a $72/hour loaded rate. Annual token cost, annual interruption cost, and the honest version.

**Q6.** Scorecard: lookup Recall@5 = 0.93, synthesis 0.41. Blended number at 75/25? At 50/50?
What does that tell you to ask the client?

**Q7.** The client cuts you to 4 minutes. What comes out?

<details>
<summary><b>Answers</b></summary>

**Q1.** (12 × 140) + (8 × 100) = **2,480 words**, call it 2,500. Less 850 of structure = 1,650.
At 400 words per idea: **about four new ideas.** Not nine. With nine you will either speed up or
overrun, and speeding up is what a recording shows most mercilessly.

**Q2.** 8 × 2.5 ≈ **20 lines.** So of `rag.py`'s 200, **pre-stage 180 and type 20** — and choose
those 20 to carry the idea: the assembly function and the verification check, not imports and
dataclasses. "Live build" doesn't mean building the whole thing live. It means the audience
watches the load-bearing part appear.

**Q3.** Not from beat 4 or 5 — those are what differentiate you (§2.3). Fuse beats 2 and 3: open
the transparency panels *while* the first answer streams, instead of running a clean query and
then re-running it with panels open. Saves 30–45 s and improves the demo, because it removes a
repetition the audience was already bored by.

**Q4.** Six queries of dead air total 11.4 s, survivable when spread across six beats. The
40-second cold ingest is not: it eats two-thirds of beat 2 and pushes every later beat past its
slot, so you finish beat 5 as they stand up — and beat 5 is the one that matters. Warm the index
before the call, run a throwaway query, confirm the panels populated, and stream everything so the
wait reads as progress rather than a frozen screen.

**Q5.** 10,400 questions/year. Tokens: 10,400 × $0.0011 = **$11.44/year** — a rounding error, and
say so out loud. It pre-empts the "what does inference cost" question and is more credible than a
padded figure.

Interruptions: ⅓ hour × $72 = $24.00 each × 10,400 = **$249,600/year gross**; at 60% deflection,
**~$150,000**.

The honest version, which you must say: *"That's redeployed time, not cash, unless headcount
changes. What it buys you is the senior ops person who answers these getting those hours back."*
Present $250K unqualified and the first sharp person in the room dismantles it, taking the rest of
your numbers with it.

**Q6.** 75/25 → (0.75 × 0.93) + (0.25 × 0.41) = **0.80**. 50/50 → **0.67**. Thirteen points of
difference, produced entirely by an assumption you made up. **So ask: "pull a hundred real
questions from your ops Slack channel and let's classify them."** That makes your number
defensible *and* converts the client from audience into participant, which is worth more than the
number.

**Q7.** Fuse 2 and 3 as in Q3 (−45 s), cut the numbers beat to one figure (−20 s), tighten the ask
(−15 s). Keep **the problem, the refusal and the limitation** at full length — those three are the
entire differentiation; the rest is what every other vendor already showed them.

</details>

---

## 4. What people get wrong

**"The demo should show everything the system can do."**
A demo makes one argument. Every capability past that argument dilutes it and eats the minutes you
needed for the refusal beat.

**"Never show it failing — they'll lose confidence."**
Inverted. They've seen ten flawless demos and watched three become disappointing pilots. Naming a
limitation before they find it is the strongest credibility move available, and it costs sixty
seconds.

**"Slides first, demo at the end if there's time."**
There is never time, and the demo is the argument. Open with the problem in their language, then
show the thing.

**"I'll get the timing right on the day."**
You will not. Beat 5 takes 90 seconds and you budgeted 60, and the only way to know is to say it
out loud with a timer running.

**"Pasting the code saves time for the important parts."**
It removes the pace, the errors and the pauses where questions land. Type the twenty lines that
carry the idea; pre-stage the other 180.

**"If someone asks a question I can't answer, I've lost the room."**
"I don't know, noting it" is the most trust-building thing an instructor does. What loses a room
is a confident guess that unravels twenty minutes later.

**"Recording is safer than live."**
Safer and inert. Nothing that can't fail is interesting to watch. Go live, with a recorded
fallback in the next tab.

**"Teaching is a soft skill."**
It has an architecture — six parts, each with a function and a measurable failure. You just spent
a week learning to evaluate a RAG system; §2.8 is where you point that discipline at yourself.

---

## 5. The trainer's angle

This section is recursive today, so make it useful: the hard part is teaching *this* material to
a room of engineers who have already decided presentation isn't real work.

**The analogy that lands with that room:** the transparency panel is distributed tracing for a
factual claim. Nobody in an infrastructure org accepts a service that returns an answer with no
trace, no correlation ID and no way to see which backend produced it — and that is exactly what
every chatbot demo is. Framed that way, "show the retrieved chunks and the assembled prompt"
stops being a UI nicety and becomes the standard they already hold their own systems to.

**The demo that makes it click:** run your own demo twice. First without beats 4 and 5 — clean,
fast, everything works. Then with them. Ask which version they'd fund. The room picks the second
out loud, and now the argument is theirs rather than yours.

**The question a sharp student will ask:** *"What do I do if it breaks live, in front of the
client?"* Have this ready, because it's the fear underneath most bad demos:

> Three layers, all built before you present. One: reproduce it three times in a row first — most
> live failures are things you'd already seen once and hoped about. Two: keep a terminal recording
> of the working run in the next tab and cut to it without apologising; "here's a capture from
> this morning" is a complete sentence. Three, and this is the one that matters: **if it breaks in
> a way you understand, debug it on screen.** You spent this week building a diagnostic order —
> refusal, retrieval, assembly, chunking. Walking that ladder live, out loud, in front of a client
> is a *better* demo than the one you planned, because it shows them what they're actually buying.
> Which is not the software. It's you, in the room, when it goes wrong.

---

## 6. Self-check

Cover the answers.

1. Give the debugging order for a wrong RAG answer, cheapest diagnostic first.
2. Name the three audiences in a client demo and the beat that serves each.
3. Which two demo beats are load-bearing, and why does each work?
4. Why does opening with the technology fail?
5. Name the four things that break demos and the mitigation for each.
6. Name the six parts of a lesson, in order.
7. What does the hook do mechanically, and does it need correct answers?
8. What's a frame for, and what's the rule about referencing it?
9. Roughly how many lines of code can you type live in 8 minutes? What follows for `rag.py`?
10. How many new ideas fit in a 20-minute lesson, and where does the constraint come from?
11. What's the fatal error in each of demo, lesson, and workshop?
12. Why is self-grading a recording subject to the same problem as an LLM judge, and what are the
    two mitigations?

<details>
<summary><b>Answers</b></summary>

1. Did it refuse when it should (clause 1)? → paste the correct chunk in (clause 2) → reorder or
   reduce k (clause 3) → do the quotes verify (clause 4)? → then chunking, then embeddings.
2. Ops user → the happy path in their vocabulary. Engineering lead → the transparency panel.
   Budget holder → the numbers.
3. The refusal, because a visible boundary converts "confident text generator" into "system with a
   known limit." And the named limitation, because naming a weakness before they find it makes
   everything else you claim believable.
4. It makes the demo about your project rather than their problem, and the ops people disengage
   before you reach anything they'd care about.
5. Dead air → stream and plan the narration. Cold start → pre-warm and run a throwaway query.
   Non-determinism → temperature 0, fixed k, recorded fallback. Derailing question → answer what
   you know, say what you don't, write it down on screen.
6. Hook, frame, live build, deliberate failure, fix-and-measure, close.
7. It creates an open question so later material lands on a retrieval cue rather than arriving
   cold. It works even when the guesses are wrong — the commitment matters, not its correctness.
8. A filing system: new facts attach to a clause instead of accumulating separately. Reference it
   out loud at least three times or it's just a slide.
9. About 20, at 2–3 lines/minute while narrating. Pre-stage 180 of `rag.py`'s 200 and type only
   the load-bearing part — assembly and verification.
10. About four. 20 minutes ≈ 2,500 spoken words; hook/frame/close take ~850; a properly explained
    idea with an example is ~400.
11. Demo: no refusal beat. Lesson: no measured fix — you asserted the improvement instead of
    showing the number move. Workshop: no time for anyone's code to break and be fixed.
12. Judge and generator are the same person, so self-preference is severe. Mitigate with written
    anchors describing a 3 versus a 5 on each dimension, and at least one objective count (filler
    words per minute) that can't be argued with.

</details>

**Scored below 8?** Re-read §2.3 and §2.5. Today's build is the UI, but today's *deliverable* is
a demo you can perform cold and a lesson someone else could learn from.

---

## 7. Going deeper (optional)

- *Make It Stick: The Science of Successful Learning* — Brown, Roediger & McDaniel (2014). The
  accessible treatment of retrieval practice, spacing and desirable difficulty — the research
  basis for this whole bootcamp, including the warm-up block you keep wanting to skip.
- *The Pretesting Effect: Do Unsuccessful Retrieval Attempts Enhance Learning?* — Richland,
  Kornell & Kao (2009). The evidence for §2.5's hook, and more surprising than the summary.
- **Cognitive Load Theory** — John Sweller, 1988 onward. The worked-example effect is the direct
  justification for §3 of every module in this course.
- *Resonate* — Nancy Duarte (2010). Presentation structure as architecture rather than taste. Skim
  the sparkline analysis; ignore the design chapters.
- *Simple Made Easy* — Rich Hickey (Strange Loop, 2011). Watch once for content, then again with a
  stopwatch, watching him hold a single frame for fifty minutes. The cleanest demonstration of
  §2.5's part 2 available.
- *Inventing on Principle* — Bret Victor (CUSEC, 2012). The reference implementation of "show,
  then explain." Note how long he lets a demo run before saying anything.

---

**Now go to `labs/DAY_06.md`.** The lab is built on §2.3 (the seven beats — you write and rehearse
them), §2.5 (the six-part lesson shape is the required structure for teach-back #6), §2.4 (warm
the index before you record), and §2.8 (the grading rubric you'll apply to your own recording).
