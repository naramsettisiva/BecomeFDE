# AWS Cost Discipline — the reference card

**Prices read off AWS pricing pages in August 2026, us-east-1. Refresh before you teach from
them.** Saying *"these are as of August 2026, here's how I check"* is more credible than
reciting numbers with false confidence — and price-checking is itself an FDE habit.

---

## The safe list — spend freely

| Service | Price | At course scale |
|---|---|---|
| **S3 Vectors** storage | $0.06 / GB-month | 2,000 × 1024-dim vectors ≈ 10 MB ≈ **$0.0006/mo** |
| **S3 Vectors** queries | $2.50 / million | 5,000 queries ≈ **$0.013** |
| **S3 Vectors** PUT | $0.20/GB, **min 128 KB per PUT** | Batched: **$0.002**. One-at-a-time: **$0.05** — batch. |
| **Lambda** | $0.20/M req + $0.0000167/GB-s | **$0** — 1M req + 400K GB-s always free, every month |
| **API Gateway HTTP API** | $1.00 / million | **$0** at course volume (and 3.5× cheaper than REST) |
| **Nova Micro** | $0.08 in / $0.24 out per 1M | 1M in + 200K out ≈ **$0.13** |
| **Nova Lite** | $0.30 / $0.90 per 1M | Same volume ≈ **$0.48** |
| **Titan Text Embeddings V2** | fractions of a cent at this scale | Embedding the whole corpus ≈ **$0.00** |
| **AgentCore Runtime** (microVM) | $0.0895/vCPU-hr + $0.00945/GB-hr | 1 vCPU + 2 GB = **$0.108/active-hour**; **idle is free** |
| **AgentCore Gateway** | $0.005 / 1,000 invocations | Negligible |
| **Bedrock Knowledge Bases** control plane | **no separate charge** | You pay embeddings + generation + vector store only |
| **AWS Budgets** (first 2 action-enabled) | free | — |
| **Cost Anomaly Detection** | free | — |

## The careful list — watch these

| Service | Price | The trap |
|---|---|---|
| **Claude Sonnet** on Bedrock | ~$3 in / $15 out per 1M | 30× Nova Lite. Judging and demos only. Use **batch (−50%)** and **prompt caching** (cache read ≈ 10% of input) |
| **AgentCore Memory** | $0.25/1K events · $0.75/1K records/mo · $0.50/1K retrievals | Long-term storage is **recurring monthly**. Delete memories in teardown |
| **Bedrock Guardrails** | $0.10–0.17 per 1,000 text units **per policy** | Four policies = **$0.50 per 1,000 units**. A naive loop is the one Bedrock feature that can surprise you |
| **Bedrock Evaluations** | model rates for both the model under test **and** the judge, + $0.21/human task | You pay token rates twice |
| **CloudWatch Logs** | $0.50/GB ingest (Infrequent Access ~$0.25) | Verbose agent tracing eats the 5 GB free tier fast. **Set retention on every log group** |
| **Fargate** | x86 ~$0.0405/vCPU-hr + $0.00445/GB-hr | Smallest possible task 24/7 = **~$9/mo** = 18% of budget. ARM/Graviton is ~20% cheaper |
| **Legacy Claude 3.5 Sonnet** | **$6 / $30** per 1M ("Public Extended Access" since Dec 2025) | **Double** current Sonnet, for a worse model. Check any pinned `claude-3-5-sonnet-*` model ID |

## The never-leave-running list

| Resource | Monthly if forgotten | Multiple of your budget |
|---|---|---|
| SageMaker `ml.g5.xlarge` real-time endpoint | **~$1,027** | **20×** |
| Amazon Kendra Basic Enterprise index | **~$1,008** | 20× |
| Amazon Kendra Basic Developer | **~$810** | 16× |
| OpenSearch Serverless **classic**, 2 OCU minimum | **~$350** | 7× |
| OpenSearch Serverless classic, dev-test (1 OCU) | **~$175** | 3.5× |
| Amazon Kendra **GenAI Enterprise** | **~$230** | 4.6× |
| API Gateway **Portals** | **$125** | 2.5× |
| Fargate, minimum task, 24/7 | ~$9 | 18% |
| AgentCore **Web Search** | **$7 per 1,000 queries** | Fastest way to burn the budget |

**None of these appear in a required lab.** SageMaker appears once, in a tightly scoped
2-hour lab with mandatory teardown (~$3–6). Kendra and OpenSearch classic appear only as
cost-design exercises — you price them, you don't provision them.

---

## The one that goes on a sticky note

> **OpenSearch Serverless NextGen went GA in May 2026 with no OCU minimum and scale-to-zero
> after 10 minutes idle.** Classic collections still bill a 2-OCU minimum (~$350/mo).
> Old blog posts, old Terraform, and possibly Bedrock's quick-create still provision
> **classic**. Check which one you're getting, every time.

Verify this in the console on Day 4 and write down what you find. If quick-create now uses
NextGen, the famous "$350 empty collection" warning is out of date — and being the person who
knows that, with evidence, is worth more than repeating the warning.

---

## What "no hard cap" actually means

AWS Budgets and Cost Anomaly Detection both read Cost Explorer, which has **up to 24 hours of
latency**. Cost Anomaly Detection also needs 24 h to activate a new monitor and ~10 days of
history to baseline.

So: a forgotten `ml.g5.xlarge` endpoint bills roughly **$34 before your budget notices**.

Budget *Actions* can apply a restrictive IAM policy or SCP, or stop EC2/RDS instances. None of
those terminate a running Fargate task, SageMaker endpoint, or OpenSearch collection — those
keep billing. **Budget Actions deny new spend; they do not stop existing spend.**

The layered guardrail, in order of how much it actually protects you:

1. **`make aws-nuke` after every AWS lab** — zero latency, the only real control
2. Free-plan account — auto-closes when credits are exhausted
3. Budget alerts at $5 / $15 / $30 / $45 — you find out in a day, not a month
4. Cost Anomaly Detection — catches the shape you didn't predict
5. Explicit CloudWatch log retention on every log group

Teach all five together. Engineers who believe a budget is a cap are the ones who get the
surprise invoice.

---

## Your projected spend

| Week | AWS lane content | Est. |
|---|---|---|
| 1 | Bedrock inference, Titan embeddings, S3 Vectors, one Knowledge Base, Bedrock Evaluations | **$4–8** |
| 2 | Bedrock tool use, AgentCore Runtime + Gateway + Memory, MCP on Lambda | **$5–10** |
| 3 | Guardrails, Lambda + HTTP API, CloudWatch, one short ECS run, **SageMaker GPU lab**, cost engineering | **$10–18** |
| 4 | Capstone on AWS, Knowledge Base rebuild, teardown drill | **$6–12** |
| | **AWS lane total** | **$25–48** |
| | Core lane (OpenAI/Anthropic direct) | $15–35 |
| | **Everything** | **$40–83** |

The overlap is deliberate: on several days you can run the AWS lane *instead of* the paid
core-lane step rather than in addition to it — Bedrock's Claude is the same model as
Anthropic's Claude. Where that swap is available, the day's lane file says so.

**If you're at $35 by Day 18**, drop the SageMaker lab to a design exercise and do the
capstone on Nova Micro. Tell me and I'll adjust the remaining days.

---

## The daily commands

```bash
make aws-cost      # every morning before the lab — 30 seconds
make aws-nuke      # end of every AWS lab — every time, even when you're sure
make aws-doctor    # when something behaves oddly
```

`aws-cost` prints month-to-date spend by service against the $50 line, plus yesterday's
delta. **If a number surprises you, chase it before writing any code that day.** That
instinct — treating an unexplained cost as a bug — is the single most transferable habit
in this lane.
