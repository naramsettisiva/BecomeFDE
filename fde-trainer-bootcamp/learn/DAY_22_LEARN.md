# Day 22 · Learn — Instructional design: building a lesson that survives contact with a room

**Read before `labs/DAY_22.md`. Budget 1:15.**

---

## 1. Where this sits

For twenty-one days you have been teaching — a recorded teach-back every afternoon against a
mechanism question you couldn't dodge. That was practice without theory. It made you fluent; it did
not make you a designer. Fluency lets you explain something you understand. Design decides *what to
put in front of someone, in what order, so that a person who does not yet understand it can do
something new by the end of the hour.*

You have most of the delivery half already: twenty-three years of steering committees and escalation
bridges means you can hold a room, read it, cut a tangent, and land a recommendation with a VP who
has six minutes. Most engineers who want to teach never get that. But name the gap precisely,
because the gap is today's work:

**Executive communication and teaching optimise for opposite things.** A QBR minimises the number of
open questions in the room at the end — front-load the conclusion, pre-wire objections, make the
audience's cognitive work as small as possible. A lesson *creates* an open question and lets the
audience close it. The cognitive work is not overhead; it is the product. Front-loading the
conclusion is the most common way an expert wastes an hour.

So the moves transfer unevenly. Reading a room, cutting scope under pressure, and speaking to the
confused person rather than the nodding one transfer whole. **Predictive questioning and deliberate
error do not transfer at all** — being wrong on purpose in front of a stakeholder costs you
credibility; in front of a learner it buys three things at once. Today is mostly about the moves
that don't transfer.

You also have an asset almost no curriculum designer has: `LEARNING_LOG.md`, twenty-one days of your
own confusions recorded *before you knew the answer*. Expertise erases the memory of not knowing.
You wrote it down while it was still true.

---

## 2. The mechanism

### 2.1 Topic organisation is the wrong index

Every AI syllabus reads: *Week 1 embeddings. Week 2 RAG. Week 3 agents. Week 4 evaluation.* That is a
table of contents, and it is the right structure **for retrieval** — if you already know the field and
want the section on reranking, topics are perfect.

It is the wrong structure for learning, mechanically. Material is retrieved by whatever it was
encoded alongside, so material filed under "Week 2: RAG" is reachable from the word *RAG*. But nobody
at work meets a topic — they meet a **symptom**: a confident wrong answer, a score that rose while
quality fell, an agent that burned $40 on one request. Nothing in the symptom names the topic.

> **Topic-organised training produces students who can recite and cannot debug. Failure-organised
> training produces students who recognise a problem when they meet it.**

They learned the material and filed it under the wrong key. A module named *"It gave a confident wrong
answer"* holds identical content — the RAG contract, chunk boundaries, citation verification — indexed
by the cue that will actually fire.

The second effect matters commercially: **failure organisation forces you to have an opinion about
what actually goes wrong**, and it cannot be faked by someone who has never deployed anything. When
you send an outline to a training organisation, the *module names* are the credential. Anyone writes
"Module 3: Retrieval." Only someone who has been on the wrong end of it writes "Module 3: It found the
document, not the answer."

You know this shape: runbooks organised by subsystem are unusable at 3am, runbooks organised by alert
are usable. You have spent twenty-three years writing failure-organised documentation and calling it
operations.

**Where topics still win** — say it before a sharp student does. Reference material should be
topic-organised, and a real prerequisite chain sometimes forces topical order. The resolution:
**failures set the module boundaries and the sequence; topics fill the module**, with prerequisites
satisfied inside a module rather than as a standalone week.

### 2.2 Adults learn when they have an open loop

The mechanism under failure-first is not that failures are interesting. It is that information
arriving with no question attached has nowhere to attach.

> **Topic-first.** "Today we'll cover retrieval-augmented generation. RAG has three components: an
> indexer, a retriever, and a generator. The indexer chunks your documents and embeds each chunk. The
> retriever embeds the query and returns the top-k nearest chunks. Let's take each in turn."

> **Failure-first.** "Here's a RAG system answering a question about detention. A customer waited five
> hours at the dock and wants to know what they owe. [runs it] It says $325. The correct answer is
> $195. Retrieval worked — the right document came back. Nothing is hallucinated; every number on
> screen is in the corpus. And the answer is wrong. In the next hour you'll learn the four places this
> breaks and how to tell, in ninety seconds, which one you're in."

Everything true in the first is true in the second. The difference is at second thirty.

After the topic opening the audience is in **reception mode**: recording, with no question they are
trying to answer, so facts arrive isolated and isolated facts decay. Worse, it feels excellent from
the front — the material flows, nobody interrupts, silence reads as comprehension. The most
comfortable failure mode in teaching.

After the failure opening they are in **resolution mode**. A sharp discrepancy is open — *retrieval
worked and the answer is wrong; both cannot be true* — and every later fact is evaluated against it.
Facts arriving as candidate answers to a live question get encoded with the question attached, which
is the same as being encoded with a cue that fires later.

Three side effects: **stakes without a stakes slide** ($325 versus $195 on a real invoice); **honest
difficulty**, teaching them in minute one that this is about a system that *looks* right; and a **free
ending** — at minute 58 you re-run the same demo, correctly, and the loop closes. **The caution the
naive version omits: the failure must be real and reproducible.** An engineering audience detects a
strawman in four seconds and then spends the hour attacking your setup.

### 2.3 The eight beats

| # | Beat | Time | What it is *for* |
|---|---|---|---|
| 1 | **FAILURE** | 2–3 min | Open the loop. Stakes and difficulty, no slide required. |
| 2 | **QUESTION** | 1 min | Name the discrepancy so the room holds *one* open loop, not eight private ones. |
| 3 | **FRAME** | 5 min | 3–5 named elements, on screen. The coat-rack every later fact hangs on. |
| 4 | **BUILD** | 20–25 min | Live, typed, incremental. Contains one deliberate error. |
| 5 | **MEASURE** | 5 min | A number moves. Converts "I followed that" into "that worked." |
| 6 | **GENERALISE** | 5 min | Transfer — where else this shape appears, so it isn't welded to your example. |
| 7 | **PRACTICE** | 15 min | They do it. Nothing before this has touched the student's hands. |
| 8 | **CLOSE** | 2 min | One repeatable sentence, one thing to try. |

Beat 2 **synchronises**: after the failure everyone holds *a* question — the embedding model, the chunk
size, whether you rigged it — and stating it aloud collapses the spread. Sixty seconds, and the
most-skipped beat. Beat 5 is under-valued by engineers and remembered by audiences: κ moving from 0.41
to 0.68 on screen is the difference between a demonstration and an argument.

Beat 6 is **what you cut when you run over — never beat 7.** Counter-intuitive under pressure, because
generalise is cheap (talking) and practice is expensive (fifteen minutes of nothing visibly
happening). Cut the cheap one: practice minus the generalisation leaves a skill; the generalisation
minus practice leaves a memory of an interesting hour.

Beat 8's sentence is an artifact, not a summary — short enough to repeat verbatim, specific enough to
be falsifiable. *"A gate tighter than your noise floor gets disabled in two weeks, and then you have
nothing"* qualifies; *"evaluation is important"* does not. It is what they say to a colleague on
Tuesday, and that is your whole distribution mechanism.

### 2.4 The four techniques

Teach the mechanism, not the trick — a technique applied without its mechanism gets applied in the
wrong place.

**(a) Predictive questioning.** Before you run anything: *"I'm raising k from 5 to 12. What happens to
answer quality?"* Take two answers, not zero and not eight. Then run it.

*Mechanism:* committing to a prediction forces the student to use their current model — most don't
know what they believe until asked — and creates a specific expectation the observation confirms or
violates. The violation is the encoding event, which is why a **wrong** guess beats no guess. The
evidence base is real (testing effects, Roediger & Karpicke 2006; Bjork's desirable difficulties);
"roughly doubles retention" is directional, not a measured constant. The cost is **thirty seconds** —
the best retention-per-second you have. *Failure mode:* telegraphing the answer. If a competent
practitioner wouldn't plausibly guess wrong, it teaches nothing.

**(b) Deliberate error.** Apply MRR to a multi-hop case mid-build. It returns 1.0; the system found
one of two required documents. Let the room sit with a perfect score on a half-right answer for
fifteen seconds before anyone speaks.

*Mechanism:* three things in one pass. **The concept**, learned from the case where it misleads — the
case that sticks. **The error surface**: the traceback, the silent wrong value, the suspiciously round
score. Recognising failure shapes is most of debugging speed and cannot be taught by description.
**The debugging process** — what you check first, what you print, what hypothesis you form and how you
falsify it, normally invisible because it happens in private. Plus a fourth that matters most for the
room's psychology: **it models being wrong gracefully.** Most students believe competent people don't
get errors, and that belief is why they hide when stuck.

*Rules:* pick a **common** error. Announce nothing. Don't rescue it early — the silence while they work
out that 1.0 is wrong *is* the teaching, and your reflex will be to fill it. One per session.

**(c) The persistent named frame.** 3–5 elements on screen, named — *the evaluation ladder*, *the RAG
contract* — and referred to by name throughout: *"we're still in clause two, retrieval; nothing we've
done touches generation."*

*Mechanism, memory:* cognitive load theory (Sweller, 1988 onward). Working memory holds very few
items; a named four-element frame turns forty facts into four buckets with contents. Mayer's
multimedia work adds that it must be **visible and stable** — a slide shown once at minute five costs
back the working memory you were saving, every time they re-derive it. *Mechanism, experience:* a
named frame is what makes an hour **feel like a thing rather than a list.** Ask someone leaving a
frameless session what it was about and you get "evals, and some stuff about judges." *Rules:* three
to five, numbered so you can say "slot 3", persistently visible, and **say the name at least three
times.** Everyone under-does this, which is why counting your uses is on tomorrow's rubric.

**(d) Pre-naming the confusion.** *"This next bit confused me for two hours. The thing that will trip
you is that the embedding of a question doesn't look like the embedding of its answer — topically
related, not propositionally. Watch what that does to top-1."*

*Mechanism:* an unannounced confusion triggers an expensive private process — *am I the only one? did
I miss something? is it rude to ask?* — which consumes exactly the working memory the concept needs
and outputs silence, so they don't learn it and you don't learn they're stuck. Pre-naming converts
private frustration into shared expectation: the confusion, on arrival, is evidence they're on track.
That it took *you* two hours is what makes it credible — "some people find this tricky" excludes you
and is worth nothing. **Your learning log is a list of these, in your future students' words.**

### 2.5 Pacing, and its two failure modes

**Too fast — the expert's default.** Symptoms, in order of reliability: typing sounds stop, chat goes
quiet, nobody asks anything, and the questions you do get are about something ten minutes ago. Every
one is easy to read as things going well — the silence of a lost room and a satisfied room are
acoustically identical. The cause is the curse of knowledge and it is **not fixable by intention**:
when you type `chunks = [c for c in split(doc, 500, overlap=50)]` you experience one action, and a
student experiences a comprehension, two parameters with guessed units, and a variable that matters
later. Instrument it rather than resolving to do better.

**Fix: a concrete-artifact checkpoint every ten minutes.** Not "any questions?", which returns silence
for structural reasons — answering it requires publicly self-identifying as behind, formulating a
coherent question about material you don't understand, and interrupting. Three costs, no benefit. Ask
for an artifact: *"Paste your top-1 score in chat, I'll wait." / "Hands — who has a number on screen?
Who has a traceback?"* Each is answerable by someone confused, costs nothing socially, and returns a
**distribution** rather than a null. Six pastes out of twenty is a fourteen-person problem you know
about at minute ten instead of minute fifty. You already do this — you don't ask a program team "any
risks?", you ask for the status of a named deliverable.

**Too slow — the nervous teacher's default.** Symptoms: the advanced half goes quiet differently —
side conversations, laptops turning to other work, people finishing your sentences. Cause is pacing to
the slowest person, and the arithmetic is bad: it loses the top 40%, who are the ones who invite you
back. **Fix: a parked stretch task**, written in advance, available from minute one — *"Done with
recall@5? Implement nDCG and compare rankings."* This is the expertise reversal effect (Kalyuga and
colleagues, early 2000s): scaffolding that helps novices actively harms experts, because processing it
costs more than the content. One pace cannot serve a spread.

**The 2.5× rule.** Live typing takes about 2.5× your estimate, because you estimate from doing it
alone, at speed, with no narration, no typos, no questions, and no waiting on a model call whose
output you have already seen. The multiplier is personal: **get yours from recordings you already
have** — planned versus actual per section on Days 6 and 12 — and plan with your number, not mine.
Then apply it where it hurts: **a 60-minute plan with 40 minutes of live typing is a 100-minute
session.** The fix is not typing faster; it is pre-writing imports, config and boilerplate and
live-typing only the eight lines carrying the idea.

### 2.6 Assessment: four levels, and why diagnosis is the real one

Bloom's taxonomy (1956; revised by Anderson & Krathwohl, 2001) decomposes "did they learn it?" Its
practical four-level form:

| Level | Measures | Instrument | Failure mode |
|---|---|---|---|
| **Recall** | They remember the frame | Name the four rungs | Passes without understanding |
| **Application** | They can do it on new material | Build an eval for an unseen corpus | Passes by pattern-matching your example |
| **Diagnosis** | They can debug it | Given a broken artifact, find the defect | **Very hard to fake** |
| **Transfer** | They apply it unprompted | Their own project's eval, two weeks later | Confounded by whether they had a project |

**Diagnosis is the real test**, because its task shape matches the job: nobody at work is handed a
blank file, they are handed a system someone else built that is producing a number nobody trusts. It
is also where recitation stops rescuing you — a student who memorised "use a judge from a different
model family" answers the recall question and still misses it in a config where the judge is named on
line 6 and the generator on line 40.

**Building one:** break your working artifact *n* ways, one defect per copy, each from a different
class. For evals: (1) judge same model family as generator; (2) CI threshold inside the noise floor;
(3) golden set with no unanswerable questions; (4) absolute 1–5 scoring confounded by verbosity;
(5) `except: return True`, so the gate silently passes on API error. Ask for defect, confirmation
method, and fix, and **weight confirmation most heavily** — identification can be pattern-matched,
confirmation cannot. The defects come from your trap lists; ~120 across 21 labs is an assessment bank
most training organisations lack.

**And the one to stop using: enjoyment.** Kirkpatrick's Level 1 (reaction) correlates weakly with
Level 2 (learning), sometimes inversely — the sessions that feel best are the smooth ones where nobody
struggled, and struggle is where learning happens. Collect it if the client needs it; never use it to
decide what to change.

### 2.7 Mining the learning log

| Extract | Becomes | Why |
|---|---|---|
| **Confusions**, verbatim | **Module boundaries** | A recorded confusion marks where the material genuinely bends. Expect 6–10 clusters; that's your spine. |
| **Trap-list items** (~120) | **Common-errors sections**, exam items | Already written as symptom + cause — the shape of a diagnosis item. |
| **Click-moments** | **Lesson hooks** | The specific demo that landed. Validated on a sample of one, which is one more than most curricula. |
| **Unanswered questions** | **The FAQ** | What students will ask live. Answer them in writing now and you are never caught flat. |

Two disciplines. **Keep the phrasing verbatim** — "I thought embeddings understood meaning, not topic"
beats "students may conflate semantic and topical similarity," because the raw sentence is in the
student's register and you can say it out loud. And **order modules by the sequence you actually hit
the failures** — the order a practitioner meets problems beats the order a textbook derives concepts.

---

## 3. Worked example — on paper

Judgement, not arithmetic. Here is a session outline of the kind submitted to meetups every week. It
is not incompetent: the content is correct and the author knows the material.

```
TOOL-USING AGENTS — A 60-MINUTE INTRODUCTION

00:00  Welcome, about me, agenda                                    5 min
00:05  What is an agent? Agent vs. workflow vs. chain               8 min
00:13  The tool-calling API: schemas, request/response shape       10 min
00:23  Frameworks landscape: LangChain, LangGraph, CrewAI, ADK      7 min
00:30  Demo: build a 3-tool agent, working, end to end             12 min
00:42  Memory and state in agents                                   6 min
00:48  Multi-agent patterns: supervisor, swarm, handoff             7 min
00:55  Best practices and pitfalls (bulleted list)                  4 min
00:59  Q&A                                                          1 min
```

**Q1.** At minute 20, what open loop is the audience holding?

**Q2.** Rewrite 00:00–00:03 as a failure-first opening. Name the failure and say why that one.

**Q3.** Apply the 2.5× rule. What actually happens, and at what timestamp does it go wrong?

**Q4.** Where does the deliberate error go, and what exactly is it?

**Q5.** Name the persistent frame — 3–5 numbered elements — and the three moments you'd say its name.

**Q6.** Two of the nine items should be cut outright. Which, and what rule do they violate?

**Q7.** The implicit assessment is Q&A at 00:59. What level is that, and what replaces it?

<details>
<summary><b>Answers — write yours first; the lab is built on this exercise</b></summary>

**Q1.** **None.** That is the whole diagnosis. Twenty minutes in, the audience has received three
correct blocks of information and not one question it wants answered — and the outline cannot be
fixed by improving those blocks, because a better definition of "agent" creates no open loop. The
defect is structural.

**Q2.**

> "This agent has three tools: look up a shipment, check a carrier scorecard, file a detention claim.
> One question — *'Ridgeline had a truck sitting at Joliet for five hours on the 14th, sort it
> out.'* [runs it] It filed a claim for $325. The correct figure is $195, and it filed against the
> wrong shipment. Every tool call succeeded. The model wasn't confused about the tools. Watch the
> trace — the failure is somewhere the framework docs don't mention. In the next hour you'll learn
> the four points in an agent loop where this happens and how to tell which one you're in."

Three criteria. (a) **Every call succeeded**, so the discrepancy is sharp and the lazy explanations —
bad model, bad prompt — are foreclosed. (b) It is **consequential**: the agent took an action against
a third party, which is what makes agents different from chat. (c) It is **real** and reproducible in
front of a sceptic. Weaker: an agent looping forever teaches only rate limiting; a hallucinated tool
name dates badly.

**Q3.** Twelve minutes of live build across three tools is realistically 25–30, so it breaks at
**00:30** and the damage lands at the end: memory, multi-agent, pitfalls and Q&A get compressed into
eleven minutes and the second half is read at speed. The deeper problem is that this outline has **no
practice beat at all**, so the overrun has nothing safe to eat and content gets cut. In an eight-beat
plan the overrun eats GENERALISE and the session survives.

**Q4.** In the build: **write the tool schema with the detention parameters as free-form strings with
no units** — `dwell_time: str`. It runs. The model passes `"5 hours"` sometimes and `"300"` sometimes,
so the claim amount is wrong *intermittently*. Let it fail, read the trace live, find the two argument
shapes, fix by typing the parameter and putting the unit in the description. Good on all counts:
extremely common; intermittent, which teaches the far more valuable lesson that a tool bug can pass
your first test; and the debugging path — go to the trace, read the actual arguments — is exactly what
you want internalised. A typo'd tool name fails loudly and teaches only "read the error".

**Q5.** *The four failure points in the agent loop:*

```
1. SELECTION       — did it choose the right tool?
2. ARGUMENTS       — did it pass the right values?
3. INTERPRETATION  — did it read the result correctly?
4. TERMINATION     — did it stop at the right time?
```

Name it at (i) minute 5, tying the opening failure to slot 2; (ii) mid-build at the deliberate error
— *"slot 2 again, arriving differently"*; (iii) at GENERALISE, walking all four slots with a
production example each, so they leave with four buckets rather than an anecdote. Test of a good
frame: they can reproduce it on a whiteboard tomorrow.

**Q6.** **00:00 "Welcome, about me, agenda"** and **00:23 "Frameworks landscape."** The rule: *nothing
occupies session time unless it closes the open loop or is required to close it.* The agenda
pre-empts the loop by announcing what they will learn. "About me" is credibility theatre — your
credibility is established by minute three of a demo reproducing a real failure, and if it isn't, a
slide won't save it. The frameworks landscape is reference material: correct, useful,
topic-organised, and it belongs in a linked doc. Recovered: 12 minutes, roughly the demo overrun —
not a coincidence, that is where the time in most technical talks goes.

Softer call: memory and multi-agent are each a *second* failure dressed as a topic. Either could stay
if reframed and given a build. Not both.

**Q7.** Q&A measures who is confident enough to speak. Replace it with a **diagnosis instrument**:
four agent traces of 20–40 steps, one defect each, one per slot.

| Trace | Defect | A good answer |
|---|---|---|
| A | Called `get_scorecard` when the question needed `get_detention_events` — **selection** | Names the correct tool and the description overlap that caused it |
| B | Passed dwell as `"5"` where the tool expects minutes — **arguments**, silently wrong | Spots that the output is wrong by 12×, not absent; checks argument units in the trace |
| C | Tool returned `{"events": []}` for an out-of-range date; agent said "no detention" — **interpretation** | Distinguishes "no data" from "no charge"; asserts on the query window |
| D | Ran 14 steps re-checking the same shipment — **termination** | Missing stop condition; step budget as the fix |

Weight **confirmation method** most heavily. The instrument is frame-shaped — every defect is one
numbered slot — so the assessment doubles as the final rehearsal of the frame.

</details>

---

## 4. What people get wrong

**"A good syllabus covers the material."**
Coverage is a property of a reference document. A lesson's job is to change what a student can do,
and you can cover everything and change nothing. With a 2.5× multiplier you always have to choose:
cut coverage, keep practice.

**"Failure-first means opening with a war story."**
A war story is a narrative you deliver; a failure-first opening is a reproducible artifact failing on
screen. The first buys admiration for you, the second creates a discrepancy the audience owns. And
don't simplify the failure for clarity — simplified, it becomes a strawman and the room spends the
hour attacking your setup.

**"Deliberate error will make me look incompetent."**
Reliably the opposite — recovering visibly demonstrates a process rather than a result. What damages
you is a *concealed* error; the room can always tell when you are quietly editing around something.

**"'Any questions?' is a comprehension check."**
It is a check on social confidence. Ask for an artifact, which the people you need to hear from can
actually produce.

**"I'll pace to the room on the day."**
You will pace to your own fluency, because the curse of knowledge doesn't respond to intention.
Instrument it: a checkpoint every ten minutes, and a multiplier you measured rather than felt.

**"Students who enjoyed it learned more."**
Weakly related, sometimes inverted. Assess diagnosis, not satisfaction.

**"Assessment is what you do at the end."**
Assessment is what you design *first*. Write the diagnosis instrument before the lesson plan and the
plan writes itself: everything that doesn't help a student pass it is coverage.

**"My learning log is a diary."**
It is your unfair advantage and it decays. The value is phrasing recorded before you knew the answer,
and every week makes your memory of not-knowing worse.

---

## 5. The trainer's angle

**Note for Days 22–24: this section is meta.** On other days it covered how you would teach that
day's topic. Today the topic *is* teaching, so this is about **teaching someone else to teach** —
the role you're in the first time a client asks you to enable their team to run enablement, or the
first time you have a TA.

**The analogy that lands:** runbooks. Everyone has used one organised by subsystem at 3am and hated
it, and one organised by alert and been grateful. Ask which they'd rather have — then point out
they've just chosen failure-organisation for themselves, and ask why their last training deck went
the other way. It uses their own preference against their own habit, which is more durable than an
argument you make.

**The demo that makes it click** — and the only honest way to teach failure-first: deliver the
topic-first opening from §2.2 *straight*, four full minutes, no signalling. Let the room go politely
blank. Stop and ask: "what question are you currently trying to answer?" Nobody has one. Then run the
failure-first version and ask again. They feel it in their own heads, which no explanation of open
loops achieves. Teaching failure-first topic-first is self-refuting, and trainees notice.

**The predictive question before that demo:** *"Same content, two ways. Which will you remember more
of tomorrow — and by how much?"* Most predict a small difference. The gap is large, and the violated
prediction is the lesson.

**The drill that builds skill fastest:** one beat, five minutes, in rotation. Everyone prepares *only*
the FAILURE beat for a topic they know, delivers it, and gets one question: "what open loop did that
create?" A vague answer means the beat failed, however well it was delivered. Beat-level rehearsal
beats full-session rehearsal early — a whole session has too many variables to attribute to.

**The scoring habit to install:** make them count, on their own recording — times the frame was named,
predictive questions asked, minutes between checkpoints, personal typing multiplier. Trainers improve
against numbers and plateau against impressions, for the same reason your evals do.

**The question a sharp trainee will ask:** *"Doesn't failure-first scare beginners off?"*

> The audience isn't deciding whether to adopt — they already have, which is why they're in the room
> — so an honest failure is useful rather than discouraging. Opening with a failure you then fix in
> front of them is a *stronger* adoption argument than hiding it, because they'll hit it in week two
> either way; the only question is whether they hit it with your diagnosis or without it. Where the
> objection has real force is sales: a pre-purchase demo is not a lesson and shouldn't be designed
> like one. Know which room you're in.

**The failure mode to warn new trainers about:** over-indexing on technique — staged errors
everywhere, telegraphed predictions, a nine-element "frame" — producing a session that is all
instrumentation and no content. The techniques are seasoning.

---

## 6. Self-check

1. Why does topic-organised training produce students who cannot debug?
2. Where does topic organisation legitimately win, and how do you reconcile it with failure organisation?
3. What is an audience in "reception mode" doing, and why does it feel like success from the front?
4. Name the eight beats in order.
5. Which beat do you cut when you run over, which do you never cut, and why that way round?
6. What is the mechanism behind predictive questioning, and why does a *wrong* prediction still help?
7. Name the four things a deliberate error teaches at once.
8. Why must the frame be visible rather than remembered?
9. Why does "any questions?" reliably return silence, and what replaces it?
10. What is the 2.5× rule, how do you get *your* number, and what do you do with it besides lengthening the plan?
11. Name the four assessment levels. Why is diagnosis the real test?
12. Four kinds of learning-log entry — what does each become?

<details>
<summary><b>Answers</b></summary>

1. Material is retrieved by whatever it was encoded alongside. Filed under a topic name, it is
   reachable from the topic and not from the symptom the student actually meets.
2. Reference material and genuine prerequisite chains. Reconciliation: failures set module boundaries
   and sequence, topics fill the module, prerequisites are satisfied inside a module in service of
   its failure.
3. Recording information with no question attached, so facts arrive isolated and decay. It feels like
   success because nothing interrupts — the silence of a lost room and a satisfied room are identical.
4. Failure → question → frame → build → measure → generalise → practice → close.
5. Cut GENERALISE, never PRACTICE. Practice is the only beat where the skill touches the student's
   hands; the generalisation alone leaves a memory of an interesting hour.
6. It forces the student to use and surface their current model, and creates a specific expectation
   the observation confirms or violates. A wrong prediction helps *more* — the surprise is the
   encoding event.
7. The concept (from the case where it misleads), what the failure looks like, the debugging process,
   and how to be wrong gracefully.
8. Cognitive load: re-deriving it from memory consumes the working memory the frame was meant to
   free. Persistently on screen, not a slide shown once.
9. It requires publicly self-identifying as behind, formulating a coherent question about material
   you don't understand, and interrupting — three costs, no benefit. Replace with a concrete artifact
   request, which returns a distribution rather than a null.
10. Live typing takes ~2.5× your estimate; measure yours by comparing planned to actual per section
    on your own recordings. Besides lengthening the plan: **type less** — pre-write imports, config
    and boilerplate, live-type only the lines carrying the idea.
11. Recall, application, diagnosis, transfer. Diagnosis matches the shape of the job — you are handed
    someone else's broken system — and it is where memorisation stops rescuing you.
12. Confusions → module boundaries; trap-list items → common-errors sections and exam items;
    click-moments → lesson hooks; unanswered questions → the FAQ.

</details>

**Scored below 9?** Re-read §2.3 and §2.4. Block 2 asks for a complete 60-minute lesson beat by beat,
and it takes twice as long if you are looking up the structure while writing it.

---

## 7. Going deeper (optional)

- Rosenshine, *Principles of Instruction* (2012) — ten pages, free, empirical, and the most practical
  item here. Written for schools; the mechanisms are identical.
- Ambrose et al., *How Learning Works* (2010) — the chapter on prior knowledge is the best
  explanation of why audiences mis-generalise from what they already know.
- Merrill, *First Principles of Instruction* (2002) — the academic form of problem-centred beats
  topic-centred, useful when a client L&D function insists on a topic outline.
- Sweller on cognitive load (1988 onward) and Mayer's multimedia principles — enough to justify the
  persistent frame and "no slides during live coding" to someone who wants a 60-slide deck.
- Roediger & Karpicke (2006) on test-enhanced learning, and Bjork on desirable difficulties.
- Your own `LEARNING_LOG.md`, all 21 entries in one sitting, **before** the lab rather than during it.
  More valuable than everything above and the only source nobody else has.

---

**Now go to `labs/DAY_22.md`.** Block 0 executes §2.7, Block 1 is §2.1–2.5 applied to your own
material, Block 2 builds the eight beats of §2.3 with the four techniques of §2.4 placed
deliberately, and Block 3 is §2.6 — build the diagnosis instrument first and let the curriculum
outline follow from it.
