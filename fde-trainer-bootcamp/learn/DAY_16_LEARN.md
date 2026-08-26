# Day 16 · Learn — Observability: what a span must carry, and the loop that outlives you

**Read before `labs/DAY_16.md`. Budget 1:15.** Pen and paper for §3 — the sampling, drift-detection and triage-yield arithmetic is the day.

---

## 1. Where this sits

Day 15 turned your stack into a service: streaming, timeouts, caches, guardrails. It runs, it
answers, it bills. What it does not yet do is **explain itself after the fact.**

Today is the day where twenty-three years of incident response is worth more than the preceding
fifteen days — and also the day where one reflex from that career will actively mislead you.

The reflex: in a normal distributed system, when a request goes wrong, the evidence is durable.
The row is in the database. The order is in the queue. The trace tells you which hop was slow and
what status code came back, and you reconstruct the rest from state that still exists. Tracing is
mostly a *latency-attribution* tool because correctness is recoverable elsewhere.

An LLM request has almost no durable state. The thing that determined the answer — the exact
assembled prompt, the five chunks that happened to win retrieval on that day's index, the model
version the provider was routing to — is constructed at request time, sent over the wire, and
thrown away. The database has the answer text and nothing that produced it.

So the trace stops being a performance tool and becomes **the only record of the function's
input**. That is the shift. When a client says *"it gave a bad answer yesterday afternoon,"* the
question is not "which service failed" — nothing failed — it's "what was in the context window at
14:12, and why that and not something else." If your span didn't capture it, that answer does not
exist anywhere in the world any more.

---

## 2. The mechanism

### 2.1 Why generic HTTP tracing under-determines an LLM failure

Take a concrete complaint. A dispatcher asks *"what's the detention on shipment
SHP-202608-0041729?"* and gets **$325**. The right answer is $195 — five hours at the dock, two
free, three chargeable at $65.

Here is what a normal, well-instrumented HTTP trace tells you:

```
POST /v1/ask                  200   4,412 ms
├─ GET  qdrant:6333/search    200      94 ms
├─ POST cohere/rerank         200     176 ms
└─ POST provider/messages     200   3,908 ms
```

Every span green. Every status 200. Latency unremarkable. This trace is completely consistent with
a correct answer and completely consistent with a $130 over-bill, and it cannot distinguish them.
It answers *did the machinery run* and the question is *what did the machinery decide*.

The four things it is missing, each of which is a different root cause:

| Missing attribute | Root cause it would have identified |
|---|---|
| `chunk_ids` + `scores` | Retrieval returned the "$65 per hour" chunk severed from the 2-hour free-time condition (Day 3 §2.6) |
| the full prompt | The chunk was there, but buried at position 4 of 5 and the model skipped it (Day 10) |
| `temperature`, `model` | Someone raised temperature to 0.9, or the provider rolled the model version underneath you |
| `retriever_config_hash` | Chunk size changed 500 → 1500 in a deploy on Tuesday |

You cannot tell those four apart without the attributes. And you cannot go back and get them,
because there is nothing to go back to.

### 2.2 The span tree, and what each node must carry

One span per operation, nested, with the trace_id threaded through async tasks and into the
agent's step loop. The shape:

| Span | Attributes that earn their place | Why this one |
|---|---|---|
| `request` | `trace_id`, `session_id`, `tenant`, `route`, `user_rating` | The join key for everything, including feedback that arrives twenty minutes later |
| `guard.input` | `verdict`, `rules_fired[]`, `redactions` | A false positive here looks to the user like a refusal (Day 15 §2.9) |
| `route` | `decision`, `confidence`, `model`, `tokens` | A misroute is silent quality loss; you need the confidence to find the near-misses |
| `retrieve` | `query`, `rewritten_query`, `k`, `candidate_count`, `chunk_ids[]`, `scores[]`, `retriever_config_hash` | The scores are the leading indicator (§2.5). The rewritten query is where half of retrieval bugs live |
| `rerank` | `model`, `in_count`, `out_count`, `score_deltas` | Tells you whether the reranker moved anything — a silently disabled reranker produces deltas of zero |
| `llm.generate` | `model`, `model_version`, `temperature`, `prompt_tokens`, `completion_tokens`, `cost_usd`, `finish_reason`, `cache_hit`, `prompt_hash`, `prompt_version`, **full prompt**, **full response** | Everything on this row is a distinct question you will be asked |
| `verify` | `citations_total`, `citations_verified`, `unverified_spans[]` | Your cheapest online quality proxy |
| `guard.output` | `verdict`, `rules_fired[]` | Same as input, other end |

Three of those deserve a sentence each because people leave them off.

**`finish_reason`.** A response truncated at max_tokens and a response that ended naturally look
identical in the answer field. Truncation is how a well-formed answer loses its last citation and
fails verification for a reason that has nothing to do with retrieval.

**`cache_hit`.** A semantic-cache hit at threshold 0.88 means the user's question was answered
with a *different* question's answer (Day 15 §2.6). When the complaint is "it answered something I
didn't ask", this single boolean is the whole diagnosis.

**`candidate_count` alongside `k`.** If you asked for k=5 and got 2 back, the filter or the ANN
search collapsed — and the model then answered confidently from two chunks. Day 17 §2.7 has the
mechanism; today you just need the number in the span.

### 2.3 Capture the full prompt — and the sampling policy that makes it affordable

The prompt is large. Four to five thousand tokens is twenty kilobytes of text per request, and the
instinct of anyone who has ever paid a logging bill is to store a hash and move on.

Resist it, and be precise about why. **A prompt hash tells you whether two requests were identical.
It cannot tell you what was wrong with either.** The exact case you need the prompt for — the one
complaint the client's VP is personally annoyed about — is the case where you need to read the
context and see that the demurrage paragraph was retrieved instead of the detention paragraph.
Storage is cheap; the debugging hour you spend trying to reproduce a request from three weeks ago
against an index that has since been rebuilt is not.

The policy that resolves the tension:

> **100% capture for errors and for low-rated responses. 10% otherwise.**

That is a *sampling* policy, not a redaction policy, and its shape matters: it is biased toward the
traces you will actually open. Unbiased head sampling — Dapper's original 1-in-1000 — is the wrong
instrument here, because the interesting population is tiny and known. This is tail sampling: make
the keep/drop decision after you know how the request went.

Also keep a skeleton for the 90% you drop the body of. A trace with attributes but no prompt still
gives you latency, cost, scores, config hashes and the metric aggregates. The thing you drop is
only the two large text fields.

And know where the threshold actually sits. §3 Q1 and Q2 do the arithmetic, and the answer at
pilot scale is genuinely surprising: **capture everything, the sampling policy saves you less than
a cent a month.** The policy is for the 2M-queries/month scenario, where it is the difference
between a manageable trace store and a compliance surface nobody wants to own.

### 2.4 Config version hashes — because "what changed on Tuesday?" is the first question

Every incident you have ever run had this shape: symptom appears, someone opens the deploy log,
and 70% of the time the answer is in the last change. Deploy markers on a Grafana graph are the
single highest-value piece of instrumentation in ordinary ops, and they work because code version
is a small, discrete, well-tracked thing.

An LLM system has four version axes and only one of them is in git in the way you're used to:

| Axis | What it covers | How it changes without a code deploy |
|---|---|---|
| `prompt_version` | The system prompt, tool schemas, few-shot examples | Someone edits a YAML file; a prompt-management UI |
| `retriever_config_hash` | Embedding model id, chunker + params, k, `ef_search`, hybrid weights, reranker model | A config map, an env var, a vector-DB setting |
| `corpus_version` | The index build id and the document set inside it | **A nightly ingestion job.** No human action at all |
| `model_version` | The provider's actual served checkpoint | **The provider rolls it.** You are not consulted |

The bottom two are the ones that make this different from ordinary ops. Your corpus changes on a
schedule, and your model changes on someone else's schedule. Neither shows up in `git log`.

So stamp all four on the span. `retriever_config_hash` is a hash of the whole serialised retrieval
config object, not of individual fields — you want one value that changes when anything relevant
changes.

**And write the config object itself somewhere resolvable.** A hash you cannot expand back into a
config is a fingerprint with no database behind it: it tells you Tuesday differs from Monday and
not how. A tiny append-only table mapping `hash → full config JSON → first_seen → last_seen` costs
nothing and turns "what changed on Tuesday" into a two-line query.

### 2.5 The metric set, and why per-node latency beats total latency

| Category | Metric | Why it's on the dashboard |
|---|---|---|
| **Traffic** | req/s by route and tenant | The denominator for everything else |
| **Latency** | p50/p95/p99 **per node** | See below — this is the important row |
| **Cost** | $/request, $/tenant/day, tokens by model | The number your sponsor watches, and the one that gets the project cancelled |
| **Quality** | citation verification rate, refusal rate, guard block rate | Online proxies, available on 100% of traffic |
| **Retrieval** | mean top-1 score, score distribution, zero-result rate | Leading indicator — §2.6 |
| **Feedback** | thumbs up/down rate, comment rate | Ground truth, and very sparse |
| **Errors** | **by type**: timeout, provider 5xx, context overflow, guard block, schema violation | Never one number |

Two of these need arguing rather than listing.

**Per-node latency.** Total latency is dominated by generation — 3,900 ms of a 4,400 ms request in
the example above. That means every other node is hiding inside the noise of one big number. If
`retrieve` p95 doubles from 95 ms to 190 ms, total p95 moves 2%, which is invisible against any
sane alert threshold. The retrieve node moved 100%, which is not. §3 Q3 does the arithmetic.

The second reason is attribution, and it is the reason you will actually feel: total latency tells
you there is a problem, per-node tells you which of your seven components caused it, and in an
incident that difference is measured in tens of minutes.

There is a third property worth knowing because someone will point at it in a review: **the p95 of
the total is not the sum of the p95 of the parts.** For roughly independent components the total's
p95 is *less* than the sum, because it's unlikely that every node has a bad day on the same
request. So a per-node dashboard that sums to more than your measured total is not broken; that's
the expected relationship. It breaks the other way — sum below total — when the slowness is
*correlated* across nodes, which is itself a finding: shared resource contention, a saturated
host, a noisy neighbour.

**Errors by type.** A single error rate averages together failures with opposite responses. A
provider timeout means retry with backoff and check the status page. A context overflow means your
retrieval is returning too much and you need to prune. A guard block may be a correct refusal or a
false positive. Bucketing them together produces a number that goes up and tells you nothing about
what to do, which is the definition of a bad metric.

### 2.6 The underrated leading indicator: the retrieval score distribution

Every other quality signal on that dashboard is *lagging*. Citation verification drops after the
answers have already gone out. Thumbs-down arrives after a user was annoyed enough to click.
Refusal rate moves after users have already been refused.

The retrieval score distribution leads all of them, because retrieval happens before generation and
its inputs — the corpus, the embedding model, the chunker — are exactly the things that change
underneath you without a code deploy.

The mechanism is simple. Mean top-1 cosine on your corpus sits at 0.81 with a spread of about 0.06.
Any of the following moves it, and none of them raises an exception:

| Change | Effect on the distribution | Why |
|---|---|---|
| Nightly ingestion re-chunks a document at a different size | Mean drops for queries against that document | The chunk that used to match the query cleanly now averages two topics (Day 3 §2.6) |
| The embedding provider ships a new model version | Whole distribution shifts | Scores are not comparable across models at all (Day 3) — the geometry changed |
| Index rebuilt with the new embeddings, queries still on the old | **Catastrophic drop**, near-random results | Two different geometries; the numbers are meaningless |
| A new tenant's documents are indexed | Mean drops slightly, low tail fattens | More near-neighbours competing; also a possible pipeline mismatch |
| `ef_search` lowered to cut latency | Mean drops slightly, occasional bad miss | Approximation error (Day 3 §2.8) |

If mean top-1 drifts 0.81 → 0.68 over a week, something on that list happened. You see it days
before users complain, because a user only complains when the degraded retrieval happens to
produce an answer they can tell is wrong, and most degraded retrieval produces answers that are
merely worse.

Three disciplines make the alert usable rather than noisy.

**Alert on both the centre and the tail.** A change that affects one document or one tenant barely
moves the mean and visibly fattens the low tail. Track mean top-1 *and* the fraction of queries
with top-1 below a floor (0.55 on our corpus). §3 Q5 is exactly this case.

**Segment by route, tenant and corpus_version.** Score distributions move when the *query mix*
moves, which is not a defect. A new tenant asking harder questions looks identical in the aggregate
to a corpus regression. Segmentation separates them; that's what the span attributes are for.

**Expect a step change when the embedding model changes, and don't page on it.** This is the case
where the alert is correct and the response is "rebaseline". Which you can only tell because the
span carries the config hash — otherwise you spend an afternoon on it.

### 2.7 PII in traces is a decision made at write time

You are about to start storing, in full, every question a freight controller types and every
document paragraph the system retrieved to answer it. Some of those contain a driver's name, a
phone number, an address, sometimes a rate a carrier considers commercially confidential.

The compliance problem is not "should we redact." It is that **redaction is a write-time decision
and everything else about it is downstream.** Once a raw prompt lands in your trace store you have
created a copy of personal data in a new system with a new retention period, a new access control
list, and a new answer to a subject-access request. You cannot un-write it by adding a filter next
month; you have to go and delete, and you have to be able to prove you did.

The three postures, and what each costs:

| Posture | What's stored | Cost | Where it fits |
|---|---|---|---|
| **Full capture, restricted store** | Everything, short TTL (7–30 days), tight IAM, audit log on reads | Best debugging; largest compliance surface; needs a named owner | Regulated clients who accept it *because* the retention is short and the access is logged |
| **Redact at the span boundary** | Detected entities replaced with `[PERSON_1]`, `[PHONE_1]` before the span is written | Debugging survives mostly intact — the structure and the retrieved policy text are what you need; entity linking is lost | The default. Start here |
| **Hash + pointer** | Prompt hash on the span; body in the system of record | Minimal new surface; you must join to debug and the source may have rotated | Where a client's counsel says no copies |

Two practical notes. Redaction is itself a detector with a false-negative rate — say so rather than
promising it catches everything, because it doesn't, and the honest version of that sentence is
what a privacy officer wants to hear. And **whatever you choose, write it down in a paragraph you
can hand over**; on Day 17 it becomes answer 5 of the eight security questions, and a client's
privacy officer will read it.

### 2.8 The feedback loop — the thing that makes the system improve after you leave

```
user thumbs-down  ─┐
unverified citation ├─→  trace with full prompt, chunks, scores, config hashes
zero-result retrieve┘              ↓
                        triage into one of five classes
                                   ↓
                        real failure → labelled eval case
                                   ↓
                        appended to the golden set (Day 13)
                                   ↓
                        fix → CI gate proves it fixed, and that nothing else broke
```

The triage step is the part that carries the information, and it works because the five classes
have **different owners and different fixes**:

| Class | The signal in the trace | Fix | Becomes an eval case? |
|---|---|---|---|
| **Retrieval miss** | Gold chunk not in `chunk_ids`, or present with a low score | Chunking, hybrid weights, reranker, k (Day 14) | Yes — with the gold chunk id as ground truth |
| **Generation error** | Gold chunk *was* retrieved, answer contradicts it | Prompt, context ordering, citation enforcement (Day 4) | Yes — faithfulness case, and the strongest kind |
| **Correct-but-unhelpful** | Answer is faithful and useless: "detention is $65/hour" when they asked what they owe | Answer shape, not retrieval. Often a product decision | Yes — but graded against a *usefulness* rubric, not faithfulness |
| **Bad question** | Ambiguous, missing referent, or asks for something not in the corpus | Nothing to fix in retrieval. Sometimes a clarifying-question behaviour | Yes — as an absent-fact or false-premise adversarial case (Day 13 §2.4) |
| **Guard false positive** | `guard.input.verdict = block` on a legitimate question | Rule tuning; measure the FP rate (Day 15 §2.9) | Yes — into the guard's own regression set |

Two properties of this loop that are easy to miss.

**Thumbs-down is sparse and biased, so it cannot be your only trigger.** Feedback rates on internal
tools run low single digits, and the users who click are not a random sample — they're the ones
with the confidence to say the machine is wrong, which skews toward power users and toward
obviously-wrong answers. The confidently-wrong answer that a junior dispatcher believes and acts on
generates no feedback at all. That's why the loop's inputs include the *automatic* triggers:
unverified citation, zero-result retrieval, top-1 below floor, refusal, guard block, truncated
`finish_reason`. §3 Q6 shows the volume ratio, and it is about 15:1 in favour of the automatic ones.

**The score goes down, and that is the success condition.** When you add ten real failures to a
250-case golden set, the suite gets harder and the number drops. A client who reads that as
regression needs the framing given to them in advance: the suite is now measuring a population
that includes your known failures, so the number is more honest and less flattering. Say it before
the number moves, not after.

---

## 3. Worked example — on paper

> **Setup, with the assumptions stated because they're assumptions.** Pilot deployment: 40 users ×
> 8 queries/day × 22 working days = **7,040 queries/month**. Average assembled prompt 4,800 tokens
> ≈ **19 KB** of text; average response 340 tokens ≈ **1.4 KB**; span skeleton attributes (ids,
> scores, hashes, counts) ≈ **2 KB**. So a full-body trace is ~**24 KB**, a skeleton-only trace is
> ~**2 KB**. Error rate 2.0%, low-rated rate 1.5%, treat as disjoint. Object storage assumed at
> **$0.023 per GB-month** — a plausible figure for commodity blob storage in 2026, and it drifts;
> re-check before you quote it.

**Q1.** Under the policy *100% for errors and low-rated, 10% otherwise*, what fraction of traces
keep the full body? What is the monthly trace storage, versus capturing 100% of bodies?

**Q2.** Convert both to dollars per month at the assumed storage price. Then redo the 100%-capture
number for Scenario C — 2,000,000 queries/month — and for a 12-month retention period. What is the
actual argument for the sampling policy, and at what scale does it start?

**Q3.** Measured p95 per node: `guard.input` 15 ms, `route` 210 ms, `retrieve` 95 ms, `rerank`
180 ms, `llm.generate` 3,900 ms, `verify` 40 ms, `guard.output` 25 ms. Measured total p95 =
4,400 ms. (a) Why is the sum of the per-node p95s larger than the total p95? (b) `retrieve` p95
doubles to 190 ms. Estimate the new total p95 and the percentage change. Your soft gate is "p95 up
more than 20%". Which alert fires?

**Q4.** Retrieval scores: reference window mean top-1 = **0.810**, σ = **0.060**, and you serve
**200 queries/day** at that route. What is the standard error of the *daily* mean? A corpus change
starts a linear drift from 0.810 to 0.680 over 7 days. On which day does a 3σ alert on the daily
mean fire? How often would that alert false-positive on a stable metric?

**Q5.** A different week: the daily mean top-1 is unchanged at 0.810, but the fraction of queries
with top-1 below 0.55 has gone from **4.0%** to **7.0%** measured over the full week (1,400
queries). Is that significant? What single class of change produces this shape — flat mean, fatter
low tail?

**Q6.** Triage yield. Feedback rate 1.8% of queries; 22% of those are thumbs-down. Separately, 6%
of all queries produce at least one unverified citation. At 90 seconds of human triage per item,
how many hours per month does each stream cost? What does that imply about how you build the tool?

**Q7.** Detection latency. Your nightly CI runs the 250-case suite. The stretch goal is online
eval: run the Day 13 judge on 5% of live traffic. At pilot traffic (7,040/month over 22 working
days), how many judged samples per day? How many days of online sampling to get a ±5-point 95%
confidence interval on faithfulness (`sd = √(0.25/n)`, ×1.96)? Redo it for Scenario C at
2,000,000 queries/month over 22 days. What's the conclusion?

<details>
<summary><b>Answers — do the arithmetic first, Q2 and Q7 are the ones that change a decision</b></summary>

**Q1.** Forced full capture = 2.0% + 1.5% = 3.5%. Of the remaining 96.5%, 10% → 9.65%. Total full
bodies = **13.15%**.

Full-body traces: 7,040 × 0.1315 = **926** × 24 KB = **22.2 MB**.
Skeleton traces: 6,114 × 2 KB = **12.2 MB**. Total ≈ **34.4 MB/month**.
100% capture: 7,040 × 24 KB = **169 MB/month**. Sampling saves ~135 MB.

**Q2.** 0.169 GB × $0.023 = **$0.0039/month**. The sampled policy: 0.034 GB × $0.023 =
**$0.0008/month**. **The sampling policy saves you a third of a cent per month.**

Scenario C at 100%: 2,000,000 × 24 KB = **48 GB/month**, so a 12-month retention holds ~576 GB
≈ **$13/month** of raw storage. Still small — and that is the trap. The real cost at that scale is
not blob storage: it is the trace backend's ingestion and indexing tier (usually priced per GB
ingested or per span, one to two orders of magnitude above blob), the query performance over
billions of spans, and — the one that actually bites — **576 GB of user text under a retention
policy somebody now has to own, defend in a SOC 2 audit, and delete on request.**

So the honest FDE answer, and it's the opposite of the reflex: **at pilot scale, capture 100% and
say so.** The sampling policy is a scale-C control. Build the sampler on day one because retrofitting
it is painful, set it to 100%, and write down the traffic level at which you'll turn it down.

**Q3.** (a) Because a request only hits the total p95 if it was slow *overall*, not if each node
independently had a bad day. With roughly independent nodes, the probability that all seven are
simultaneously at their own 95th percentile is vanishingly small, so **p95(total) < Σ p95(node)**.
Sum here = 4,465 ms vs. total 4,400 ms — consistent. (If the sum came out *below* the measured
total, that would indicate correlated slowness — shared saturation — and would itself be the
finding.)

(b) Retrieve adds ~95 ms → total p95 ≈ **4,495 ms**, a **+2.2%** change. The 20% soft gate on total
latency does **not** fire. The per-node view shows `retrieve` at **+100%**, which any sane threshold
catches. **That single comparison is the entire argument for per-node latency**, and it's the one to
put on screen in a teach-back: 2.2% versus 100%, same event.

**Q4.** SE of the daily mean = 0.060/√200 = **0.00424**. 3σ threshold = **0.0127**.
Drift = (0.810 − 0.680)/7 = **0.0186/day**. After day 1 the mean is 0.7914, a drop of 0.0186 >
0.0127 — **the alert fires on day 1**, six days before the drift completes and well before the
complaint volume moves.

False-positive rate: a two-sided 3σ test on a stable normal metric fires with probability ~0.0027,
i.e. about **one false page every 370 days per metric**. Which is why 3σ and not 2σ: at 2σ you'd be
paged roughly every three weeks for nothing, and by month two the alert is muted (Day 13 §2.9 — same
social decay, different metric).

**Q5.** Under the null p = 0.040, n = 1,400: sd = √(0.040 × 0.960 / 1400) = **0.00524**.
z = (0.070 − 0.040)/0.00524 = **5.7σ**. Unambiguously significant, while the mean did not move.

Sanity-check why the mean didn't move: if 3% of queries fell from ~0.80 to ~0.45, the mean shifts
by 0.03 × 0.35 = 0.0105 — about 2.5 SE on a *daily* window, under a 3σ gate. The mean genuinely
hides it.

The shape — flat centre, fat low tail — is the signature of a change affecting **a subset of the
corpus or a subset of the queries**, not the whole system: one document re-chunked, one tenant's
documents indexed through a mispointed pipeline, or a new query type entering the mix. Segment by
`tenant`, `route` and `corpus_version` and the subset names itself.

**Q6.** Feedback: 7,040 × 1.8% = 127 ratings; × 22% = **28 thumbs-down/month**. At 90 s that is
**42 minutes/month** — trivially affordable, do it by hand, every one.

Unverified citations: 7,040 × 6% = **422/month**. At 90 s that is **10.6 hours/month**, which is
not affordable and will not happen.

Two consequences for the tool. **Cluster before you triage** — group by retrieved chunk id and by
query embedding, because 422 items are not 422 distinct problems; ten clusters usually cover half
of them. And **sample the long tail, triage the head exhaustively**. The ratio is the other lesson:
**automatic triggers produce ~15× the volume of user feedback.** A loop wired only to thumbs-down
sees 6% of its available evidence.

**Q7.** Pilot: 7,040/22 = 320 queries/day; 5% = **16 judged/day**.
n for ±5 points: 0.25 × (1.96/0.05)² = **384 samples** → 384/16 = **24 days**.

Scenario C: 2,000,000/22 = 90,909/day; 5% = **4,545/day** → 384 samples in **under two hours**; a
full day gives ±1.5 points.

Conclusion, and it's the one worth carrying into the lab's stretch goal: **at pilot traffic, online
eval has essentially no statistical power and your nightly offline suite is the detector** — 250
fixed cases at n=250 beat 16 noisy live samples, and the CI suite catches a regression the same
night. Online eval becomes the faster detector somewhere in the hundreds of thousands of queries
per month, at which point it detects in hours what CI detects in a day. Knowing *which regime the
client is in* is the answer; recommending online eval at pilot scale is expensive theatre.

</details>

---

## 4. What people get wrong

**"We already have distributed tracing, so we're covered."**
You have latency attribution. You do not have the prompt, the chunk ids, the scores, or the config
hashes — and the failure mode here is a 200 with a wrong answer, which every existing span shows as
healthy.

**"Log the prompt hash, not the prompt."**
A hash answers "were these two requests the same?" It cannot answer "what was wrong with this one",
which is the only question anyone asks.

**"Sample traces at 1% like we always have."**
Uniform head sampling optimises for a large uninteresting population. Your interesting population
is errors and low-rated responses, and it's tiny — so sample on the tail, after you know the
outcome, and keep 100% of the interesting classes.

**"Redaction is a logging concern; we'll add a filter later."**
Once a raw prompt is written, you own a copy of personal data with a retention period and a
subject-access obligation. It's a write-time decision.

**"Alert on p95 latency."**
Alert on p95 latency *per node*. Generation dominates the total so completely that a doubling
anywhere else is invisible in the aggregate — 2.2% versus 100% in §3 Q3.

**"One error rate."**
Timeout, provider 5xx, context overflow, guard block and schema violation have four different
responses and one of them isn't an error at all. A combined number tells you to do nothing in
particular.

**"Retrieval scores are an internal detail."**
The score distribution is the only *leading* quality signal you have. Everything else on the
dashboard tells you about answers that already went out.

**"Mean top-1 is flat, so retrieval is fine."**
A change confined to one document or one tenant fattens the low tail and barely moves the mean.
Track both, and segment — because the converse error is just as common: a dropped score also
follows an embedding model version change, a new tenant, or a shift in query mix. The alert is a
question, not a verdict, and the config hashes are how you answer it.

**"We collect thumbs-down, so we have a feedback loop."**
You have a feedback *collector*. It's a loop when a thumbs-down becomes a labelled eval case in a
regression suite. Without that last hop it's theatre, and users notice within a month that clicking
the thumb changes nothing.

**"The golden set score dropped after triage — we regressed."**
The suite got harder. That's the loop working. Frame it before the number moves.

**"A thirty-panel dashboard is thorough."**
It's unread. Six panels on one screen is a forcing function for deciding what actually drives a
decision, and the discipline is the deliverable.

---

## 5. The trainer's angle

**The analogy that lands with an ops room:** a trace is a flight data recorder, not a log. The
distinction people feel immediately is that a log records *that* something happened and a recorder
captures *the state of every control surface at that moment*, because the investigation happens
after the aircraft is gone. Your LLM request is gone the instant it returns — the prompt was never
persisted anywhere else — so the recorder is not a nice-to-have, it's the only evidence chain that
will ever exist.

**The second analogy, for the config hashes:** deploy markers on a dashboard. Everyone has used
them and everyone trusts them. Then the twist that makes the point land: *your corpus redeploys
itself every night at 2am, and your model gets redeployed by a vendor who doesn't tell you.* Two of
your four version axes are outside your change management. That's why the version goes on the span
rather than in the deploy log.

**The demo that makes it click:** open one real trace in Phoenix and scroll to the prompt. Read the
retrieved chunks out loud. A room that has been told "the model hallucinated" for six months watches
you point at the actual paragraph that got retrieved and say *"it didn't hallucinate, it answered
this."* Ten seconds. It reframes every conversation they've had about the system.

**The second demo:** the 2.2% versus 100% number from §3 Q3, on screen, with the total-latency chart
next to the per-node chart. The total chart is flat. The retrieve chart has a step in it you can see
from the back of the room.

**The predictive question before you run anything:** *"I'm going to open the ten most expensive
requests from last week. What do you think they'll have in common?"* Collect two guesses — people
say "long answers" or "the big model". It's almost always agent step count or a retrieval that
returned unusually long chunks, and being wrong in public for five seconds is what makes the answer
stick.

**The question a sharp student will ask:** *"We already pay for Datadog. Why do I need a new tool
for this?"* Have this ready:

> You don't, necessarily — and I'd rather you didn't add a vendor if you don't have to. What you
> need is the *attribute schema*: the chunk ids, the scores, the config hashes, the prompt and the
> response, on nested spans, with the trace id threaded through the async work. Any OpenTelemetry
> backend will take those; there are emerging GenAI semantic conventions for the attribute names
> and I'd follow them so you're not inventing a private vocabulary. The two things a purpose-built
> LLM tool buys you are a UI that renders a prompt readably instead of as a 20 KB string blob, and
> the ability to *search by retrieved chunk id* — "show me every request that retrieved chunk
> 02-detention-b in the last month" is a query you will run constantly and a general APM tool makes
> awkward. That's a UX and cardinality argument, not an architecture one. Start in the stack you
> already operate; move if the queries you need are the ones it's bad at.

**The follow-up they'll ask next:** *"Isn't storing every prompt a GDPR problem?"* Yes, and §2.7 is
the answer — but the shape of the answer matters more than the content. Don't say "we redact PII."
Say: here is the posture, here is the retention period, here is who can read it and where the access
audit lives, and here is the false-negative rate of the redactor. A privacy officer has heard "we
redact PII" from every vendor; the number is what tells them you've actually thought about it.

---

## 6. Self-check

Cover the answers.

1. Why is a trace more load-bearing for an LLM system than for a normal CRUD service? Name the
   property that causes it.
2. A trace shows all spans at 200 with unremarkable latency and the answer was wrong. Name four
   distinct root causes and the span attribute that distinguishes each.
3. Why capture the full prompt rather than a hash?
4. State the sampling policy and explain why it's tail sampling rather than head sampling.
5. Name the four version axes, and which two change without a code deploy.
6. Why must a config hash be resolvable back to a config object?
7. Why does per-node latency beat total latency? Give both the detection argument and the
   attribution argument.
8. Is p95(total) bigger or smaller than Σ p95(node), and what does the other direction indicate?
9. Why is the retrieval score distribution a *leading* indicator when citation verification is not?
10. Mean top-1 is flat but the below-0.55 rate has doubled. What class of change does that shape
    point at, and what do you segment by?
11. Name the five triage classes and say which one's fix is not a retrieval or prompt change.
12. Why can't thumbs-down be the only input to the feedback loop? Give two reasons.

<details>
<summary><b>Answers</b></summary>

1. The state that determined the answer — the assembled prompt, the retrieved chunks, the model
   version — is constructed at request time and discarded. Nothing else persists it, so the span is
   the only record of the function's input.
2. Retrieval miss (`chunk_ids` + `scores`); context ordering / lost-in-the-middle (the full prompt);
   temperature or model version change (`temperature`, `model_version`); a config change such as
   chunk size (`retriever_config_hash`).
3. A hash tells you whether two requests were identical and nothing about what was wrong with
   either. The debugging question is always "what was in the context", which requires the text.
4. 100% for errors and low-rated responses, 10% otherwise. It's tail sampling because the keep/drop
   decision is made after the outcome is known; head sampling would keep a uniform slice of a
   population that is 96% uninteresting.
5. `prompt_version`, `retriever_config_hash`, `corpus_version`, `model_version`. The last two:
   corpus changes on the ingestion schedule, model changes when the provider rolls it.
6. Otherwise it only tells you that Tuesday differs from Monday, not how. Keep an append-only
   `hash → config JSON → first_seen → last_seen` table.
7. Detection: generation dominates the total, so a 100% regression in a small node is a ~2% change
   in the aggregate and no sane threshold fires. Attribution: in an incident, "there's a problem"
   versus "it's the reranker" is tens of minutes.
8. Smaller — a request only reaches the total p95 if it was slow overall, not if each node
   independently had a bad day. The sum coming out *below* the measured total indicates correlated
   slowness: shared saturation or a noisy neighbour.
9. Retrieval happens before generation, and its inputs (corpus, embedding model, chunker) change
   without a deploy. Citation verification, refusal rate and feedback all measure answers that have
   already been served.
10. A change confined to a subset — one document re-chunked, one tenant's documents indexed through
    the wrong pipeline, or a new query type in the mix. Segment by tenant, route and corpus_version.
11. Retrieval miss, generation error, correct-but-unhelpful, bad question, guard false positive.
    Correct-but-unhelpful is usually an answer-shape or product decision, not a retrieval or
    faithfulness fix.
12. It's sparse (low single-digit percentage of queries) and it's biased — confident users clicking
    on obviously-wrong answers. The confidently-wrong answer a junior user believes generates no
    feedback at all. Automatic triggers produce roughly 15× the volume.

</details>

**Scored below 9?** Re-read §2.4 and §2.6. The lab's incident drill gives you a planted regression
and no `git diff`, and the only two things that will find it in under fifteen minutes are the config
hashes on the span and the retrieval score panel on the dashboard.

---

## 7. Going deeper (optional)

- *Dapper, a Large-Scale Distributed Systems Tracing Infrastructure* — Sigelman et al., Google,
  2010. The original. Read the sampling section specifically, then reread §2.3 and notice that the
  LLM case inverts its central assumption: Dapper samples uniformly because the interesting
  population is unknown, and you sample on the tail because yours is known and tiny.
- *Site Reliability Engineering* — Beyer et al., 2016, chapter 6 ("Monitoring Distributed Systems").
  The four golden signals and, more usefully, the argument about symptom-based versus cause-based
  alerting. §2.6's score distribution is a cause-based alert, which the chapter is sceptical of —
  worth reading the scepticism and forming your own view before you teach it.
- *Observability Engineering* — Majors, Fong-Jones and Miranda, 2022. The high-cardinality argument.
  Chunk ids and prompt hashes are exactly the kind of dimension the book says traditional metrics
  systems handle badly, and it explains why.
- *Hidden Technical Debt in Machine Learning Systems* — Sculley et al., NeurIPS 2015. Pre-dates all
  of this and still the sharpest statement of why ML systems rot in ways ordinary services don't.
  The CACE principle ("changing anything changes everything") is §2.4's justification.
- OpenTelemetry's **GenAI semantic conventions** — the `gen_ai.*` attribute namespace. Worth reading
  so your span attribute names match what tooling expects rather than being a private vocabulary.
  Check the current status before you rely on it: this area has been evolving and marked
  experimental, so treat the specific attribute names as a moving target and the *shape* as stable.
- Arize Phoenix docs — the tool the lab uses. Read the tracing quickstart and the "sessions" concept
  before Block 2; it'll save you twenty minutes.

---

**Now go to `labs/DAY_16.md`.** The lab builds directly on §2.2 (the span attribute set you'll
instrument), §2.4 and §2.6 (the config hashes and the score-distribution panel — between them,
these are what solve the planted-regression drill without a `git diff`), §2.5 (the six-panel
dashboard), and §2.8 (the triage tool and the five classes it makes you choose between).
