# Day 17 — Deployment: Docker, Cloud, CI/CD, and the Handover

**Fri Sep 18, 2026** · Week 3 · Maps to: **Module 08 — Production I** · Backend: **hosted** · Est. cost: **$2–5**

> **Before you start — read `learn/DAY_17_LEARN.md` (1:15).**
> Deployment topologies, the egress question, tenant isolation. The lab below assumes it and does not re-explain it.


---

## Why today matters

**FDE lens.** "Forward deployed" is in the title. The job is to get the thing running in
*their* environment — which has a VPC, an approval process, a security team, and no
internet egress from the app subnet. Today you deploy publicly (fast, for your portfolio)
and then write the private-deployment design (what actually happens on an enterprise
engagement). Both matter; the second is what gets you hired.

**Trainer lens.** Students who can't deploy can't demo, and a project that only runs on
the author's laptop doesn't get them a job. A crisp deployment session is one of the most
gratefully received things in any bootcamp.

---

## Objectives

1. Containerise the service properly: multi-stage, non-root, healthchecked, small.
2. Deploy to a public URL you can put in a portfolio.
3. Build a CI/CD pipeline: test → eval gate → build → deploy → smoke test.
4. Write the enterprise deployment design: VPC, secrets, private model access, data residency.

---

## Schedule (5:00)

| Block | Time | What |
|---|---|---|
| 0 | 0:30 | Warm-up |
| 1 | 1:15 | **Learn** — `learn/DAY_17_LEARN.md` |
| 2 | 2:45 | Lab: Dockerfile → deploy → CI/CD → enterprise design doc |
| 3 | 0:30 | Teach-back #17 |

---

## Block 0 — Warm-up (0:30)

<!--cards-->
> **Cards first — 5 minutes.** Open **Warm-up drill** in the sidebar of `fde-bootcamp.html`.
> It deals you every card that is due from the days you have finished, hardest box first, and
> it is capped at 20 so it stays a drill. Cards you miss come back tomorrow; cards you know
> go 1 → 2 → 4 → 8 → 16 days out. Then do the recall below, closed book.
<!--/cards-->


1. Which regression was planted, and what signal gave it away first?
2. How long did the incident drill take? What would have made it faster?
3. Name the leading indicator for retrieval drift.
4. What do you capture in a span that a normal HTTP trace wouldn't?

---

## Block 1 — Learn (1:15)

**Read `learn/DAY_17_LEARN.md` and work its examples on paper before continuing.**
Take the self-check at the end. Anything you miss goes on a flashcard and into tomorrow's
warm-up. The material below consolidates the module — it is not a substitute for it.

### 1.1 Four deployment topologies

| Topology | Where | Client type | Constraint you'll hit |
|---|---|---|---|
| **Managed PaaS** (HF Spaces, Render, Railway, Fly) | Public cloud | Startups, demos, your portfolio | No VPC peering; secrets in their vault |
| **Container on their cloud** (ECS/Fargate, Cloud Run, AKS) | Client's account | Mid-market | IAM, VPC endpoints, image scanning |
| **Kubernetes** | Client's cluster | Enterprise | Their platform team's rules, Helm, admission controllers |
| **Fully air-gapped** | On-prem, no egress | Defence, healthcare, some finance | **No hosted model at all** — self-hosted weights, vLLM, GPU capacity planning |

The last row is the one that catches people. If the client cannot send data to a provider,
your entire architecture changes: you need model weights on their hardware, which means
GPU sizing, quantisation choices, throughput math, and a much smaller model than you
prototyped with. **Ask about egress in the first meeting.** It's the single question that
most changes the shape of an engagement, and asking it early makes you look experienced.

### 1.2 What enterprise security will ask

Have answers ready. Write them in `capstone/service/SECURITY_ANSWERS.md`:

1. Where does prompt data go, and is it retained by the provider? (Know the zero-retention
   options and how to enable them.)
2. How do you prevent prompt injection from causing tool execution? (Your Day 15 guards
   plus tool-level authorisation.)
3. What's the blast radius of the agent's most dangerous tool?
4. How are secrets managed and rotated?
5. Is PII redacted before it leaves the boundary? Before it enters logs and traces?
6. What's the audit trail for a given answer? (Your trace_id.)
7. What happens if the provider has an outage? (Your Day 15 degradation path.)
8. How do you prevent one tenant's data reaching another? (Index partitioning, filter
   enforcement at the retriever, not the prompt.)

Number 8 is the one that fails in real systems: a metadata filter applied in the *prompt*
("only use documents where tenant=X") is not a security control. It must be enforced in
the retriever query. Say this out loud once and you'll never build it wrong.

### 1.3 The handover artifact set

An engagement ends when the client can run it without you. That means:

- `README` with a genuinely working local setup (test it on a clean machine)
- `ARCHITECTURE.md` with the diagram and the decisions
- `RUNBOOK.md` — how to deploy, roll back, rotate keys, and what to do for the top 5 alerts
- `CAPACITY.md` — from Day 15
- `SECURITY_ANSWERS.md` — from today
- The eval suite, running in their CI
- A recorded walkthrough

**This document set is your differentiator.** Plenty of people can build the system. The
one who hands over a runbook gets referred to the next team.

---

## Block 2 — Lab (2:45)

### 2.1 Dockerfile, done properly (45 min)

`capstone/service/Dockerfile` — multi-stage, non-root, small:

```dockerfile
# ---- builder ----
FROM python:3.12-slim AS builder
RUN pip install --no-cache-dir uv
WORKDIR /build
COPY requirements.txt .
RUN uv venv /opt/venv && \
    VIRTUAL_ENV=/opt/venv uv pip install --no-cache -r requirements.txt

# ---- runtime ----
FROM python:3.12-slim
RUN useradd -m -u 10001 app
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY --chown=app:app src/ ./src/
COPY --chown=app:app capstone/service/ ./service/
COPY --chown=app:app data/index/ ./data/index/
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s \
  CMD python -c "import httpx,sys; sys.exit(0 if httpx.get('http://localhost:8000/healthz').status_code==200 else 1)"
CMD ["uvicorn", "service.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

Checklist:
- [ ] Image under 1.5 GB (check with `docker images`; if it's 4 GB, find out why —
      usually torch pulled in by sentence-transformers. Decide whether the reranker runs
      in-process or as a separate service. **That's a real architecture decision, made
      for you by image size.**)
- [ ] Runs as non-root
- [ ] `.dockerignore` excluding `.venv`, `.git`, `data/corpus`, recordings
- [ ] Index baked in **or** mounted — decide and document why
- [ ] No secrets in the image. Verify: `docker history --no-trunc` and grep for your key
- [ ] `docker compose up` brings up service + Qdrant + Phoenix together

### 2.2 Deploy publicly (45 min)

Pick one and ship it:

- **Hugging Face Spaces (Docker SDK)** — free tier, great for portfolio, HF-native
- **Render / Railway** — closest to real cloud deployment, free tier available
- **Fly.io** — good regional control, real container semantics

Requirements:
- [ ] Public URL, working, with the Chainlit UI reachable
- [ ] Secrets from the platform's secret store, not the image
- [ ] Rate limiting on (you're exposing an endpoint that costs you money — **this is not
      optional**; put a hard daily spend cap in front of it)
- [ ] A demo mode with a fixed budget that degrades gracefully when exhausted
- [ ] Custom 429 and 503 pages that explain what happened

Add the URL to your portfolio README. **A live URL in a job application is worth more than
a repo**, because a hiring manager will click a link and won't clone a repo.

### 2.3 CI/CD (45 min)

`.github/workflows/deploy.yml`:

```
on: push to main
jobs:
  test:     ruff + pytest + type check
  eval:     fast eval suite with hard gates (Day 13)   ← blocks on regression
  build:    docker build, scan (trivy), push to registry
  deploy:   deploy to staging
  smoke:    hit /healthz, /readyz, and one real /v1/ask; assert a verified citation
  promote:  manual approval → production
```

The smoke test asserting a **verified citation** — not just a 200 — is the detail that
matters. A service that returns 200 with a hallucinated answer is "healthy" by every
normal check. Your smoke test should catch a broken index.

Test the whole pipeline by pushing a deliberate eval regression and watching deploy get
blocked. Screenshot for the portfolio.

### 2.4 The enterprise design doc (60 min)

`capstone/service/ENTERPRISE_DEPLOYMENT.md` — this is the writing exercise, and it's the
most FDE-shaped thing you'll do this week.

Scenario: *a mid-size 3PL, AWS, data cannot leave their VPC, SOC 2, 40 internal users
initially, 500 within a year.*

Cover:

1. **Architecture diagram** — VPC, subnets, ALB, ECS/Fargate, RDS, OpenSearch or a
   self-hosted Qdrant, VPC endpoint to Bedrock. Draw it.
2. **Model access** — Bedrock via VPC endpoint (data stays in their account) vs. self-hosted
   on `g5.xlarge` with vLLM. Give both options with costs and a recommendation.
3. **Secrets** — Secrets Manager, rotation, IAM task roles, no long-lived keys.
4. **Data flows** — what leaves the VPC (ideally nothing), what's logged, retention periods.
5. **Multi-tenancy** — index partitioning and filter enforcement at the retriever.
6. **Cost model** — monthly at 40 users and at 500. Show your arithmetic. Include the
   fixed infrastructure cost, which people always forget and which dominates at low volume.
7. **Rollout** — pilot cohort, success criteria, expansion gates.
8. **Runbook pointers** — the five alerts and their first response.

Aim for 3–4 pages. **Write it as if you're sending it to a client architect on Monday**,
because on a real engagement, you are.

---

## Block 3 — Teach-back #17 (0:30)

Record 12 min: **"Deploying is easy. Deploying inside someone else's VPC is the job."**
`teaching/recordings/day_17.mov`

Show the public deploy in three minutes. Then spend nine on the enterprise design: the
egress question, the tenant-filter-must-be-in-the-query point, and the cost model at two
scales. Close with the handover artifact list.

---

## Done when

- [ ] Multi-stage Dockerfile, non-root, under 1.5 GB, healthchecked, no secrets
- [ ] `docker compose` bringing up the full local stack
- [ ] Live public URL with rate limits and a spend cap
- [ ] CI/CD with an eval gate that provably blocks a regression, plus a smoke test that
      asserts a verified citation
- [ ] `ENTERPRISE_DEPLOYMENT.md`, 3–4 pages, with two model-access options and costs at two scales
- [ ] `SECURITY_ANSWERS.md` with all eight answers

---

## Trap list

- Secrets baked into the image. Check `docker history`.
- A public endpoint with no spend cap. People will find it.
- Tenant filtering expressed in the prompt rather than the query. Not a security control.
- Deploying without a rollback path. Know your rollback command before you need it.
- A smoke test that only checks `/healthz`. It will pass with a broken index.
- Quoting only variable costs. Fixed infra dominates at low volume and clients notice
  when your estimate is off by 5×.

---

## Stretch

Add **blue/green with automatic rollback**: deploy green, run the fast eval suite against
it in production, and promote only if metrics hold. Auto-rollback on breach. Then
demonstrate it by deploying a bad prompt change and watching the system roll itself back.
That demo, recorded, is a genuinely senior artifact — very few people have built it.
