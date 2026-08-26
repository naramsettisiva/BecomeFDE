# Day 24 · Learn — Making the work visible, and what sustains after

**Read before `labs/DAY_24.md`. Budget 0:30.**

---

## 1. Where this sits

You finish today with a deployed agentic system, a 250-case eval suite with a measured κ, a
fifty-attack red-team report, a cost model at three scales, an MCP server, twenty-plus recorded
sessions, a ten-module curriculum, and a sixty-minute lesson you have delivered live and reviewed
against a rubric. That is more shipped, measured work than most people have after a year of courses.

**And nobody knows about it.** That is the asymmetry today closes, and it is not a vanity problem.
Every artifact you built has an audience of one: the eval suite proves the system works — to you; the
red-team report proves you thought adversarially — to you. A hiring manager, a conference committee,
or a client deciding whether to let you near their team has none of it, and cannot get it, because
the evidence is spread across a private repo and your own memory.

So: **demo, portfolio and writing are not self-promotion. They are the last mile of the work
itself.** An engineering system that nobody can operate is unfinished; you have believed that for
twenty-three years. A body of work that nobody can evaluate is unfinished in exactly the same sense
and for the same reason — the value is realised at the interface, not in the implementation.

The second half of today is harder. **The structure that has carried you for twenty-four days ends
tonight** — five hours a day, a lab with a definition of done, a module telling you what to read.
Structure has to be replaced deliberately with habit, and the default outcome of not doing that is a
fortnight of momentum followed by nothing, which is what happens to most people who finish an
intensive.

Much of this is familiar: you have run programs, and you know an owner and a date beats an intention.
What is new is that **you are now the only stakeholder** — every mechanism you have relied on to keep
a program honest, from a steering committee to a review date someone else called, is gone. What
replaces them has to be built on purpose.

---

## 2. The mechanism

### 2.1 The eight-minute demo

**8 minutes. 6 slides. One live demo.** The constraint is not arbitrary — it is roughly the length of
a conference lightning slot, an interview "walk me through something you built", and the attention
budget of a hiring manager watching a recording at their desk. If it works at eight minutes it works
everywhere; if it needs twenty it works nowhere.

| # | Beat | Time | What it is *for* |
|---|---|---|---|
| 1 | **The problem** | 1:00 | Establish that a real cost exists, in units a non-specialist recognises: 60 contracted carriers, half an analyst-day per quarterly review, ~30 analyst-days a quarter, reviews late and inconsistent. |
| 2 | **What I built** | 0:45 | One sentence and one diagram. If it needs two sentences, the system isn't scoped, it's a list. |
| 3 | **Live demo** | 3:00 | The 40-second generation — then **open the trace and follow one number back to the query that produced it.** |
| 4 | **How I know it works** | 1:30 | Baseline versus final. Factual accuracy 100%. Three carrier profiles reaching genuinely different conclusions. |
| 5 | **The hard part** | 1:15 | One real adversarial failure you found and fixed. Show it breaking, then fixed. |
| 6 | **What's next, what it costs** | 0:30 | Cost model at two scales, named limitations, what two more weeks would buy. |

Two beats carry disproportionate weight.

**Beat 3's trace step is what separates you from a demo video.** Anyone can show generated output;
generated output is now unremarkable and mildly suspect. Following a number from the document back to
the SQL query that produced it is a claim about *verifiability*, and it is the thing a technical
audience is actually trying to assess. It takes twenty seconds and it changes what the demo means.

**Beat 5 is the slide people remember**, and every instinct says to cut it — you have eight minutes
and you are about to spend 15% of them on your system failing.

Do it anyway. **Anyone can demo a working system**, which tells the audience only that you can build
on the happy path — table stakes, and half-assumed to be cherry-picked. Showing an indirect prompt
injection through an indexed carrier document, the system doing something it should not, and then the
defence that stops it tells them four things at once: you tested adversarially unasked, you found
something real, you understood it well enough to fix it, and you will show your system failing —
which means the other five slides are probably honest too.

That last inference does the work. **A presenter who shows one failure is trusted on everything
else**; one who shows none is discounted across the board, because the audience assumes the failures
exist and were hidden.

Rehearse three times, timed, the third from memory and standing. And put slide 1 in front of someone
outside logistics — it is always the one that needs rework, because you have spent four weeks
somewhere "OTIF" and "detention" need no explanation and your audience has not.

### 2.2 Portfolio: three surfaces, three different jobs

The common mistake is treating these as three copies of the same content at three lengths. They have
different readers, different jobs, and different failure modes.

| Surface | Reader | Job | Failure mode |
|---|---|---|---|
| **Repo** | An engineer who will skim, then look at 2–3 files | Evidence of **process** | A README that opens with setup instructions |
| **Case study** | A hiring manager or client, reading properly | The **argument** that you can do this | Narrating what you built rather than what you decided |
| **Profile** | A recruiter or stranger, 20 seconds | **Framing** — making the pivot read as continuity | "Excited to announce my AI journey" |

**The repo's job is process, and the commit history is the artifact.** Anyone can produce a finished
repo; a history showing a failing eval, a diagnosis, a fix and the eval passing is evidence of a
*practice*, which a snapshot cannot fake. Don't squash four weeks into one clean commit. Do open the
README with what it is and why you'd care, in two sentences, with a screenshot — setup instructions
belong below the fold, because the reader skimming at 11pm is deciding whether to care, not whether
to install.

**The case study is the thing a hiring manager actually reads**, and it is the highest-leverage
artifact you will produce today, because it is the only one that carries *reasoning*. A repo shows
what exists; a case study shows what you decided, what you rejected, and what it cost. Its spine:

```
The problem, in the client's units (not yours)
The constraint that made it hard
What you tried that didn't work        ← the section that makes it credible
What you built, and the decision behind each choice
How you measured it — baseline and final numbers
What broke adversarially, and the fix
What it costs to run, at two scales
What you'd do differently
```

Section three is the credibility section and the one everyone omits. A case study with no failed
approach in it reads as marketing, because real projects have them and the reader knows it.

**The profile's job is framing.** You have twenty-three years and existing credibility — don't
rewrite, reframe the top. The pivot must read as **continuity, not a break**: "I spent 23 years
making large distributed systems work in production; I now do the same for AI systems — evaluation,
observability, cost, security, and teaching client teams to own what I build." That recruits your
history as evidence instead of asking the reader to discount it. The alternative — career-changer
learning AI — discards your only structural advantage and puts you behind people ten years younger
with the same GitHub.

### 2.3 Why narrow, data-backed writing travels

Given a choice between *"Lessons from building a production AI system"* and *"Someone put
instructions in my documents: indirect prompt injection in enterprise RAG, with before/after
numbers"*, write the second. It reaches more people, and the mechanism has three parts.

**It is findable.** Someone with your exact problem searches your exact words. Nobody searches for
"lessons from building."

**It is checkable.** A specific claim with numbers can be argued with, which is what makes it worth
sharing — a reader forwards a piece because it settles or sharpens something concrete, not because it
was broadly sensible. Broad writing gives the reader nothing to do.

**It is evidence rather than assertion.** "I understand LLM security" is a claim about you. "Here is
an injection through an indexed document, here is the defence, here is the attack success rate before
and after" is a demonstration, and the reader draws the conclusion themselves — which is a
conclusion they believe, because it is theirs.

And a fourth that matters for the job search: **broad posts are indistinguishable from each other.**
Ten thousand people can write "lessons from building an AI system"; roughly nobody can write your
injection post, because it needs a real corpus, a real attack and real measurements. Scarcity travels.

600 words is enough: one finding, the numbers, the fix, what you'd do differently.

### 2.4 Honest gap assessment, and the discipline of picking two

Rate yourself 1–5 across the competency list, **with evidence in the row.** The evidence column is
the whole exercise — a rating without it is a mood. "Evals: 4 — built a 250-case suite, measured κ =
0.61, set a CI gate above a measured noise floor" is a rating you can defend in an interview. "Evals:
4" is not, and worse, you cannot tell six weeks later what you meant.

Two structural facts fall out of the list, and both belong in interviews.

**Curriculum design, live teaching, facilitation and discovery are where twenty-three years of
program management is an unfair advantage.** Say so explicitly. The scarce combination is not "can
build agents" — there are a lot of those — it is "can build agents *and* run the room." Those are
usually different people, and the second is what makes a forward-deployed engineer deployable.

**Self-hosting and GPU sizing, fine-tuning, and multimodal are the honest gaps this course did not
cover.** Naming them is a strength: an engineer who can state their own boundary is trusted inside
it.

**Then pick two. Not three.** This feels wrong and is not.

A plan that closes every gap closes none, for reasons you have watched destroy programs: three
concurrent tracks each get a third of the attention, none reaches a visible artifact, and at day 90
you have three half-finished things that prove nothing. Two gaps at full attention produce two
shipped, written-up projects, and the third stays open — an open gap you can name is a far better
position than three shallow ones you can't demonstrate.

Selection rule: gaps that are (a) genuinely blocking roles you target, and (b) closeable with a
*shippable artifact* rather than a course. Self-hosting closes with a deployment and a throughput
number. Multimodal closes with document understanding over scanned BOLs and PODs — freight paperwork
is images, a real unmet need in a domain where you're already fluent. Both produce a post.
Fine-tuning, without a real dataset and baseline, tends to produce a notebook.

### 2.5 Replacing structure with habit

The course provided four things you are about to lose: a schedule, a definition of done, a feedback
signal, and an external expectation. Five habits replace them, and each is deliberately small enough
to survive a bad week.

| Habit | Cadence | Replaces | Why it is the one that works |
|---|---|---|---|
| **Weekly review** | Fri, 20 min, in `LEARNING_LOG.md` | The daily retro | Same file, same discipline. What shipped, what didn't, next week's *one* priority. Written down, it becomes a record you can read at day 90 instead of a feeling. |
| **Reading loop** | 2 papers/posts a week | The curriculum | Three sentences each in the log — **not a summary; what you'd do differently.** A summary is transcription; a decision is learning. |
| **Eval habit** | Every project ships with a scorecard | The lab's "done when" | This is now your professional signature. Most people's side projects have no numbers; yours always do. Protect it. |
| **Teaching habit** | One recorded explanation a month, minimum | The daily teach-back | The muscle atrophies fast, and it atrophies invisibly — you don't notice until you are in front of people. |
| **Standing benchmark** | Keep the freight corpus + golden set | The whole course's ground truth | See below. |

**The standing benchmark is the one to protect hardest**, for asymmetric leverage. A new model ships
and the industry argues about it from vibes and vendor benchmarks; you can have a real answer **in an
hour**, against a corpus you know intimately, a golden set you labelled, and a scorecard whose noise
floor you measured.

Almost nobody has this. Building it takes weeks; keeping it takes nothing. And it makes you fast
exactly where speed is visible — a client asking "should we switch models?", a CFP with a two-week
deadline, an interview question about last month's technique. In all three, "I measured it on my own
suite, here's the number" is a different kind of answer.

**Don't let it rot.** A benchmark you haven't run in four months is one you don't trust, which is one
you won't use. Run it monthly against your current stack even when nothing changed — that is what
tells you the harness still works and what your baseline is now.

### 2.6 The three tracks, and why the teaching track needs a calendar

Three tracks in parallel, ~13 hours a week, down from 30. Sustainable and still compounding.

| Track | Hours | Output | External deadline? |
|---|---|---|---|
| **A — Build in public** | 6 | One project a month, shipped and written up; one narrow post a month | **Weak** — self-imposed, but the artifact accumulates visibly |
| **B — Teaching reps** | 3 | Lunch-and-learn → meetups → conference CFP / workshop | **None** |
| **C — Role search** | 4 | 5 targeted applications, 2 conversations a week | **Strong** — other people reply, or don't, on their schedule |

The last column predicts exactly what will happen. **Track C has external deadlines** — applications
get responses, interviews get scheduled, and the feedback is immediate and emotionally loud. **Track A
has weak ones**: nobody is waiting for your project, but the work visibly accumulates. **Track B has
none.** Nobody is expecting a talk; no CFP notices you missed it; skipping a week costs nothing
observable and produces no signal at all.

So it will not happen unless it is calendared. Not "prioritised" — **calendared**, a recurring block
with a specific artifact due, the way you'd treat a milestone nobody is chasing.

And it has the highest long-run return, which is the trap. Track C is a numbers game with low
per-attempt yield. Track B compounds: each delivery improves the next, produces a recording that
deepens the portfolio, and generates the contacts and credential that make Track C work. A talk at a
logistics meetup is a portfolio artifact, a rehearsal, a network event and a differentiator at once.
Nothing in Track C does four jobs.

The ladder, in escalating stakes so nothing is a leap: a work lunch-and-learn in weeks 1–2 (free,
low-stakes, real audience — the audience is the point, since teaching to a camera plateaus); two local
meetups and one virtual community in weeks 3–6, where you're only writing abstracts because the
session exists; one regional CFP and one free 90-minute workshop for a logistics group in weeks 7–12.
That last matters disproportionately — an audience nobody else in AI is serving, where your domain
fluency is decisive rather than incidental.

Then the move most people never make: approach one or two training organisations with the curriculum
outline and a sample recording. **Instructor and TA roles get filled from people who show up with
materials already built**, and you will have a ten-module outline, a complete lesson with starter and
solution repos, a diagnosis instrument, and a recording. That is not an application, it is an audition
tape.

**Three dated checkpoints, in the calendar, today** — not "monthly reviews", actual dates: day 30
(project 2 shipped, one talk delivered, 20 applications out), day 60 (project 3, two talks, first
interviews in flight), day 90 (reassess: what's working, what isn't, what changes). A checkpoint
without a date is a hope, and you have known that for two decades.

---

## 3. Worked example — on paper

Two artifacts to diagnose and rewrite. Both are real shapes — this is what a first draft looks like.

**Artifact A — the opening of a case study:**

> ## Carrier Review Copilot
>
> Over the past few weeks I have been working on an exciting project using cutting-edge AI
> technology to automate the carrier review process. Using a modern stack including Python, FastAPI,
> LangGraph, and vector search, I built an agentic system that leverages large language models to
> generate comprehensive quarterly business reviews for freight carriers. This project taught me a
> great deal about the challenges of building production AI systems, and I'm excited to share what I
> learned. In this post I'll walk through the architecture, the tech stack, and some of the lessons
> along the way.

**Artifact B — a portfolio README:**

> # mcp-freight-ops
>
> An MCP server for freight operations.
>
> ## Installation
> ```bash
> git clone https://github.com/.../mcp-freight-ops
> cd mcp-freight-ops
> pip install -r requirements.txt
> cp .env.example .env
> ```
> ## Configuration
> Set `DATABASE_URL` and `ANTHROPIC_API_KEY` in your `.env` file...
>
> ## Usage
> See `examples/` for usage examples.

**Q1.** Artifact A: name the four distinct defects, most damaging first.

**Q2.** Rewrite A's opening — the first three sentences only.

**Q3.** A says the project "taught me a great deal about the challenges of building production AI
systems." What should replace that sentence, and what is the general rule?

**Q4.** Artifact B: what is the reader trying to decide in their first ten seconds, and does the
README help?

**Q5.** Rewrite B's first six lines.

**Q6.** Both artifacts share one root cause. Name it.

**Q7.** You have one hour and can fix exactly one of the two. Which, and why?

<details>
<summary><b>Answers — write yours first</b></summary>

**Q1.** In order of damage:

1. **No problem statement.** The reader never learns what was wrong before or what it cost — and
   without a cost there is no achievement. A system automating something nobody struggled with is a
   toy, and the reader cannot tell which this is.
2. **No numbers, anywhere.** Everything is adjectival: exciting, cutting-edge, modern, comprehensive.
   The fastest way to make a case study credible is a number in the first paragraph.
3. **Tech-stack-first framing.** "Python, FastAPI, LangGraph, vector search" is a list of tools, not
   decisions. A hiring manager assumes you can pip-install a framework; what they can't assume is
   that you chose it for a reason and know what you traded away.
4. **It promises a walkthrough rather than a finding.** A table of contents gives the reader no reason
   to continue.

Minor but real: "over the past few weeks" and "I'm excited to share" position this as personal
development. The reader cares whether the system works, not about your development.

**Q2.**

> Ridgeline Freight's quarterly business review took an analyst half a day. Across 60 contracted
> carriers, that is roughly 30 analyst-days a quarter, and the reviews still arrived late and
> inconsistent — two analysts looking at the same detention data would reach different conclusions
> about whether a Lane Review was triggered. I built a system that generates the review in 40
> seconds, with every number traceable to the query that produced it and every policy claim cited.

Three sentences: cost, why it was hard, what changed — with numbers in all three. Note what is
absent: the stack. It appears later, attached to a decision, where it means something.

**Q3.** Replace it with the *specific* thing, with its number. For example:

> The hardest problem was not generation. It was that a system with 100% correct numbers can still
> reach the same conclusion for a carrier at FTA 94% and one at 78% — a templating system with a
> working data path — and the failure is invisible unless you test three carrier profiles and diff
> the conclusions, not the figures.

**The general rule: replace every claim about your learning with the specific thing you learned.**
"I learned a lot about X" is a claim the reader must take on faith, and it carries zero information
because everyone writes it. The specific finding carries the same claim implicitly, plus evidence,
plus something the reader can use.

**Q4.** The reader is deciding **"is this relevant to my problem, and is it any good?"** — in roughly
ten seconds, on a phone, having arrived from a search or a link.

The README answers neither. "An MCP server for freight operations" gives the category and nothing
else — which tools, against what, toy or real database, does it work with Claude Desktop. Then it
spends the reader's attention on `git clone`, a step taken *after* deciding, not before. **Setup
instructions above the fold answer a question nobody has asked yet.**

**Q5.**

> # mcp-freight-ops
>
> An MCP server exposing freight operations data — shipments, carrier scorecards, detention events —
> to any MCP client. Ask Claude Desktop "which carriers had detention over $5k at Joliet last
> quarter?" and get an answer computed from your TMS, not guessed.
>
> Six tools over a Postgres schema, typed parameters, read-only by default, with an audit log of
> every query issued. Built against a 200-document freight corpus; runs locally.
>
> ![Claude Desktop querying detention events](docs/demo.png)
>
> **[Quickstart](#quickstart)** · **[Tools](#tools)** · **[Design notes](#design-notes)**

It names the concrete capability, shows a question a real person would ask, states the properties an
engineer evaluates (typed, read-only, audited — three signals an adult built it), shows a screenshot,
and *then* offers setup. The install block isn't deleted; it's below the decision it was interrupting.

**Q6.** **Both are written from the author's perspective rather than the reader's.** A is organised
around the author's journey — what I did, over what period, what I learned. B is organised around the
author's mental model of the repo — here is how you set up my thing. Neither asks what the reader
arrived wanting to know.

That single inversion fixes both. The reader of A wants to know whether a real problem was solved and
whether the solution can be trusted. The reader of B wants to know whether this does the thing they
need. Answer the arriving question first; everything else is below the fold.

**Q7.** **The case study.** Three reasons. **Highest ceiling** — a fixed README is merely adequate,
while the case study is the only artifact that makes the argument that you can do this work, and the
one a hiring manager reads properly. **Load-bearing** — its opening becomes your profile's About
paragraph, your demo's slide 1, your answer to "walk me through something you built", and a CFP
abstract; fixing it once fixes five artifacts, while the README fixes one repo. And **it is the
harder of the two**, so it is the one that won't get fixed later: the README is thirty minutes of
mechanical work you will genuinely do next week, whereas rewriting the opening requires deciding what
the project was actually about, and deferred, that decision doesn't get made.

Counter-argument worth holding: if `mcp-freight-ops` is the repo most likely to get organic
attention, its README is your highest-traffic surface. Fair — but that fix is thirty minutes. Case
study now, README tonight.

</details>

---

## 4. What people get wrong

**"The work speaks for itself."**
It does not, because nobody can hear it. A private repo has an audience of one. Distribution is part
of the work, not a separate distasteful activity appended to it.

**"A demo should show the system working."**
It should show the system working *and* one real thing that broke. Anyone can demo a happy path, and
an audience shown no failures assumes they were hidden and discounts everything.

**"I'll write the case study when I have more to say."**
You have maximum detail today and it decays fast. In six weeks you will remember the outcome and not
the decision, and the decisions are the content.

**"Broad topics reach more people."**
Inverted. Broad posts are interchangeable and unsearchable; a narrow post with real numbers is
findable, arguable, and scarce, and scarcity is what gets shared.

**"Squash the history — it looks messy."**
The history *is* the artifact for a repo whose job is evidence of process. A clean single commit
proves nothing that a snapshot doesn't already show.

**"Rewrite the profile around AI."**
Reframe the top; keep the twenty-three years. The pivot must read as continuity, or you have
discarded your only structural advantage and joined a queue of people with the same GitHub and less
history.

**"I should close all my gaps."**
A plan that closes every gap closes none. Two, at full attention, produce two shipped artifacts. The
third stays open and named, which is a defensible position.

**"I'll keep teaching when an opportunity comes up."**
No opportunity will come up. The teaching track is the only one with no external deadline, which
means it is the only one that requires a calendar entry to exist at all.

**"The corpus was for the course."**
It is a standing benchmark, and it is the reason you can answer "is this new model better for us?" in
an hour instead of a fortnight. Almost nobody has one.

---

## 5. The trainer's angle

**This section is meta on Days 22–24** — it is about teaching someone else to teach and to make their
work visible, not about teaching today's topic.

**The exercise that does the most work: the ten-second test, run live.** Put a trainee's README or
case-study opening on screen for ten seconds, take it away, and ask the room what the project does
and whether it works. The answers will be wrong or empty. Nothing you say about reader-centred
writing achieves what ten seconds of an audience failing to extract the point does — and the author
watches it happen, which is the part that changes behaviour.

**The rewrite drill:** everyone rewrites their opening paragraph in eight minutes with two rules —
a number in the first sentence, and no tool names before the third. Then read them aloud in pairs.
The constraint does the teaching; you barely have to comment, because the difference between the two
drafts is audible.

**Where new trainers get demo day wrong**, and it is nearly universal: they cut the hard-part slide
under time pressure. It feels like the optional one — it is 15% of the runtime and it makes them look
bad. Pre-empt it by name before they build the deck, explain the inference the audience draws from a
failure-free demo, and then hold them to it in rehearsal. Told after they have cut it, they will
rationalise; told before, they keep it.

**The uncomfortable thing to teach directly:** many strong engineers experience portfolio work as
self-promotion and quietly refuse. Do not argue with the value; reframe the category. Ask whether
they would ship a service with no runbook and no dashboard. They wouldn't — because an unoperable
system is unfinished. Same argument, same person, applied to their own body of work. That reframing
lands where "you need to market yourself" does not.

**The question a sharp trainee will ask:** *"Isn't a portfolio just signalling? Shouldn't the work be
enough?"*

> The work is enough *once someone can evaluate it*, and the argument is really about who bears the
> cost of that evaluation. Left as a repo, evaluation costs the reader an hour they will not spend,
> so the work goes unevaluated. A case study moves the cost to you, where it is cheap because you
> already have the context. That is not signalling — signalling is claiming a quality you can't
> demonstrate. Publishing an attack, its fix, and the before/after numbers is the opposite: it hands
> the reader the evidence and lets them draw the conclusion. If it were signalling, it would be
> cheaper to fake, and it isn't.

**The habit to install in every trainee you ever have:** the standing benchmark. Most people finish a
course with knowledge and no instrument. The person who keeps a corpus, a golden set and a scorecard
they trust can evaluate every new claim in the field in an hour, forever, and that is the difference
between staying current and reading about staying current.

---

## 6. Self-check

1. State the asymmetry today closes, and why it is a completeness problem rather than a marketing one.
2. What are the six demo-day beats and their times?
3. What does the trace step in beat 3 prove that generated output does not?
4. Why is the hard-part slide the one people remember, and what inference does the audience draw from
   a demo with no failure in it?
5. Name the three portfolio surfaces, their readers, and each one's job.
6. Why is the commit history the artifact for the repo?
7. Which section of a case study is the credibility section, and why is it usually missing?
8. Give three reasons narrow data-backed writing travels further than broad writing.
9. What makes a self-rating defensible?
10. Why does a plan that closes every gap close none?
11. Name the five sustaining habits and what each replaces.
12. Why is the standing benchmark corpus the highest-leverage thing to keep?
13. Rank the three tracks by strength of external deadline. What does the ranking predict?
14. Why does the teaching track compound faster than the role-search track?

<details>
<summary><b>Answers</b></summary>

1. You finish with a substantial body of work and an audience of one. It is completeness because an
   artifact nobody can evaluate is unfinished in the same sense as a service nobody can operate —
   value is realised at the interface.
2. Problem (1:00), what I built (0:45), live demo (3:00), how I know it works (1:30), the hard part
   (1:15), what's next and what it costs (0:30).
3. Verifiability. Generated output is now unremarkable and mildly suspect; following a number back to
   the query that produced it is a claim a technical audience is actually trying to assess.
4. Anyone can demo a working system. Showing a real adversarial failure and its fix proves you tested
   adversarially unasked, found something real, understood it, and will show your system failing —
   from which they infer the other five slides are honest. A demo with no failure is assumed to be
   hiding some, and everything gets discounted.
5. Repo → an engineer skimming → evidence of process. Case study → a hiring manager reading properly
   → the argument that you can do this. Profile → a stranger in 20 seconds → framing the pivot as
   continuity.
6. Anyone can produce a finished repo. A history showing a failing eval, a diagnosis, a fix, and the
   eval passing is evidence of a practice, which a snapshot cannot fake.
7. "What I tried that didn't work." It is omitted because it feels like admitting weakness, and its
   absence is exactly what makes a case study read as marketing — real projects have failed
   approaches and the reader knows it.
8. Findable (people search the specific words); checkable (a claim with numbers can be argued with,
   which is why it gets shared); evidence rather than assertion (the reader draws the conclusion, so
   they believe it). Fourth: scarcity — broad posts are interchangeable, yours needs a real corpus
   and real measurements.
9. Evidence in the row. "Evals: 4 — 250-case suite, κ = 0.61, CI gate above a measured noise floor"
   is defensible in an interview; "Evals: 4" is a mood you can't reconstruct in six weeks.
10. Three concurrent tracks each get a third of the attention, none reaches a visible artifact, and
    at day 90 you have three half-finished things that prove nothing. Two at full attention produce
    two shipped, written-up projects; the third stays open and *named*, which is defensible.
11. Weekly review (replaces the daily retro); reading loop (the curriculum); eval habit (the lab's
    definition of done); teaching habit (the daily teach-back); standing benchmark (the course's
    ground truth).
12. It lets you evaluate any new model or technique in an hour against a corpus you know, a golden
    set you labelled, and a scorecard whose noise floor you measured. Weeks to build, nothing to
    keep, and almost nobody has one — so it makes you fast exactly where speed is visible.
13. C strongest (other people reply on their schedule), A weak (self-imposed, but the artifact
    accumulates visibly), B none. It predicts that B is skipped first and permanently unless it is
    calendared with a specific artifact due.
14. Each delivery improves the next, produces a recording that deepens the portfolio, and generates
    contacts and credibility that feed the role search. One meetup talk is a portfolio artifact, a
    rehearsal, a network event and a differentiator at once. Track C is a numbers game with low
    per-attempt yield and no compounding.

</details>

**Scored below 10?** Re-read §2.2 and §2.6 before the lab. Block 2 is the portfolio and Block 3 is
the plan, and both go faster if the surfaces and the deadline asymmetry are already clear.

---

## 7. Going deeper (optional)

- Read three case studies from engineers whose work you rate, and time how long it takes to learn
  what problem was solved. If it's over fifteen seconds, note what got in the way — it will be the
  same thing that's in the way of yours.
- Any well-regarded narrow technical post with real numbers in it. Note the structure: problem,
  measurement, finding, fix, caveat. It is almost always the same five beats in the same order.
- Your own `LEARNING_LOG.md`, read end to end one last time. It is the raw material for the second
  post, the FAQ, and the honest gap assessment — and it is the only document that records what four
  weeks actually felt like.
- Your Day 6 and Day 23 recordings, three minutes each, back to back. Not nostalgia: it is the
  evidence you cite when someone asks whether you can teach, and it is more convincing than any
  certificate.

---

**Now go to `labs/DAY_24.md`.** Block 1 is §2.1 (rehearse three times and keep slide 5), Block 2 is
§2.2–2.3, Block 3 is §2.4 and §2.6 — pick two gaps, calendar Track B — and Block 4 is §2.5.
