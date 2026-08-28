# Day 15 · Learn — Production serving: streaming, cancellation, timeouts, caching, guardrails

**Read before `labs/DAY_15.md`. Budget 1:15.** Pen and paper for §3 — the cache-cost and false-positive arithmetic are the two numbers you'll be asked for on an engagement.

---

## 1. Where this sits

You have a system. Day 12 integrated it, Day 13 gave it gates that survive contact with a team, Day 14
made retrieval good enough to trust. All of it runs on your laptop, in a process you start by hand.

Today it becomes a service other people's software calls — and this is the day where **twenty-three
years of your career is worth more than everything in the preceding fourteen days combined.** A
request handler with layered timeouts, bounded concurrency, structured logging and a cache hierarchy
is a thing you have built many times.

The reason this module exists is that four properties of an LLM endpoint break the reflexes that
normally serve you, and the failures they produce don't look like failures. They look like a slightly
higher bill and a slightly slower service.

---

## 2. The mechanism

### 2.1 The four ways an LLM endpoint is not a normal API

| Property | Normal API | LLM endpoint | What it forces |
|---|---|---|---|
| **Latency** | 20–200ms | **1–30s** | Streaming is mandatory, not a feature |
| **Cost per request** | Effectively zero | **$0.001–0.05, variable** | Caching and per-tenant cost attribution are day-one |
| **Determinism** | Same input → same output | **Non-deterministic** | Idempotency keys don't dedupe naturally |
| **Failure modes** | 4xx, 5xx, timeout | **Novel and content-shaped** | Content filters and context overflow aren't 500s |

**Slow.** A 12-second request with no output until the end is indistinguishable from a hung request.
Users refresh, load balancers with a 10-second idle timeout kill the connection, mobile clients give
up. Streaming isn't there to feel modern — a byte on the wire every few hundred milliseconds is what
keeps every layer between you and the user from concluding you're dead.

**Expensive per request, and variably so.** When a request costs nothing you can afford not to know
who made it. When it costs three cents and one tenant sends forty thousand a day, **cost attribution
is a functional requirement**, and retrofitting it means threading a tenant ID and a token-accounting
object through every layer you've already written. Do it on day one: every response carries its own
cost, tagged by tenant and route, in a log line and a response header. Same for rate limiting —
per-tenant, because a global limit means one tenant's runaway script is an outage for everyone.

**Non-deterministic.** The standard idempotency pattern — client sends `Idempotency-Key`, you return
the stored response — works because the operation was going to produce the same result anyway. With an
LLM a retry produces a *different answer*, so a client retrying after a timeout gets a second answer
that may contradict the first, and you paid twice. **The idempotency key must map to a stored
response, not to a "we already did this" flag** — which makes idempotency here and §2.5's exact cache
the same machinery wearing two names.

**Fails in novel ways.** Your error taxonomy needs categories that don't exist elsewhere:

| Failure | Looks like | Should be |
|---|---|---|
| Content filter refusal | HTTP 200 with an apology in the body | A distinct status and metric |
| Context window overflow | Provider 400, or silent truncation | 413-shaped, with the token count |
| Malformed structured output | 200 with unparseable JSON | Retry-then-fail, counted separately |
| Provider 429 / capacity | 429, sometimes 529, sometimes a slow 200 | Backoff, then degrade to a fallback model |
| Retrieval returned nothing | 200 with a fabricated answer | A refusal, and an alarm |

The dangerous rows return **200**. A content-filter refusal and a fabrication over an empty context are
both, to your monitoring, perfectly healthy responses. If your dashboard is error rate and p95 latency
you are blind to the two failures that damage a client relationship. Classify at the response layer
and emit a metric per class.

### 2.2 Streaming: SSE, and when you'd need WebSocket

**Server-Sent Events** is a one-directional stream over an ordinary HTTP response. The response never
ends; the server writes `data:` lines separated by blank lines. It's part of the HTML standard,
`EventSource` is built into browsers, and — the property that matters most in an enterprise — **it is
just HTTP.** It traverses corporate proxies, API gateways and WAFs, because as far as they're
concerned it's a slow response.

```
event: token
data: {"delta": "Detention accrues at $"}

event: token
data: {"delta": "65 per hour"}

: heartbeat

event: done
data: {"citations": [...], "cost_usd": 0.0031, "trace_id": "..."}
```

Two details that are easy to get wrong. **Send a final event carrying the metadata** — citations,
cost, trace ID — because you cannot put them in headers; the headers went out before the first token
existed. And **send a heartbeat** (a bare `:` comment line) every 15 seconds or so, because most
proxies enforce an *idle* timeout on the gap between bytes, not on total duration. An agent step that
thinks for 25 seconds before emitting a token is a 25-second silence, and a 20-second idle timeout
kills it.

**WebSocket** is full-duplex after an HTTP upgrade. You need it when the client must send something
*during* the response: the user interrupts mid-generation; voice or any real-time bidirectional media;
the client returns tool results mid-turn; you want one connection multiplexing many concurrent turns.

You do not need it for "show tokens as they arrive," which is what most people reach for it for. The
costs are real — WebSocket connections are stateful, which means sticky routing, which makes your
horizontal scaling story worse, and they're the thing enterprise network teams block. **Choose SSE,
and know the four cases that would change your mind.** Note too that "the user can interrupt" has a
cheaper answer: the client closes the HTTP connection and the server treats that as cancellation —
the next section, and the one that costs money.

### 2.3 Client disconnect, and the silent continuous money leak

A user asks a question, the answer starts streaming, they read the first sentence, get what they
needed, and close the tab.

What happens next, if you wrote the obvious code, is that **your service keeps streaming tokens from
the provider into a socket nobody is reading, and you pay for every one of them.** The generation
doesn't know the client left. Your handler doesn't check.

This is the purest example of the class of bug this module exists for:

- **It never errors.** No exception, nothing in your error rate.
- **It doesn't distort latency metrics** — or if it does, it looks like a slightly slow request.
- **It is continuous and proportional to traffic.** It doesn't spike. It scales with your success.
- **It also consumes a concurrency slot** for the remainder of the generation, degrading capacity for
  the users who *are* still there.

§3 Q1 sizes it; the capacity effect is arguably worse than the money.

The fix is structural. In an async handler the disconnect must **propagate as cancellation all the way
to the provider call**:

```
client closes socket
  → framework disconnect signal
    → cancel the task running the agent step
      → HTTP client cancels the in-flight streaming request
        → provider stops generating (and stops billing)
```

Every link has to actually cancel. The two that commonly don't: a provider SDK call wrapped in
something that swallows cancellation, and a synchronous call inside an async handler — which blocks
the event loop and cannot be cancelled at all, because there is no await point at which cancellation
can be delivered. **A synchronous LLM client in an async framework is not slow, it is uncancellable**,
and that's the more serious defect.

Then prove it. Start a stream, kill the client, and confirm from your cost log that token accounting
stopped. "I handled disconnects" is a claim; a cost log that flatlines at the moment of disconnect is
evidence — and that distinction is most of what an FDE deliverable is.

### 2.4 Layered timeouts, strictly nested — including retries

You know this pattern. What's specific to today is that there are more layers than usual and one of
them sits inside a loop.

```
gateway / load balancer      30s
  └─ per-request              25s
       └─ per-agent-step       7s
            └─ per-LLM-call    5s   (+ retry budget!)
```

**Each must be strictly smaller than the one containing it.** Otherwise the outer one fires first and
you lose the only useful information in the failure — *which layer was slow.* A 504 from your gateway
tells you nothing. "Per-LLM-call timeout on step 2 of 3; retrieval took 180ms; first call took 4.9s"
tells you exactly where to look. **Timeouts that aren't nested are decorative**: configured, present,
and never firing in an order that teaches you anything.

The layer people get wrong is the retry budget. Set the per-call timeout to 8s, add two retries with
backoff, feel responsible — and now one logical call can take `8 + 1 + 8 + 2 + 8 = 27 seconds`, which
blows through a 7-second step budget, a 25-second request budget, and the gateway. **The retry budget
lives inside the step timeout, not outside it.** Do that arithmetic explicitly (§3 Q2), because the
intuitive configuration is almost always internally inconsistent.

Two things that make timeouts useful rather than merely present. **Deadline propagation beats
independent timeouts** — compute one absolute deadline at request arrival, pass it down, and have each
layer take `min(its own limit, time remaining)`; otherwise step 3 happily starts a 7-second budget
with 2 seconds left on the request clock. Same mechanism as a gRPC deadline. And **a timeout should
return the partial answer** — you have been streaming tokens, so close the stream with a truncation
event and return 504 with what you had.

**Bounded concurrency is the other half.** A local model with four inference slots and a mean request
of 2.1s has a hard throughput ceiling of `4 / 2.1 = 1.9 req/s` — Little's Law, and no async cleverness
changes it. Offer it 3 req/s and the queue grows without bound until everything times out at once.
**Bound the queue with a semaphore and shed with 429 plus `Retry-After`** rather than accepting work
you cannot do — the standard overload argument from the SRE literature, applying with unusual force
because your capacity is measured in single digits.

### 2.5 Cache layer 1: exact response, and the version in the key

Hash the request, store the response, serve it back.

```
key = sha256(question ‖ model_id ‖ prompt_version ‖ retrieval_config ‖ CORPUS_VERSION)
```

Every component is load-bearing, and the last one is the one people omit.

**Omit the corpus version and you serve stale answers forever.** You re-index on Tuesday because the
tender acceptance policy moved to Revision 8 and the FTA threshold is now 94%. Everyone who asked
"what FTA do primary carriers need to maintain" before Tuesday keeps getting 92%, from cache, with
citations to a document that no longer says that, for as long as the TTL allows — and if you set a
generous TTL because responses are expensive, that's weeks. There is **no error, no alarm, and no way
to notice** except a person who happens to know the answer changed.

Include it and the re-index invalidates the affected entries automatically, because the key changed.
The version can be a hash of the index manifest or a monotonic build number; what matters is that it
moves when the corpus moves. Same logic for `prompt_version`.

Hit rate is modest, **5–15%**, because exact repetition requires byte-identical queries. Worth having
anyway: nearly free, exact so it carries no correctness risk, and it's the machinery your idempotency
keys need.

### 2.6 Cache layer 2: semantic, and the threshold you must calibrate yourself

Embed the incoming query, search the cache's own vector index, serve the stored answer if something
sits above a threshold. **15–30%** hit rates are realistic, because real traffic is Zipf-shaped — a
handful of questions asked constantly, phrased slightly differently each time.

And it is the one cache layer that can be **wrong**, which changes how you treat it.

Day 3's lesson applies exactly: a similarity score is not calibrated, and the threshold at which two
queries share an answer is a property of your embedding model on your corpus.

```
"what's the detention rate for a reefer"      ┐  cosine ≈ 0.94
"what's the detention rate for a dry van"     ┘
```

Those are 0.94 similar and do **not** have the same answer. Worse — and this connects straight to Day
13's absent-fact category — the corpus contains no reefer-specific rate at all, so the correct
behaviour for the reefer query is to say so. A false semantic hit doesn't return a mediocre answer; it
**manufactures a fact the system had correctly refused to state.** You built a refusal behaviour on
Day 13 and a cache is now defeating it.

So: **calibrate empirically, on your own query pairs.** Sample ~100 pairs from real or persona traffic
above 0.93; hand-check whether one answer serves both; compute the false-hit rate per similarity band;
pick the threshold where it crosses your tolerance, and **write down both the number and the
evidence.** That second clause is the deliverable. A threshold in a config file with no provenance is
a number the next engineer changes on a hunch; a threshold with a table of 100 hand-checked pairs next
to it is a decision.

Two operational rules: **log near-misses** just below your threshold — they're the sample for your next
calibration — and **let callers bypass the cache**, because `Cache-Control: no-cache` should work on
your endpoint the way it works everywhere else.

### 2.7 Cache layer 3: provider prompt caching, and the ordering it forces

The other two caches are yours. This one is the provider's, it works on the **prefix** of your prompt,
and it changes something you'd otherwise never think about: **the order in which you assemble a
prompt.**

The provider stores the computed attention state for a prefix. If your next request begins with a
byte-identical prefix, it reuses that state and charges a steep discount on those input tokens —
commonly around 90% off the read, though the exact economics and the write cost differ by provider.

The constraint is **prefix**. The cache hits only up to the first byte that differs:

```
BAD                                    GOOD
──────────────────────────             ──────────────────────────
user question           ← varies       system prompt          ← stable  ┐
retrieved chunks        ← varies       tool schemas           ← stable  │ cacheable
system prompt           ← stable       few-shot examples      ← stable  │ prefix
tool schemas            ← stable       procedural memory      ← stable  ┘
                                       ─────────────────────────────────
                                       retrieved chunks       ← varies
                                       user question          ← varies
```

In the left layout the very first token differs on every request and **the cache never hits at all.**
Same tokens, same model, same answer, zero discount.

The size of this is not marginal. In a RAG system with a substantial system prompt, tool schemas and
few-shot examples, the stable prefix is often the *majority* of your input tokens — §3 Q3 works a case
where correct ordering cuts cost per query by 47%, with no behaviour change and no engineering beyond
concatenating strings in a different order.

**Three things silently break it**, all ordinary-looking code: **a timestamp in the system prompt**
("Current date: 2026-09-10T14:22:07Z" changes every second — use a date, not a datetime);
**non-deterministic serialisation**, such as a JSON dump without `sort_keys`; and **any variable
content above the stable block**, which uncaches everything below it.

This is also the optimisation that made Day 14's contextual retrieval cheap: parent document first and
unchanged, chunk last. Same mechanism, different side of the system.

**The three layers stack, and they save different things.** Exact and semantic caches save
*everything* — the request never happens. Prompt caching saves only input tokens, but it applies to
the requests that *do* happen, which is all the ones the first two missed. That's why cost per query
keeps dropping after the hit-rate column stops moving.

### 2.8 Guardrails: input, output, and the escalation ladder

**Input guards run before you spend money:** size and rate limits; PII detection and redaction
(freight data is full of driver names, phone numbers, delivery addresses); prompt-injection
heuristics; scope checking — is this even a freight-ops question?

**Output guards run before the user sees it:** groundedness — every claim cited and verified, from Day
4; PII leakage in the other direction; schema validity; refusal appropriateness, which is Day 13's
adversarial taxonomy applied at serving time.

The output side has a property that catches people out: **you are streaming.** By the time your
groundedness check has an answer to check, the user has already read it. Three honest positions:

| Approach | Behaviour | Cost |
|---|---|---|
| **Buffer, check, then send** | Fully safe | You lose streaming — back to a 12s blank screen |
| **Stream, check at the end, append a warning** | Keeps streaming | The bad content was already read |
| **Stream with a delay window** | Hold N tokens back, check incrementally | Complex; partial claims are hard to verify |

Most systems take the second and are quiet about it. Say it out loud instead: *"output guards on a
streaming endpoint are detective, not preventive — preventive ones have to be on the input side, or
you give up streaming."*

**The escalation ladder — cheapest tier first, escalate only what's uncertain:**

| Tier | Latency | Cost | Catches | Use for |
|---|---|---|---|---|
| **1 · Regex / heuristic** | <1ms | 0 | Structured patterns: phone, email, "ignore previous instructions" | Everything, first |
| **2 · Small classifier** | 5–30ms | ~0 | Fuzzy categories: off-topic, toxicity, injection-shaped | What tier 1 flags uncertain |
| **3 · LLM judge** | 0.5–2s | Real | Semantic and contextual judgements | The narrow uncertain band |
| **4 · Human review** | Minutes–hours | Expensive | Genuinely ambiguous cases | Async, offline, on a sample |

The principle is the one behind every cache hierarchy you have built: **put the cheap filter in front
and only pay for the expensive one on what survives.** If tier 1 resolves 95% of traffic confidently,
your mean guardrail cost is 95% of nothing plus 5% of an LLM call. Tier 4 is the one people leave off
the diagram, and it's what makes the system improvable — sampled human review is where your next
classifier's training data comes from, and where you learn your tier-1 regex is firing on shipment IDs.

### 2.9 The number nobody measures: the false-positive rate

The guardrail conversation usually goes: someone builds an injection detector, runs it against twenty
attack strings, catches nineteen, reports **95% detection**. Everyone is pleased.

Nobody asks the other question: **how many legitimate requests does it block?**

That number determines whether the guard is a net positive, and it's almost never measured, for a
structurally interesting reason: the blocked legitimate user doesn't file a bug. They rephrase, give
up, or tell their manager the tool doesn't work. The failure is distributed across your users and
invisible to you, while the failure it prevents would have been concentrated and visible. **Your
instrumentation is biased toward over-blocking and you must correct for it deliberately.**

Two things make it worse than it first appears.

**The base rate.** Your red-team set is 50/50. Real traffic is not. If one in a thousand requests is a
genuine injection attempt, then even a guard with an excellent 1.5% false-positive rate on ordinary
traffic blocks **far more legitimate users than it catches attackers** — §3 Q5, and the ratio is worse
than anyone guesses. This is exactly the prevalence effect from Day 5 and Day 13's kappa work in a new
costume: a metric measured on a balanced set does not transfer to an unbalanced population.

**The queries that look most dangerous are often the most legitimate.**

| Query | Looks like | Actually is |
|---|---|---|
| *"what's the phone number on the BOL for SHP-202608-0041729?"* | PII extraction | A normal dispatcher task |
| *"ignore the 92% target, what did rev 6 say?"* | Prompt injection | Day 14's near-duplicate question |
| *"give me every carrier below 70 with their contact details"* | Bulk PII harvest | Routine Bronze-band remediation |

A PII guard tuned to block phone numbers blocks row 1 every time. That's not an edge case — it's a
core workflow for the people the system was built for. **A guard blocking 3% of legitimate traffic is
usually worse than the risk it prevents**, because it produces a constant, certain, distributed cost
to buy protection against a rare, uncertain one.

So the deliverable is a **confusion matrix, not a detection rate**:

```
                    guard: block    guard: allow
should block             TP              FN        ← what you missed
should allow             FP              TN        ← what you broke
```

Report precision, recall and the false-positive rate **separately**, then have the conversation the
numbers enable: *"at this threshold we catch 85% of attacks and block 1.5% of legitimate queries; at a
looser one we catch 60% and block 0.2%. Which do you want?"* That's a business decision and you should
not be making it silently on their behalf.

Two practices follow. **Prefer redaction to blocking** where the shape allows — `[REDACTED-PHONE]`
costs a legitimate user very little, a block costs them the whole task. And **make every block
observable**: a reason, a trace ID they can quote, and a metric per guard per rule, so you can find
which rule owns your false positives rather than guessing.

---

## 3. Worked example — on paper

> **Setup.** The freight ops service in production: **10,000 queries/day**. Mean completion **800
> output tokens** at **45 tokens/sec**. Input **$0.30/M**, cached-read **$0.03/M**, output **$3.00/M**.

**Q1 — the leak.** 10% of streaming requests are abandoned, on average **4 seconds** into an
**18-second** generation. With no disconnect handling: output tokens per day generated after the client
has gone, and the monthly cost? Then, at a peak arrival of 2 req/s — by Little's Law, how many
concurrent slots do abandoned requests hold that they shouldn't?

**Q2 — the nest.** Gateway timeout **30s**. You propose: per-request 25s, per-agent-step 7s,
per-LLM-call 8s with 2 retries and 1s/2s backoff. (a) Every violation of strict nesting. (b) Worst case
for one LLM call including retries — does it fit the step budget? (c) Fix it so a 3-step agent fits
inside the request budget with retries counted.

**Q3 — the cache stack.** Per query: **8,000 input tokens**, of which the stable prefix (system prompt
1,200 + tool schemas 1,800 + few-shot 2,400 + procedural memory 600) is **6,000** and the variable part
(retrieved chunks 1,600 + question 400) is **2,000**. Output **350 tokens**.
(a) Cost per query with no caching at all. (b) With the prefix ordered correctly so 6,000 tokens hit
the provider cache. (c) Adding exact (11%) and semantic (26% cumulative) caches on top of (b) — cost
per query, and monthly cost at 10,000/day versus baseline. (d) Hit rate didn't change between (a) and
(b); why did cost drop?

**Q4 — the threshold.** 100 query pairs above 0.93, hand-checked for whether one answer serves both:

| Band | pairs | same answer |
|---|---|---|
| 0.93–0.95 | 45 | 22 |
| 0.95–0.97 | 32 | 26 |
| 0.97–0.99 | 18 | 17 |
| ≥ 0.99 | 5 | 5 |

For thresholds 0.93, 0.95, 0.97 and 0.99, compute hits and the **false-hit rate** (fraction of hits
returning a wrong answer). Which would you ship, and what does the blog-post default of 0.95 cost you?

**Q5 — the guard.** Red-team set: 40 cases, 20 should-block, 20 legitimate-but-risky-looking. Your
guard catches 17 of 20 attacks and blocks 3 of 20 legitimate. (a) Precision, recall, false-positive
rate on that set. (b) In production **1 in 1,000** requests is a genuine injection attempt and the
guard's false-positive rate on ordinary traffic is **1.5%**; at 10,000/day, give attacks caught,
legitimate queries blocked, and production precision. (c) What do you tell the client?

**Q6 — the knee.** Local model, **4 concurrent slots**, mean request holds a slot **2.1s**.
(a) Throughput ceiling. (b) At 1.7 req/s, utilisation and the queueing inflation factor `1/(1−ρ)`.
(c) What should the service do at 3 req/s?

**Q7 — streaming and the SLO.** Variant A streams: **TTFT 1.4s**, total 8.2s. Variant B returns
nothing for **6.9s**, then everything. (a) Which feels faster, and what should A's latency SLO be
measured on? (b) Your longest silent gap is an agent step thinking for **22s** and the proxy's idle
timeout is **20s** — does a 15s heartbeat save you? What if the idle timeout were 10s?

<details>
<summary><b>Answers — Q3 and Q5 are the two you'll be asked for on an engagement</b></summary>

**Q1.** Fraction remaining at abandonment `1 − 4/18 = 0.778` → `800 × 0.778 = 622` wasted tokens per
abandoned request. Abandoned/day `10,000 × 0.10 = 1,000` → **622,000 tokens/day** → **$1.87/day** →
**$56/month**. Annoying rather than alarming at this volume — but it scales linearly, so at 500,000
queries/day it's **$2,800/month**, entirely waste.

Concurrency, `L = λW`: abandoned arrivals at peak `2 × 0.10 = 0.2/s`, each holding a slot for the
remaining 14s → `0.2 × 14 = ` **2.8 concurrent slots** permanently occupied by requests nobody is
reading. Against Q6's 4-slot model that is **70% of your capacity** serving closed browser tabs. **The
money is the small half of this bug.**

**Q2.** (a) Per-LLM-call (8s) is **larger** than per-agent-step (7s), so the inner layer can't fire
first and a slow call surfaces as a step timeout — diagnosis lost. And 3 steps × 7s = 21s plus
retrieval sits uncomfortably close to the 25s request budget.
(b) `8 + 1 + 8 + 2 + 8 = ` **27s** worst case — larger than the step budget, the request budget *and*
the gateway. The retry budget was never counted.
(c) One workable nest: per-LLM-call **4s** with **1 retry** and 1s backoff → worst case `4+1+4 = 9s`;
per-agent-step **10s**; **max 2 steps** → 20s; per-request **22s**; gateway **30s**. Every layer
strictly inside the next *with retries counted*, and a failure names the layer that caused it.

**Q3.** (a) Input `8,000 × $0.30/M = $0.00240`; output `350 × $3.00/M = $0.00105`. Total ≈
**$0.0034/query**.
(b) Cached prefix `6,000 × $0.03/M = $0.00018`; uncached `2,000 × $0.30/M = $0.00060`; output
`$0.00105`. Total ≈ **$0.00183** — a **47% reduction from reordering a prompt.**
(c) 26% never reach the model: `0.74 × $0.00183 = ` **$0.00135 ≈ $0.0014/query**. Monthly at 300,000
queries: baseline **$1,020**, full stack **$405** — a saving of **$615/month, 60%**, from three caches
and a string concatenation order.
(d) Exact and semantic caches save **whole requests**; prompt caching saves **input tokens on the
requests that still happen**, which is 74% of them. Different populations, so they compose rather than
overlap. That's the row in the lab's table that surprises people: hit rate flat, cost halved.

**Q4.**

| Threshold | Hits | Wrong hits | False-hit rate |
|---|---|---|---|
| 0.93 | 100 | 30 | **30.0%** |
| 0.95 | 55 | 7 | **12.7%** |
| 0.97 | 23 | 1 | **4.3%** |
| 0.99 | 5 | 0 | **0.0%** |

The default of **0.95 returns a wrong answer on roughly one cache hit in eight.** At a 26% hit rate
that's ~3% of all traffic answered wrongly — silently, with confident citations attached.

Ship **0.97**: it cuts hits from 55 to 23, giving up most of the cache saving, to get the false-hit
rate to 4.3%. **The semantic cache's value is capped by how much wrongness the domain tolerates**,
which is a business question rather than a tuning one. In a support FAQ 0.95 might be fine. In
accessorial billing it is not.

**Q5.** (a) Precision **85%**; recall **85%**; FP rate on the risky set `3/20 = ` **15%**.
(b) Attacks/day `10,000 × 0.001 = 10`, caught at 85% = **8.5**. Legitimate `9,990 × 1.5% = ` **150
blocked/day**. Production precision `8.5 / 158.5 = ` **5.4%**.

**Fewer than 1 block in 18 is a real attack.** Same guard, same threshold, same code — the number moved
by a factor of sixteen purely from the base rate.
(c) *"This catches roughly 8 or 9 real injection attempts a day and blocks about 150 legitimate ops
queries doing it. At a looser threshold: 6 caught, 20 blocked. Which do you want, and what's the actual
consequence of a successful injection here?"* If the consequence is a wrong answer in a read-only
assistant, the looser setting is almost certainly right. If the agent can issue a tender, it isn't.
**The threshold is a function of blast radius, and that's their call, made with your numbers.**

**Q6.** (a) `4 / 2.1 = ` **1.90 req/s** — a hard ceiling set by the model, not your handler.
(b) `ρ = 1.7/1.90 = 0.895`; `1/(1−ρ) = ` **9.5×**. This is the knee: at 89% utilisation every additional
0.1 req/s roughly doubles the queue, and it looks fine on a throughput graph right up until it doesn't.
(c) **Shed.** 3 req/s against a 1.9 ceiling means an unbounded queue and universal timeouts. A bounded
semaphore plus **429 with `Retry-After`** keeps accepted requests fast and honest; accepting work you
cannot complete converts a partial outage into a total one.

**Q7.** (a) **A feels much faster** despite taking 19% longer end to end, because the user is reading
at 1.4s instead of staring at nothing until 6.9s. So A's SLO must be on **TTFT** (say p95 < 2s) plus an
inter-token gap or tokens/sec floor. A p95-on-total-duration SLO rates B higher, which is backwards —
and it's why teams that stream without changing their SLO optimise the wrong thing.
(b) Yes: a 15s heartbeat means the longest gap the proxy sees is 15s, under the 20s idle timeout, even
though the model is silent for 22s. With a 10s idle timeout, 15s is **not** enough — drop to ~5s. The
rule is `heartbeat interval < idle timeout` with margin, and the number you must know is **the longest
silent gap your own pipeline can produce**, which for an agent is a full tool-calling step.

</details>

---

## 4. What people get wrong

**"Streaming is a UX nicety."**
It's a keepalive. Without bytes on the wire, proxies, load balancers and mobile clients conclude you're
hung, and they're not wrong to.

**"Idempotency keys will handle retries."**
Retrying an LLM call produces a different answer. The key must map to a *stored response*, which makes
it a cache — the same machinery as §2.5, not a dedup flag.

**"If a request fails I'll see it in the error rate."**
Content-filter refusals, empty-retrieval fabrications and truncated context all return 200. The two
most damaging failures are invisible to error-rate monitoring.

**"The client disconnected, so the request ended — and anyway it's a small leak."**
Only if something cancelled the upstream call; otherwise you pay for the full completion into a dead
socket. And it's continuous, proportional to traffic, invisible in every dashboard you have, and at
peak it can occupy most of a small model's concurrency slots.

**"We have timeouts at every layer."**
Are they strictly nested *including the retry budget*? Three retries of an 8-second call is 27 seconds
inside a 7-second step budget, and then the outer timeout always fires first and hides the real error.

**"Cache key is a hash of the question."**
Without the corpus version you serve pre-re-index answers forever, with citations to text that
changed, with no error anywhere.

**"0.95 is the standard semantic cache threshold, and a cache miss is just a slower request."**
0.95 is a number from a blog post; on this corpus it returns a wrong answer on one hit in eight. And a
false *hit* can resurrect an answer for a question the system correctly refuses — "detention rate for
a reefer" served from the dry van entry — defeating the refusal behaviour you built on Day 13.

**"Prompt caching is a provider feature we get for free."**
Only if your prefix is stable. A timestamp in the system prompt, non-deterministic JSON key order, or
the user's question at the top means the hit rate is zero and nothing tells you.

**"Our guard catches 95% of attacks, and our red-team precision was 85%."**
Blocking what fraction of legitimate traffic? Without that you've reported half a trade-off. And the
red-team set is balanced while production isn't: at 1-in-1,000, production precision is 5.4%.
Prevalence effects again — Day 5, Day 13, and now here.

**"Blocking is the safe default."**
Blocking has a certain, continuous, distributed cost and buys protection against an uncertain, rare
one. Redact where you can, and let the client choose the threshold with your numbers in front of them.

---

## 5. The trainer's angle

**The analogy that lands, and it's already theirs:** every mechanism today is a pattern this room has
shipped, with one property changed.

| Today | You already know it as |
|---|---|
| Layered timeouts + deadline propagation | gRPC deadlines, `context.WithDeadline` |
| Bounded concurrency + 429 | Load shedding, admission control |
| Three cache layers | L1 / L2 / CDN, with different invalidation domains |
| Corpus version in the cache key | Cache-busting a static asset by content hash |
| Cheapest-tier-first guardrails | Bloom filter in front of an expensive lookup |
| Client disconnect → cancel upstream | Cancellation propagation in any RPC framework |

Open with that table. It reframes the day from "new AI infrastructure" to "your infrastructure, with a
slow expensive non-deterministic dependency" — truer and much less intimidating — and it sets up the
one genuinely new thing, **the failure modes that return 200**.

**The demo that makes it click, and it's the best one in the bootcamp:** the cancellation leak, live.
Start a stream. Show tokens arriving. Kill the client. Then put the cost log on screen and show tokens
**still being billed** for the next ten seconds — let the room watch a counter increment for an answer
nobody will ever read. Then apply the fix and do it again: the counter stops at the instant of
disconnect.

It works because **everyone in the room has this bug and does not know it.** It isn't a hypothetical
they have to imagine caring about; it's a line item on their current bill.

**The second demo:** prompt reordering. Same prompt, same model, same answer, two orderings, cost
counter on screen. Half the cost. Ninety seconds, and "this change is a different order of string
concatenation" is a sentence that gets remembered.

**The third, for a room that likes arguing:** put the guardrail confusion matrix up and ask *"what
false-positive rate would you accept?"* People say 1%, confidently. Then show what 1.5% means at their
volume — 150 blocked legitimate ops queries a day against 8.5 attacks caught — and watch the number
they'd accept move. The point isn't that there's a right answer; it's that they were about to ship a
threshold without knowing what it cost.

**The predictive question before you run anything:** *"I'm about to kill this client mid-stream. What
happens to the token counter?"* Almost everyone says it stops.

**The question a sharp student will ask:** *"If the semantic cache can be wrong, why ship it at all?"*

> Because everything in serving is a wrongness budget and you're already spending from it. Your
> retriever misses ~10% of the time, your model hallucinates at some non-zero rate, your corpus
> contains a superseded revision. The question isn't whether the cache introduces error — it's whether
> that error is small relative to what's already there and whether you can *measure and bound* it.
> Which you can, exactly, because you calibrated on 100 hand-checked pairs. That's more than you can
> say about most of the pipeline. Then the trade is explicit: at 0.97 you buy a 23% saving for a 4.3%
> false-hit rate; if the domain can't tolerate that — and accessorial billing arguably can't — set it
> at 0.99, take a 5% hit rate, and you've still saved something for free. What you must never do is
> ship 0.95 because a blog post said so, because then you have an unbounded, unmeasured error you
> can't describe to the client.

**The second question, usually from the platform lead:** *"Can't we put this behind our existing API
gateway and be done?"* Mostly yes — but a gateway cannot cancel your upstream provider call on
disconnect, cannot attribute cost per tenant because it can't see token counts, and its timeout is the
*outermost* layer, so it tells you a request was slow and never which part. Necessary, not sufficient.

---

## 6. Self-check

Cover the answers.

1. Name the four ways an LLM endpoint differs from a normal API, and one design consequence of each.
2. Why don't idempotency keys dedupe naturally here, and what must the key map to instead?
3. Name two LLM failure modes that arrive as HTTP 200, and why that matters for monitoring.
4. What is SSE, why is it usually right in an enterprise network, and why does it need a heartbeat?
5. Name two situations that genuinely require WebSocket instead.
6. Describe the client-disconnect money leak, and three reasons it's hard to notice.
7. What makes a synchronous LLM client inside an async handler worse than merely slow?
8. State the timeout nesting order, and explain what the retry budget does to it.
9. What must be in an exact cache key besides the question, and what happens if the corpus version
   is missing?
10. How do you calibrate a semantic cache threshold, why can't you copy one, and give an example
    where a false hit is worse than a miss.
11. Why does provider prompt caching dictate prompt component *order*? Name two things that silently
    break the prefix, and say why all three cache layers stack rather than overlap.
12. State the guardrail escalation ladder. Why are output guards on a streaming endpoint detective
    rather than preventive, and why is production precision far below red-team precision?

<details>
<summary><b>Answers</b></summary>

1. Slow → streaming, and a request timeout inside the gateway's. Expensive per request → caching and
   per-tenant cost attribution as day-one features. Non-deterministic → idempotency must be a
   deliberate response cache. Novel failures → an error taxonomy with categories for content filters,
   context overflow and empty retrieval.
2. A retry produces a different answer, so there's nothing to deduplicate. The key must map to a
   *stored response*, which makes it the exact cache.
3. Any two: content-filter refusal, fabricated answer over empty retrieval, silently truncated
   context, unparseable structured output. They're invisible to error-rate monitoring, so the most
   reputationally damaging failures page nobody.
4. A one-way stream over an ordinary HTTP response, part of the HTML standard, with `EventSource` in
   browsers. Right in enterprises because proxies and WAFs treat it as a slow HTTP response rather than
   something to block. It needs a heartbeat because proxies enforce idle timeouts on the gap between
   bytes, and an agent step can be silent for tens of seconds.
5. Any two: the user must interrupt mid-generation over the same connection; real-time bidirectional
   media such as voice; the client returns tool results mid-turn; multiplexing many turns over one
   connection.
6. The client closes the socket but nothing cancels the upstream call, so you generate and pay for the
   entire completion into a dead connection. Hard to notice because it never errors, doesn't distort
   latency metrics, and is continuous and proportional to traffic rather than spiky. It also holds a
   concurrency slot for the remainder.
7. It blocks the event loop, so there's no await point at which cancellation can be delivered — the
   request is *uncancellable*, not merely slow.
8. per-LLM-call < per-agent-step < per-request < gateway. The retry budget must be counted inside the
   call's contribution to the step: three retries of an 8s call is 27s, which blows every outer layer,
   and then the outermost timeout fires first and hides which layer was actually slow. Deadline
   propagation is the stronger form — each layer takes `min(its limit, time remaining)`.
9. Model ID, prompt version, retrieval config, and **corpus version**. Without it a re-index
   invalidates nothing: you serve pre-update answers with citations to text that changed, for as long
   as the TTL allows, with no error anywhere.
10. Sample ~100 real query pairs above a floor similarity, hand-check whether one answer serves both,
    compute the false-hit rate per band, pick where it crosses your tolerance, and record the evidence.
    You can't copy one because it's a property of your embedding model on your corpus and of how much
    wrongness the domain tolerates. Example: "detention rate for a reefer" served from the dry van
    entry at 0.94 — the corpus has no reefer rate, so the correct behaviour was a refusal, and the
    false hit manufactures a fact.
11. The provider caches a *prefix*, and the hit ends at the first differing byte, so stable content
    goes first and variable content last. Two silent breakers: a timestamp or request ID in the system
    prompt, and non-deterministic JSON/dict serialisation order. The layers stack because exact and
    semantic caches eliminate whole requests while prompt caching reduces input cost on the requests
    that still happen — different populations.
12. Regex/heuristic → small classifier → LLM judge → human review; resolve most traffic with the cheap
    filter and pay for the expensive one only on what survives. Output guards are detective because by
    the time you have a complete answer to check, the user has read it — preventing it means buffering,
    which means giving up streaming. And production precision collapses on base rate: a balanced
    red-team set doesn't transfer to a population where 1 request in 1,000 is an attack.

</details>

**Scored below 9?** Re-read §2.3 (cancellation), §2.7 (prompt ordering) and §2.9 (the false-positive
rate). Those three are the lab's hardest deliverables — a provable disconnect-cancels-upstream demo, a
measured input-cost reduction from prefix reordering, and a red-team confusion matrix — and the lab
will not re-explain any of them.

---

## 7. Going deeper

<!--reading:15-->

### If you read one thing this week

**[Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)** — Anthropic · docs · ~30 min

Read the cache-breakpoint placement rules and the write/read pricing table together — provider prompt caching is the one cache layer of §2.5–2.6 with no analogue in your existing intuition, and its rules (prefix-only, TTL, what invalidates a cache) decide how you order a system prompt.

### Then, in the order I'd take them

- **[Using server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)** — MDN Web Docs contributors (Mozilla) · docs · ~30 min  
  The SSE wire format, EventSource, custom event types and automatic reconnection with Last-Event-ID — everything §2.2's transcript assumes, including why a comment line works as a heartbeat against proxy idle timeouts.
- **[GPTCache: An Open-Source Semantic Cache for LLM Applications Enabling Faster Answers and Cost Savings](https://aclanthology.org/2023.nlposs-1.24/)** — Fu Bang · paper · ~25 min  
  Short workshop paper laying out the semantic-cache architecture — embedding, vector store, similarity threshold, eviction — and it is the cleanest place to see why the threshold is a correctness knob, not a performance knob, which is §2.6's whole warning.
- **[Fixing retries with token buckets and circuit breakers](https://brooker.co.za/blog/2022/02/28/retries.html)** — Marc Brooker · essay · ~20 min  
  Simulated comparison of no-retry, fixed-N retry, adaptive token bucket and circuit breaker — the reasoning transfers unchanged to a provider that returns 429s and 529s, and it tells you which of §2.4's layered-timeout-plus-retry designs actually degrades gracefully under a capacity event.
- **[Guardrails — OpenAI Agents SDK](https://openai.github.io/openai-agents-python/guardrails/)** — OpenAI · docs · ~15 min  
  Input and output guardrails as tripwires that run in parallel with the main call — a concrete shape for §2.9, and the parallel-vs-blocking choice is precisely where the false-positive rate stops being a quality question and becomes a latency one.

<!--/reading-->

### Also mentioned in this module

- *Release It!* — Michael Nygard, 2nd ed. 2018. Timeouts, circuit breakers, bulkheads. Pre-dates all of
  this, and every pattern in §2.4 is in it.
- *Site Reliability Engineering* — Beyer, Jones, Petoff & Murphy, 2016. The chapters on handling
  overload and on cascading failures are the argument behind §2.4's shed-don't-queue rule. Free online.
- *Timeouts, retries and backoff with jitter* — AWS Builders' Library. Why an unbounded retry budget
  defeats a carefully chosen timeout.
- *Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect
  Prompt Injection* — Greshake et al., 2023. The indirect case — injection arriving inside a retrieved
  document — which is the one your RAG system is exposed to. Pair with the *OWASP Top 10 for LLM
  Applications* as a checklist to argue with, and with Simon Willison's running account since 2022;
  his conclusion that no prompt-level defence is reliable, so the mitigation must be architectural, is
  worth internalising before you promise a client a detector.

---

**Now go to `labs/DAY_15.md`.** The lab builds directly on §2.1–§2.2 (the endpoint contract and the SSE
event shape you'll implement), §2.3 (client-disconnect cancellation, which you must *prove* from the
cost log), §2.4 (layered timeouts and the load test that finds §3 Q6's knee), §2.5–§2.7 (three cache
layers, the calibrated threshold from §3 Q4, and the prefix optimiser), and §2.8–§2.9 — the red-team
set and the confusion matrix, where the false-positive rate is the number that matters.
