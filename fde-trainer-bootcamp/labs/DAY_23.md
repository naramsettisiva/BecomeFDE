# Day 23 — Deliver It Live: Teaching Under Real Conditions

**Sat Sep 19, 2026** · Week 4 · Maps to: **the trainer role** · Backend: n/a · Est. cost: **$0–1**

> **Before you start — read `learn/DAY_23_LEARN.md` (0:30).**
> Pre-flight, recovering live, the five question types, facilitation. The lab below assumes it and does not re-explain it.


---

## Why today matters

Every recording so far has been forgiving. You could stop, restart, and edit. Live teaching
has none of that: a demo fails at minute 12, someone asks a question you can't answer at
minute 20, and half the room is stuck on an install error while the other half is bored.

Today is a stress test. You deliver the full 60-minute lesson **once, straight through, no
stopping**, then you handle a hostile Q&A, then you run a workshop-facilitation drill.
Whether you ever teach a cohort or not, this is the skill that turns "I know this" into
"people learn this from me" — and it's what makes the difference in client enablement
sessions, conference talks, and internal brown-bags alike.

---

## Objectives

1. Deliver the 60-minute lesson live, unedited, with a real audience if possible.
2. Handle 15 minutes of hard questions, including three you can't answer.
3. Run the workshop-facilitation drill: multiple skill levels, broken environments, time pressure.
4. Produce a self-assessment against a rubric, and a revised lesson plan.

---

## Schedule (5:00)

| Block | Time | What |
|---|---|---|
| 0 | 0:20 | Setup + dry-run the demos |
| 1 | 0:30 | **Learn** — `learn/DAY_23_LEARN.md` |
| 2 | 1:15 | **Live delivery** — 60 min, one take, no stopping |
| 3 | 0:45 | Hostile Q&A drill |
| 4 | 1:00 | Workshop facilitation drill |
| 5 | 0:50 | Review, self-assess, revise |
| 6 | 0:20 | Ship the teaching portfolio |

---

## Block 0 — Setup (0:20)

**Get a real audience if you possibly can.** Two or three people is plenty. A colleague, a
friend in tech, someone from a local meetup, your son if he'll sit still. A real audience
changes your delivery in ways a webcam cannot simulate — you can see when you've lost them.

If you can't: record to camera, but put a printed sheet of six faces at eye level and
address them. It sounds silly. It measurably changes your pacing.

Pre-flight checklist — do this before every session you ever teach:

- [ ] Every demo run once, start to finish, in the exact state you'll present from
- [ ] Terminal font size 18pt+, editor 16pt+. **Check by standing 6 feet back from the screen**
- [ ] Notifications off, calendar closed, Slack quit
- [ ] Fallback outputs saved for every live demo (a pre-generated result you can paste if
      the live run fails — you will need this eventually)
- [ ] Local model warm, API keys valid, index loaded
- [ ] Water within reach
- [ ] Timer visible to you, not to the audience
- [ ] Recording started **before** you begin talking

---

## Block 1 — Learn (0:30)

**Read `learn/DAY_23_LEARN.md` and work its examples before continuing.**
Take the self-check at the end. This is a build day, so the module is short and deliberately practical — read it once, properly, then build.

---

## Block 2 — Live delivery (1:15)

**Deliver the full 60-minute evals lesson. One take. Do not stop. Do not restart.**

Whatever happens, keep going:
- A demo fails → debug it live, out loud, or fall back to the saved output and move on
- You forget a point → skip it; nobody knows what was on your plan
- You go over time → cut the generalise section, never the practice section
- Someone asks something off-topic → "great question, let me take that at the end" and
  actually write it down

That last one matters. Parking a question and then genuinely returning to it is one of the
strongest trust signals an instructor gives.

Extra 15 minutes in the block is buffer. Use it for setup overrun, not for a second take.

---

## Block 3 — Hostile Q&A drill (0:45)

Get an LLM (or a friend who enjoys this) to play a difficult audience. Prompt it:

> You are attending a technical session on LLM evaluation. Ask hard questions, one at a
> time. Mix: (a) genuinely difficult technical questions, (b) sceptical challenges to the
> premise, (c) questions about things not covered, (d) questions with false premises, (e)
> one question that's really a disguised sales objection. Be polite but persistent.
> Follow up when the answer is vague. Do not be satisfied with hand-waving.

Answer **out loud**, recorded, in real time. 15 questions minimum.

Questions you should expect and should have answers to:

- "Isn't this just what RAGAS does? Why build it?"
- "We have 200,000 documents. Does any of this hold at that scale?"
- "How many eval cases is enough? Give me a number."
- "Our lawyers won't let us send data to OpenAI. Does this all still work?"
- "We tried RAG last year and it didn't work. Why is this different?"
- "What's the ROI? My CFO will ask."
- "Doesn't the model just get better every six months and make this obsolete?"
- "Who at your last company actually used this?"

**The three you can't answer are the point of the drill.** For each, practise the correct
response, which has three parts and takes ten seconds:

> "I don't know. Here's how I'd find out: [specific method]. I'll follow up by [when]."

Then actually go find out — that's your 20 minutes after the drill. Add all of it to
`teaching/lesson_evals/FAQ.md`.

Grade yourself on:
- [ ] Did you say "I don't know" when you didn't know, without padding?
- [ ] Did you answer the question asked, or the one you wanted?
- [ ] Did you get defensive on the sceptical ones? (Watch the recording. You'll see it.)
- [ ] Did you use a concrete number or example in at least half your answers?
- [ ] Did you ever bluff? Be honest. If yes, that's the habit to kill.

---

## Block 4 — Workshop facilitation drill (1:00)

Teaching a lesson is one skill. Running a hands-on workshop where 20 people are typing is
a different one, and it's the format most client-enablement sessions actually take.

Simulate the four situations. For each, write your response in
`teaching/FACILITATION_PLAYBOOK.md` and then practise it out loud:

**1. The install disaster (0:00–0:10).** A third of the room can't get the environment
running. Your options: (a) fix them one by one — you lose the session; (b) push everyone to
a pre-built Codespace/Colab — you lose local realism; (c) pair the broken with the working
— you halve the problem and build the room. Decide your default now, and **have the
fallback environment built and tested before the session**, not during it.

**2. The spread.** Two people finish the core exercise in 6 minutes; four are still on step
one at 15. Fix: tiered exercises (you have these), and recruit the fast finishers as
floaters. This is not a coping mechanism — being asked to help is the most engaging thing
that can happen to an advanced student.

**3. The derailer.** Someone asks increasingly tangential questions and the room is
drifting. Script it, kindly and firmly:
> "That's a real question and it's outside what we can do justice to today — let me grab
> it for the end and make sure I get you a proper answer. Right now I want to make sure
> everyone's got output from step two. Who's got a number?"

Redirect + commitment + a concrete check that re-engages the room.

**4. The silent room.** No questions, no chat, nothing. Never ask "any questions?" Instead:
- "Paste your recall@5 in the chat. I'll wait." (Concrete artifact, low social cost)
- "Turn to the person next to you and compare your numbers. Two minutes." (Peer first)
- "Show of hands: who got something above 0.7? Below?" (Binary, anonymous-ish)

Then run a **20-minute mini-workshop** with your real audience if you have one: give them
the core exercise from your lesson, float, and practise the checkpoints. Watch how long
things actually take versus your plan. Update your personal multiplier.

---

## Block 5 — Review and revise (0:50)

Watch your 60-minute delivery back **in full**. No skipping. Score it:

| Dimension | 1–5 | Evidence (timestamp) |
|---|---|---|
| Opened with a real failure that created a question | | |
| Frame stated and referenced 3+ times | | |
| Live typing at a followable pace | | |
| Predictive question used before at least one demo | | |
| Deliberate error included and debugged live | | |
| A number visibly moved | | |
| Checkpoint every ~10 min | | |
| Recovered from at least one unplanned problem | | |
| Filler words per minute (count a 5-min sample and extrapolate) | | |
| Closed with a repeatable sentence | | |
| Finished within ±5 min of plan | | |

Then revise `teaching/lesson_evals/LESSON_PLAN.md` with what you learned:
- Which section ran long? Cut it or plan for it.
- Which demo is fragile? Add a fallback or replace it.
- Which explanation didn't land? Rewrite it, and note the version that failed — that's
  data, and you'll be tempted to try it again in six months.

Compare against your **Day 6** recording. Watch three minutes of each back to back. Write
down, specifically, what changed. Eighteen sessions of deliberate practice produce a visible
difference and you should see it — that's the evidence you're a trainer now, not the
certificate.

---

## Block 6 — Ship the teaching portfolio (0:20)

`teaching/README.md` — the page you send when you ask to teach anything:

```markdown
# Technical Training — AI Engineering & Forward Deployment

I teach production AI engineering the way it's actually encountered: organised
around the failures practitioners hit, not the topics vendors sell.

## Sample session (full recording)
**"Evals: why your AI system's score is lying to you"** — 60 min
[video] · [lesson plan] · [starter repo] · [solution] · [exercises]

## Curriculum
Ten failure-organised modules, from "it gave a confident wrong answer" through
"they can't run it without me." [full outline]

## Formats
- 60-90 min single session (conference, meetup, internal brown-bag)
- Half-day hands-on workshop
- 10-session programme
- Client enablement — teaching a team to own a system after handover

## Background
23 years in distributed systems and supply-chain platforms. Built and deployed
[Carrier Performance Copilot] — production agentic system with evals, tracing,
guardrails, and a red-team report.
```

Pick three recordings that show range — a tutorial (Day 6), an architecture review
(Day 12), and the full lesson (today) — and link them.

```bash
git add -A && git commit -m "Day 23: live lesson delivery, Q&A drill, facilitation playbook, teaching portfolio" && git push
```

---

## Done when

- [ ] 60-minute lesson delivered live, one take, unedited, recorded
- [ ] 15+ hostile questions answered live; three "I don't know"s researched and added to the FAQ
- [ ] Facilitation playbook with scripted responses to all four situations
- [ ] Full self-assessment against the 11-point rubric with timestamps
- [ ] Lesson plan revised based on what actually happened
- [ ] Day 6 vs. Day 23 comparison written
- [ ] Teaching portfolio page published

---

## Trap list

- Stopping and restarting. The whole point is not stopping.
- No fallback outputs for live demos.
- Small fonts. Stand back and check.
- Bluffing an answer. It is always visible and it costs more than the ignorance would have.
- "Any questions?" Ask for an artifact.
- Watching the recording on 2× and calling it review.
- Fixing environments one by one while 15 people wait.

---

## Note on the audience

If you couldn't get one today, get one within two weeks. Post the lesson to a local meetup,
offer it as a lunch-and-learn at work, run it for three people on a video call. Teaching to
a camera plateaus; teaching to people who can be confused at you does not. Tomorrow's
90-day plan makes this concrete.
