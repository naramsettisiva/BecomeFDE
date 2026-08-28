# Progress

Tick as you go. Five hours a day, 24 working days.
Runs Thu Aug 27 → Tue Sep 29.

Each day is **learn then build**: read `learn/DAY_NN_LEARN.md` and take its self-check
before opening the lab. The sub-line under each day tracks that.

## Week 1 — Foundations (Aug 27 – Sep 3)

- [ ] **Day 01** · Thu Aug 27 · Environment, first tokens, the discipline
  - [ ] read `learn/DAY_01_LEARN.md` + self-check
- [ ] **Day 02** · Fri Aug 28 · Python for AI engineers: structure, async, failure
  - [ ] read `learn/DAY_02_LEARN.md` + self-check
- [ ] **Day 03** · Mon Aug 31 · Embeddings and vector search, by hand
  - [ ] read `learn/DAY_03_LEARN.md` + self-check
- [ ] **Day 04** · Tue Sep 1 · RAG v1, end to end
  - [ ] read `learn/DAY_04_LEARN.md` + self-check
- [ ] **Day 05** · Wed Sep 2 · Evals: making "it seems better" into a number
  - [ ] read `learn/DAY_05_LEARN.md` + self-check
- [ ] **Day 06** · Thu Sep 3 · **Capstone** — ship it, demo it, teach it
  - [ ] read `learn/DAY_06_LEARN.md` + self-check

## Week 2 — Agents (Sep 4 – Sep 11)

- [ ] **Day 07** · Fri Sep 4 · Tool calling and the agent loop, from first principles
  - [ ] read `learn/DAY_07_LEARN.md` + self-check
- [ ] **Day 08** · Mon Sep 7 · Agentic RAG: routing, decomposition, self-correction
  - [ ] read `learn/DAY_08_LEARN.md` + self-check
- [ ] **Day 09** · Tue Sep 8 · Multi-agent: supervisors, handoffs, deep research
  - [ ] read `learn/DAY_09_LEARN.md` + self-check
- [ ] **Day 10** · Wed Sep 9 · Memory and context engineering
  - [ ] read `learn/DAY_10_LEARN.md` + self-check
- [ ] **Day 11** · Thu Sep 10 · MCP, tools, and skills
  - [ ] read `learn/DAY_11_LEARN.md` + self-check
- [ ] **Day 12** · Fri Sep 11 · **Capstone** — the agentic system, integrated
  - [ ] read `learn/DAY_12_LEARN.md` + self-check

## Week 3 — Production (Sep 14 – Sep 21)

- [ ] **Day 13** · Mon Sep 14 · Evals at depth: synthetic data, judges, regression gates
  - [ ] read `learn/DAY_13_LEARN.md` + self-check
- [ ] **Day 14** · Tue Sep 15 · Advanced retrieval: hybrid, rerank, context engineering
  - [ ] read `learn/DAY_14_LEARN.md` + self-check
- [ ] **Day 15** · Wed Sep 16 · Production I: serving, streaming, caching, guardrails
  - [ ] read `learn/DAY_15_LEARN.md` + self-check
- [ ] **Day 16** · Thu Sep 17 · Observability: tracing, metrics, the feedback loop
  - [ ] read `learn/DAY_16_LEARN.md` + self-check
- [ ] **Day 17** · Fri Sep 18 · Deployment: Docker, cloud, CI/CD, handover
  - [ ] read `learn/DAY_17_LEARN.md` + self-check
- [ ] **Day 18** · Mon Sep 21 · Production II: cost, performance, adversarial security
  - [ ] read `learn/DAY_18_LEARN.md` + self-check

## Week 4 — The craft (Sep 22 – Sep 29)

- [ ] **Day 19** · Tue Sep 22 · The FDE craft: discovery, scoping, the first two weeks
  - [ ] read `learn/DAY_19_LEARN.md` + self-check
- [ ] **Day 20** · Wed Sep 23 · **Capstone build 1** — skeleton to working
  - [ ] read `learn/DAY_20_LEARN.md` + self-check
- [ ] **Day 21** · Thu Sep 24 · **Capstone build 2** — harden, evaluate, package
  - [ ] read `learn/DAY_21_LEARN.md` + self-check
- [ ] **Day 22** · Fri Sep 25 · The trainer craft: designing curriculum that sticks
  - [ ] read `learn/DAY_22_LEARN.md` + self-check
- [ ] **Day 23** · Mon Sep 28 · Deliver it live: teaching under real conditions
  - [ ] read `learn/DAY_23_LEARN.md` + self-check
- [ ] **Day 24** · Tue Sep 29 · Demo day, portfolio, and the 90-day launch
  - [ ] read `learn/DAY_24_LEARN.md` + self-check

---

## Teach-back log

| # | Day | Topic | Length | Self-grade | Recurring flaw noted |
|---|---|---|---|---|---|
| 1 | 01 | Why your first LLM call needs a seam | 5 min | | |
| 2 | 02 | Three ways to get JSON out of an LLM | 6–8 min | | |
| 3 | 03 | Right document, wrong paragraph | 8 min | | |
| 4 | 04 | The four-clause RAG contract | 8–10 min | | |
| 5 | 05 | Your eval is lying to you | 10 min | | |
| 6 | 06 | **Full lesson** — RAG you can defend | 20 min | | |
| 7 | 07 | An agent is a while-loop | 10 min | | |
| 8 | 08 | Agentic RAG is four patterns | 10 min | | |
| 9 | 09 | You probably don't need multi-agent | 10 min | | |
| 10 | 10 | Bigger context ≠ less context engineering | 10 min | | |
| 11 | 11 | MCP in fifteen minutes | 10 min | | |
| 12 | 12 | **Architecture review** | 25 min | | |
| 13 | 13 | Your eval flakes because of the threshold | 12 min | | |
| 14 | 14 | Retrieval ablation: what each technique buys | 12 min | | |
| 15 | 15 | Your agent is now an HTTP service | 12 min | | |
| 16 | 16 | Find the bad answer from Tuesday | 12 min | | |
| 17 | 17 | Deploying inside someone else's VPC | 12 min | | |
| 18 | 18 | Someone will put instructions in your documents | 12 min | | |
| 19 | 19 | Scope it with an eval, not a spec | 12 min | | |
| 20 | 23 | **Live delivery, one take** | 60 min | | |
| 21 | 24 | **Demo day** | 8 min | | |

---

## Scorecard history

Record every scorecard run so the curve is visible on Day 24.

| Date | Day | Recall@5 | Faithfulness | Citation verified | Cost/query | p95 latency | Note |
|---|---|---|---|---|---|---|---|
| Sep 2 | 05 | | | | | | first baseline |
| Sep 7 | 08 | | | | | | agentic patterns |
| Sep 11 | 12 | | | | | | integrated |
| Sep 14 | 13 | | | | | | 250-case suite |
| Sep 15 | 14 | | | | | | 200-doc corpus |
| Sep 21 | 18 | | | | | | post-optimisation |
| Sep 24 | 21 | | | | | | capstone final |

---

## Cost tracker

Soft budget for the month: **$100**. Run `python -m fdekit.cost` any time.

| Week | Est. | Actual |
|---|---|---|
| 1 | $3–7 | |
| 2 | $10–20 | |
| 3 | $16–34 | |
| 4 | $10–22 | |
| **Total** | **$39–83** | |
