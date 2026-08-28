# Day 02 · Learn — Typed output, bounded concurrency, and failures you can name

**Read before `labs/DAY_02.md`. Budget 1:15. Pen and paper for §3 — the concurrency arithmetic is the point.**

---

## 1. Where this sits

Yesterday you learned what a model call is and what it costs: one call, in a notebook, returning
a string a human reads.

Today's problem is the gap between that and a component you can put in a pipeline. **A string is
not a record** — downstream code needs `detention_minutes: int`, not a paragraph that mentions
180 minutes. And **one call is not a workload** — tomorrow you embed a corpus, on Day 5 you run a
60-case eval, on Day 13 a 200-case suite, and sequential execution makes all three unusable.

None of today is LLM-specific magic. It's typed contracts, admission control, retry policy and
testing — the things you've spent 23 years doing. What's different is that the component at the
centre is non-deterministic and can fail without raising, so each ordinary pattern needs one
adjustment. Learning which adjustment is the whole day.

---

## 2. The mechanism

### 2.1 Why "just ask it for JSON" fails

Recall Day 1: the model emits a distribution over the next token and a sampler picks one.
**Nothing in that loop knows your schema exists.** "Return JSON with keys shipment_id and
detention_minutes" is just more tokens conditioning the distribution. It makes correct JSON
*likely*, not certain.

The failure taxonomy, in rough order of frequency:

| Failure | What you get | Why |
|---|---|---|
| Fenced output | ` ```json\n{...}\n``` ` | Training data is full of fenced code blocks |
| Prose preamble | `Here is the JSON you requested:\n{...}` | Instruction-tuned models are trained to be helpful and explain themselves |
| Trailing comma | `{"a": 1,}` | Valid in JS, common in training data, invalid JSON |
| Wrong type | `"detention_minutes": "180"` | String is a perfectly plausible continuation |
| Invented enum value | `"stop_type": "delivery"` when you allowed `origin`/`destination` | Your enum is a suggestion in the prompt |
| Missing field | Optional-looking fields silently dropped | Nothing enforces presence |
| Truncation mid-object | `{"rules": [{"topic": "deten` | `max_tokens` hit. Day 1's silent failure, now producing a parse error — which is the *good* case |

At a 2% violation rate this looks fine in a demo and produces twelve failures in a 600-record
batch. That's the whole argument for the rest of this section.

### 2.2 The three levels

Know all three and know when each applies, because on a client site you will find all three in
the same codebase and you'll have to say which one to keep.

| Level | Mechanism | Guarantees | Use when |
|---|---|---|---|
| **1 — Ask nicely** | Instruction in the prompt, `json.loads` | None | Never, past a demo |
| **2 — Schema + parse + repair** | Emit JSON Schema from your model into the prompt; parse; on `ValidationError` send the error text back once | Eventually-valid, at the cost of an extra call on the failure path | **Your default.** Works on any model, including a local Ollama with no structured-output support |
| **3 — Constrained decoding** | Provider masks the logits at each step to only tokens the grammar permits | Syntactically valid by construction | Available and you control the model |

Level 2 is the default not because it's best but because it's *portable*. Half your engagements
will run on a model you didn't pick — a local Llama behind the client's firewall, a Bedrock
model their security team already approved. Level 3 evaporates the moment you lose control of
the endpoint. Level 2 never does.

### 2.3 What constrained decoding actually does — and the distinction that matters

At each generation step the provider computes the set of tokens that could legally continue a
valid instance of your schema, sets every other token's score to negative infinity, and samples
from what's left. If you're two characters into `{"stop_type": "` and the schema says
`Literal["origin","destination"]`, then `o` and `d` are the only permitted next tokens.

So the output *cannot* violate the grammar. Which leads to the most important distinction in
this section:

> **Constrained decoding guarantees validity. It says nothing about correctness.**

`{"shipment_id": "SHP-202608-0041729", "detention_minutes": 45}` is schema-valid whether the
real answer is 45 or 180. You have eliminated malformed output completely, not touched
hallucination, and made the result *look* more trustworthy — which is mildly dangerous.

There's also a cost people don't mention. Masking forces the model down branches it assigned low
probability. If it "wanted" to reason for two sentences before committing to a number, and your
schema's first field is that number, you've removed its ability to compute before answering.
**The field is genuinely divided on how large this effect is** — Tam et al. (2024) reported
measurable reasoning degradation under format restriction, and the result was contested on the
grounds that prompts weren't matched. My read: small for extraction, larger for anything needing
multi-step arithmetic. Design around it rather than argue about it (see §2.4).

### 2.4 The schema is a prompt, and field order is an instruction

Two properties of pydantic models that people treat as documentation and are actually behaviour.

**Descriptions and constraints reach the model.** Once you put the generated JSON Schema in the
prompt, `Field(description="Verbatim span from the source text")` and `Field(ge=0, le=1440)` are
instructions. Naming a field `evidence_quote` rather than `q` measurably changes output quality.
Free prompt engineering, living in your type definitions where it can't drift.

**Field order is generation order.** The model emits fields in schema order, autoregressively,
and — Day 1, consequence 2 — cannot revise. So:

```python
class PolicyRule(BaseModel):
    evidence_quote: str      # ← emitted first: forces it to locate the span
    reasoning: str           # ← then explain
    numeric_value: float | None  # ← only now commit to a number
    unit: str | None
```

`numeric_value` first makes the model guess the number and then write a quote justifying the
guess. Last makes it find the text and read the number off it. Same fields, materially different
accuracy — and this is also how you recover most of what §2.3's masking costs you: give the model
tokens to think with *inside* the schema.

### 2.5 The evidence quote — a hallucination detector that costs nothing

Require a verbatim span, then assert it's a substring of the source:

```python
verified = rule.evidence_quote in source_text
```

No LLM. No human. Microseconds. And it converts a silent failure into a loud one, which is the
entire theme of Day 1's §2.6.

Three things to know before you trust it:

- **Normalise both sides first.** Smart quotes, non-breaking spaces and collapsed newlines produce
  false negatives constantly. Casefold, collapse whitespace, normalise Unicode punctuation, *then*
  compare — otherwise your hallucination rate looks worse than it is.
- **It proves provenance, not support.** The model can quote a real sentence that doesn't support
  the claim it made. Verification is necessary, not sufficient — Day 5's faithfulness judge
  catches the rest.
- **The rate is a metric, not a gate.** A 6% unverified rate is information. Hard-failing the
  batch on it throws away 94% of good work.

### 2.6 Concurrency: two different controls that everyone conflates

An LLM call is IO-bound: 1.2 seconds waiting on a socket, about a millisecond of work. `asyncio`
is a single-threaded reactor that parks a coroutine at every `await` and runs another. You know
this shape — it's `epoll` with better ergonomics. Nothing is faster per call; you've stopped
waiting serially.

Three ways people get it wrong:

1. **Blocking inside a coroutine.** A synchronous SDK call in an `async def` blocks the entire
   loop. Use the async client or `asyncio.to_thread`. Symptom: your "concurrent" run takes
   exactly as long as the sequential one.
2. **No per-task error isolation.** `asyncio.gather` propagates the first exception and abandons
   the rest. In a 200-case eval you want the other 199 results. Always `return_exceptions=True`,
   then partition.
3. **Confusing a concurrency limit with a rate limit.** The subtle one, and where §3 lands.

On (3): a `Semaphore(8)` bounds **in-flight requests** — a connection pool. A provider's
`500 RPM` bounds **arrivals per unit time** — a token bucket. Different quantities, related by
Little's Law:

```
L = λ · W          in-flight = arrival rate × service time
```

A semaphore of 8 at 1.2s mean service time produces 8 / 1.2 = 6.67 req/s = 400 RPM. If the
provider's real ceiling is lower, your semaphore is manufacturing 429s. **You need both
controls** — a semaphore so you don't exhaust sockets and memory, a client-side rate limiter so
you don't exceed the bucket. Most codebases have only the first and treat the 429s as weather.

And the trap the lab calls out: a local Ollama serving one model on one GPU queues server-side.
A semaphore of 16 gives you sixteen requests in a queue, the same wall clock as a semaphore of 2,
and worse tail latency. Measure your concurrency; don't declare it.

### 2.7 Resilience primitives

| Primitive | Protects against | The way it's misused |
|---|---|---|
| **Timeout** | A hung request holding a slot forever | Set below P99, so you manufacture failures — and each retry re-sends the full input |
| **Retry + exponential backoff + jitter** | Transient 429/500/connection reset | Retrying a 400 (your bug), a 401 (your key), or a content filter (never succeeds) |
| **Client-side rate limiter** | Exceeding the provider's bucket | Absent entirely; 429s treated as normal |
| **Circuit breaker** | Hammering a provider that is fully down | Opening on one failure; no half-open probe |
| **Fallback model** | Provider outage, context overflow | Degrading silently, with no telemetry saying it happened |

**The classification rule: retry only failures that are both transient and idempotent.** Read
your provider's exception hierarchy once and write the list down — `RateLimitError` and
`APIConnectionError` retryable, `BadRequestError` and `AuthenticationError` not. A policy that
catches bare `Exception` hides your own bugs behind three seconds of backoff.

**Why jitter.** You know this from every incident review you've run: deterministic backoff
synchronises the herd, so everyone returns at the same instant and the recovering service falls
over again. Full jitter — `sleep = uniform(0, base · 2^attempt)` — de-synchronises it and halves
expected wait as a side effect. And if the response carries `Retry-After`, obey it rather than
guessing.

### 2.8 Testing something non-deterministic

"You can't test LLM output" is false. People believe it because they're imagining one kind of
test. There are four, and only the last is fuzzy:

**Schema tests** — does the output parse into `ExtractionResult`? Deterministic, runs in CI, free
if you cache a fixture.

**Invariant tests** — properties that hold regardless of wording. Every `evidence_quote` is a
substring of its source; `detention_minutes >= 0`; any USD-per-hour rate is under 500.
Deterministic assertions about non-deterministic output, and the highest-value tests you'll write.

**Golden-fact tests** — facts the corpus definitely contains, asserted loosely: detention is
`$65/hour`, TONU is `$150`, the grocery DC window is `-30/+0 minutes`. Assert value and unit, not
phrasing.

**Regression snapshots** — store today's output, compare tomorrow's, flag a delta beyond
tolerance.

That fourth one is the mindset shift: **for LLM systems, some tests are alarms, not gates.** A
gate says "this is wrong, block the merge." An alarm says "this moved more than I expected, look
at it." Faithfulness dropping 0.86 → 0.81 is not a build failure — it might be noise, and Day 5
quantifies exactly how much. Wire it as a gate and you'll disable it within a week; a disabled
alarm measures nothing.

---

## 3. Worked example — on paper

> **Scenario.** You're batch-extracting policy facts from 600 documents. Mean call latency
> **1.2 s**; P95 **2.6 s**; P99 **4.5 s**. Each call is **1,500 input + 400 output tokens**.
> Your provider tier allows **500 requests/minute** and **200,000 tokens/minute**, and counts
> input + output against the token budget.

**Q1.** Sequential wall clock for all 600 calls?

**Q2.** Wall clock with `Semaphore(8)`, ignoring provider limits?

**Q3.** Which provider limit actually binds — RPM or TPM? What is your real maximum throughput
in requests/minute?

**Q4.** Using Little's Law, what in-flight count corresponds to that throughput? What semaphore
value follows?

**Q5.** Real wall clock at that throughput. What's the true speedup over sequential?

**Q6.** Retry policy: 3 total attempts, full jitter, base 1s, multiplier 2. Worst-case and
expected added sleep for a call that fails twice. If the transient failure rate is 4% per
attempt and independent, how many of the 600 calls fail permanently?

**Q7.** You set `timeout=3.0s`. Roughly what fraction of calls do you break yourself, and why is
the cost worse than the retry latency suggests?

<details>
<summary><b>Answers — do the arithmetic first</b></summary>

**Q1.** 600 × 1.2 = **720 s = 12 minutes**.

**Q2.** 720 / 8 = **90 s**. This is the number that makes people set the semaphore to 8.

**Q3.** RPM ceiling: **500 req/min**. TPM ceiling: 200,000 / 1,900 = **105.3 req/min**. **TPM
binds, by a factor of nearly five.** Your real ceiling is ~105 req/min = 1.75 req/s. This is why
"we're on the 500 RPM tier" is almost never the operative number, and why teams report throttling
at a fifth of their stated limit and blame the provider.

**Q4.** L = λ·W = 1.75 × 1.2 = **2.1 in flight**, so the correct semaphore is about **2**, not 8 —
plus a token-bucket limiter at 105 req/min, because the semaphore doesn't know about the token
budget and drifts over it as latency varies.

**Q5.** 600 / 105.3 = **5.7 minutes ≈ 342 s**. Speedup is **2.1×**, not 8×. The gap between the
90 s you expected and the 342 s you get is the whole lesson of §2.6.

**Q6.** Full jitter draws from U(0, 1) then U(0, 2): worst case **3 s**, expected **1.5 s**.
Permanent failures = 600 × 0.04³ = **0.038**, so you'd expect a clean batch ~96% of the time.
Meanwhile ~24 calls retry once, adding about 12 s across a 342 s run. **Retry is nearly free
here; concurrency misconfiguration cost you 4×.** Optimise in that order.

**Q7.** 3.0 s sits between P95 (2.6) and P99 (4.5), so you're killing between 1% and 5% — crudely
**~3%, about 18 calls**. Three compounding costs: each retry re-sends 1,500 input tokens you
already paid for; the retry draws from the same distribution, so ~3% of retries also time out;
and worst, the server-side generation was probably still running when you hung up — **you paid for
tokens you threw away.** A timeout belongs above P99 with headroom. It bounds pathological hangs;
it does not enforce a latency SLO. For that, shorten the output (Day 1, consequence 1).

</details>

---

## 4. What people get wrong

**"Constrained decoding means the output is correct."**
It means the output is *valid*. Shape and truth are orthogonal, and a schema-perfect wrong number
is harder to spot than a parse error, not easier. Pydantic checked types and ranges;
`detention_minutes: 45` passes every constraint you wrote and may still be fabricated.

**"asyncio makes the calls faster."**
It makes them *overlap*. Per-call latency is unchanged, and if your bottleneck is the provider's
token bucket, asyncio buys you nothing beyond the bucket rate — see §3 Q5.

**"More concurrency is more throughput."**
Only up to the binding constraint. Past it you get queueing, 429s, retries and worse tail latency
at the same throughput. Same curve as any thread pool you've ever tuned.

**"Retries make the system reliable."**
Retries make *transient* failures invisible. They make persistent failures slower and more
expensive, and under load they amplify — the retry storm is how a degraded provider becomes a
down one. Cap attempts, jitter, and put a breaker in front.

**"`confidence: 0.87` means the model is 87% sure."**
It's a token the model emitted because it looked plausible — not a calibrated probability, and
typically clustered around 0.85–0.95 regardless of truth. You'll measure how bad it is on Day 13.
Until then, don't threshold on it.

**"Money can be a float."**
$16.25 per 15-minute increment, forty increments, and floating-point rounding is now in an
invoice. Use `Decimal` for anything that reaches a ledger.

**"You can't test non-deterministic output."**
Three of the four patterns in §2.8 are fully deterministic. Only the snapshot is fuzzy, and it's
an alarm rather than a gate.

---

## 5. The trainer's angle

**The analogy that lands:** a pydantic model is an IDL, and the three levels are points on a
spectrum the room already knows. Level 1 is a REST endpoint returning untyped JSON and hoping.
Level 2 is validating at the boundary and returning a 400 the client can act on — except your
"client" is a model that reads the error and tries again. Level 3 is a protobuf wire format where
the invalid message is unrepresentable. This frames Level 2 as *the portable choice* rather than
the weak one, which is the point people miss.

For §2.6 the analogy is even more direct: **the semaphore is a connection pool and the rate
limiter is a token bucket.** Anyone who has tuned a pool knows what happens when you set it above
what the downstream absorbs. The only new fact is that LLM providers meter on tokens, so the
binding constraint moves with your prompt size.

**The demo that makes it click:** run Level 1 live and let it fail — ask a local model for JSON,
watch it return a markdown fence, watch `json.loads` raise. Then run it four more times and show
it succeeding three of those. **The intermittency is the lesson**: a 20% failure rate looks like
"works, mostly" in a demo and like an incident at 600 records. Then run Level 3 twenty times and
show zero violations.

**The question a sharp student will ask:** *"If Level 3 makes violations impossible, why would I
ever ship Level 2?"* Have this ready:

> Three reasons, in order of how often they decide it. Availability: you frequently don't control
> the model, and a client running Llama on-prem has no constrained-decoding endpoint — "switch
> providers" isn't a sentence you get to say in month one. Portability: a Level 2 extractor runs
> unchanged across every backend, which is what makes your Day 1 provider seam worth anything.
> And the genuinely contested one: grammar masking forces the model onto token paths it scored
> low, and there's published evidence that costs accuracy on tasks needing intermediate
> reasoning. The effect size is disputed. The practical answer is to use Level 3 where it exists
> *and* order your schema so the model reasons before it commits — good practice at every level.

---

## 6. Self-check

Cover the answers.

1. Why does "return JSON" fail even on a strong model? Answer in terms of the sampler.
2. Name four distinct ways Level 1 output breaks a `json.loads`.
3. What exactly does constrained decoding guarantee, and what does it not?
4. Why is Level 2 the default on client engagements rather than Level 3?
5. Why does field order in a pydantic model change output accuracy?
6. What does the evidence-quote substring check prove, and what can still be wrong?
7. Two reasons the substring check reports false negatives, and the fix.
8. State Little's Law and use it to convert `Semaphore(8)` at 1.2 s mean latency into RPM.
9. A semaphore and a rate limiter bound different quantities. Which is which, and why do you
   need both?
10. Which HTTP failures do you retry, and which do you never retry? Give the rule, not a list.
11. Why does deterministic backoff make an outage worse?
12. Name the four test patterns, and say which one is an alarm rather than a gate.

<details>
<summary><b>Answers</b></summary>

1. The sampler draws from a distribution your prompt only *conditions*. A schema instruction
   raises the probability of well-formed JSON; it never constrains the sampler.
2. Fences; prose preamble; trailing commas; wrong types; invented enum values; missing fields;
   truncation at `max_tokens`. (Any four.)
3. Guarantees syntactic validity — the invalid token is masked out. Guarantees nothing about
   whether the values are true, complete, or drawn from the source.
4. You often don't control the model. Level 2 runs on any endpoint, including local models with
   no structured-output support, which is the common on-prem case.
5. Generation is autoregressive and unrevisable, so earlier fields condition later ones. Evidence
   and reasoning before the number changes "guess then justify" into "locate then read off."
6. Proves provenance — the span exists verbatim in the source. Doesn't prove the span supports
   the claim; the model can quote a real sentence that says something else.
7. Unicode punctuation and whitespace differences. Normalise both sides — casefold, collapse
   whitespace, normalise punctuation — before comparing.
8. L = λ·W. 8 = λ × 1.2 → λ = 6.67 req/s = **400 RPM**.
9. Semaphore bounds in-flight requests (a pool); the rate limiter bounds arrivals per second (a
   bucket). Both, because the provider meters arrivals and tokens while your process is bounded
   by sockets and memory — and the mapping between them moves with latency.
10. Only transient *and* idempotent: 429, 500/502/503, connection resets. Never a 400, a 401, or
    a content-policy refusal — those fail identically forever, and retrying a 400 is retrying
    your own bug.
11. Every backed-off client returns at the same instant, so the recovering service takes a
    synchronised herd and fails again. Jitter spreads the return.
12. Schema, invariant, golden-fact, regression snapshot. The snapshot is the alarm — a delta means
    "look at this," not "block the merge."

</details>

**Scored below 8?** Re-read §2.6 and §2.7 before the lab. The async fan-out and the retry
decorator are where you'll actually lose time today, and the lab won't re-explain either.

---

## 7. Going deeper

<!--reading:02-->

### If you read one thing this week

**[Structured outputs (JSON outputs and strict tool use)](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)** — Anthropic · docs · ~25 min

This is Level 3 of §2.2 as an actual product surface — read the schema-complexity limits and the grammar-compilation caching notes, because those constraints are exactly what decide whether Level 3 is available to you or you fall back to Level 2 with a repair loop.

### Then, in the order I'd take them

- **[Efficient Guided Generation for Large Language Models](https://arxiv.org/abs/2307.09702)** — Brandon T. Willard & Rémi Louf (2023) · paper · ~40 min  
  The finite-state-machine construction under constrained decoding, and the section you want is §3 — it makes clear that the constraint masks logits rather than checking output, which is the distinction §2.3 hangs on.
- **[Let Me Speak Freely? A Study on the Impact of Format Restrictions on Performance of Large Language Models](https://arxiv.org/abs/2408.02442)** — Tam, Wu, Tsai, Lin, Lee & Chen (2024) · paper · ~30 min  
  The contested claim that forcing JSON costs you reasoning quality — read the tables, then note the methodology critiques, because a trainer who can describe a disputed result honestly is worth more than one who asserts it.
- **[Pydantic — JSON Schema](https://pydantic.dev/docs/validation/latest/concepts/json_schema/)** — Pydantic documentation · docs · ~20 min  
  `model_json_schema()` output is literally what you paste into the prompt at Level 2, so read how `Field` descriptions and constraints serialise — that serialisation is why §2.4's claim that field order is an instruction actually holds.
- **[Exponential Backoff And Jitter](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)** — Marc Brooker (AWS Architecture Blog, 2015) · essay · ~15 min  
  You have seen this before, but it is the canonical citation for §2.7 and the simulation graphs are the fastest way to win the 'why full jitter, not plain exponential' argument in a client's codebase.

<!--/reading-->

### Also mentioned in this module

- *Release It!* — Michael Nygard (2nd ed., 2018), on Circuit Breaker and Bulkhead. You've seen
  these; the value is having the vocabulary when arguing for them in someone else's codebase.
- *Let Me Speak Freely?* — Tam et al. (2024). Read it alongside its critiques; a good example of a
  contested result you should describe rather than assert.

---

**Now go to `labs/DAY_02.md`.** The lab is built on §2.2 (the three levels — you implement
Level 2 with the repair loop), §2.4 (schema design), §2.5 (evidence verification), §2.6 (the
semaphore, which you should size using §3's arithmetic rather than the default 4), and §2.8
(all four test patterns).
