# Day 15 — Production I: Serving, Streaming, Caching, Guardrails

**Thu Sep 10, 2026** · Week 3 · Maps to: **Module 08 — Production I** · Backend: **local** + `[PAID]` · Est. cost: **$2–4**

> **Before you start — read `learn/DAY_15_LEARN.md` (1:15).**
> The serving contract, three cache layers, guardrail false positives. The lab below assumes it and does not re-explain it.


---

## Why today matters

**FDE lens.** Today your laptop project becomes a service. Everything here — streaming,
timeouts, backpressure, caching, guardrails — is what separates "we built a prototype" from
"we handed over something operable." It is also, bluntly, where most AI engineers are weak,
because it's ordinary backend work and they'd rather do model work. Being strong here is a
durable differentiator.

**Trainer lens.** A cohort full of people who can build agents and cannot serve them is the
normal state of the world. A session on "your agent is now an HTTP service" is one of the
most requested and least available things in AI education.

---

## Objectives

1. Serve the Day 12 system as a FastAPI service with SSE streaming and proper lifecycle.
2. Implement three cache layers and measure the hit rate and savings of each.
3. Build input and output guardrails, and measure their false-positive rate.
4. Handle concurrency, timeouts, cancellation, and backpressure — and prove it under load.

---

## Schedule (5:00)

| Block | Time | What |
|---|---|---|
| 0 | 0:30 | Warm-up |
| 1 | 1:15 | **Learn** — `learn/DAY_15_LEARN.md` |
| 2 | 2:45 | Lab: FastAPI service + caching + guardrails + load test |
| 3 | 0:30 | Teach-back #15 |

---

## Block 0 — Warm-up (0:30)

1. Why RRF instead of score blending?
2. Which technique gave the biggest recall jump, and what did it cost in latency?
3. The three ways to handle near-duplicate policy revisions; which is best and why?
4. What happened to your scores when the corpus went from 10 to 200 docs?

---

## Block 1 — Learn (1:15)

**Read `learn/DAY_15_LEARN.md` and work its examples on paper before continuing.**
Take the self-check at the end. Anything you miss goes on a flashcard and into tomorrow's
warm-up. The material below consolidates the module — it is not a substitute for it.

### 1.1 The serving contract

An LLM endpoint is unlike a normal API in four ways, and each one demands a design decision:

| Property | Consequence |
|---|---|
| **Slow** (1–30s) | Streaming is mandatory. So is a request timeout shorter than your gateway's |
| **Expensive per request** | Caching, rate limiting per tenant, and cost attribution are day-one features |
| **Non-deterministic** | Idempotency keys don't dedupe naturally; you must cache deliberately |
| **Fails in novel ways** | Content filters, context overflow, provider outages — none look like 500s |

Design decisions to make explicitly today:

- **Streaming protocol**: SSE (simple, HTTP, works through most proxies) vs. WebSocket
  (bidirectional, needed for interruption). Choose SSE, and know why you might not.
- **Cancellation**: when the client disconnects mid-stream, you must stop the upstream
  call. Otherwise you pay for tokens nobody reads. This is a real and common money leak.
- **Timeouts, layered**: per-LLM-call < per-agent-step < per-request < gateway. Each must
  be strictly smaller than the next or your timeouts are decorative.
- **Cost attribution**: every response carries its own cost, tagged by tenant and route.

### 1.2 The three cache layers

| Layer | Key | Hit rate | Saves | Risk |
|---|---|---|---|---|
| **Exact response cache** | hash(query + config + corpus version) | 5–15% | Everything | Stale answers after a corpus update — **version your key** |
| **Semantic cache** | embedding of query, threshold ~0.95 | 15–30% | Everything | False hits. "detention for reefer" vs "detention for dry van" are 0.94 similar and have different answers |
| **Provider prompt cache** | Provider-side, prefix-based | High on stable prefixes | Input tokens (~90% discount) | Requires stable prompt prefixes — put variable content LAST |

That last row changes how you write prompts: system prompt, tool schemas, and procedural
memory go **first and unchanged**; retrieved chunks and the user question go **last**. Getting
this ordering right can cut input cost dramatically at volume and costs you nothing.

The semantic cache threshold is the interesting engineering problem. Measure it: sample
100 query pairs above 0.93 similarity and hand-check how many actually have the same
answer. Set your threshold from that data. **Do not use 0.95 because a blog post said so.**

### 1.3 Guardrail taxonomy

**Input guardrails** (before you spend money):
- Prompt injection detection
- PII detection and redaction (shipment data contains names, addresses, phone numbers)
- Off-topic / out-of-scope rejection
- Rate limit and size limit

**Output guardrails** (before the user sees it):
- Groundedness check — every claim cited and verified (you have this from Day 4)
- PII leakage check
- Format / schema validation
- Refusal-appropriateness — did it answer something it should have declined?

Implementation ladder, cheapest first: **regex/heuristic → small classifier model → LLM
judge → human review.** Use the cheapest tier that works; escalate only what's uncertain.

And measure the thing nobody measures: **the false-positive rate.** A guardrail that blocks
3% of legitimate queries is worse than the risk it prevents in most business contexts. You
must be able to state that number.

---

## Block 2 — Lab (2:45)

### 2.1 FastAPI service (70 min)

`capstone/service/app.py`:

```python
POST /v1/ask            {question, session_id?, stream?}  → answer + citations + cost + trace_id
GET  /v1/ask/stream     SSE: token deltas, then a final event with citations + cost
GET  /v1/traces/{id}    the full trace (your Day 12 viewer, as JSON)
POST /v1/feedback       {trace_id, rating, comment}   → feeds tomorrow's observability
GET  /healthz           liveness — no dependencies checked
GET  /readyz            readiness — model reachable, index loaded, vector store up
GET  /metrics           Prometheus format
```

Must-haves:

- [ ] `lifespan` context manager: load the index and warm the model **once** at startup,
      not per request. (Measure the difference — it's often 2–3 seconds per request.)
- [ ] SSE streaming with a heartbeat every 15s so proxies don't kill idle connections
- [ ] Client-disconnect detection → cancel the upstream LLM call. **Prove it**: start a
      stream, kill the client, confirm in your cost log that no further tokens were billed
- [ ] Layered timeouts with a clean 504 carrying a partial answer where possible
- [ ] Per-request `trace_id` in every log line and in the response headers
- [ ] `X-Cost-USD` and `X-Trace-Id` response headers
- [ ] Structured JSON logging

### 2.2 Caching (45 min)

`src/fdekit/cache.py` — all three layers, each independently toggleable:

```python
class ExactCache:      # key includes corpus_version — non-negotiable
class SemanticCache:   # calibrate the threshold; log near-misses for review
class PromptPrefixOptimiser:
    """Reorders prompt components so the stable prefix maximises provider cache hits.
    Reports the stable-prefix token count."""
```

Then measure with a realistic query distribution (Zipf — a few questions asked constantly,
a long tail asked once):

```
                 hit rate   mean latency   cost/query   stale risk
no cache            —          2.1s        $0.0034         —
exact              11%         1.9s        $0.0030        low
+ semantic         26%         1.6s        $0.0025       medium
+ prefix opt       26%         1.5s        $0.0014        none
```

The prefix optimisation row is the surprise: it doesn't change hit rate but it halves cost,
because it turns 4,000 input tokens into cached input tokens. **Show that to a client and
you've paid for a week of your time.**

Calibrate the semantic threshold with the 100-pair experiment. Write the number and the
evidence in `evals/day15_cache_calibration.md`.

### 2.3 Guardrails (40 min)

`src/fdekit/guardrails.py`:

```python
class InputGuard:
    def check(self, text, session) -> GuardResult:   # allow | redact | block
        # 1. size + rate limit
        # 2. PII detect + redact (regex first: phone, email, SSN-shaped, address-shaped)
        # 3. prompt injection heuristics, then a classifier for uncertain cases
        # 4. scope check — is this a freight-ops question?

class OutputGuard:
    def check(self, answer, context) -> GuardResult:
        # 1. citation verification (Day 4)
        # 2. PII leakage
        # 3. schema validity
        # 4. refusal appropriateness
```

Build a **red-team set**: 40 cases — 20 that should be blocked (injections, off-topic, PII
extraction attempts), 20 that look risky but are legitimate ("what's the phone number on
the BOL for SHP-...?" is a normal ops question). Measure precision and recall of each
guard, and the false-positive rate specifically.

Report it as a confusion matrix. `evals/day15_guardrail_eval.md`.

### 2.4 Load test (25 min)

```bash
pip install locust
locust -f scripts/loadtest.py --headless -u 50 -r 5 -t 3m --host http://localhost:8000
```

Measure: p50/p95/p99 latency, throughput, error rate, and cost per minute. Then find your
knee — where does p95 blow up, and what's the bottleneck? (Usually the local model's
queue, or an unbounded semaphore, or a synchronous call in an async path.)

Write `capstone/service/CAPACITY.md`: at what concurrency does this degrade, what's the
first bottleneck, and what would you do about it. That document is exactly what an SRE
team will ask you for on a real engagement.

---

## Block 3 — Teach-back #15 (0:30)

Record 12 min: **"Your agent is now an HTTP service. Four things will surprise you."**
`teaching/recordings/day_15.mov`

The four: streaming + cancellation (show the money leak, live), layered timeouts, prompt
prefix ordering for cache hits (show the cost drop), and guardrail false positives (show
your confusion matrix and ask the room what FP rate they'd accept).

The cancellation demo is the best one — kill a client mid-stream and show tokens still
being billed, then show the fix. Everyone in the room has this bug and doesn't know it.

---

## Done when

- [ ] FastAPI service with all seven endpoints, streaming, and lifespan warm-up
- [ ] Client disconnect provably cancels upstream calls — evidenced in the cost log
- [ ] Three cache layers with measured hit rates and a calibrated semantic threshold
- [ ] Prompt prefix reordering with the input-cost reduction measured
- [ ] Input + output guards with a 40-case red-team set and a confusion matrix
- [ ] Load test run; `CAPACITY.md` written with the knee identified

---

## Trap list

- Loading the index per request. Measure your cold path.
- Semantic cache threshold copied from a blog post.
- Cache key without a corpus version. Update the corpus, serve stale answers forever.
- No client-disconnect handling. Silent, continuous money leak.
- Timeouts that aren't strictly nested. Then the outer one always fires first and you
  never see the real error.
- Guardrails with no false-positive measurement. You've traded a rare risk for a constant one.
- Variable content early in the prompt, killing your provider cache hit rate.

---

## Stretch

Add **request-level graceful degradation**: on provider timeout or 429, fall back to a
cheaper/local model, mark the response `degraded: true`, and emit a metric. Then load-test
with the primary provider blocked and show the service staying up at reduced quality
instead of erroring. Demonstrating graceful degradation under an induced outage is one of
the highest-trust things you can show an enterprise buyer.
