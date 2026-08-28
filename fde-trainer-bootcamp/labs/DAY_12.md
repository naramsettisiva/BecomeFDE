# Day 12 — Week 2 Capstone: The Agentic System, Integrated

**Fri Sep 11, 2026** · Week 2 · Maps to: **Modules 03 + 07** · Backend: **local** + `[PAID]` · Est. cost: **$3–5**

> **Before you start — read `learn/DAY_12_LEARN.md` (0:45).**
> Integration effects, p95, and the architecture-review format. The lab below assumes it and does not re-explain it.


---

## Why today matters

**FDE lens.** You've built six things in isolation. Today you integrate them, and
integration is where the real problems live: state that doesn't flow, costs that compound,
latency that stacks, and a failure in step 4 that surfaces as a weird answer in step 9.
This is what "forward deployed" actually feels like.

**Trainer lens.** Your second full lesson. Week 1's was a tutorial. This one is an
**architecture review** — a different and harder teaching format, and the one you'll use
most with senior audiences.

---

## Objectives

1. Integrate agentic RAG + multi-agent + memory + MCP into one coherent system.
2. Evaluate the *whole system* end to end, not the parts.
3. Build a trace viewer you can put on screen in front of a client.
4. Deliver a 25-minute architecture-review lesson.

---

## Schedule (5:00)

| Block | Time | What |
|---|---|---|
| 0 | 0:30 | Warm-up: Week 2 recall |
| 1 | 0:45 | **Learn** — `learn/DAY_12_LEARN.md` |
| 2 | 1:30 | Build: integrate + trace viewer |
| 3 | 0:45 | Evaluate the integrated system |
| 4 | 1:00 | Teach-back #12 — architecture review |
| 5 | 0:30 | Week 2 retro |

---

## Block 0 — Week 2 recall (0:30)

<!--cards-->
> **Cards first — 5 minutes.** Open **Warm-up drill** in the sidebar of `fde-bootcamp.html`.
> It deals you every card that is due from the days you have finished, hardest box first, and
> it is capped at 20 so it stays a drill. Cards you miss come back tomorrow; cards you know
> go 1 → 2 → 4 → 8 → 16 days out. Then do the recall below, closed book.
<!--/cards-->


Closed book:

1. The agent loop, five steps.
2. Difference in tool-call wire format between OpenAI and Anthropic.
3. Four agentic-RAG patterns; the bucket each fixes; the cost each adds.
4. Three multi-agent topologies; the decision rule for using more than one agent.
5. The three multi-agent failure modes.
6. Four memory types; which is most skipped.
7. What gets evicted first from your context budget, and why.
8. Which compaction strategy loses negations.
9. MCP's three primitives and who controls each.
10. The stdio gotcha that silently breaks an MCP server.
11. Your reliability ceiling from the needle experiment.
12. Best quality-per-dollar strategy from the Day 8 bake-off.

---

## Block 1 — Learn (0:45)

**Read `learn/DAY_12_LEARN.md` and work its examples before continuing.**
Take the self-check at the end. This is a build day, so the module is short and deliberately practical — read it once, properly, then build.

---

## Block 2 — Integrate (1:30)

`capstone/week2/` — the **Freight Operations Copilot**.

```
                       ┌──────────────────┐
   user ──────────────►│  Chainlit UI     │◄──── trace viewer pane
                       └────────┬─────────┘
                                ▼
                       ┌──────────────────┐
                       │   SUPERVISOR     │◄── procedural memory (learned rules)
                       │   + router       │◄── semantic memory (org facts)
                       └──┬────┬────┬─────┘◄── episodic memory (this session)
              ┌───────────┘    │    └────────────┐
              ▼                ▼                 ▼
      ┌──────────────┐  ┌────────────┐  ┌────────────────┐
      │ PolicyAgent  │  │ DataAgent  │  │ AnalystAgent   │
      │ FullStack RAG│  │ MCP: TMS   │  │ calc + compare │
      └──────────────┘  └────────────┘  └────────────────┘
              │                │                 │
              └────────────────┴─────────────────┘
                               ▼
                    ┌────────────────────┐
                    │ verification layer │  substring-check every citation
                    └────────────────────┘
```

Requirements:

- [ ] Router sends simple lookups straight to single-shot RAG (don't pay for the supervisor when you don't need it)
- [ ] Data access goes through **your MCP server**, not direct function calls — this proves the abstraction
- [ ] Memory persists across turns; semantic facts survive a restart
- [ ] Every answer carries verified citations; unverified claims are visibly flagged
- [ ] Full budget enforcement: max steps, max cost, max wall clock, with clean partial answers
- [ ] Complete trace captured per request and rendered in the UI

### The trace viewer (spend 45 min here — it's worth it)

```
Request 7f3a · 6.8s · $0.0071 · 11 LLM calls
├─ route              120ms   $0.0000  → "multi_hop" → supervisor
├─ supervisor plan    890ms   $0.0012  → 3 sub-tasks
├─ ▸ policy           2.1s    $0.0028  → 2 retrievals, 4 chunks, 2 citations
│   ├─ rewrite        310ms   $0.0002  "FTA threshold consecutive quarters"
│   ├─ retrieve        45ms   $0.0000  4 chunks (0.87, 0.81, 0.62, 0.55)
│   ├─ grade          420ms   $0.0004  3/4 relevant
│   └─ generate       1.3s    $0.0022  ✓ 2 citations verified
├─ ▸ data             980ms   $0.0009  → mcp:carrier_scorecard(Ridgeline, 2026-08)
├─ ▸ analyst          2.4s    $0.0019  → band=Silver, quarterly business review
└─ verify              8ms    $0.0000  3/3 citations verified ✓
```

Collapsible. Clickable to see the exact prompt at each node. **This is the artifact that
sells you.** In a room full of people demoing chat boxes, showing the machinery — with
timings and dollars attached — is what makes a technical buyer trust you. It's also how
you debug your own system at 11pm.

---

## Block 3 — Evaluate the whole system (0:45)

Extend the golden set to **80 cases**, adding 20 that require the integrated behaviour:
multi-turn references, data + policy combined, questions requiring refusal after a
retrieval attempt.

Run the full scorecard. Then answer:

1. Did integration *regress* anything vs. the best individual component? (It usually
   does — routing sends some queries down a worse path. Find it.)
2. What's the cost per query at p50 and p95? The p95 is what blows up a budget.
3. Where is p95 latency spent? Attribute it to a node, not "the LLM."
4. What fraction of requests hit a budget limit? If it's >5%, your limits are wrong or
   your agent is inefficient — determine which.

Write `evals/day12_integrated_scorecard.md`.

---

## Block 4 — Teach-back #12: architecture review (1:00)

Record **25 minutes**: *"Architecture review: a production agentic system, node by node."*
`teaching/recordings/day_12_lesson.mov` + outline in `teaching/lesson_02_architecture.md`

This is a different format from Day 6. You're not teaching someone to build; you're
walking a senior audience through a system and justifying every decision. Structure:

| Time | Beat |
|---|---|
| 0–2 | The requirement, in business terms. What question does this answer, for whom, how often |
| 2–5 | The architecture diagram. Every box, one sentence |
| 5–10 | **Three decisions and their alternatives.** Why route before the supervisor. Why MCP instead of direct calls. Why verify citations rather than trust them. For each: what you gave up |
| 10–16 | Live trace walkthrough on a real question. Point at timings and dollars |
| 16–20 | **What's wrong with it.** Where it's slow, where it's fragile, what you'd fix with two more weeks |
| 20–24 | The numbers: scorecard, p50/p95 cost and latency, monthly projection at 10k queries |
| 24–25 | What you'd need to productionise |

The 16–20 segment is what makes this credible. Any consultant can present a diagram.
Presenting its weaknesses, unprompted, is what senior audiences actually respond to.

Watch it back and grade it. Different rubric from Day 6:

| Dimension | 1–5 |
|---|---|
| Did you justify decisions with alternatives, not just describe them? | |
| Could a non-engineer follow the first 5 minutes? | |
| Did you name real weaknesses without hedging? | |
| Were the numbers specific and sourced? | |
| Did you avoid jargon you hadn't defined? | |
| Would a VP fund this after watching? | |

---

## Block 5 — Week 2 retro (0:30)

In `LEARNING_LOG.md`:

1. Scorecard: Day 5 → Day 8 → Day 12. Plot it.
2. Cost per query across the same three points. Plot that too. (Both curves went up.
   That's the real story of Week 2 and you should be able to narrate it.)
3. Your Week 2 teaching focus from the Day 6 retro — did it improve? Watch 60 seconds of
   Day 6 and 60 seconds of Day 12 back to back. Be specific about what changed.
4. Pick your Week 3 teaching focus.
5. Time honesty. Still 5 hours? If you're consistently at 6+, say so — Week 3 has more
   optional material than required and I'd rather cut it deliberately than have you burn out.

```bash
git add -A && git commit -m "Week 2 capstone: integrated Freight Ops Copilot with trace viewer" && git push
```

---

## Done when

- [ ] Integrated system running, all four subsystems wired
- [ ] Data access flows through MCP, not direct calls
- [ ] Trace viewer showing per-node timing, cost, and prompts
- [ ] 80-case golden set, integrated scorecard, p50/p95 analysis
- [ ] At least one regression from integration identified and explained
- [ ] 25-minute architecture review recorded and graded
- [ ] Week 2 retro with two plotted curves

---

## Week 2 is done

You now have an agentic system with memory, tool portability, measured quality, and a
trace you can defend in front of a technical buyer.

**Week 3 is production.** Everything you've built runs on your laptop and would fall over
under any real load. Days 13–18 fix that: deeper evals, better retrieval, a real server,
observability, deployment, cost modelling, and security.

Tonight, 10 minutes: skim `labs/DAY_13.md` concept section.
