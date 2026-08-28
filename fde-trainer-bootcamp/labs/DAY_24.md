# Day 24 — Demo Day, Portfolio, and the 90-Day Launch

**Tue Sep 29, 2026** · Week 4 · Backend: n/a · Est. cost: **$0–1**

> **Before you start — read `learn/DAY_24_LEARN.md` (0:30).**
> Demo structure, the three portfolio surfaces, sustaining habits. The lab below assumes it and does not re-explain it.


---

## Why today matters

You finish today with a deployed system, a measured eval suite, a security report, a cost
model, a case study, 20+ recorded sessions, a complete curriculum, and a lesson you've
delivered live. That's a real body of work — more than most people have after a year of
courses.

What you don't have yet is **anyone who knows about it.** Today converts the work into
opportunity: a demo you can give cold, a portfolio that survives a 90-second skim, and a
90-day plan with specific actions and dates.

This is the last day I set the agenda. From tomorrow, the plan is yours to run.

---

## Objectives

1. Deliver a demo-day presentation, recorded, that stands on its own.
2. Finish the portfolio so a stranger gets it in 90 seconds.
3. Write the 90-day plan: skill gaps, target roles, teaching reps, and a weekly cadence.
4. Set up the systems that keep this going after the structure ends.

---

## Schedule (5:00)

| Block | Time | What |
|---|---|---|
| 0 | 0:20 | Full-course recall |
| 1 | 0:30 | **Learn** — `learn/DAY_24_LEARN.md` |
| 2 | 1:15 | Demo day — build and deliver |
| 3 | 1:15 | Portfolio finish |
| 4 | 1:10 | The 90-day plan |
| 5 | 0:30 | Sustaining systems |

---

## Block 0 — Full-course recall (0:20)

<!--cards-->
> **Cards first — 5 minutes.** Open **Warm-up drill** in the sidebar of `fde-bootcamp.html`.
> It deals you every card that is due from the days you have finished, hardest box first, and
> it is capped at 20 so it stays a drill. Cards you miss come back tomorrow; cards you know
> go 1 → 2 → 4 → 8 → 16 days out. Then do the recall below, closed book.
<!--/cards-->


Closed book, 25 questions spanning all 24 days. Write them yourself from your flashcard
misses, then answer them. Anything still wrong after 24 days is a genuine gap — write it at
the top of your 90-day plan as a study item, not a shame item.

---

## Block 1 — Learn (0:30)

**Read `learn/DAY_24_LEARN.md` and work its examples before continuing.**
Take the self-check at the end. This is a build day, so the module is short and deliberately practical — read it once, properly, then build.

---

## Block 2 — Demo day (1:15)

### Build the presentation (45 min)

**8 minutes. 6 slides maximum. One live demo.** `portfolio/demo_day/`

| Slide | Content | Time |
|---|---|---|
| 1 | **The problem.** 60 contracted carriers, quarterly reviews, half a day of analyst time each, 30 analyst-days a quarter, reviews arriving late and inconsistent | 1:00 |
| 2 | **What I built**, in one sentence and one diagram | 0:45 |
| 3 | **LIVE DEMO.** The 40-second generation. Then open the trace and show a number tracing back to its query | 3:00 |
| 4 | **How I know it works.** Scorecard: baseline vs. final. Factual accuracy 100%. Three carrier profiles producing genuinely different conclusions | 1:30 |
| 5 | **The hard part.** Pick one — indirect injection through indexed carrier documents, or the contradictory policy revisions. Show it breaking, then fixed | 1:15 |
| 6 | **What's next and what it costs.** Cost model at two scales, limitations, what you'd build with two more weeks | 0:30 |

Slide 5 is what people remember. Anyone can demo a working system; showing a real
adversarial failure you found and fixed is what makes a technical audience lean in.

Rehearse **three times, timed.** Third time from memory, standing up.

### Deliver it (30 min)

Record it. Then get it in front of at least one real person today — a colleague, a friend,
a video call — and get one piece of feedback. Revise slide 1 based on whether they
understood the problem without you explaining it. Slide 1 is the one that always needs
rework; if a non-freight person doesn't get the problem in 60 seconds, it's still too
insider.

Post the recording. LinkedIn, YouTube unlisted, wherever. **A demo nobody sees is a demo
that didn't happen.**

---

## Block 3 — Portfolio finish (1:15)

Three surfaces. Each gets a specific job.

### 1. GitHub (30 min)

- [ ] `fde-trainer-bootcamp` — pinned, with a README that opens with what's in it and a
      screenshot of the trace viewer. Not a wall of setup instructions
- [ ] `carrier-performance-copilot` — capstone extracted into its own repo, clean history,
      live demo link at the top, case study linked
- [ ] `mcp-freight-ops` — the MCP server as a standalone repo. **This is the one most
      likely to get organic stars**; MCP servers are being searched for right now
- [ ] Every repo: description, topics, license, a README opening with *what it is and why
      you'd care* in two sentences
- [ ] Profile README linking the three, plus the teaching page

### 2. The written case study (25 min)

Polish `portfolio/case_studies/carrier-review-copilot.md` from Day 21. Then publish it
somewhere with a URL — a personal site, Medium, dev.to, LinkedIn article. Anywhere with a
link you can paste into an application.

Then write a **second, shorter piece** (600 words) on one narrow technical finding. The
best candidate from this month: *"Someone put instructions in my documents: indirect prompt
injection in enterprise RAG"* — you have a real demo, a real fix, and real before/after
numbers. Narrow technical posts with real data travel much further than broad ones.

### 3. LinkedIn (20 min)

You have an existing profile and 23 years of credibility. Don't rewrite it — **reframe the
top**:

- **Headline**: `AI Forward Deployed Engineer | Production agentic systems, evals, and
  enablement | 23 yrs distributed systems & supply chain`
- **About**: lead with the pivot as continuity, not a break. "I spent 23 years making
  large distributed systems work in production. I now do the same for AI systems — the
  unglamorous parts: evaluation, observability, cost, security, and teaching client teams
  to own what I build." Then the capstone with its link.
- **Featured**: demo video, case study, GitHub, teaching page.
- **Experience**: add the four weeks honestly — "Independent intensive: built and deployed
  a production agentic system with eval harness, observability, and red-team assessment."
  Link the repo. Don't inflate it; the artifacts speak.

Then **one post**, today: the demo video, three sentences on the problem, one specific
finding, links. Do not write a "I'm excited to announce my AI journey" post. Write the
finding. Technical specificity is what gets shared and what gets you found.

---

## Block 4 — The 90-day plan (1:10)

`portfolio/NINETY_DAY_PLAN.md`. This is the deliverable that matters most today, because
the structure that has carried you for 24 days ends tonight.

### 3.1 Honest gap assessment (25 min)

Rate yourself 1–5, with evidence, on each:

| Competency | Rating | Evidence | Gap action |
|---|---|---|---|
| Python / async / typed systems | | | |
| Retrieval systems (chunking, hybrid, rerank) | | | |
| Agent design and orchestration | | | |
| Evals and measurement | | | |
| Production serving | | | |
| Observability and incident response | | | |
| Cost engineering | | | |
| LLM security | | | |
| Deployment (cloud, containers, CI/CD) | | | |
| Self-hosted models / GPU sizing | | | |
| Fine-tuning and adaptation | | | |
| Multimodal (vision, voice) | | | |
| Discovery and scoping | | | |
| Live teaching | | | |
| Workshop facilitation | | | |
| Curriculum design | | | |

The last four rows are where 23 years of program management is an unfair advantage. Say so
in interviews — the scarce combination is not "can build agents," it's "can build agents
*and* run the room."

Rows 10–12 are the honest gaps this course didn't cover: self-hosting/GPU, fine-tuning, and
multimodal. Pick **two** to close in the next 90 days. Don't pick all three.

### 3.2 The three tracks (45 min)

Run all three in parallel. Each gets a weekly commitment you actually write down.

**Track A — Build in public (6 hrs/week).**
- One project per month, shipped and written up. Suggested: (1) a self-hosted model
  deployment with real throughput numbers — closes a gap and is a great post; (2) a
  multimodal document-understanding system on freight paperwork — BOLs and PODs are
  scanned images, this is a real unmet need; (3) an agent-simulation harness.
- One technical post per month, narrow and data-backed.
- Keep the eval discipline. Every project ships with a scorecard. It's your signature.

**Track B — Teaching reps (3 hrs/week).**
This is the one that will not happen unless you schedule it. Concrete ladder:
1. **Weeks 1–2**: deliver the evals lesson to a work team as a lunch-and-learn. Free, low
   stakes, real audience.
2. **Weeks 3–6**: submit to two local meetups (Nashville has an active tech scene — Nashville
   Analytics Summit, local Python/data groups) and one virtual community. Your session is
   already built; you're only writing abstracts.
3. **Weeks 7–12**: submit to one regional conference CFP, and offer a free 90-minute
   workshop to a logistics or supply-chain group — that's an audience nobody else in AI is
   serving and where your domain fluency is decisive.
4. Record everything. Each delivery makes the next one better and the portfolio deeper.
5. Approach one or two training organisations or bootcamps with your curriculum outline and
   sample recording. Instructor and TA roles get filled from people who show up with
   materials already built. If a cohort you're interested in comes around later, you'd be
   approaching it as a candidate instructor, not a student.

**Track C — Roles (4 hrs/week).**
- Target titles: Forward Deployed Engineer, AI Solutions Engineer, AI Solutions Architect,
  Applied AI Engineer, Technical Instructor / Curriculum Engineer (AI).
- Target companies, three buckets: (1) AI labs and platform vendors with FDE functions;
  (2) AI-forward vertical SaaS in logistics and supply chain — where your domain is the
  differentiator and the competition is thin; (3) consultancies building AI practices.
- **Your pitch, one sentence, memorised**: *"I spent 23 years shipping distributed systems
  in supply chain; I now build production AI systems for that domain and I can teach the
  client's team to run them."* Very few people can say all three parts.
- 5 targeted applications a week, each with a note referencing something specific about
  them. Not 50 generic ones.
- 2 conversations a week — former colleagues, meetup contacts, people whose work you've read.
- Keep your system-design practice going. Your Oracle loop identified this as the weak
  point; one design problem a week, written out, in the same disciplined format you've used
  for four weeks.

### 3.3 The calendar (20 min)

Put it in an actual calendar with actual times:

```
Mon 6:00-8:00am   Build (Track A)
Tue 6:00-7:00am   Applications + outreach (Track C)
Wed 6:00-8:00am   Build (Track A)
Thu 6:00-7:00am   System design practice
Fri 6:00-7:00am   Teaching prep / CFP writing (Track B)
Sat 8:00-11:00am  Build + write-up
Sun               off
```

13 hours a week, down from 30. Sustainable, and it keeps compounding.

**Set three dated checkpoints, in the calendar, now:**
- **Day 30 (Oct 21)**: project 2 shipped, one talk delivered, 20 applications out.
- **Day 60 (Nov 20)**: project 3 shipped, two talks delivered, first interviews in flight.
- **Day 90 (Dec 20)**: reassess. What's working, what isn't, what changes.

---

## Block 5 — Sustaining systems (0:30)

The structure ends tonight. These replace it:

1. **The weekly review.** Friday, 20 minutes. What shipped, what didn't, what's next week's
   one priority. Write it in `LEARNING_LOG.md` — same file, same discipline.
2. **The reading loop.** Two papers or engineering posts a week. Write three sentences on
   each in the log. Not a summary — what you'd *do* differently.
3. **The eval habit.** Every project ships with a scorecard. This is now your professional
   signature; protect it.
4. **The teaching habit.** One recorded explanation a month minimum, even with no audience.
   The muscle atrophies fast.
5. **The corpus.** Keep the freight corpus and the golden set. They're your standing
   benchmark — when a new model or technique appears, you can measure it against a suite
   you trust in an hour. Almost nobody has this, and it makes you fast in exactly the
   situations where speed is visible.

Final commit:

```bash
git add -A
git commit -m "Day 24: demo day, portfolio complete, 90-day plan. 24 days, 120 hours, one system."
git push
```

---

## Done when

- [ ] 8-minute demo recorded, delivered to one real person, revised, and posted publicly
- [ ] Three GitHub repos clean, described, and pinned
- [ ] Case study published with a public URL; second narrow technical post drafted
- [ ] LinkedIn reframed; one specific, technical post published
- [ ] `NINETY_DAY_PLAN.md` with gap assessment, three tracks, weekly calendar, and three
      dated checkpoints
- [ ] Sustaining systems written down and the calendar populated

---

## What you built in 24 days

- A RAG system built from the vector arithmetic up, with verifiable citations
- A 250-case eval suite with a calibrated judge (κ measured, not assumed) and CI gates
- Six retrieval techniques, ablated on a 200-document corpus with near-duplicates
- An agent loop written by hand, then rebuilt on a framework, with the trade-off documented
- A multi-agent supervisor system and a deep-research agent
- Four memory types and a context budget allocator, with a needle heatmap for your stack
- An MCP server running in Claude Desktop, and a client so your agents consume any server
- A production FastAPI service: streaming, cancellation, three cache layers, guardrails
- Full OpenTelemetry tracing, a six-panel dashboard, and a completed incident drill
- A deployed, publicly reachable application with CI/CD and an eval gate
- A cost model at three scales, and an 84% cost reduction with the quality trade quantified
- A 50-attack red-team report with defence-in-depth results and named residual risk
- A capstone that turns half a day of analyst work into 40 seconds
- An FDE toolkit: discovery guide, scoping canvas, eval-first proposal, week-one plan
- A failure-organised 10-module curriculum
- A complete 60-minute lesson — plan, slides, starter, solution, exercises, FAQ,
  instructor notes — delivered live, unedited, and reviewed
- 20+ recorded sessions showing four weeks of visible improvement

You are an AI Forward Deployed Engineer who can teach. The work is done; what remains is
being seen.

Go run your plan.
