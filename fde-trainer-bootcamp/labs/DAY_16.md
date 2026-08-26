# Day 16 — Observability: Tracing, Metrics, and the Feedback Loop

**Fri Sep 11, 2026** · Week 3 · Maps to: **Module 08 — Production I** · Backend: **local** + `[PAID]` · Est. cost: **$1–3**

> **Before you start — read `learn/DAY_16_LEARN.md` (1:15).**
> What an LLM trace must capture, and the feedback loop. The lab below assumes it and does not re-explain it.


---

## Why today matters

**FDE lens.** When a client says "it gave a bad answer yesterday afternoon," you need to
find that request, replay it, and see exactly which chunk was retrieved and what prompt
was sent. Without tracing you are debugging by anecdote. With it, you're the person who
resolves the complaint in ten minutes while everyone else is speculating. That moment —
more than any model work — is what gets an FDE renewed.

**Trainer lens.** Observability is treated as an afterthought in almost every AI
curriculum. Teaching it as a *first-class* topic, with a real trace on screen, is
differentiating.

---

## Objectives

1. Instrument the full stack with OpenTelemetry spans that capture LLM-specific attributes.
2. Run a local trace backend (Phoenix) and use it to diagnose a real regression.
3. Define the metric set that matters for LLM systems, and build the dashboard.
4. Close the loop: user feedback → labelled eval case → regression test.

---

## Schedule (5:00)

| Block | Time | What |
|---|---|---|
| 0 | 0:30 | Warm-up |
| 1 | 1:15 | **Learn** — `learn/DAY_16_LEARN.md` |
| 2 | 2:45 | Lab: instrument, dashboard, debug a planted regression, close the loop |
| 3 | 0:30 | Teach-back #16 |

---

## Block 0 — Warm-up (0:30)

1. Your three cache hit rates and the cost per query at each layer.
2. What did prompt prefix reordering save, and why did it save it?
3. Guardrail false-positive rate — and is it acceptable? Argue it.
4. Where's the knee in your load test, and what's the bottleneck?

---

## Block 1 — Learn (1:15)

**Read `learn/DAY_16_LEARN.md` and work its examples on paper before continuing.**
Take the self-check at the end. Anything you miss goes on a flashcard and into tomorrow's
warm-up. The material below consolidates the module — it is not a substitute for it.

### 1.1 What a trace must capture

A span per operation, nested. For LLM systems the attributes that matter are specific —
generic HTTP tracing is not enough:

```
span: request                    trace_id, session_id, tenant, route
├─ span: guard.input             verdict, rules_fired, redactions
├─ span: route                   decision, confidence, model, tokens
├─ span: retrieve                query, rewritten_query, k, candidate_count,
│                                chunk_ids, scores, retriever_config_hash
├─ span: rerank                  model, in_count, out_count, score_deltas
├─ span: llm.generate            model, temperature, prompt_tokens,
│                                completion_tokens, cost_usd, finish_reason,
│                                cache_hit, prompt_hash, FULL PROMPT, FULL RESPONSE
├─ span: verify                  citations_total, citations_verified
└─ span: guard.output            verdict, rules_fired
```

Two things people get wrong:

1. **Capture the full prompt and response.** Yes, it's large. Sample if you must (100% for
   errors and low-rated responses, 10% otherwise), but a trace without the prompt is
   nearly useless for the exact case you need it for. Budget for the storage; it's cheap
   relative to the debugging time it saves.
2. **Capture config hashes.** `retriever_config_hash`, `prompt_version`, `corpus_version`.
   When quality changes on a Tuesday, the first question is "what changed?" and these
   fields answer it in seconds instead of days.

Also: **PII in traces is a real compliance problem.** Redact at the span-writing boundary,
not later. Decide today, and be able to explain the decision — a client's privacy officer
will ask.

### 1.2 The metrics that matter

| Category | Metric | Why |
|---|---|---|
| **Traffic** | requests/sec, by route and tenant | Baseline |
| **Latency** | p50/p95/p99 **per node**, not just total | Total latency tells you there's a problem; per-node tells you where |
| **Cost** | $/request, $/tenant/day, tokens by model | The number your sponsor watches |
| **Quality** | citation verification rate, refusal rate, guard block rate | Your online proxies for quality |
| **Retrieval** | mean top-1 score, score distribution, zero-result rate | **Leading indicator.** Score distribution shifting = corpus or embedding drift |
| **Feedback** | thumbs up/down rate, comment rate | Ground truth, sparse |
| **Errors** | by type — timeout, provider, context overflow, guard | Never a single "error rate" |

The retrieval score *distribution* is the underrated one. If your mean top-1 score drops
from 0.81 to 0.68 over a week, something changed — a corpus update, an embedding model
version, a chunking change — and you'll see it days before users complain. Alert on it.

### 1.3 The feedback loop

This is the flywheel that makes a system improve after you leave:

```
user thumbs-down
   ↓
trace captured with full prompt + retrieved chunks
   ↓
triage: retrieval miss? generation error? correct-but-unhelpful? bad question?
   ↓
if a real failure → becomes a labelled eval case
   ↓
added to the golden set → the regression suite now covers it
   ↓
fix → CI gate proves it fixed and nothing else broke
```

Build the tooling for this today, even at zero traffic. On an engagement, having this in
place from week one is what turns "the AI is unreliable" into a burndown list — and it's
what a client's team can operate without you.

---

## Block 2 — Lab (2:45)

### 2.1 Instrument with OpenTelemetry (60 min)

`src/fdekit/tracing.py`:

```python
def init_tracing(service_name: str, endpoint: str | None = None) -> None: ...

@traced("llm.generate")               # decorator that captures LLM-specific attributes
def generate(...): ...

class SpanContext:
    """Ensures trace_id flows through async tasks and into the agent's step trace."""
```

Instrument every node in the Day 12/15 stack. Then run Phoenix locally:

```bash
python -m phoenix.server.main serve      # http://localhost:6006
```

Send 100 varied requests. Explore the traces in the UI. Find, by clicking:
- the slowest request, and which span dominated it
- a request where retrieval scored poorly but the model answered confidently anyway
- the most expensive request, and why it was expensive

Write what you found in `evals/day16_trace_findings.md`. You will find at least one thing
about your own system you didn't know. That's the point of the exercise.

### 2.2 Metrics + dashboard (45 min)

Prometheus metrics from `/metrics`, then a Grafana dashboard (or a simple Streamlit one —
faster, and you control it):

```
┌─── Traffic ────────┐ ┌─── Latency (p95, by node) ─┐
│                    │ │ retrieve ▁▂▁▁▂▁            │
│  req/min           │ │ rerank   ▂▂▃▂▂▂            │
└────────────────────┘ │ generate ▄▅▄▆▅▄            │
┌─── Cost ───────────┐ └────────────────────────────┘
│ $/hr  $/req        │ ┌─── Retrieval health ───────┐
│ by model           │ │ mean top-1 score  0.79     │
└────────────────────┘ │ zero-result rate  1.2%     │
┌─── Quality ────────┐ │ score distribution ▁▃▅▇▅▂  │
│ citation verif 94% │ └────────────────────────────┘
│ refusal rate    7% │ ┌─── Errors by type ─────────┐
│ guard blocks  0.8% │ │ timeout 3 · provider 1     │
└────────────────────┘ └────────────────────────────┘
```

Six panels, one screen. **Resist adding more.** A dashboard nobody reads is worse than
none, and the discipline of choosing six panels is itself the lesson.

### 2.3 Debug a planted regression (45 min)

Have a partner — or write a script that picks randomly and doesn't tell you — introduce
**one** of these into the codebase:

1. Chunk size changed 500 → 1500
2. Reranker silently disabled
3. Semantic cache threshold lowered 0.95 → 0.88
4. `k` lowered 5 → 2
5. Embedding model swapped for a different one (index not rebuilt — the nasty one)
6. Temperature raised 0.0 → 0.9
7. A guardrail rule made overly broad

Then diagnose it **using only the dashboard and traces** — no `git diff`. Time yourself.

Write up: what signal you noticed first, what hypotheses you formed, what you checked, how
long it took. `evals/day16_incident_drill.md`.

This drill is the single best preparation for real FDE work in the entire bootcamp.
Repeat it with a different fault if you have time — the second one will be much faster,
and noticing *why* it's faster is the meta-lesson.

### 2.4 Close the loop (30 min)

Build `scripts/triage.py`:

```
1. Pull all traces with rating <= 2 or with unverified citations
2. For each: show question, answer, retrieved chunks with scores, and the prompt
3. Prompt you to classify: retrieval_miss | generation_error | correct_but_unhelpful
                          | bad_question | guard_false_positive
4. On a real failure: auto-generate a golden-set case with the expected answer
   (you fill it in), append to evals/goldenset_v3.jsonl
5. Print a weekly summary: failure counts by class
```

Run it on your worst 10 traces. Add them to the golden set. Re-run the CI suite and watch
the score drop — **your eval just got harder and more honest.** That's what a real eval
suite does over time: it accumulates the failures you actually hit.

---

## Block 3 — Teach-back #16 (0:30)

Record 12 min: **"Find the bad answer from Tuesday afternoon."**
`teaching/recordings/day_16.mov`

Frame it as the incident drill. Open with the complaint. Then: dashboard → notice the
signal → traces → find the request → open the prompt → see the retrieved chunk → diagnose.
Live, on screen, start to finish.

Then show the triage tool turning that one complaint into a permanent regression test.
The line to close on: *"Now this specific failure can never come back silently."*

---

## Done when

- [ ] Full OTel instrumentation with LLM-specific attributes and config hashes
- [ ] Phoenix running; three specific findings written up from exploring your own traces
- [ ] Six-panel dashboard, including retrieval score distribution
- [ ] Incident drill completed using only telemetry; write-up with your time
- [ ] Triage tool converting bad traces into golden-set cases
- [ ] Golden set grown; CI re-run showing the harder, more honest score

---

## Trap list

- Traces without the prompt. Useless exactly when you need them.
- No config version in the span. "What changed?" becomes archaeology.
- A single "error rate" metric. Timeouts and content filters need different responses.
- Alerting on total latency only. Alert per node.
- PII in traces with no redaction decision. Handle it at write time.
- A 30-panel dashboard. Nobody looks at it, including you.
- Collecting feedback with no path from feedback to eval case. Then it's theatre.

---

## Stretch

Implement **online eval sampling**: run your Day 13 judge on 5% of live traffic
asynchronously, and chart faithfulness over time as a live metric. Then plant a regression
and see how long it takes the online metric to detect it, versus your offline CI suite.
The gap between those two detection times is a genuinely interesting number and a great
discussion prompt for a senior audience.
