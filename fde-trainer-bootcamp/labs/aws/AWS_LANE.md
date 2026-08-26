# The AWS Lane — read this before Day 1

**Platform: macOS (Apple Silicon or Intel). Every command in this course is written for a Mac.**
**Hard budget: $50 total across 24 days.**

---

## Why a parallel lane rather than a replacement

You already have AWS skills. That changes the right design: you don't need AWS taught to you,
you need the **GenAI-specific AWS surface** taught to you, and you need to know precisely where
the managed services help and where they hide something you'll be asked to explain.

So the course runs two lanes side by side:

| | **Core lane** | **AWS lane** |
|---|---|---|
| What | Build it from scratch — numpy, your own loop, your own eval harness | Rebuild the same capability on managed AWS services |
| Why | You cannot teach what you have only imported | You cannot deploy at a client without it |
| Cost | ~$0 (Ollama local) | ~$50 over four weeks, with discipline |
| The payoff | You can explain what Bedrock Knowledge Bases is *doing* | You can stand it up in a client account on day three |

**The sentence this whole design exists to earn**, and one you will say in a client meeting
within a month of starting an engagement:

> *"Bedrock Knowledge Bases will get you 80% of this in an afternoon. Here's the 20% it
> doesn't do, here's what it costs at your volume, and here's the specific failure mode you'll
> hit with your document set. Let's decide deliberately rather than by default."*

Nobody can say that who has only used one of the two lanes.

---

## The budget is the constraint, and that is the point

$50 across 24 days is genuinely tight for AWS GenAI work — and it is the most realistic
constraint in the whole course, because **cost discipline is the FDE skill clients notice
first.** A forgotten resource in a client account is a career event, not an inconvenience.

The three numbers to internalise before you touch the console:

| Resource | Left running for one month | As a fraction of your budget |
|---|---|---|
| SageMaker `ml.g5.xlarge` real-time endpoint | **~$1,000** | 20× |
| OpenSearch Serverless *classic* collection, minimum 2 OCU | **~$350** | 7× |
| Amazon Kendra GenAI Enterprise index | **~$230** | 4.6× |
| Fargate, smallest possible task, 24/7 | **~$9** | 18% |

Meanwhile:

| Resource | Cost at course scale |
|---|---|
| S3 Vectors — 2,000 vectors, 5,000 queries/month | **under $0.10** |
| Lambda — every lab in this course | **$0** (1M req + 400K GB-s always free) |
| Nova Lite — 1M in / 200K out tokens | **~$0.48** |
| AgentCore Runtime microVM, 1 vCPU / 2 GB | **$0.108 per active compute-hour**, idle free |

**That asymmetry is the entire lesson of the AWS lane.** The right architecture for a $50
budget is also, very often, the right architecture for a client's pilot — because a pilot at
7,000 queries a month has the same shape as your bootcamp. You will use this table in a real
scoping conversation.

---

## The stack this course uses, and why

| Need | We use | We do **not** use | Why |
|---|---|---|---|
| Inference | **Bedrock** — Nova Micro/Lite default, Claude Sonnet for judging and demos | Provisioned throughput | On-demand only; provisioned Cohere embeddings alone are $7.12/hr |
| Vectors | **S3 Vectors** | OpenSearch Serverless *classic* | $0.06/GB-month vs. a 2-OCU minimum |
| Managed RAG | **Bedrock Knowledge Bases** on S3 Vectors | Kendra | Kendra's floor is $230/mo |
| Agents | **Bedrock AgentCore** Runtime + Gateway + Memory | AgentCore Web Search | Web Search is $7 per 1,000 queries |
| Compute | **Lambda** (+ HTTP API Gateway) | Fargate 24/7 | Lambda's always-free tier covers this whole course |
| Containers | **ECS Fargate**, one short lab, `desiredCount: 0` between runs | Always-on service | ~$9/mo even at minimum size |
| Self-hosted | **SageMaker** real-time endpoint, one 2-hour lab, hard teardown | Anything left running | ~$1,000/mo if forgotten |
| Observability | **CloudWatch** with explicit 1–7 day retention | Default retention | Agent traces are verbose; 5 GB free goes fast |
| Guardrails | **Bedrock Guardrails** | — | $0.10–0.17 per 1,000 text units per policy |

---

## The honest caveats

Three things I could not verify from AWS documentation, and you should check in the console
before you rely on them. Checking them yourself is a five-minute task and a good habit:

1. **Does the Bedrock Knowledge Bases quick-create flow default to S3 Vectors, or to an
   OpenSearch Serverless collection — and if the latter, is it NextGen (scales to zero) or
   Classic (2-OCU minimum, ~$350/mo)?** Historically quick-create provisioned classic
   OpenSearch, which is the single most expensive accidental click in AWS GenAI. **On Day 4's
   AWS lane, read the console screen carefully before clicking Create, and write down what it
   actually provisions.** OpenSearch Serverless NextGen went GA in May 2026 with no OCU
   minimum and scale-to-zero after 10 minutes idle — if quick-create uses NextGen, the old
   warning no longer applies and you should say so when you teach this.

2. **Current SageMaker GPU hourly rates.** Historical us-east-1 list prices are roughly
   `ml.g4dn.xlarge` $0.74/hr, `ml.g6.xlarge` $1.01/hr, `ml.g5.xlarge` $1.41/hr. Confirm in the
   console or the Pricing Calculator before you quote them — a stale GPU price is exactly what
   an experienced audience will catch.

3. **Claude Sonnet 5 and Haiku 4.5 token prices on Bedrock.** Both models are GA; neither
   price was published on a fetchable AWS page. Check the Bedrock console's model catalogue.

Everything else in `AWS_COST_DISCIPLINE.md` was read directly off an AWS pricing page in
August 2026. **Refresh all of it before you teach from it** — that refresh is itself part of
the discipline, and saying "these prices are as of August 2026, here's how I check them"
is more credible than reciting numbers with false confidence.

---

## How the lane is structured

Each week has one file:

- `labs/aws/WEEK_1_AWS.md` — account, budgets, Bedrock, S3 Vectors, Knowledge Bases, Evaluations
- `labs/aws/WEEK_2_AWS.md` — Bedrock tool use, AgentCore Runtime/Gateway/Memory, MCP on AWS
- `labs/aws/WEEK_3_AWS.md` — Guardrails, hybrid retrieval, Lambda + API Gateway, CloudWatch, ECS, IAM/VPC, cost engineering, SageMaker
- `labs/aws/WEEK_4_AWS.md` — the AWS-shaped discovery conversation, capstone on AWS, the well-architected teardown, and the enterprise design

Each day's AWS lane says how long it takes and what it costs. **Total AWS lane time: about
19 hours across 24 days** — roughly 45 minutes a day inside your existing 5.

Where the AWS lane needs more than 45 minutes (Days 4, 11, 15, 17, 21), the day's file tells
you which core-lane stretch goal to drop. **Do not add hours. Trade them.**

---

## The three rules of this lane

**1. Nothing is created without a teardown written first.**
Every AWS lab has an `up` and a `down`. You write `down` before you run `up`. This feels
pedantic on day one and saves you $400 on day seventeen.

**2. `make aws-nuke` runs at the end of every AWS lab. Every one.**
It lists everything the course could have created and deletes it. Run it even when you're
sure there's nothing to delete — that's how it becomes reflexive rather than remembered.

**3. `make aws-cost` runs every morning, before the lab.**
Thirty seconds. It shows spend-to-date against the $50 line. If a number surprises you,
that surprise is the most valuable thing that will happen to you that day — chase it before
you write any code.

---

## Before Day 1 — the AWS setup

Do this the same evening as the core Day Zero setup. Budget 45 minutes.
Full instructions in **`labs/aws/AWS_SETUP.md`**. The short version:

```bash
brew install awscli jq
aws --version                    # want v2.x

# Then, in order — details in AWS_SETUP.md:
#  1. Create the account on the FREE PLAN (not Paid) — closest thing AWS has to a hard cap
#  2. Enable IAM Identity Center; create an admin user; never use root again
#  3. aws configure sso   → profile name: fde
#  4. Set budgets at $5 / $15 / $30 / $45 with SNS email alerts
#  5. Turn on Cost Anomaly Detection (free)
#  6. Request Bedrock model access: Nova Micro, Nova Lite, Claude Sonnet, Titan Embeddings V2
#  7. bash scripts/aws/preflight.sh    → must be green before Day 1
```

Step 6 matters more than it looks: **Bedrock model access is not granted by default** and
approval is not always instant. Request it the night before, not the morning you need it.
