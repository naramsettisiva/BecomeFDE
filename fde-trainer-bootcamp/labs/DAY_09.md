# Day 09 — Multi-Agent Systems: Supervisors, Handoffs, and Deep Research

**Tue Sep 8, 2026** · Week 2 · Maps to: **Module 03 — Multi-Agent Systems** · Backend: **local** + `[PAID]` · Est. cost: **$3–6**

> **Before you start — read `learn/DAY_09_LEARN.md` (1:15).**
> Three topologies, three failure modes, handoff design. The lab below assumes it and does not re-explain it.


---

## Why today matters

**FDE lens.** Multi-agent is the most oversold pattern in the field and occasionally the
right one. Clients arrive having read that "agent swarms" solve everything. Your job is
to know the three topologies, the two real reasons to use more than one agent, and the
failure mode nobody mentions (context loss at handoff). Then to build the simplest thing
that works.

**Trainer lens.** The honest lesson — *most multi-agent systems should be one agent with
better tools* — is unpopular and correct. Teaching it well means demonstrating both: build
the multi-agent version, build the single-agent version, and show the numbers.

---

## Objectives

1. Implement three topologies: **supervisor/worker**, **sequential pipeline**, **peer handoff**.
2. Build a deep-research agent that plans, fans out, synthesises, and cites.
3. Name and instrument the handoff failure modes: context loss, responsibility diffusion, cost explosion.
4. Produce the honest comparison: multi-agent vs. one good agent, on the same task.

---

## Schedule (5:00)

| Block | Time | What |
|---|---|---|
| 0 | 0:30 | Warm-up |
| 1 | 1:15 | **Learn** — `learn/DAY_09_LEARN.md` |
| 2 | 2:30 | Lab: supervisor system + deep research agent + the honest comparison |
| 3 | 0:30 | Teach-back #9 |
| 4 | 0:15 | Ship |

---

## Block 0 — Warm-up (0:30)

<!--cards-->
> **Cards first — 5 minutes.** Open **Warm-up drill** in the sidebar of `fde-bootcamp.html`.
> It deals you every card that is due from the days you have finished, hardest box first, and
> it is capped at 20 so it stays a drill. Cards you miss come back tomorrow; cards you know
> go 1 → 2 → 4 → 8 → 16 days out. Then do the recall below, closed book.
<!--/cards-->


1. Four agentic-RAG patterns and the bucket each one fixes.
2. Your bake-off: best quality-per-dollar strategy? Show the arithmetic.
3. When does decomposition have to be sequential rather than parallel?
4. What did the LangGraph state machine buy you over the loop?

---

## Block 1 — Learn (1:15)

**Read `learn/DAY_09_LEARN.md` and work its examples on paper before continuing.**
Take the self-check at the end. Anything you miss goes on a flashcard and into tomorrow's
warm-up. The material below consolidates the module — it is not a substitute for it.

### 1.1 The three topologies

**Supervisor / worker (hub-and-spoke).**
```
            ┌────────────┐
            │ SUPERVISOR │  owns the plan, routes, decides when done
            └──┬───┬───┬─┘
               ▼   ▼   ▼
          policy  data  calc      workers: narrow, tool-rich, stateless
```
Best default. The supervisor holds the plan and the state; workers are effectively
specialised tools with their own reasoning. Easy to debug because there's one brain.

**Sequential pipeline.**
```
research → analyse → draft → critique → revise
```
Best when the stages are genuinely distinct and ordered. This is a *workflow*, not really
a multi-agent system, and that's a compliment — it's testable and cheap. Most "multi-agent"
production systems that work are this.

**Peer handoff (swarm).**
```
agent A ⇄ agent B ⇄ agent C   any agent can transfer control
```
Most flexible, hardest to reason about, easiest to loop. Use when the routing genuinely
can't be centralised. Rare in enterprise. If a client wants this, ask what breaks with a
supervisor — usually nothing.

### 1.2 The three real failure modes

1. **Context loss at handoff.** Agent A did 6 steps of research. It hands to B with a
   3-sentence summary. B doesn't know what A ruled out, so B re-explores it. This is the
   dominant cost sink in multi-agent systems and it is *invisible* unless you trace it.
   Mitigations: structured handoff objects (not prose), shared scratchpad, or explicit
   "what I ruled out and why" fields.
2. **Responsibility diffusion.** Every agent assumes another agent verified the fact.
   Nobody did. Mitigation: exactly one agent owns verification, and it's named.
3. **Cost explosion.** Each agent re-sends its own context every step. Three agents × 6
   steps × 8k context = 144k input tokens for one question. Instrument per-agent token
   spend from the first line of code you write today, not after you get the bill.

### 1.3 State: shared vs. passed

| Model | How | Good | Bad |
|---|---|---|---|
| **Shared blackboard** | All agents read/write one state object | No context loss, cheap | Race conditions, prompt bloat, agents distracted by irrelevant state |
| **Message passing** | Explicit handoff payloads | Clean boundaries, testable | Context loss, serialisation overhead |
| **Hybrid** | Shared read-only facts + passed instructions | Usually right | More code |

Build the hybrid. In LangGraph this is a typed state dict with reducers; hand-rolled it's
a `ResearchState` dataclass. Either way: **make the handoff payload a pydantic model.**
Prose handoffs are where multi-agent systems go to die.

---

## Block 2 — Lab (2:30)

### 2.1 Supervisor system (60 min)

`src/fdekit/multiagent.py`. Workers, each with a narrow tool set and a narrow system prompt:

- **PolicyAgent** — owns the document corpus, uses your Day 8 `FullStack` strategy.
- **DataAgent** — owns the synthetic TMS tables (build 3 small CSVs: shipments, stops,
  carrier scores — ~200 rows each; generate them with a script and commit them).
- **AnalystAgent** — owns computation and comparison; no retrieval, only `calculate`
  and structured reasoning over what it's given.
- **Supervisor** — plans, routes, decides completion, assembles the final answer with
  citations from whichever worker supplied each fact.

Handoff contract:

```python
class Handoff(BaseModel):
    to: Literal["policy", "data", "analyst"]
    task: str                       # a complete, standalone instruction
    context_summary: str            # what has been established so far
    already_tried: list[str]        # <- the field everyone forgets
    expected_output: str            # what "done" looks like for this sub-task
```

`already_tried` is the anti-loop mechanism. Add it now and watch your step count drop.

Test task: *"Carrier Ridgeline Freight has an FTA of 83% on DAL→CHI for two quarters and
we've paid $4,200 in detention on that lane this quarter. What's their scorecard band,
what happens to their primary position, and what should we do at the next bid?"*

This genuinely needs all three workers: policy (docs 01, 04, 06), data (their actual
numbers), analyst (the recommendation).

### 2.2 Deep research agent (60 min)

`capstone/deep_research.py`. Different shape from the supervisor — this is plan-and-execute:

```
1. PLAN      : decompose the question into 4-8 research sub-questions.
               Output a typed plan. Show it to the user before executing.
2. FAN OUT   : run sub-questions concurrently (Semaphore(4)).
               Each returns findings + citations + confidence + gaps.
3. REFLECT   : are there gaps? contradictions between findings?
               If yes, generate up to 3 follow-up questions. Loop once, max twice.
4. SYNTHESISE: write a structured brief with inline citations.
5. VERIFY    : substring-check every citation. Flag unverified claims in the output.
```

Output a real markdown brief to `capstone/research_output/`. Test question:

> "Should we convert our Dallas–Chicago truckload volume to intermodal? Consider cost,
> service risk, our carrier's current performance, and what could go wrong."

Two design points that make this good rather than generic:

- **Show the plan before executing.** A research agent that reveals its plan is one a
  user can steer. This is a UX decision with a big trust payoff, and it costs nothing.
- **Track `gaps` explicitly.** An honest research brief says what it couldn't determine.
  Yours should have a "What we could not establish" section, populated from the workers'
  reported gaps. Clients notice this immediately — it's the difference between a report
  and a plausible essay.

### 2.3 The honest comparison (45 min)

Run the same two tasks through:
- **A** — your three-agent supervisor system
- **B** — a single Day 7 agent with *all* the same tools available to it
- **C** — a fixed sequential pipeline (retrieve → compute → draft), no agency at all

Fill in `evals/day09_multiagent_comparison.md`:

| | A: Supervisor | B: One agent | C: Pipeline |
|---|---|---|---|
| Answer quality (judge, 1–5) | | | |
| Facts correct (hand-checked) | | | |
| Total LLM calls | | | |
| Total tokens (in / out) | | | |
| Cost | | | |
| Wall clock | | | |
| Lines of code | | | |
| Could you debug it in front of a client? | | | |

Then write the paragraph you'd say to a client. Be prepared for B to win on the simpler
task. **If it does, say so.** That's the finding, and it's more valuable than a
multi-agent system that works.

---

## Block 3 — Teach-back #9 (0:30)

Record 10 min: **"You probably don't need multi-agent. Here's how to tell."**
`teaching/recordings/day_09.mov`

Show the comparison table. Then give the decision rule you'd actually use:

> Use more than one agent when (a) the tool sets are large enough that one agent's tool
> list degrades its choices, or (b) different sub-tasks need genuinely different system
> prompts or models. Not because the problem "has multiple steps."

Then show the context-loss trace — agent B re-exploring something agent A already ruled
out. That trace is the single most convincing artifact in this lesson.

---

## Block 4 — Ship (0:15)

```bash
git add -A && git commit -m "Day 09: supervisor multi-agent, deep research agent, honest topology comparison" && git push
```

---

## Done when

- [ ] Three workers + supervisor completing the Ridgeline task correctly
- [ ] Typed `Handoff` model with `already_tried` — and evidence it reduced step count
- [ ] Deep research agent producing a cited brief with an explicit gaps section
- [ ] Per-agent token and cost accounting in the trace
- [ ] Three-way comparison table filled in with real numbers
- [ ] Your written recommendation, including the case where single-agent wins

---

## Trap list

- Prose handoffs. Type them.
- No `already_tried`. Agents will redo work forever.
- Giving every worker every tool. Then it's one agent with extra latency.
- Not tracking cost per agent — you can't fix what you can't attribute.
- A supervisor that does the work itself instead of delegating. Watch for this; it's
  common and it means your worker descriptions are bad.
- Demoing multi-agent on a task a single agent handles. Clients notice.

---

## Stretch

Add a **critic agent** to the deep-research flow: it reads the draft brief and returns
structured criticism (unsupported claims, missing considerations, overconfident language).
Feed it back for one revision. Then measure: did the critic improve the judge score, or
just make the brief longer? Verbosity masquerading as quality is a real failure mode and
measuring it is a genuinely advanced teaching moment.
