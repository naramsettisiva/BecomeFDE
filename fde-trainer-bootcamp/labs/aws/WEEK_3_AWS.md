# AWS Lane — Week 3 (Sep 8–14)

**macOS. Est. AWS spend this week: $10–18 — the heaviest week. Est. added time: 5h across six days.**

This week the AWS lane carries the most weight, because production *is* the AWS lane. Days 15,
16 and 17 in the core lane are largely rehearsals for what you build here.

**Day 18 contains the only GPU lab in the course.** Read its teardown section before you start it.

```bash
make aws-cost      # every morning. This week, actually read it.
make aws-nuke      # after every AWS block.
```

---

## Day 13 — Bedrock Evaluations at depth, and the judge you can't calibrate · 45 min · ~$3

Time trade: drop the Day 13 stretch (DSPy-style prompt optimisation) if you're tight.

### Do

1. Run **Bedrock RAG Evaluation** (retrieve-and-generate) on your 250-case suite against the
   Knowledge Base. Use Nova Lite as the model under test — you pay token rates for both the
   model under test and the judge, so a frontier model here is how a $3 lab becomes a $30 one.

2. **Build the head-to-head** — `evals/day13_managed_vs_own.md`:

   | | Your harness | Bedrock Evaluations |
   |---|---|---|
   | Faithfulness on the same 250 cases | | |
   | Agreement with your hand labels (κ) | | |
   | Segmented by your difficulty labels | yes | no |
   | Adversarial + persona cases supported | yes | you supply the dataset |
   | Runs as a CI gate | yes | API, awkward |
   | Noise floor measurable across 5 runs | yes | expensive to try |
   | Cost per full run | | |

3. **The point of this lab, stated plainly:** a managed eval gives you a *number*. Your harness
   gives you a number **plus the ability to prove it means what you think it means**. On an
   engagement, the client's domain expert is the ground truth, and only a calibrated judge
   connects a dashboard metric to that expert's judgement.

   The recommendation you should end up writing is usually: *use Bedrock Evaluations for the
   broad regression sweep, keep a calibrated custom judge for the metrics you actually gate
   on.* Both, for different jobs. Write it in your own words.

4. **CI on AWS:** wire the fast eval suite into CodeBuild (or keep GitHub Actions with an OIDC
   role — no long-lived keys, and it's the pattern a client's security team will want to see).
   Prove the gate blocks a deliberately regressed change.

---

## Day 14 — The hybrid-retrieval problem S3 Vectors can't solve · 45 min · ~$1

Today's AWS lane is where a managed service's limitation becomes a design decision — the most
FDE-shaped moment in the whole lane.

### The problem

Your Day 14 core lane proved hybrid (BM25 + dense, fused with RRF) is worth 10–13 points of
recall, and that it wins specifically on the queries dense retrieval fails: acronyms (`TONU`),
identifiers (`SHP-202608-0041729`), rare tokens.

**S3 Vectors is semantic-only. No BM25. No hybrid.**

So you have a real architecture decision, with four options and no obvious winner:

| Option | Cost | What you give up |
|---|---|---|
| **A.** S3 Vectors only | ~$0.01/mo | 10–13 pts recall on acronym/ID queries |
| **B.** S3 Vectors + client-side BM25 over the same corpus, fused with RRF | ~$0.01/mo + your compute | Two systems to keep in sync; BM25 index lives in your app |
| **C.** OpenSearch Serverless **NextGen** (scale-to-zero) | storage + burst OCU | Complexity; verify the no-minimum claim yourself |
| **D.** OpenSearch Serverless **classic** | **~$350/mo minimum** | Your entire budget, 7× over |

### Do

1. **Implement B.** `rank_bm25` over the corpus locally, S3 Vectors for dense, RRF fuse. It's
   about 40 lines and it recovers most of the hybrid gain for ~$0.

2. **Measure all of A, B, and the local Day-14 hybrid** on the same golden set:

   | | Recall@5 | Recall on ID/acronym queries | p50 latency | $/month at 2M vectors |
   |---|---|---|---|---|
   | A. S3 Vectors only | | | | |
   | B. S3 Vectors + client BM25 | | | | |
   | Local hybrid (Day 14) | | | | — |

3. **Investigate C** without provisioning it. Read the NextGen docs, price it at your scale,
   and write down what you'd need to verify before recommending it. If you're curious enough
   to create one, create it, measure it, and **delete it within the hour** — set a phone timer.
   At $0.24/OCU-hour a couple of hours is fine; a forgotten weekend is $17.

4. **Write the decision memo** — half a page, `evals/day14_aws_retrieval_decision.md`:
   the four options, the recall each buys, the monthly cost at pilot scale (7K queries) and at
   production scale (2M queries), and your recommendation with the crossover point named.

   **This memo is a portfolio artifact.** It is exactly the deliverable an FDE produces in
   week two of an engagement, and it demonstrates something a code sample can't: that you
   choose infrastructure with numbers rather than habit.

---

## Day 15 — Lambda + HTTP API, and Guardrails · 60 min · ~$1

Time trade: drop the Day 15 stretch (graceful degradation) to Day 17 — you'll have better
infrastructure for it there.

### Part A — serverless serving (35 min)

```bash
bash scripts/aws/lab_up.sh day15     # Lambda + HTTP API + CloudWatch log group w/ 7-day retention
```

Requirements — the same contract as your FastAPI service, different substrate:

- [ ] **HTTP API, not REST API.** $1.00/M vs. ~$3.50/M — 3.5× cheaper for what you need
- [ ] **Response streaming** via Lambda function URL with `RESPONSE_STREAM` (API Gateway does
      not stream). Note that constraint — it's a real architectural fork and it surprises people
- [ ] `aws-lambda-powertools` for structured logging, tracing, and metrics
- [ ] **Log retention set explicitly** — Lambda creates log groups with *never expire* by
      default, and verbose agent traces will eat the 5 GB CloudWatch free tier
- [ ] Cold-start measured. Then measured again with the index loaded from S3 at init rather
      than per-request

Then the comparison — `evals/day15_lambda_vs_fargate.md`:

| | FastAPI on your Mac | Lambda + HTTP API | Fargate (priced, not run) |
|---|---|---|---|
| Cold start | n/a | | ~30s task start |
| p50 / p95 latency | | | |
| Cost at 7K req/month | $0 | **$0** (free tier) | ~$9 |
| Cost at 2M req/month | | | |
| Streaming | SSE | function URL only | SSE |
| Max duration | ∞ | 15 min | ∞ |

**The crossover matters.** Lambda is free at pilot scale and stops being cheapest somewhere
around sustained high traffic. Find roughly where, for your workload. *"Start on Lambda, move
to Fargate at roughly X requests per second"* is a recommendation with a number in it.

### Part B — Bedrock Guardrails (25 min)

1. Create a guardrail with content filters, denied topics, a PII filter, and **contextual
   grounding**. That last one is Bedrock's built-in hallucination check — the managed version
   of your Day 4 citation verification.

2. **Run your 40-case red-team set through it** and compare against your hand-built guards:

   | | Your guards | Bedrock Guardrails | Both layered |
   |---|---|---|---|
   | True blocks (of 20) | | | |
   | **False positives (of 20 legitimate)** | | | |
   | Latency added | | | |
   | Cost per 1,000 requests | | | |

3. **The pricing shape to internalise:** guardrails bill **per policy per 1,000 text units**.
   Four policies enabled = **$0.50 per 1,000 units** on every guarded call. At 2M requests/month
   that's $1,000/month for guardrails alone — potentially more than your inference.

   So the design question isn't "should we use Guardrails?" It's **"which policies, on which
   routes?"** Not every request needs contextual grounding. Write the routing rule.

4. Watch the **false-positive** row. A managed guardrail tuned for general safety will block
   legitimate freight questions — *"what's the driver's phone number on the BOL for SHP-…?"*
   is a normal ops question that trips a PII filter. Measure the rate. **A guardrail that
   blocks 3% of legitimate traffic is usually worse than the risk it prevents**, and being able
   to quantify that is the conversation that gets you listened to in a security review.

---

## Day 16 — CloudWatch, X-Ray, and the incident drill · 50 min · ~$0.50

### Do

1. **Enable Bedrock model invocation logging** (S3 + CloudWatch) and **AgentCore observability**.
   Note immediately: **PII now flows into your logs.** Decide the redaction boundary today and
   write it down — a client's privacy officer will ask, and "we hadn't decided" is a bad answer.

2. **Build the CloudWatch dashboard**, six widgets, same discipline as the core lane:
   traffic · p95 latency by node · cost (custom metric you emit) · citation verification rate ·
   retrieval score distribution · errors by type.

   Remember: **3 dashboards and 10 alarm metrics are free**; after that it's $3/dashboard/month
   and $0.10/alarm-metric/month. The six-widget constraint isn't just editorial taste here — it
   also happens to be the free tier. Say that when you teach it; people remember constraints
   that have two reasons.

3. **Emit your own cost metric.** Bedrock doesn't give you per-request cost in CloudWatch. Emit
   it from your Lambda using EMF (Embedded Metric Format) via Powertools:

   ```python
   metrics.add_metric(name="RequestCostUSD", unit=MetricUnit.None_, value=usd)
   metrics.add_dimension(name="Route", value=route)
   ```

   Now cost is a first-class dimension you can alarm on and chart per tenant. **Almost nobody
   does this**, and it's the single most appreciated thing you can add to a client's AI
   observability — because their finance team has been asking for it and nobody could answer.

4. **Run the incident drill on AWS.** Same rules: a script plants one regression, you diagnose
   from telemetry only, no `git diff`, and you time yourself. Add three AWS-specific faults to
   the list:
   - Knowledge Base sync silently failed — the index is stale
   - Bedrock throttling (`ThrottlingException`) under burst, retried into latency
   - A guardrail rule quietly blocking a legitimate route

   The stale-index one is the most realistic and the hardest. **In production, a failed sync is
   the most common "the AI got worse" cause that isn't the model.** Write it up.

5. **CloudWatch cost discipline:** set retention on every log group (1–7 days for this course),
   and consider **Infrequent Access** log class at roughly half the ingest price for trace-heavy
   groups. Check what your week actually ingested.

---

## Day 17 — ECS Fargate, IAM, VPC, and the real deployment · 70 min · ~$2

Time trade: drop the Day 17 stretch (blue/green auto-rollback) — Day 21 has a better slot.

### Part A — containerise for Fargate (30 min)

```bash
# Apple Silicon: build ARM64. Fargate supports it and it's ~20% cheaper than x86.
docker buildx build --platform linux/arm64 -t fde-bootcamp-copilot .
```

- [ ] Push to ECR
- [ ] Task definition with `"cpu": "256", "memory": "512"` — the minimum
- [ ] **`desiredCount: 0` by default.** Scale to 1 for the lab, back to 0 immediately after.
      At ~$9/month for the smallest possible always-on task, this is 18% of your budget for a
      container doing nothing
- [ ] Task role with **least privilege** — Bedrock invoke on specific model ARNs, S3 Vectors
      read on one bucket. Not `bedrock:*`
- [ ] Secrets from Secrets Manager or SSM Parameter Store, never in the task definition
- [ ] Verify: `docker history --no-trunc` and grep for anything key-shaped

**The architecture failure to recognise:** an ARM image on an x86 task definition fails with
an exec-format error that reads like a corrupt binary. It's architecture. You now know.

Run it for fifteen minutes, hit it, then scale to zero and tear it down.

### Part B — the enterprise design, made concrete (40 min)

Your Day 17 core lane wrote `ENTERPRISE_DEPLOYMENT.md` for a mid-size 3PL. **Now make it
specific**, because you have real numbers:

1. **VPC design.** Private subnets, no IGW for the app tier, **VPC endpoints** for Bedrock,
   S3, CloudWatch Logs, ECR, Secrets Manager. Draw it.

   The load-bearing point: **an interface VPC endpoint for Bedrock means prompt data never
   traverses the public internet.** That single fact resolves most enterprise objections to
   using a hosted model, and being able to state it precisely is worth a great deal in a
   security review. Note that interface endpoints cost ~$0.01/hour each — real money at scale,
   and a line item clients forget.

2. **Model access options, priced:**

   | | Bedrock via VPC endpoint | Self-hosted on SageMaker |
   |---|---|---|
   | Data leaves account? | No | No |
   | Fixed monthly cost | $0 | GPU instance × 730h |
   | Marginal cost | per token | $0 |
   | Break-even | — | *compute it tomorrow* |
   | Ops burden | none | capacity planning, patching, scaling |

3. **Answer the eight security questions** from your core lane with AWS specifics —
   `capstone/service/SECURITY_ANSWERS.md`. Question 8 (tenant isolation) is the one to get
   exactly right:

   > Tenant filtering is enforced in the **retriever query** — an S3 Vectors metadata filter
   > applied server-side, derived from the caller's IAM/JWT identity. It is never expressed in
   > the prompt. A prompt instruction is not an access control.

4. **CI/CD with OIDC**, not access keys. A GitHub Actions role assumed via OIDC with no
   long-lived credentials is what a client's security team wants to see, and it's a five-minute
   setup that signals you've done this before.

```bash
make aws-nuke      # ECS service, cluster, task defs
```

---

## Day 18 — The GPU lab, and the cost model that decides it · 70 min · ~$4–7

**This is the only lab in the course that provisions a GPU. Read the teardown section first.**

It closes one of the three named gaps in the course — self-hosted serving and capacity
planning — and it produces the arithmetic behind one of the most common client questions.

### Before you start

```bash
make aws-cost      # if you are above $35, STOP. Do Part B only, as a paper exercise.
```

Set a **phone timer for 90 minutes**, right now, labelled "DELETE SAGEMAKER ENDPOINT". Not a
note. A timer that makes noise. The endpoint bills whether or not you remember it.

### Part A — deploy a model on SageMaker (45 min, ~$3–6)

```bash
bash scripts/aws/lab_up.sh day18-gpu     # prints the teardown command before it creates anything
```

1. Deploy a small open model (Llama 3.1 8B or similar) to a **real-time endpoint** on
   `ml.g5.xlarge`. **Verify the current hourly rate in the console before you start** — historical
   list price is roughly $1.41/hr, but confirm it. Quoting a stale GPU price to a technical
   audience is exactly the error that costs you credibility.

2. **Load test it.** Concurrency 1, 4, 16. Measure:

   | concurrency | tokens/sec | p50 latency | p95 latency | GPU utilisation |
   |---|---|---|---|---|

   The shape you're looking for: throughput rises with batching until the GPU saturates, and
   latency degrades gracefully then sharply. **Find the knee.** That knee is the number
   capacity planning is built on, and most people quote vendor benchmarks instead of measuring it.

3. **Note what serverless can't do:** SageMaker Serverless Inference is **CPU-only**. There is
   no GPU serverless option. If a workload needs a GPU it needs a real-time or async endpoint,
   which means a fixed hourly cost, which means utilisation is the whole economic question.

### TEARDOWN — do this before Part B, not after

```bash
make aws-nuke
aws sagemaker list-endpoints --status-equals InService   # must return empty
make aws-cost                                            # confirm
```

**Do not proceed to Part B until that list is empty.** An `ml.g5.xlarge` left running is
~$1,027/month — twenty times your entire course budget. Part B is a writing exercise; it will
happily wait ninety seconds.

### Part B — the break-even model (25 min)

Now you have measured throughput, so you can do the arithmetic properly rather than quoting
someone's blog post:

```
ml.g5.xlarge on-demand ≈ $1.41/hr ≈ $1,029/month at 100% uptime
Your measured throughput at the knee: ____ output tokens/sec
  → ____ output tokens/month at 100% utilisation

Bedrock Nova Lite output: $0.90 / 1M tokens
  → break-even = $1,029 / $0.90 = ~1.14 BILLION output tokens/month

At 500 tokens per response that is ~2.3M responses/month ≈ 3,100/hour, sustained, 24/7.
```

Then the honest version, which is the part that makes you useful:

- **At 100% utilisation**, self-hosting wins above roughly that threshold.
- **At realistic utilisation** (business hours, weekday, bursty — call it 15–25%), multiply the
  break-even volume by 4–6×.
- **Add ops burden**: patching, scaling, on-call, capacity planning. That's a person, not a
  line item.
- **The real driver is usually not cost.** It's data residency, latency floors, or model
  customisation. Say so.

**Write `capstone/service/SELFHOST_ANALYSIS.md`** with your measured numbers, the break-even,
the utilisation sensitivity, and a recommendation.

This is the single most credible thing in the AWS lane. Everyone in the room has an opinion
about self-hosting; you'll have measured it. And the conclusion — *"for your volume, Bedrock
is cheaper by an order of magnitude, and here's the volume at which that flips"* — is usually
the opposite of what the vendor in the room is saying.

### Part C — AWS cost levers (as part of the core-lane optimisation table)

Add three AWS-specific rows to your Day 18 optimisation table:

| Lever | Typical saving | Cost to you |
|---|---|---|
| **Bedrock prompt caching** (stable prefix first) | cache read ≈ 10% of input price | nothing — do it first |
| **Bedrock batch inference** | **50% off** on-demand | latency; non-interactive paths only |
| **Route to Nova** for lookup-class queries | 30× on those queries | a classifier + an eval proving quality holds |

Measure each on your own traffic mix. The prompt-caching one usually wins largest and costs
nothing but attention to prompt ordering — system prompt and tool schemas first and unchanged,
retrieved chunks and the user question last.

---

## Week 3 AWS lane — done when

- [ ] Bedrock Evaluations vs. your harness, head to head on 250 cases, with κ
- [ ] CI eval gate running on AWS with OIDC (no long-lived keys), blocking a regression
- [ ] Four-option retrieval decision memo with recall, cost at two scales, and a crossover
- [ ] Lambda + HTTP API serving, log retention set, cold start measured and improved
- [ ] Guardrails false-positive rate measured against your 40-case red team
- [ ] Guardrail per-policy cost projected to 2M requests, with a routing rule written
- [ ] Six-widget CloudWatch dashboard, including a per-request cost metric you emit yourself
- [ ] AWS incident drill completed from telemetry only, including the stale-index fault
- [ ] Fargate task running ARM64, least-privilege task role, scaled to zero and torn down
- [ ] VPC endpoint design drawn; tenant isolation enforced in the query, not the prompt
- [ ] **GPU endpoint deployed, load-tested, and verifiably deleted**
- [ ] `SELFHOST_ANALYSIS.md` with your measured throughput and the break-even arithmetic
- [ ] Three AWS cost levers measured on your own traffic
