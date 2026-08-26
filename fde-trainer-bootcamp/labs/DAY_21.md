# Day 21 — Capstone Build, Day 2: Harden, Evaluate, Package

**Thu Sep 17, 2026** · Week 4 · Maps to: **Modules 07 + 08 + 09** · Backend: **all** · Est. cost: **$5–10**

> **Before you start — read `learn/DAY_21_LEARN.md` (0:30).**
> Defensibility, the teardown question, the case study. The lab below assumes it and does not re-explain it.


---

## Why today matters

Yesterday you proved it works. Today you make it defensible. The gap between those two is
the gap between a bootcamp project and something a client would pay for — and it's the gap
any serious reviewer, interviewer, or buyer will probe first.

Everything you built in Week 3 exists to be applied today: guardrails, tracing, cost
model, deployment, evals. This is the integration exam.

---

## Objectives

1. Close the eval gap — get the capstone scorecard to a number you'd show a client.
2. Apply production hardening: guardrails, tracing, cost caps, graceful failure.
3. Deploy properly, with a demo mode that survives a stranger clicking it.
4. Write the case study — the artifact that outlives the code.

---

## Schedule (5:00)

| Block | Time | What |
|---|---|---|
| 0 | 0:15 | Triage `TOMORROW.md` |
| 1 | 0:30 | **Learn** — `learn/DAY_21_LEARN.md` |
| 2 | 1:15 | Close the eval gap |
| 3 | 1:15 | Production hardening |
| 4 | 0:45 | Deploy + demo mode |
| 5 | 1:00 | Case study + portfolio |

---

## Block 0 — Triage (0:15)

Open `TOMORROW.md`. Move at least two items from SHOULD to WON'T **right now**, before you
start. You will not get through the list, and choosing the cuts while you're fresh produces
better choices than cutting at 5pm in a panic.

Confirm the demo moment still works. If it doesn't, that's the only thing you work on until
it does.

---

## Block 1 — Learn (0:30)

**Read `learn/DAY_21_LEARN.md` and work its examples before continuing.**
Take the self-check at the end. This is a build day, so the module is short and deliberately practical — read it once, properly, then build.

---

## Block 2 — Close the eval gap (1:15)

Run the full capstone eval. Sort failures by severity, then work down. Timebox each fix to
20 minutes; if it overruns, note it as a known limitation and move on. **A documented
limitation is a professional outcome. An overrun is not.**

Common failure classes and the actual fixes:

| Failure | Real fix |
|---|---|
| Number in the document ≠ number from the query | Almost always a join or date-boundary bug. Make the writer agent quote the query result verbatim and diff programmatically — don't let it retype numbers |
| Policy citation unverified | Chunk boundary severed the claim. Use parent-document retrieval (Day 14) for policy sections |
| Recommendations generic | Feed the writer the three worst *specific events* with dates, IDs, and amounts — not aggregates. Specificity in, specificity out |
| Good and bad carriers get similar reviews | Your prompt is describing structure, not judgement. Add explicit judgement criteria with thresholds, and require a stated verdict before the narrative |
| Tone wrong for external use | Separate the internal analysis from the external-facing draft. Two outputs, two prompts |

Target: **structural 100%, factual 100%, quality ≥ 4.0/5.** Factual at 100% is
non-negotiable — a document with a wrong number is worse than no document, and any domain
expert will find it in thirty seconds.

Record the final scorecard in `capstone/evals/FINAL_SCORECARD.md` with the baseline
alongside it, so the delta is visible.

---

## Block 3 — Production hardening (1:15)

Apply Week 3 systematically. Checklist:

- [ ] **Input guardrails** — carrier name validated against the known list (an unknown
      carrier should produce a clean error, not an invented review), quarter format checked
- [ ] **Output guardrails** — no PII in the external draft; citation verification blocking;
      a numeric-provenance check that fails the run rather than shipping an unsourced figure
- [ ] **Tracing** — full OTel trace per generation; `trace_id` printed in the document
      footer so any claim is auditable back to the run that made it
- [ ] **Cost cap** — hard per-generation limit; on breach, produce a partial document with
      an explicit "incomplete — budget exhausted" banner rather than failing silently
- [ ] **Timeouts** — layered, with a partial result on breach
- [ ] **Graceful degradation** — provider outage falls back to local model, document marked
      `degraded`, metric emitted
- [ ] **Idempotency** — regenerating the same carrier/quarter uses cache unless `--force`
- [ ] **Structured logging** with `trace_id` on every line

The trace_id in the document footer is a small touch with a large effect. When a carrier
disputes a figure six weeks later, you can reproduce the exact run. Say that in your demo;
people who've lived through a dispute will notice immediately.

---

## Block 4 — Deploy + demo mode (0:45)

- [ ] Deployed to your public URL, running the current build
- [ ] **Demo mode**: three pre-seeded carriers, a hard spend cap, rate limit per IP, and a
      graceful "demo budget exhausted, here's a pre-generated sample" fallback
- [ ] Landing page: what this is, who it's for, the 30-second explanation, and a link to
      the repo and case study
- [ ] Sample outputs viewable **without** running a generation (a stranger with 20 seconds
      should see the value; only interested people will wait 40 seconds)
- [ ] Test it on your phone, on cellular, logged out. Something will be broken. Fix it.

That last check catches more problems than any other five minutes you'll spend. Recruiters
and clients open links on phones.

---

## Block 5 — Case study (1:00)

`portfolio/case_studies/carrier-review-copilot.md`. This is the artifact that does the most
work for you over the next year — a recruiter or client reads it in three minutes and knows
whether to talk to you.

Structure — 1,000–1,500 words, and lead with the problem, never the tech:

**1. The problem (150 words).** A quarterly carrier business review takes an analyst
half a day: pulling scorecards, reconciling detention against policy, finding the specific
events behind a bad number, writing it up. With 60 contracted carriers that's 30 analyst-days
a quarter, and the reviews arrive late and inconsistent.

**2. The approach (200 words).** Eval-first. Before building, define what a good review is:
structural completeness, factual accuracy against source data, verified policy citations,
and specificity of recommendations. Then build to the metric.

**3. The architecture (250 words + diagram).** The multi-agent split and why. Why MCP for
data access. Why verification is a separate layer.

**4. The hard parts (300 words).** This is the section that gets you hired — pick three:
- Near-duplicate policy revisions returning contradictory thresholds, and how you handled it
- Generic recommendations, and the specific-events-in fix
- Indirect prompt injection through indexed carrier documents
- The appointment-timezone data trap and what it means for any OTIF claim

**5. The results (200 words).** Baseline vs. final scorecard. Time saved per review. Cost
per review vs. analyst time. Be specific and be honest about what's estimated.

**6. The limitations (150 words).** What it can't do. What needs human review before
anything goes to a carrier. What you'd build next. **Do not skip this section** — it is the
single strongest credibility signal in the document, and its absence is the tell that a
case study is marketing.

**7. Links.** Live demo, repo, 6-minute video (recorded tomorrow).

Also update `portfolio/README.md` — the top-level index a hiring manager lands on:

```markdown
# Siva Naramsetti — AI Forward Deployed Engineer

23 years in distributed systems and supply-chain platforms. Now building
production AI systems for freight and logistics operations.

## Featured: Carrier Performance Copilot
[live demo] · [case study] · [6-min video] · [repo]
Generates quarterly carrier business reviews from TMS data and policy
documents. Every number traced to its query, every policy claim cited and
verified. Half a day of analyst work in 40 seconds.

## Also built (24-day intensive, Aug–Sep 2026)
- Freight Ops Copilot — multi-agent RAG with memory, MCP, and full tracing
- MCP server for freight operations — [repo] · works in Claude Desktop
- Eval harness — 250-case suite, calibrated judge (κ=0.7x), CI regression gates
- Retrieval ablation study — six techniques measured on a 200-doc corpus
- Red-team report — 50 attacks across 5 classes, with defence-in-depth results

## Teaching
18 recorded technical sessions. [Curriculum] · [Sample lesson]
```

---

## Done when

- [ ] Structural and factual eval at 100%; quality ≥ 4.0
- [ ] All eight hardening items applied
- [ ] Deployed with demo mode, spend cap, and phone-tested
- [ ] Case study written including the limitations section
- [ ] Portfolio README updated
- [ ] Known limitations documented rather than hidden

---

## Trap list

- Fixing the fun bug instead of the severe one. Sort by severity.
- Shipping a document with an unsourced number. Fail the run instead.
- Demo mode with no spend cap on a public URL.
- A case study that leads with the architecture.
- Omitting limitations. Its absence is louder than its content.
- Not testing on a phone.

```bash
git add -A && git commit -m "Capstone day 2: hardened, evaluated, deployed, case study" && git push
```

---

Tomorrow you stop building and start teaching. Bring the case study — Day 22 mines it for
curriculum.
