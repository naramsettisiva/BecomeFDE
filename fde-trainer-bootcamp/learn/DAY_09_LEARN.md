# Day 09 · Learn — Multi-agent systems, and the case against most of them

**Read before `labs/DAY_09.md`. Budget 1:15. Pen and paper for §3 — the token accounting is the argument.**

---

## 1. Where this sits

Day 7 gave you one loop. Day 8 gave that loop a retrieval strategy and a price list. Today you
split the loop across several agents, and the honest headline is this: **splitting is a
distributed-systems decision wearing an LLM costume, and it has the same trade-offs it has always
had.**

You have run this play before. Break a monolith into services and you don't get a smarter system.
You get explicit ownership boundaries, independent configuration, and — in exchange — serialisation
at every boundary, latency you didn't have, and invariants nobody owns. Multi-agent is that with
one twist: the serialisation format is **natural language**, which is lossy in a way a protobuf
isn't.

Clients arrive having read that agent swarms solve everything. Your job is to know the three
topologies, the real reasons to split, and the failure mode nobody mentions — then build the
simplest thing that works. Usually that's one agent with better tools, and saying so with numbers
behind it is worth more than a working swarm.

---

## 2. The mechanism

### 2.1 A worker agent is a tool whose implementation is another loop

Before topologies, demystify. There is no new primitive today.

A "multi-agent system" is still one process, still your code, still Day 7's while-loop. The only
change is that **one agent's output becomes another agent's input context**, and the routing
decision is itself a tool call:

```python
registry.register(
    name="ask_policy_agent",
    description="Delegates a policy-corpus question to the PolicyAgent...",
    args_model=Handoff,
)
def ask_policy_agent(h: Handoff) -> str:
    return PolicyAgent(...).run(h).final_answer   # <- another Day 7 loop
```

That's it. `transfer_to_data_agent` is a tool. The supervisor doesn't "talk to" the worker; it
emits a tool call, your code runs a nested loop, and the worker's final string comes back as an
observation. Everything else today is topology, state, and what gets lost at that boundary.

Carry the payoff into every client conversation: **the supervisor's context contains the worker's
*summary*, not the worker's steps.** That one fact is simultaneously why multi-agent saves tokens
(the supervisor never pays for the worker's six observations) and why it loses information (§2.3).
Same mechanism, both signs.

### 2.2 The three topologies

**Supervisor / worker (hub-and-spoke).**

```
            ┌────────────┐
            │ SUPERVISOR │   owns the plan, routes, decides when done
            └──┬───┬───┬─┘
               ▼   ▼   ▼
          policy  data  calc     workers: narrow, tool-rich, stateless
```

The right default. One brain holds the plan and the state; workers are specialised tools that
happen to reason. Easy to debug precisely because there is one place the decisions are made.

**Sequential pipeline.**

```
research → analyse → draft → critique → revise
```

Best when the stages are genuinely distinct and ordered. This is a *workflow*, not really a
multi-agent system, and that's a compliment — it's testable, cheap, and deterministic in structure.
**Most production "multi-agent" systems that actually work are this.**

**Peer handoff (swarm).**

```
agent A ⇄ agent B ⇄ agent C     any agent can transfer control
```

Most flexible, hardest to reason about, easiest to loop. Use when routing genuinely can't be
centralised. Rare in enterprise. If a client wants this, ask what breaks with a supervisor —
usually nothing.

| | Supervisor | Pipeline | Swarm |
|---|---|---|---|
| Control | Central | Fixed | Distributed |
| Debuggability | Good — one decision point | Best | Poor |
| Adaptivity | High | None | Highest |
| Loop risk | Low (one budget) | None | High |
| Cost | Medium | Lowest | Highest |
| Right when | Sub-tasks vary per question | Stages are known and ordered | Routing can't be centralised |

A note for someone with your background, because the instinct misfires here: a swarm is **not**
more robust for having no single point of control. There is no partition to survive — it's all one
process, sharing one Python heap. Hub-and-spoke is easier precisely *because* there's a single
point. This is a legibility problem, not a fault-tolerance problem, and the distributed-systems
reflex that says "avoid the coordinator" is the wrong reflex today.

### 2.3 Failure mode 1 — context loss at handoff

The dominant cost sink in multi-agent systems, and **invisible without tracing**, because each
agent's own trace looks perfectly reasonable in isolation.

The mechanism. PolicyAgent runs six steps: searched the corpus four different ways, found the Lane
Review rule in document 01, found the band table in document 06, established that the detention cap
does *not* apply per-lane. Roughly 9,000 tokens of exploration. It hands over a 400-token summary.
AnalystAgent receives the summary, doesn't know what was already searched, and searches the policy
corpus again.

What gets dropped is **negative information** — what was tried and returned nothing, what was ruled
out, what error a tool threw. It's dropped systematically rather than randomly, because summarisers
are trained to report *findings* and non-findings don't read like findings. So the most expensive
information to rediscover is exactly what the handoff carries worst.

How to see it: fingerprint every tool call as `(tool_name, canonical_json(args))` and count
fingerprints appearing under more than one agent in a run. That's your context-loss metric and it
should be zero. §3 prices two duplicate calls at **+27% on the run's cost**.

Mitigations in ascending effort: typed handoff objects (§2.7), a shared read-only scratchpad both
agents append to, and a required "what I ruled out and why" field.

### 2.4 Failure mode 2 — responsibility diffusion

Every agent assumes another agent verified the fact. Nobody did.

The mechanism is prompt-level. Each worker's system prompt describes it as a specialist embedded in
a team — exactly the framing that makes "someone else checks this" a reasonable inference. So
verification becomes everyone's assumed job, which is nobody's. You've seen the human version: an
on-call rotation with three secondaries and no primary.

The fix is boringly organisational. **Exactly one agent owns verification, it's named in every other
agent's system prompt, and it runs last.** In this lab that's Day 2 §2.5's substring citation check,
owned by the supervisor at assembly time, applied to every fact regardless of source.

The mirror-image failure is common and looks like the opposite: **a supervisor that does the work
itself instead of delegating**, because it has `search_policy` in its own tool list or because the
worker descriptions are vague enough that answering directly looks easier. Both are Day 7 §2.7
again — worker descriptions *are* tool descriptions.

### 2.5 Failure mode 3 — cost explosion

Day 7 §2.5 gave you the per-agent growth: `n·B + o·n(n−1)/2`, quadratic in steps. Multi-agent does
not turn that into a bigger linear cost. It gives you **a sum of quadratics, plus the supervisor's
own quadratic on top**, whose observations are the worker summaries.

```
total ≈ Σ_agents [ nᵢ·Bᵢ + oᵢ·nᵢ(nᵢ−1)/2 ]  +  supervisor's own quadratic
```

Two things make this better than it sounds. Each worker has a **small base** `B` — narrow prompt,
three tools instead of nine — and the supervisor's observations are 350-token summaries rather than
900-token chunk sets, so its quadratic has a small coefficient. Isolation genuinely saves tokens: in
§3 the well-behaved three-agent run costs only 1.13× the single agent.

One thing makes it worse: every duplicate step from §2.3 lands *inside* a quadratic. Two redundant
searches don't add two observations' worth of tokens — they add two observations and re-send
everything before them, twice. That's how §3's 1.13× becomes 1.43×.

**Instrument per-agent token and cost accounting from the first line of code today, not after the
bill.** You can't fix what you can't attribute, and "the multi-agent system is expensive" isn't a
finding — "AnalystAgent is 38% of spend and most of that is a duplicate policy search" is.

### 2.6 State: blackboard, message passing, hybrid

| Model | How | Good | Bad |
|---|---|---|---|
| **Shared blackboard** | All agents read/write one state object | No context loss; cheap to write | Prompt bloat; agents distracted by state they don't need |
| **Message passing** | Explicit handoff payloads | Clean boundaries, testable, small contexts | Context loss (§2.3) |
| **Hybrid** | Shared read-only facts + passed instructions | Usually right | More code |

The blackboard's real failure is not race conditions — you're in one process and usually one event
loop. It's **distraction**: every agent sees everything, so the AnalystAgent's context now contains
four policy chunks it doesn't need, which costs tokens *and* degrades its tool selection. That's
the same lost-in-the-middle and tool-list-dilution effect you've met twice already.

Build the hybrid: an append-only, citation-keyed facts store both agents can read, plus a typed
instruction passed on the edge.

### 2.7 Typed handoffs, and the field everyone forgets

```python
class Handoff(BaseModel):
    to: Literal["policy", "data", "analyst"]
    task: str                # a complete, standalone instruction
    context_summary: str     # what has been established so far
    already_tried: list[str] # <- the anti-loop mechanism
    expected_output: str     # what "done" looks like for this sub-task
```

Why prose handoffs fail is mechanical, not aesthetic. Prose is unconstrained, so the model writes
what feels natural — and what feels natural is findings. **`already_tried` is a schema slot for
negative information**, which is exactly what §2.3 says gets dropped, and a required field with a
description is an instruction the model can't quietly skip (Day 2 §2.4).

Three more things typing buys that prose can't:

- **Testable.** Assert `already_tried` grows monotonically across the run. Assert no tool
  fingerprint appears under two agents. Both are deterministic tests over non-deterministic output
  — Day 2's invariant pattern.
- **`task` must be standalone.** The field description says so, which forces the supervisor to
  resolve pronouns and carry the entities. "Check their scorecard" becomes "Compute the composite
  scorecard band for carrier Ridgeline Freight."
- **`expected_output` is a termination condition** for the worker. Without it, workers over-run —
  they don't know what "done" looks like, so they keep going until `max_steps`.

### 2.8 Plan-and-execute vs. supervisor

Two shapes, and the lab builds both.

| | Supervisor | Plan-and-execute |
|---|---|---|
| When the plan is made | Re-decided every step | Once, up front |
| Adaptivity | High | Low until the reflect step |
| Parallelism | Hard — next call depends on the last | Easy — independent sub-tasks fan out |
| Cost predictability | Poor | Good; you can price the plan before running it |
| Steerability | None mid-run | **You can show the user the plan and let them edit it** |

Plan-and-execute is the deep-research shape: plan 4–8 sub-questions, fan out under a `Semaphore(4)`
(Day 2 §2.6), reflect once on gaps and contradictions, synthesise, verify citations. Showing the
plan before executing is a UX decision with a large trust payoff that costs nothing.

Note what "reflect once, max twice" is: **Day 7's termination limits applied at the plan level
instead of the step level.** Same problem one layer up, and the same rule — bound it by cost and
wall clock too, because a reflection round is a whole fan-out.

### 2.9 The honest argument

Most multi-agent systems should be one agent with better tools. Here is the version you can defend.

**Reasons that are real:**

1. **Tool-list degradation.** Past some number of tools, one agent's selection accuracy falls. The
   effect is real; the threshold is model-dependent and I'd distrust any specific number you're
   quoted. Splitting gives each agent a short list.
2. **Genuinely different system prompts or models.** A worker that needs a long domain preamble, a
   worker that needs a cheap fast model, a worker that needs a reasoning model. One agent can't be
   three configurations.
3. **Permission boundaries / blast radius.** The agent that may write to the TMS should have three
   auditable tools and a separate credential. This one is underrated and it's the argument that
   lands with a security team.

**Reasons that are not reasons:** the task has multiple steps (that's a pipeline); it feels like a
team; parallelism (you get that from `asyncio.gather` over independent sub-tasks inside *one*
agent — that's Day 8's decomposition); the demo looks more impressive.

---

## 3. Worked example — on paper

> **Task.** *"Carrier Ridgeline Freight has an FTA of 83% on DAL→CHI for two quarters and we've
> paid $4,200 in detention on that lane this quarter. What's their scorecard band, what happens to
> their primary position, and what should we do at the next bid?"*
> Ridgeline's composite is **78.5**. Pricing: **$3/M input, $15/M output.**

**Q1.** Answer the domain question. Band and consequence? Tender-acceptance consequence? And
given the $650 per-event detention cap, what is the *minimum* number of detention events consistent
with $4,200? Which worker owns each of those three facts?

**Q2 — Config B, one agent, all 8 tools.** System 300 + tool schemas 1,100 = base 1,400, plus an
80-token task. 7 steps; observations average 700 tokens; outputs 60 per step except a 400-token
final answer. Total input, total output, cost?

**Q3 — Config A, supervisor + 3 workers.**
*Supervisor:* system 350 + 3 worker-tool schemas 400 = 750, plus task 80. 4 steps (3 delegations +
assembly). Worker summaries come back at 350 tokens. Outputs: 120 per delegation, 400 final.
*Workers:* each has system 300 + own tools 450 + handoff payload 200 = base 950; outputs 60 per
step plus a 350-token summary.
· PolicyAgent 4 steps, observations 900 · DataAgent 3 steps, observations 250 · AnalystAgent
3 steps, observations 120.
Total input, total output, cost? Ratio to Config B?

**Q4.** The trace shows AnalystAgent ran a policy search PolicyAgent had already run — 2 extra
steps with 900-token observations, before its own two steps. Recompute AnalystAgent and the run
total. New ratio to B? At 40,000 questions/month, what does that delta cost?

**Q5.** Wall clock. Model latency 1.2 s/step for the supervisor and analyst, 1.4 s for policy,
1.3 s for data; assembly 1.5 s. Policy and Data are independent and run concurrently; Analyst
depends on both. Critical path for Config A (clean run)? For Config B at 1.4 s/step plus 0.5 s of
tool time?

**Q6.** Which failure mode caused Q4's delta, which trace metric detects it, and which `Handoff`
field prevents it?

**Q7.** Config A costs more and runs slower. Name the condition under which you ship it anyway.

<details>
<summary><b>Answers — do the arithmetic first</b></summary>

**Q1.** Composite 78.5 → **Silver (70–79)** → **quarterly business review required** (doc 06).
FTA 83% is below 85% for two consecutive quarters → **Lane Review, and they may be removed from
primary position at the next bid cycle** (doc 01). Minimum detention events: the per-event cap is
$650, so $4,200 / $650 = 6.46 → **at least 7 events** (and more if any event fell under the cap).
Ownership: bands and Lane Review → **PolicyAgent**; the 78.5 and the $4,200 → **DataAgent**; the
"at least 7 events" inference and the bid recommendation → **AnalystAgent**. Three facts, three
owners — this task genuinely needs the split, which is why the lab chose it.

**Q2.** Step *k* input = 1,480 + 760(k−1): 1,480 · 2,240 · 3,000 · 3,760 · 4,520 · 5,280 · 6,040 =
**26,320**. Output = 6×60 + 400 = **760**.
Cost = 26,320×$3/M + 760×$15/M = $0.07896 + $0.0114 = **$0.0904**.

**Q3.** Supervisor: base 830, step input = 830 + 470(k−1) → 830 · 1,300 · 1,770 · 2,240 =
**6,140**; output 3×120 + 400 = 760.
PolicyAgent: 950 · 1,910 · 2,870 · 3,830 = **9,560**; output 3×60 + 350 = 530.
DataAgent: 950 · 1,260 · 1,570 = **3,780**; output 470.
AnalystAgent: 950 · 1,130 · 1,310 = **3,390**; output 470.
Total input **22,870**, output **2,230**. Cost = $0.06861 + $0.03345 = **$0.1021**.
Ratio to B = **1.13×**. Notice that's *lower* than most people guess — worker isolation genuinely
saves input tokens even while adding calls. Say this in a teach-back; it's the credible half of the
argument and it makes the next number land harder.

**Q4.** AnalystAgent now: 950 · 1,910 · 2,870 · 3,050 · 3,230 = **12,010**; output 4×60 + 350 = 590.
Run total input = 6,140 + 9,560 + 3,780 + 12,010 = **31,490**; output **2,350**.
Cost = $0.09447 + $0.03525 = **$0.1297**. Ratio to B = **1.43×**.
Delta vs. the clean run = $0.0276 per query; vs. Config B = $0.0393. At 40,000 queries/month that
is **$1,574/month** attributable to two duplicated steps — and neither agent's individual trace
looks wrong. This is §2.3 with a price on it, and it's the single most useful number in today's
module.

**Q5.** Config A critical path: supervisor plan 1.2 + max(policy 4×1.4 = 5.6, data 3×1.3 = 3.9) +
analyst 3×1.2 = 3.6 + assembly 1.5 = **11.9 s**. Fully serial it would be 15.8 s, so concurrency
buys 3.9 s.
Config B: 7×1.4 + 0.5 = **10.3 s**. **The single agent is also faster**, because the supervisor's
plan and assembly steps are pure overhead on the critical path. Expect this. Report it.

**Q6.** Context loss at handoff (§2.3). Detected by counting tool-call fingerprints
`(tool, canonical_args)` that appear under more than one agent — here it's 2, and it should be 0.
Prevented by **`already_tried`** in the `Handoff`, which is the schema slot for exactly the negative
information a prose summary drops.

**Q7.** When it's *right* and B is wrong. Cost and latency only decide between two correct answers.
Ship A when B's tool list is long enough to degrade selection, when the workers need different
prompts or models, or when one worker needs a permission boundary — §2.9. If B produces the same
answer at 0.70× the cost and 0.87× the latency, **B wins and that's the finding.** Write it down.

</details>

---

## 4. What people get wrong

**"Multi-agent means multiple models or multiple processes."**
One process, one heap, usually one event loop. A worker is a tool whose implementation is another
Day 7 loop.

**"Agents collaborate."**
They don't communicate. One agent's output is appended to another's context. There is no
negotiation, no shared belief state, no back-channel, and no agent can interrupt another.

**"The supervisor knows what the workers did."**
It knows what they *reported*. That gap is §2.3, and it's the difference between a 1.13× system and
a 1.43× one.

**"More agents means more capability."**
Every split adds a lossy boundary. Capability comes from tools and context, and splitting reduces
context by construction.

**"A swarm is more robust — no single point of failure."**
Inverted. There's no partition to survive; it's one process. Hub-and-spoke is easier to operate
*because* there's a single decision point. This is legibility, not fault tolerance.

**"Handoff summaries are lossless if the model is good."**
They systematically drop negative information, because summarisers report findings and non-findings
don't read like findings. Model quality doesn't change the incentive.

**"Cost scales linearly with agent count."**
A sum of quadratics plus the supervisor's own quadratic. And every duplicated step lands *inside*
one of them.

**"`already_tried` is a nice-to-have."**
It's the anti-loop mechanism and the only structural fix for the dominant failure mode. §3 Q4
prices its absence at $1,574/month.

**"Multi-agent is how you get parallelism."**
You get parallelism from `asyncio.gather` over independent sub-tasks inside one agent. That's Day
8's decomposition and it needs no second agent.

**"The more impressive demo is the better system."**
Demoing multi-agent on a task one agent handles is the fastest way to lose a technical audience —
someone always asks what the second agent contributed.

---

## 5. The trainer's angle

**The analogy that lands, and it's exact:** splitting one agent into three is splitting a monolith
into microservices. You do not get a smarter system. You get explicit ownership, independent
configuration, blast-radius containment — and in exchange, serialisation at every boundary, added
latency, and invariants nobody owns. The reasons to do it are the same reasons: team boundaries
(here: prompt, model, and permission boundaries), not "the code has multiple steps."

Then push the analogy one notch further, because this is where it earns its keep: **the handoff is
a DTO, and your DTO has no field for what the caller ruled out.** A rich internal state got
serialised into four sentences, and the fields that survived are the ones a summariser thinks are
interesting. `already_tried` is you adding the missing field to the DTO. For someone who has spent
twenty-three years watching information die at service boundaries, that lands in one sentence.

**The demo that makes it click** — and it's the most convincing artifact in the lesson: two traces
side by side, PolicyAgent's step 3 and AnalystAgent's step 2, with identical tool fingerprints
highlighted. The room sees the same search run twice, sees that each agent's trace looks entirely
reasonable on its own, and sees the token count. Then add `already_tried`, re-run, and show the step
count drop. Before-and-after on a metric you defined is worth more than any diagram.

**The predictive question:** *"This task needs a policy lookup, a data query, and arithmetic. How
much does the three-agent version cost versus the one-agent version? Write down two numbers."* Then
reveal §3 Q2–Q3: the clean multi-agent run is only 1.13×, which is *more* favourable than most
rooms expect — and then Q4 takes it to 1.43× for a reason they didn't consider. Being surprised
twice in opposite directions is what makes a lesson stick.

**The question a sharp student will ask:** *"Anthropic published a multi-agent research system that
substantially beat single-agent. Doesn't that contradict everything you just said?"*

> No — read what it was *for*. Breadth-first research over many independent sources is the one shape
> where fan-out genuinely wins, because the sub-tasks are independent, there's no bridging entity,
> and the extra tokens buy parallel exploration rather than repeated context. They were also candid
> that it burned on the order of fifteen times the tokens of a chat interaction, and that some
> tasks can't be parallelised at all. That's the trade, stated honestly by the people who shipped
> it. Now look at our question: "what's Ridgeline's band and what do we do at the next bid" is three
> lookups and a calculation with a dependency chain. It is not breadth-first research. Match the
> topology to the shape of the work, not to the impressiveness of the demo — and notice that
> "should we convert Dallas–Chicago to intermodal?" *is* breadth-first, which is why the lab makes
> you build the research agent with a different shape from the supervisor.

---

## 6. Self-check

Cover the answers.

1. Mechanically, what is a worker agent? What does the supervisor actually see of its work?
2. Name the three topologies and the condition each is right for.
3. Why is a swarm *not* more robust than hub-and-spoke? Answer in terms of what's actually running.
4. What specific class of information is lost at a handoff, and why is it lost systematically?
5. How do you *measure* context loss? What should the number be?
6. What is responsibility diffusion, and what's the fix in one sentence?
7. What's the mirror-image failure of a supervisor, and what does it tell you about your prompts?
8. Why isn't multi-agent cost linear in agent count? Write the shape.
9. Name one way worker isolation makes cost *better*, and one way it makes it worse.
10. What is the blackboard's real failure mode — and what it is *not*?
11. Why does `already_tried` work? Name the two invariant tests typed handoffs enable.
12. Give the three real reasons to use more than one agent, and two reasons that aren't reasons.

<details>
<summary><b>Answers</b></summary>

1. A tool whose implementation is another Day 7 loop. The supervisor sees only the worker's final
   summary as an observation — never its steps.
2. Supervisor/worker: sub-tasks vary per question; the default. Sequential pipeline: stages known
   and ordered; cheapest and most testable. Peer handoff/swarm: routing genuinely can't be
   centralised; rare.
3. It's all one process, one heap. There's no partition to survive, so distributed control buys no
   fault tolerance and costs legibility. Hub-and-spoke is easier *because* of the single point.
4. **Negative information** — what was tried and failed, what was ruled out, what error a tool
   returned. Lost systematically because summarisers are trained to report findings, and
   non-findings don't read like findings.
5. Fingerprint every tool call as `(tool, canonical_json(args))` and count fingerprints appearing
   under more than one agent in a run. It should be **zero**.
6. Every agent assumes someone else verified the fact; nobody did. Fix: exactly one named agent
   owns verification, named in every other system prompt, running last.
7. A supervisor that does the work itself instead of delegating. It means your worker descriptions
   are bad — and worker descriptions are tool descriptions (Day 7 §2.7).
8. `Σ_agents [nᵢ·Bᵢ + oᵢ·nᵢ(nᵢ−1)/2]` plus the supervisor's own quadratic. A sum of quadratics, and
   duplicated steps land inside one.
9. Better: each worker has a small base `B` (narrow prompt, few tools) and the supervisor's
   observations are short summaries, not chunk sets. Worse: every duplicated step is re-sent by
   every later step in that agent's run.
10. Not race conditions — you're in one process. **Distraction and prompt bloat**: every agent sees
    state it doesn't need, costing tokens and degrading tool selection.
11. It's a required schema slot for exactly the negative information prose drops, and a required
    field with a description is an instruction the model can't quietly skip. Tests: `already_tried`
    grows monotonically; no tool fingerprint appears under two agents.
12. Real: tool-list degradation; genuinely different prompts/models; permission boundaries and blast
    radius. Not reasons: the task has multiple steps; you want parallelism (use `asyncio.gather`
    inside one agent); it feels like a team; the demo looks better.

</details>

**Scored below 9?** Re-read §2.3 and §2.7. The lab's `Handoff` model and the evidence that
`already_tried` cut your step count are exactly those two, and the three-way comparison is
uninterpretable without the context-loss metric.

---

## 7. Going deeper (optional)

- *Building Effective Agents* — Schluntz & Zhang, Anthropic engineering blog, 2024. Read the
  workflow patterns section before the agent section; it's the best short statement of §2.9.
- *How we built our multi-agent research system* — Anthropic engineering, 2025. The honest
  counter-case to today's argument, including the token multiple and which tasks don't parallelise.
- *Why Do Multi-Agent LLM Systems Fail?* — Cemri et al., 2025 (UC Berkeley). An empirical failure
  taxonomy across real frameworks; §2.3–2.5 here are three of its categories, and the paper has
  more.
- *AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation* — Wu et al., 2023. The
  conversational-topology framing, and a good example of how easy it is to build a system you can't
  debug.
- *MetaGPT: Meta Programming for a Multi-Agent Collaborative Framework* — Hong et al., 2023.
  Encoding standard operating procedures as topology.
- *The Contract Net Protocol* — Reid G. Smith, IEEE Transactions on Computers, 1980. Supervisor/
  worker with typed task announcements and bids, forty-five years ago. Worth twenty minutes purely
  for the perspective it gives you in a room full of people who think this is new.

---

**Now go to `labs/DAY_09.md`.** The lab builds on §2.2 (three topologies — you implement the
supervisor and compare against a pipeline), §2.3 (instrument the fingerprint metric before you need
it), §2.5 (per-agent cost accounting from line one), §2.7 (the typed `Handoff` and the evidence
`already_tried` earned its place), and §2.8 (plan-and-execute for the deep-research agent).
