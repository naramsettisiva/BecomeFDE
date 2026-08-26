# Day 19 — The FDE Craft: Discovery, Scoping, and the First Two Weeks

**Tue Sep 15, 2026** · Week 4 · Maps to: **the role itself** · Backend: n/a · Est. cost: **$0–1**

> **Before you start — read `learn/DAY_19_LEARN.md` (1:15).**
> The FDE operating model, discovery, eval-first scoping. The lab below assumes it and does not re-explain it.


---

## Why today matters

You have spent 18 days becoming technically capable. Today is about the part of the job
that is not code, and it is the part that determines whether you're a contractor who
builds what he's told or a Forward Deployed Engineer who reshapes what gets built.

The distinguishing skill of an FDE is **converting a vague business complaint into a
scoped, evaluable, shippable system — fast, in the room, with the client**. Nobody teaches
this. Most people learn it by failing on two engagements. You have 23 years of program
management behind you; today is about mapping that experience onto this specific job so
you can use it deliberately.

**Trainer lens.** Every cohort has strong builders who cannot scope. A session on
discovery and scoping — with real templates and a role-play — is often the most-remembered
session of a programme, because it's the one that changes how people work on Monday.

---

## Objectives

1. Run a discovery conversation using a structured framework, and produce a scoped design from it.
2. Build your reusable FDE toolkit: discovery guide, scoping canvas, eval-first proposal, week-one plan.
3. Practise the four hard conversations: no, not yet, it'll cost more, and it can't do that.
4. Map your existing TPM experience explicitly onto FDE competencies.

---

## Schedule (5:00)

| Block | Time | What |
|---|---|---|
| 0 | 0:20 | Week 3 recall |
| 1 | 1:15 | **Learn** — `learn/DAY_19_LEARN.md` |
| 2 | 2:25 | Build the toolkit + run a live discovery role-play |
| 3 | 0:30 | Teach-back #19 |
| 4 | 0:30 | Capstone selection + Day 20 prep |

---

## Block 0 — Week 3 recall (0:20)

1. Noise floor → threshold setting: what's the rule?
2. Which retrieval technique gave the biggest jump, and at what latency cost?
3. Cancellation: what does the money leak look like and how do you prove it's fixed?
4. Leading indicator of retrieval drift?
5. The self-hosting break-even, in one sentence.
6. Why is indirect injection more dangerous than direct?

---

## Block 1 — Learn (1:15)

**Read `learn/DAY_19_LEARN.md` and work its examples on paper before continuing.**
Take the self-check at the end. Anything you miss goes on a flashcard and into tomorrow's
warm-up. The material below consolidates the module — it is not a substitute for it.

### 1.1 What the job actually is

An FDE sits between the client's problem and the product. Not a consultant (who advises
and leaves), not a solutions engineer (who demos and hands off), not a staff engineer
(who owns a system long-term). The FDE **builds in the client's environment, with their
data, against their constraints, and leaves something their team can run.**

The four modes, and you'll switch between them within a single day:

| Mode | What you're doing | Failure if you overdo it |
|---|---|---|
| **Discovery** | Understanding the real problem behind the stated one | Analysis paralysis; the client wanted a demo in week one |
| **Prototyping** | Building the smallest thing that proves or kills the idea | Demo-ware that can't be productionised |
| **Hardening** | Evals, observability, deployment, handover | Gold-plating something nobody validated |
| **Enablement** | Teaching their team to own it | Becoming the bottleneck you were meant to remove |

The most common FDE failure is staying in prototyping mode because it's the most fun and
the client keeps clapping. The second most common is skipping discovery because the client
already "knows what they want."

### 1.2 The discovery framework

Run every discovery conversation through these six, in this order. Write them into
`portfolio/fde-toolkit/DISCOVERY_GUIDE.md` with your own follow-up questions under each.

**1. The complaint, in their words.**
> "Tell me about the last time this went wrong. Walk me through that specific day."

Never accept the abstract version ("we need better visibility"). Get one dated incident.
Specific incidents contain the real requirements; abstractions contain someone's guess at
a solution.

**2. The current path.**
> "Today, when that happens, who does what? How long does it take? What do they open?"

You are looking for the manual process you're automating. If nobody does it manually
today, ask why not — often the answer is that it isn't actually valuable, and you've just
saved everyone six weeks.

**3. The volume and the value.**
> "How many times a week? What does each one cost you in time or money when it goes wrong?"

This is your ROI numerator and it tells you the cost budget. 20 events a week at 30 minutes
each is not a $200k project, and knowing that early is a gift to both sides.

**4. The data.**
> "Where does that information live? Can I see a real example — not a sanitised one?"

**Ask for real data in the first meeting.** The gap between the described data and the
actual data is the single largest source of schedule overrun in this work. (Your Day 5
data dictionary — the appointment field with no timezone — is exactly the kind of thing
you only find by looking.)

**5. The constraints.**
> "Can data leave your network? Who has to approve this? What's the security review
> process? Is there a system of record this has to write back to?"

Ask about egress in the first meeting. Always. (Day 17.)

**6. The definition of done.**
> "Six months from now, this worked. What's different? Who noticed? What number moved?"

If nobody can answer this, you don't have a project — you have an experiment, and it should
be scoped and funded as one. Saying that is allowed and it makes you more trusted, not less.

### 1.3 Eval-first scoping

Here is the move that distinguishes you from every other AI consultant a client has met.

Most proposals say: *we'll build X, it'll take 8 weeks.*
Yours says: *before we build anything, here are 50 real questions from your ops team.
Here's how a system would be scored on them. Week one, we build the scoring harness and
measure a baseline. Then every week you see the number move.*

This does four things at once:
- Turns a vague ask into a measurable one — often revealing the ask is unmeasurable, which
  is a finding worth more than the project.
- Forces the client to produce real examples, which surfaces data problems in week one.
- Gives you a defensible definition of done.
- Makes your progress visible to a sponsor who cannot read code.

And it de-risks *you*: when the client says "it doesn't feel right," you have a number and
a set of failing cases instead of a debate.

**Write your proposal template around this.** It's your differentiator and it's grounded in
everything you've built since Day 5.

---

## Block 2 — Build the toolkit + role-play (2:25)

### 2.1 The toolkit (75 min)

`portfolio/fde-toolkit/` — five documents you'll reuse for years:

**1. `DISCOVERY_GUIDE.md`** — the six areas, with 4–6 follow-ups each, plus the questions
that surface a doomed project early ("who asked for this?", "what happens if we don't do
it?", "has this been tried before here?").

**2. `SCOPING_CANVAS.md`** — one page, filled in during the meeting, on screen:
```
Problem (their words) │ Current path      │ Volume/value
Users & who signs off │ Data + access     │ Constraints (egress, compliance, SoR)
Success metric        │ Eval set source   │ Out of scope (explicit!)
Riskiest assumption   │ Week 1 deliverable│ Kill criteria
```
The two fields nobody else has: **"out of scope, explicit"** and **"kill criteria."**
Writing down what would make you stop is the most senior thing on the page.

**3. `PROPOSAL_TEMPLATE.md`** — eval-first, three phases:
- Phase 0 (week 1): eval harness + baseline + data assessment. Fixed fee. **Ends with a
  go/no-go.** This is the whole trick — a small, fixed, low-risk first phase that produces
  a decision.
- Phase 1 (weeks 2–5): build to a target metric.
- Phase 2 (weeks 6–8): harden, deploy, hand over, enable.

**4. `WEEK_ONE_PLAN.md`** — the hour-by-hour first week:
```
Day 1  am  kickoff, discovery interviews ×2
       pm  environment access, repo, first look at real data
Day 2  am  50 questions collected from ops team (workshop, 90 min)
       pm  eval harness scaffold
Day 3  am  ingest a real document sample; baseline retrieval measured
       pm  naive RAG baseline; first number on the board
Day 4  am  demo the *baseline and its failures* to the sponsor
       pm  scope adjustment based on what the failures revealed
Day 5  am  written findings + phase 1 plan
       pm  go/no-go conversation
```
Note Day 4: **you demo the failures.** Showing a client where the baseline breaks, in week
one, is counterintuitive and enormously effective. It sets expectations honestly and makes
every subsequent improvement feel earned.

**5. `HANDOVER_CHECKLIST.md`** — from Day 17, plus: their engineer has deployed it
themselves at least once with you watching, they've added an eval case without you, and
they've resolved one alert.

### 2.2 Discovery role-play (45 min)

Use Claude (or any capable model) as the client. Prompt it:

> You are Dana Okonjo, VP of Transportation at a $2B food distributor. You have a
> problem: "our team spends too much time chasing carrier issues." You are busy,
> somewhat sceptical of AI, and you have already been pitched by two vendors. You have
> a real underlying problem but you will describe it badly at first, and you will
> propose your own solution ("we want a dashboard with AI") which is not the right one.
> Answer questions realistically and briefly. Do not volunteer information unless
> asked. If asked for real data examples, be initially reluctant. Stay in character.

Run a **30-minute discovery**, out loud, recorded. Then 15 minutes: fill in the scoping
canvas from the transcript and write the phase-0 proposal.

Then grade yourself:

- Did you get a **specific dated incident**, or did you accept the abstraction?
- Did you ask about **egress and approvals**?
- Did you ask for **real data**?
- Did you resist designing a solution before finishing discovery? (This is the hard one.
  Count how many minutes in you started proposing.)
- Did you get a **success metric with a number**?
- Did you name something **out of scope**, in the meeting?
- Did you talk less than 40% of the time? Time it.

That last one is the most reliable predictor of a good discovery call, and it's measurable.

### 2.3 The four hard conversations (30 min)

Practise each out loud, twice. Record. These are muscle memory, not knowledge.

**1. "No, that won't work."**
> "I want to flag something now rather than in week six: the appointment data doesn't
> carry a timezone, so any answer about on-time performance will be wrong for about 40%
> of facilities. We can fix it, but it's a data project before it's an AI project. Want
> me to scope that separately, or should we start with the accessorial questions where
> the data is clean?"

Note the structure: name the problem → quantify it → offer two paths → let them choose.
Never "no" alone.

**2. "Not yet."**
> "We could add that, and it'd take about a week. But we haven't validated that anyone
> uses the first thing yet. Can we put it on the list and revisit after the pilot has
> two weeks of usage data?"

**3. "That'll cost more than you think."**
> "The build is four weeks. The part that surprises people is the security review and
> the data access — at your company that's historically taken six to eight weeks. I'd
> rather start that in parallel on day one than discover it in week five."

**4. "It can't do that reliably."**
> "It'll be right about 85% of the time on that class of question, and it will be
> confident when it's wrong. So the question is what the workflow does with the other
> 15%. If a human reviews before anything is sent, 85% is a big win. If it's fully
> automated, 85% is a liability. Which is it?"

That fourth one is the highest-value sentence in this entire bootcamp. Almost nobody says
it and almost every failed AI project needed someone to.

---

## Block 3 — Teach-back #19 (0:30)

Record 12 min: **"Scope it with an eval, not a spec."**
`teaching/recordings/day_19.mov`

Show the scoping canvas. Walk through the phase-0 proposal. Then role-play the fourth hard
conversation on camera — the 85% one. It's the segment people will quote back to you.

---

## Block 4 — Capstone selection (0:30)

Days 20–21 are your capstone build. Choose now so tomorrow starts at full speed.

**Recommended: the Freight Carrier Performance Copilot** — build on everything you have, add
a genuine business workflow (quarterly carrier business review generation), and lean on your
23 years of domain credibility. The AI-portfolio landscape is full of chat-with-your-PDF
demos; almost none of them are built by someone who knows what a routing guide is. That
asymmetry is your whole advantage — use it.

Requirements whichever you pick:
- Solves a workflow, not a question. Someone's Tuesday should get shorter.
- Uses ≥5 of: agentic RAG, multi-agent, memory, MCP, hybrid retrieval, evals, observability, guardrails.
- Deployed, publicly reachable.
- Evaluated, with a scorecard.
- Has a 6-minute demo and a written case study.

Write `capstone/CAPSTONE_BRIEF.md` tonight: problem, user, workflow, success metric, the
eval set you'll build, architecture sketch, and what's explicitly **out of scope** for two
days. That last section is what makes a two-day capstone finishable.

---

## Done when

- [ ] Five toolkit documents written and reusable
- [ ] 30-minute recorded discovery role-play, with a completed scoping canvas and phase-0 proposal
- [ ] Self-graded on all seven discovery criteria, including talk-time percentage
- [ ] Four hard conversations rehearsed and recorded
- [ ] `CAPSTONE_BRIEF.md` written with explicit out-of-scope

---

## Trap list

- Accepting the abstract complaint. Get a dated incident.
- Designing during discovery. Notice the urge; write it down and keep asking.
- Not asking for real data in meeting one.
- Proposing a big phase 1 with no phase 0. Small, fixed, decision-producing first phase.
- No kill criteria. Then a doomed project runs for six months.
- Talking more than the client.
- Promising reliability without asking what the workflow does with the failures.
