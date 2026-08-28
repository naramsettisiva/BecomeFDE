# Day 17 · Learn — Deployment topologies, the egress question, and the handover

**Read before `labs/DAY_17.md`. Budget 1:15.** Pen and paper for §3 — the KV-cache and concurrency arithmetic is the part that changes an architecture.

---

## 1. Where this sits

Yesterday you made the system explain itself. Today you move it somewhere that isn't your laptop —
and the word in your job title is *forward deployed*, so "somewhere" means a client's environment,
which has a VPC, a change advisory board, a security team with a spreadsheet, and no internet
egress from the application subnet.

You have deployed services into other people's infrastructure for twenty-three years. Most of what
you know transfers directly: images, health checks, IAM, rollback, blue/green. Three things don't,
and they're the three that decide the engagement.

**The first is that one network question reshapes the entire architecture.** In a normal migration,
"can this subnet reach that database" is a firewall ticket. Here, the equivalent question — can
request data leave the client's boundary — has an answer that either lets you keep the model you
prototyped with or forces you onto self-hosted open weights, GPU capacity planning, and a model
several capability tiers below the one your evals were built against. Ask it in the first meeting
or find out in week six.

**The second is that a healthy service can be completely broken.** A 200 with a fabricated answer
passes every check in your normal repertoire. The deploy pipeline needs a test that can tell the
difference, and it turns out there is exactly one cheap test that can.

**The third is that the deliverable isn't the service.** It's the document set that lets their team
run it without you — and specifically the runbook, which is the artifact that decides whether you
get referred to the next team.

---

## 2. The mechanism

### 2.1 The four topologies and the constraint each one hits

| Topology | Where it runs | Typical client | The constraint that bites |
|---|---|---|---|
| **Managed PaaS** (HF Spaces, Render, Railway, Fly) | Vendor's cloud | Startups, demos, your portfolio | No VPC peering, so no private path to their data; secrets live in the vendor's store; you inherit their region list |
| **Container in the client's cloud** (ECS/Fargate, Cloud Run, ACA) | Client's account | Mid-market | IAM task roles, VPC endpoints for every AWS service you touch, image scanning in their registry, and their tagging/cost-allocation rules |
| **Kubernetes** | Client's cluster | Enterprise with a platform team | You are now a tenant of another team's platform: their Helm conventions, their admission controllers, their pod security standards, their release train. Technical work is small; the calendar is not |
| **Fully air-gapped** | On-prem, no egress | Defence, healthcare, parts of finance and pharma | **No hosted model exists for you.** Self-hosted weights, GPU sizing, throughput math, and a much smaller model than you prototyped with |

The first three differ mostly in ceremony. The fourth is a different engagement.

A useful way to hold it: rows one to three are *deployment* decisions and row four is an
*architecture* decision that happens to be triggered by a network fact. Which is why the question
that separates them comes first.

### 2.2 The egress question — and why it's actually three questions

"Can data leave your VPC?" is the question everyone knows to ask. It's not enough, because a client
who says "no" may mean any of three quite different things, and the architectures diverge sharply.

| Question | A "no" means | What it forces |
|---|---|---|
| **1. Can request data traverse the public internet?** | Traffic must stay on private network paths | A PrivateLink / VPC endpoint to a managed model service. Architecture otherwise unchanged. This is the easy no |
| **2. Can request data leave the client's cloud account or tenancy — even privately?** | Inference must happen on compute they own | **Self-hosted weights.** A VPC endpoint keeps traffic off the internet, but inference still executes in the provider's service account. Different boundary, different answer |
| **3. Can data leave the jurisdiction?** | Region pinning, and a check that the model you want is *offered* in that region | Frequently the model menu shrinks. Your frontier model may not be available in the region their DPA requires |

Question 2 is the one that catches people, and it catches them late. An architect says "nothing
leaves our VPC," you propose a managed model behind a VPC endpoint, everyone nods, and in week six
their security team reads the service description and points out that the inference is executing on
the provider's fleet. Now you are rebuilding on open weights, six weeks in, against evals calibrated
on a model you can no longer use.

Ask all three, in that order, in the first technical meeting. Then ask the fourth, which is about
time rather than space: **does the provider retain prompts, for how long, and is there a
zero-retention option you have to enable rather than one you get by default?** That's a contractual
question with a technical checkbox behind it, and it's answer 1 of the eight in §2.6.

### 2.3 What an air-gapped answer actually changes

If the answer to question 2 is no, here is the shape of what changes. Not "you self-host the model"
— that's one line. Everything downstream of it:

| Dimension | Hosted | Self-hosted, air-gapped |
|---|---|---|
| **Model** | Frontier class | 8B–70B open weights, usually quantised |
| **Capability** | Handles multi-hop synthesis, follows long instructions | Needs scaffolding: tighter retrieval, harder reranking, shorter prompts, enforced structured output, more decomposition into small steps |
| **Cost shape** | Variable per token; zero at zero traffic | **Fixed per GPU-hour**, whether or not anyone asks a question |
| **Capacity planning** | The provider's problem | Yours, and it is a *memory* problem before it's a compute problem (§3 Q1–Q3) |
| **Availability** | Provider's SLA | Yours. Two GPUs minimum, or your rolling deploy is an outage |
| **Model updates** | Arrive whether you want them | Never arrive unless you do it — which is a benefit for reproducibility and a liability for capability |
| **Your evals** | Ported unchanged | **Ported unchanged — and this is the point.** The eval suite is the only thing that tells you what the smaller model costs you in quality, and it's why Days 5/13 were worth the time |

The last row is the one to say out loud in a client meeting. When someone asks "can we run this on
an 8B model on our own hardware?", the honest answer is *"I don't know, and I can tell you in a
day, because we have 250 cases and a calibrated judge."* Nobody else in the room can say that.

And the arithmetic that determines how many GPUs: at long context, **concurrency is bounded by KV
cache memory, not by compute.** Each in-flight request holds a per-token key/value cache in GPU
memory for its entire generation. That's a connection-pool sizing problem with a memory budget, and
it's §3 Q1–Q3.

### 2.4 Container discipline

Nothing here is new to you; it's a checklist you already believe in. It's here because two items on
it have LLM-specific consequences.

- **Multi-stage build.** Builder stage installs; runtime stage copies only the virtualenv. Keeps
  compilers, headers and package caches out of the shipped image.
- **Non-root.** `useradd -m -u 10001 app`, `COPY --chown`, `USER app`. Many enterprise clusters have
  an admission controller that rejects root containers outright, so this is a deploy blocker rather
  than a nicety.
- **`.dockerignore`.** `.venv`, `.git`, `data/corpus`, recordings, notebooks. `.git` is the one that
  silently adds hundreds of megabytes and, worse, ships your history.
- **No secrets in the image.** Verify rather than assert: `docker history --no-trunc` and grep. A key
  passed as a build arg is in a layer forever, even if a later layer deletes the file.
- **Health check *and* readiness, and they are different.** `/healthz` says the process is alive.
  `/readyz` must assert the things that make this service useful: the index is loaded and non-empty,
  the vector store answers, the model endpoint is reachable, the prompt version resolved. An LLM
  service's readiness is expensive and meaningful; treat it as a real check, not a `return 200`.
- **Index baked in or mounted — decide and write down why.** Baked in gives you an immutable,
  reproducible artifact and a rollback that rolls back the index too; the image gets large and a
  corpus update needs a rebuild. Mounted gives you independent corpus updates; now your image and
  your index can drift, and you need `corpus_version` on the span (Day 16 §2.4) to tell which pair
  produced an answer.

### 2.5 Image size as an architecture forcing function

Here is the specific thing that happens. You add a cross-encoder reranker on Day 14 via
`sentence-transformers`. That pulls `torch`. The default PyPI torch wheel for Linux drags the
bundled CUDA runtime libraries with it, and your 400 MB image becomes 4 GB.

The first response is a packaging fix, and it's the right first response: install the **CPU-only
torch wheel** from PyTorch's CPU index, which drops the CUDA payload entirely. That alone usually
gets you back under 1.5 GB, and you should always do it before concluding you have an architecture
problem.

But if it's still large, the question stops being a packaging question:

| | Reranker in-process | Reranker as its own service |
|---|---|---|
| **Image** | API image carries torch + model weights | API image stays small; one heavy image |
| **Latency** | No hop | +5–15 ms plus serialisation |
| **Scaling** | Reranker memory is paid on **every API replica**, whether or not that replica is reranking | Scales independently; can be GPU-backed later without touching the API |
| **Cold start** | Model load on every replica start — slow rollouts, slow autoscale | One warm pool; API replicas start in seconds |
| **Failure isolation** | Reranker OOM takes the request handler with it | Isolated; degrade to fusion-only ranking (Day 15's degradation path) |
| **Ops burden** | One deployable, one rollback, one alert set | Two of each, plus a service-discovery entry and a network policy |

The point worth teaching is the direction of causation. **Image size didn't cause the decision; it
surfaced a decision that was already there.** The reranker has a different resource profile and a
different scaling curve from your API, and coupling them was always a choice — the 4 GB image is
just the first time anyone noticed.

And then the arithmetic usually says *don't split yet*. §3 Q5 runs it: at pilot scale the split
saves about $72 a month and costs you a second deployable, a second rollback path and a second
on-call surface. Split when the reranker needs a GPU, or when its traffic profile genuinely
diverges from the API's — not because an image is big.

### 2.6 The eight questions an enterprise security review will ask

Write the answers before you're asked, in `SECURITY_ANSWERS.md`. Not because the review is a
formality — because a written answer that names the specific control is the difference between a
two-week review and a two-month one.

| # | The question | What they're really asking | Where your answer is evidenced |
|---|---|---|---|
| 1 | Where does prompt data go, and is it retained by the provider? | Is our data training someone's model, and for how long does it exist outside our control? | The zero-retention setting, screenshotted as enabled; the DPA clause; §2.2's three questions answered |
| 2 | How do you prevent prompt injection from causing tool execution? | Can a document make your system do something? | Day 15 guards **plus** tool authorisation in code (Day 18 §2.9) |
| 3 | What's the blast radius of the agent's most dangerous tool? | If everything else fails, what's the worst outcome? | The tool inventory, with read-only vs. write marked, and the write ones scoped |
| 4 | How are secrets managed and rotated? | Are there long-lived keys in a repo? | Secrets Manager + IAM task roles, no static credentials, rotation period stated |
| 5 | Is PII redacted before it leaves the boundary, and before it enters logs and traces? | Have you created a second copy of our personal data? | Day 16 §2.7 — the posture, the retention period, the access audit, the redactor's false-negative rate |
| 6 | What's the audit trail for a given answer? | If a customer disputes an answer, can you reconstruct it? | `trace_id`, and the config hashes that pin the exact system version that produced it |
| 7 | What happens if the provider has an outage? | Does our business stop? | Day 15's degradation path: fallback model, cached answers, honest failure |
| 8 | **How do you prevent one tenant's data reaching another?** | The one that fails in real systems | §2.7. This one gets its own section |

### 2.7 Tenant filtering must be enforced in the retriever query

Say this out loud once and you will never build it wrong:

> **A prompt instruction saying "only use documents where tenant = X" is not an access control.**

The reason is structural, not a matter of the model being unreliable. A prompt is a *request* to a
system whose behaviour is statistical and whose instruction-following can be overridden by other
text in the same context window — including, per Day 18, text that arrived from a retrieved
document. You are asking the thing that just read untrusted input to enforce a boundary on that
input. In your world: it's the same category error as validating in JavaScript and trusting the
result on the server.

The correct mechanism is a chain, and every link is in your code:

```
authenticated request
  → validated token (signature verified — NOT a header the client set)
  → tenant_id extracted from a verified claim
  → passed as a filter INTO the retriever query
  → post-retrieval assertion: every returned chunk's tenant_id == the caller's
  → if any mismatch: drop the result, log it as a security event, alert
```

The post-retrieval assertion is cheap and worth having even though the filter should make it
impossible. It's a tripwire: if it ever fires, you have a filter bug or an index-hygiene bug, and
you'd rather find out from a log line than from a client.

**And there's a retrieval-quality trap hiding inside this**, which is the part almost nobody warns
about. How the vector database applies your filter matters enormously:

| Approach | Mechanism | Failure |
|---|---|---|
| **Post-filter** | Run ANN search over the whole index, then discard chunks from other tenants | If the tenant is a small share of the index, almost nothing survives. §3 Q6: a tenant holding 0.4% of the index, `ef_search`=128, k=5 → you get **five results roughly once in four thousand queries** |
| **Pre-filter / filtered ANN** | The filter participates in graph traversal, so the search stays inside the tenant's subgraph | The correct default. Check your vector DB actually does this — the terminology varies and so does the implementation quality |
| **Index (or collection) per tenant** | Physical separation | Best blast radius and best recall; costs memory per index and gets awkward past a few hundred tenants |

The nasty part is the symptom. A post-filtered system doesn't return other tenants' data — it's
*secure* — it just quietly returns two chunks when you asked for five, and the model answers
confidently from two. It looks like a quality problem, and people spend weeks on the embeddings.
Day 16 §2.2 put `candidate_count` next to `k` on the span for exactly this.

### 2.8 CI/CD, and the smoke test that asserts a verified citation

```
on: push to main
  test     ruff + pytest + type check
  eval     fast eval suite, hard gates (Day 13 §2.9)   ← blocks on regression
  build    docker build → scan → push to registry
  deploy   → staging
  smoke    /healthz, /readyz, and one real /v1/ask asserting a VERIFIED CITATION
  promote  manual approval → production
```

Only two stages need arguing.

**The eval gate is a hard gate with thresholds derived from measured σ** — Day 13's whole point. A
gate set tighter than the noise floor gets `continue-on-error: true` within a fortnight and then
you have nothing.

**The smoke test is the one that's different from every pipeline you've built.** Your normal smoke
test asserts a 200. Consider what a 200 survives here:

| Broken thing | `/healthz` | 200 on `/v1/ask` | `/readyz` asserting index count > 0 | Verified-citation assertion |
|---|---|---|---|---|
| Process crashed | ✗ catches | ✗ catches | ✗ catches | ✗ catches |
| Index volume failed to mount (index empty) | passes | **passes** | ✗ catches | ✗ catches |
| Index mounted but built from the wrong corpus | passes | **passes** | **passes** | ✗ catches |
| Embedding model env var points at the wrong model | passes | **passes** | **passes** | ✗ catches |
| Prompt version rolled back, citations no longer emitted | passes | **passes** | **passes** | ✗ catches |

A service returning 200 with a hallucinated answer is healthy by every ordinary definition. The
citation assertion is the cheapest test that crosses the whole system — index, retriever, prompt
assembly, model, citation verifier — in one request, because it can only pass if a real chunk was
retrieved and the model quoted it and the verifier matched the quote back to the source.

Build it as a *fixed* case with a *stable* expected source: ask the detention question, assert the
answer verifies against the accessorials document. One query, one assertion, deterministic at
temperature 0. §3 Q7 prices it, and the number is small enough to be funny.

Two operational notes. It must run **against the deployed artifact at its real URL**, not against a
locally-imported app object — half the failures above are deployment-environment failures and a
local import doesn't have a deployment environment. And **know your rollback command before you
need it**, written in the runbook, tested once on purpose. A deploy path without a rehearsed
rollback is a one-way door dressed as a pipeline.

### 2.9 The handover artifact set

An engagement ends when the client can run the system without you. Not when it works — when they
can operate it. Those are different dates and the second one is the one that matters.

| Artifact | The question it answers | How you know it's actually good |
|---|---|---|
| **README** | Can a new engineer get this running? | A colleague clones it on a **clean machine**, follows it literally, and you are not allowed to speak. Every place they stop is a bug in the README |
| **ARCHITECTURE.md** | Why is it shaped like this? | It records the decisions *and the alternatives you rejected and why* — chunking strategy, hybrid weights, in-process vs. separate reranker. Otherwise the next engineer re-litigates all of them |
| **RUNBOOK.md** | It's 2am and citation verification just dropped. Now what? | See below |
| **CAPACITY.md** | What happens at 10× traffic, and what breaks first? | From Day 15's load test, with the measured knee and the bottleneck named |
| **SECURITY_ANSWERS.md** | The eight questions | Their security team reads it without asking you a follow-up |
| **The eval suite, in their CI** | Did our change break it? | It runs on *their* pipeline, on their credentials, and it has blocked at least one of their PRs before you leave |
| **A recorded walkthrough** | What is this and how does it fit together? | 20–30 minutes, screen recorded, watched by someone who joins in month four |

**The runbook is the one that gets you referred.** The reasoning is worth being explicit about,
because it's a career fact rather than an engineering one.

The person who decides whether your firm gets called again is rarely the sponsor who signed the
statement of work. It's the engineer who got paged at 2am four months after you left, and who
either found a page in your runbook that told them exactly what to check — *"citation verification
below 0.85: check `corpus_version` on recent spans against the last successful ingestion run; if it
changed, the nightly ingest re-chunked; roll the index back with `make index-rollback`"* — or
didn't, and spent four hours reverse-engineering your retrieval pipeline while their VP asked for
updates.

That engineer's opinion of you is formed entirely at 2am, and it's the opinion that gets repeated
in the room where the next engagement is discussed. So the runbook covers the **five alerts you
actually configured**, each with: what it means, the first three things to check, the remediation,
and the escalation if remediation fails. Five alerts, one page each. Not a wiki.

---

## 3. Worked example — on paper

> **Setup, and the prices are assumptions.** A mid-size 3PL, on AWS, answers **no** to egress
> question 2 (§2.2): inference must run on compute they own. 500 users × 12 queries/day, working
> hours only, 22 working days/month. Measured from your own system: 4,800 input tokens and 340
> output tokens per query.
>
> Model: **Llama-3.1-8B-class**, 32 layers, 8 KV heads (grouped-query attention), head dimension
> 128. GPU: one A10G with **24 GiB**, assume **$1.006/hour** on demand ≈ **$734/month**. Hosted
> alternative assumed at **$0.50 per 1M input tokens, $2.00 per 1M output tokens**. Fargate assumed
> at **$0.04048/vCPU-hour** and **$0.004445/GB-hour**, 730 hours/month. *Every one of these prices
> drifts — re-derive before you quote them to anyone.*

**Q1.** KV cache is 2 tensors (K and V) × layers × KV heads × head_dim × 2 bytes (fp16) per token.
Compute the bytes per token, and the GPU memory one in-flight request holds at an 8,000-token
context.

**Q2.** fp16 weights for an 8.03B-parameter model, plus ~2 GiB of framework and activation
overhead. On the 24 GiB card, how much is left for KV cache and how many concurrent 8k-token
requests fit? Redo it with int8 weights.

**Q3.** Little's law. 500 users × 12 queries/day, concentrated in an 8-hour working day, with a
peak factor of 3. Prefill runs at ~2,500 tok/s and decode at ~45 tok/s per stream. Compute offered
concurrency, then compare it against both answers from Q2. How many GPUs do you provision?

**Q4.** Monthly cost of the self-hosted deployment at the GPU count from Q3, versus the hosted
alternative at the assumed token prices. What is the ratio, and what is the actual argument for
self-hosting here?

**Q5.** The reranker split. In-process needs 2 vCPU / 4 GB per API task, and you run 6 tasks.
Split, the API tasks need 1 vCPU / 2 GB and the reranker runs as 2 tasks at 2 vCPU / 4 GB. Monthly
Fargate cost each way. What does the number tell you to do?

**Q6.** Post-filter recall. The index holds 500,000 chunks; tenant A owns 2,000 of them.
`ef_search` = 128, k = 5, post-filtering. Expected number of tenant-A chunks among the candidates,
and roughly how often you get all 5. What `ef_search` would you need, and what does that cost?

**Q7.** Your smoke test issues one real query per deploy at a measured $0.0031. At 20 pushes to
main per day over 22 days, what does the smoke test cost per month? Which of the five failures in
§2.8's table does it catch that `/readyz` does not?

<details>
<summary><b>Answers — Q1–Q3 are the ones that change an architecture</b></summary>

**Q1.** 2 × 32 × 8 × 128 × 2 = **131,072 bytes = 128 KiB per token.**
At 8,000 tokens: 8,000 × 128 KiB = **1,000 MiB ≈ 1 GiB per in-flight request.**

Worth pausing on: your *context length* is now a memory budget line item. Every extra 1,000 tokens
of retrieved context costs 128 MiB of GPU memory **per concurrent user**. Trimming k from 5 to 3
stopped being a token-cost optimisation and became a capacity decision.

**Q2.** fp16 weights: 8.03e9 × 2 bytes = 16.06 GB ≈ **15.0 GiB**. Plus 2 GiB overhead = 17 GiB
committed. Remaining: 24 − 17 = **7 GiB → 7 concurrent requests** at 8k context.

int8 weights: ~8.03 GB ≈ **7.5 GiB**, plus 2 = 9.5 GiB. Remaining: **14.5 GiB → 14 concurrent.**

**Quantisation roughly doubled your concurrency, and it did it by freeing memory, not by going
faster.** That's the sentence that reframes quantisation for anyone who thinks of it as a speed
knob. (It costs some quality — which you measure with the eval suite, not by reading a blog post
about perplexity.)

**Q3.** 500 × 12 = 6,000 queries/day ÷ 8 hours = 750/hour = **0.208/s** average; × 3 peak factor =
**0.625/s**.

Occupancy per request: prefill 4,800/2,500 = 1.9 s; decode 340/45 = 7.6 s; total ≈ **9.5 s**.

Little's law: L = λW = 0.625 × 9.5 = **5.9 concurrent requests at peak.**

Against Q2: fp16 gives 7 slots, so ρ = 5.9/7 = **84% utilisation** — which is not "fits", it's
"queues". At 84% on a small number of servers, waiting time is a large multiple of service time and
your p95 goes through the floor of acceptable. int8 gives 14 slots, ρ = **42%** — comfortable.

Provision **2 GPUs regardless**, because one GPU means a rolling deploy is an outage and a hardware
failure is an outage. So: 2 × g5.xlarge, int8 weights, and you have real headroom. The interesting
part is that the sizing argument never mentioned FLOPs.

**Q4.** Self-hosted: 2 × $734 = **$1,468/month**, before ops.

Hosted: 132,000 queries/month. Input 132,000 × 4,800 = 633.6M tokens × $0.50/1M = **$316.80**.
Output 132,000 × 340 = 44.9M × $2.00/1M = **$89.76**. Total ≈ **$407/month.**

Self-hosting is **~3.6× more expensive**, and that's before the ops burden of GPU nodes, model
version management, vLLM upgrades and capacity planning — which is a person, not a line item
(Day 18 §2.6).

So the argument for self-hosting here is **not cost, and you must say so plainly.** It's that
egress question 2 was answered "no", and no amount of arithmetic changes a compliance boundary.
Presenting it the other way round — pretending the GPU is a saving — is the thing that gets your
cost model disbelieved when they check it.

**Q5.** In-process: vCPU 6 × 2 = 12 × $0.04048 × 730 = **$354.60**; memory 6 × 4 = 24 GB ×
$0.004445 × 730 = **$77.88**. Total **$432.48**.

Split: API 6 × 1 = 6 vCPU → $177.30; 6 × 2 = 12 GB → $38.94 → **$216.24**. Reranker 2 × 2 = 4 vCPU
→ $118.20; 2 × 4 = 8 GB → $25.96 → **$144.16**. Total **$360.40**.

Saving: **$72/month** — for a second deployable, a second rollback path, a second alert set and a
network policy. **Don't split.** Fix the image with the CPU-only torch wheel and revisit when the
reranker needs a GPU or its traffic diverges from the API's. This is the arithmetic telling you
that an aesthetic preference for microservices costs more than it saves at this scale.

**Q6.** Tenant A is 2,000/500,000 = **0.4%** of the index. Expected tenant-A chunks among 128
candidates = 128 × 0.004 = **0.51**.

Modelling the count as Poisson(0.51): P(at least 5) ≈ **0.00024** — roughly **once in 4,200
queries** do you get a full k=5. Most queries return zero or one chunk.

For an expected 5 you'd need `ef_search` ≈ 5/0.004 = **1,250**, and for *reliably* 5 you'd want
2,500–3,000 — a 20× increase in graph traversal, which destroys your retrieve latency and does it
for every tenant, including the large ones that didn't need it.

The fix is **pre-filtered / filtered ANN search**, or an index per tenant. And note the failure
signature: this system is *secure* — no cross-tenant leakage — it just answers small tenants badly,
which presents as a quality complaint from exactly the customers least able to tolerate one.

**Q7.** 20 × 22 = 440 deploys × $0.0031 = **$1.36/month.**

It catches every row `/readyz` doesn't: a wrong-corpus index, a mispointed embedding model, and a
prompt rollback that stopped emitting citations. All three produce a fully "ready" service with a
populated index that returns confident, wrong, uncitable answers.

**The most valuable test in your pipeline costs $1.36 a month.** That's a good line to end a
deployment session on.

</details>

---

## 4. What people get wrong

**"Can data leave your VPC?" is the egress question.**
It's one of three. The account/tenancy question is separate and it's the one that forces self-hosted
weights. A VPC endpoint keeps traffic off the internet; inference still runs in the provider's
service account.

**"Air-gapped just means we self-host the model."**
It means a smaller model, a memory-bound capacity plan, a fixed cost floor, your own availability
story, and a re-run of the entire eval suite to find out what you lost.

**"Self-hosting will be cheaper."**
At the scale most pilots run, it's several times more expensive before you count the person who
operates it. Do the arithmetic in front of them; the credibility from being the one who says this
is worth more than the deal it might cost you.

**"GPU sizing is about compute."**
At realistic context lengths it's about KV cache memory — 128 KiB per token per request, and
concurrency is whatever's left after the weights. Which is also why "quantisation makes it faster"
is the wrong emphasis: primarily it makes it *fit*, and halving the weights roughly doubled
concurrency in §3 Q2 with no change in per-token speed.

**"The image is 4 GB because Python is bloated."**
It's the CUDA runtime bundled into the default torch wheel. Install the CPU-only wheel first; only
then decide whether you have an architecture problem — and if you do, split on divergent resource
profiles and scaling curves, not on megabytes. §3 Q5 puts the saving at $72/month.

**"We filter tenants in the system prompt."**
That is not an access control. It's a request to a statistical system that has just read untrusted
retrieved text. The filter goes in the retriever query, derived from a signature-verified identity
claim — not a header the client set — with a post-retrieval assertion behind it.

**"Filtering is a security concern only."**
Post-filtered ANN search quietly destroys recall for small tenants. It's a security control that is
simultaneously a retrieval-quality decision, and its symptom is a quality complaint.

**"The smoke test hits /healthz."**
A service with an empty index passes `/healthz`, `/readyz` and a 200 on `/v1/ask`. Assert a verified
citation, or your pipeline cannot distinguish a working system from a confidently broken one.

**"Handover is documentation, and we'll write the runbook at the end."**
Handover is a *test*: someone who didn't build it stands up the system from the README on a clean
machine and resolves an alert from the runbook, while you say nothing. And the runbook is both the
deliverable most likely to determine whether you're referred and the first thing cut when the
timeline compresses. Write it as you build each alert.

---

## 5. The trainer's angle

**The analogy that lands, and it lands hardest with an infrastructure audience:** the egress
question is the "can this subnet reach that database" question — the one that has reshaped every
migration any of them has run. The twist that makes it land is that here the answer doesn't change
a firewall rule, it changes the *model*, and therefore the prompts, the retrieval tuning, the
capacity plan and the eval baseline. Draw the two architectures side by side, five minutes, no
slides. The room understands immediately why it's the first question.

**The analogy for tenant filtering:** client-side validation. Everyone in the room has shipped a
bug where the server trusted something the browser said. "The prompt is the browser" gets a
laugh and then a nod, and the nod is the moment it becomes unforgettable.

**The demo that makes it click:** deploy with the index volume unmounted. Hit `/healthz` — green.
Hit `/readyz` — green, if your readiness is lazy. Ask a real question — a confident, fluent,
entirely fabricated answer, 200 OK. Then run the citation-asserting smoke test and watch it go red.
Ninety seconds, and it retires the phrase "the health check passes" from that team's vocabulary.

**The second demo:** `docker history --no-trunc | grep -i key` on an image someone built with a
build-arg secret. Show the key sitting in a layer that a later `rm` did not remove.

**The predictive question before you run anything:** *"This tenant has 0.4% of the documents in the
index and we're post-filtering. How many of the five results do you think they'll get?"* People say
"about five, maybe four." The answer is zero or one, and the Poisson arithmetic in §3 Q6 takes
thirty seconds to show why.

**The question a sharp student will ask:** *"If we call the model over a VPC endpoint, the traffic
never touches the internet. Why isn't that good enough for a client who says data can't leave?"*
Have this ready:

> Because "leave" means two different things and the client usually hasn't distinguished them. A
> VPC endpoint is a **network path** control: your packets go over the cloud provider's backbone
> instead of the public internet, and that satisfies a threat model about interception and about
> exposure to the open network. It does not change *where the inference executes*. The tokens are
> processed on the model provider's fleet, in their service account, under their operational
> control, subject to their retention policy. If the client's concern is interception, the endpoint
> is a complete answer and you should say so confidently. If the concern is a legal or contractual
> boundary — data must be processed only on infrastructure we control, or by processors named in
> our DPA — the endpoint doesn't touch it, and you need self-hosted weights. So the question I ask
> is: *is this a network requirement or a processing requirement?* Nine times out of ten, asking it
> that way is the first time anyone in the room has separated them, and it saves you six weeks.

**The follow-up:** *"Couldn't we just tell the model not to use other tenants' documents, as
defence in depth?"* You can, and it costs nothing, and it is worth roughly nothing. Rank your
defences by whether they have a proof: the retriever filter is deterministic and testable; the
prompt instruction is a probabilistic request to a system that has just read untrusted input. Put
the prompt instruction in if you like, but never let it appear in a security answer as a control —
if a reviewer sees it listed as one, they will reasonably wonder what else you've mislabelled.

---

## 6. Self-check

Cover the answers.

1. Name the four topologies and the constraint each hits.
2. State the three egress questions, and say which one forces self-hosted weights.
3. Name five things that change when a client answers "no" to the account/tenancy question.
4. What bounds concurrency on a self-hosted model at long context, and what's the per-token figure
   for an 8B GQA model in fp16?
5. Why does quantisation increase concurrency?
6. Why is a 4 GB image usually not a Python problem, and what's the first fix?
7. Give two conditions under which you *should* split the reranker into its own service, and one
   that isn't a reason.
8. Why is a prompt-level tenant instruction not an access control? Give the structural reason.
9. Describe the full tenant-filtering chain from request to result.
10. What does post-filtered ANN do to a small tenant's recall, and what's the symptom the client
    reports?
11. Name three deployment failures that a 200 on `/v1/ask` does not catch but a verified-citation
    smoke test does.
12. Which handover artifact most determines whether you're referred to the next team, and why?

<details>
<summary><b>Answers</b></summary>

1. Managed PaaS — no VPC peering, vendor secret store. Container in their cloud — IAM, VPC
   endpoints, image scanning. Kubernetes — you're a tenant of another team's platform and its
   release train. Air-gapped — no hosted model at all.
2. (a) Can data traverse the public internet? (b) Can it leave the client's account/tenancy even
   privately? (c) Can it leave the jurisdiction? **(b)** forces self-hosted weights — a VPC endpoint
   fixes the network path, not where inference executes.
3. Smaller model; more scaffolding to compensate; fixed rather than variable cost; capacity planning
   becomes yours and is memory-bound; availability becomes yours (two GPUs minimum); model updates
   only happen when you do them; the eval suite must be re-run to quantify the capability loss.
   Any five.
4. KV cache memory. 2 × layers × KV heads × head_dim × 2 bytes = 2 × 32 × 8 × 128 × 2 =
   **128 KiB per token**, so ~1 GiB per in-flight 8k-token request.
5. It shrinks the weights, freeing GPU memory that becomes KV cache budget. More KV budget, more
   in-flight requests. It's a memory effect, not a speed effect.
6. The default PyPI torch wheel bundles the CUDA runtime libraries. Install the CPU-only torch wheel
   first; that usually recovers 2.5 GB.
7. Split when the reranker needs a GPU, or when its scaling profile genuinely diverges from the
   API's (and cold-start cost on every API replica is hurting rollouts). Not a reason: the image is
   big.
8. A prompt is a request to a statistical system whose instruction-following can be overridden by
   other text in the same context — including retrieved text from untrusted sources. You'd be asking
   the component that just read the untrusted input to enforce a boundary on it.
9. Authenticated request → signature-verified token → tenant_id from a verified claim → passed as a
   filter into the retriever query → post-retrieval assertion that every chunk matches → mismatch
   drops the result, logs a security event and alerts.
10. It collapses recall: with 0.4% of the index and ef_search=128 the expected hit count is ~0.5, so
    they get zero or one chunk instead of five. The symptom is a *quality* complaint — vague or
    refused answers — not a security one, so people debug the embeddings.
11. An empty or unmounted index; an index built from the wrong corpus; a mispointed embedding model;
    a prompt rollback that stopped emitting citations. Any three.
12. `RUNBOOK.md`. The person who decides whether you're called back is usually the engineer paged at
    2am four months after you left, and their opinion of you is formed entirely by whether the
    runbook told them what to check.

</details>

**Scored below 9?** Re-read §2.2 and §2.7. The lab's enterprise design doc is essentially an
extended answer to §2.2, and §2.7 is the one point in the whole document that a client's security
architect will read closely — the lab will not re-explain either.

---

## 7. Going deeper

<!--reading:17-->

### If you read one thing this week

**[OWASP Top 10 for LLM Applications (2025)](https://genai.owasp.org/llm-top-10/)** — OWASP GenAI Security Project · docs · ~40 min

This is the checklist a client's security team will actually hand you; knowing it before the meeting is the difference between leading the review and surviving it.

### Then, in the order I'd take them

- **[The Twelve-Factor App](https://12factor.net/)** — Adam Wiggins · docs · ~35 min  
  Config, backing services and disposability are exactly the properties your Day 17 container needs; it predates LLM work and is still the clearest statement of why secrets live in the environment.
- **[Multi-stage builds](https://docs.docker.com/build/building/multi-stage/)** — Docker · docs · ~15 min  
  The exact pattern in your Dockerfile — build deps in one stage, copy the artefact into a slim runtime — read it once so image size becomes a decision rather than an accident.
- **[Configuring OpenID Connect in Amazon Web Services](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws)** — GitHub Docs · docs · ~20 min  
  The no-long-lived-keys CI pattern from Day 17's checklist, written out; it takes twenty minutes and it is the single clearest signal to a platform team that you have done this before.

<!--/reading-->

### Also mentioned in this module

- *Accelerate* — Forsgren, Humble and Kim, 2018. The empirical case that deployment frequency,
  lead time, change-failure rate and restore time move together. Useful for the argument you'll have
  about why the eval gate belongs in the pipeline rather than in a pre-release checklist.
- *The Site Reliability Workbook* — Beyer et al., 2018. The chapter on canarying releases is the
  right mental model for §2.8's promote step, and the SLO chapters give you language for the
  conversation about what "working" means when correctness is probabilistic.
- *Efficient Memory Management for Large Language Model Serving with PagedAttention* — Kwon et al.,
  SOSP 2023. The vLLM paper. Read it specifically for the KV-cache-as-memory-allocator framing: it
  is §3 Q1–Q3's arithmetic taken seriously, and it will feel very familiar to anyone who has thought
  about page tables and fragmentation.
- The grouped-query attention work (Ainslie et al., 2023) is the reason the KV figure in §3 Q1 is
  8 heads rather than 32 — a 4× reduction in cache size. Worth ten minutes if you want to explain
  why newer models are cheaper to serve at long context.
- Your cloud provider's PrivateLink / VPC endpoint documentation for their managed model service.
  Read the section on *where inference executes* rather than the network diagram — that's the
  paragraph §2.2's question 2 turns on, and it is usually one sentence.

---

**Now go to `labs/DAY_17.md`.** The lab builds directly on §2.4–§2.5 (the Dockerfile and the
image-size decision), §2.8 (the pipeline, and the smoke test that asserts a verified citation rather than
a 200), §2.6–§2.7 (`SECURITY_ANSWERS.md`, with question 8 as the one that has to be right), and
§2.2–§2.3 (the enterprise design doc, which is the egress question answered in four pages).
