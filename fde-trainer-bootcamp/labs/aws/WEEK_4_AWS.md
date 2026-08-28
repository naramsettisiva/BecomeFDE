# AWS Lane — Week 4 (Sep 22 – Sep 29)

**macOS. Est. AWS spend this week: $6–12. Est. added time: 4h across six days.**

Week 4 is where the AWS lane stops being technical practice and becomes the thing you sell:
a deployed system in a real cloud account, a cost model with measured numbers behind it, and
the ability to have the build-vs-buy conversation without hand-waving.

```bash
make aws-cost      # every morning. You should be around $25-40 by now.
```

If you're above $40 on Day 19, say so and I'll cut the Day 20–21 AWS scope to Nova Micro
only. Finishing under budget is a better outcome than a slightly richer capstone.

---

## Day 19 — The AWS-shaped discovery conversation · 45 min · no AWS spend

Your Day 19 core lane built a discovery framework. On a real engagement, a large share of
clients are on AWS, and there are questions that only matter there — asking them in the first
meeting is a strong signal that you've done this before.

### Do

1. **Extend `DISCOVERY_GUIDE.md` with an AWS section.** Not a service checklist — questions
   whose answers change the architecture:

   **Landing zone and identity**
   - Single account or Control Tower with an OU structure? Who owns the account you'll build in?
   - Is there an existing SCP that would block Bedrock, or restrict regions?
   - How do humans and CI get credentials today? (If the answer is long-lived IAM access keys,
     you've just found your first improvement, and it's an easy win.)

   **The egress question, asked properly**
   - Can data leave the VPC? (Then: can it leave the *account*? Those are different answers
     and people conflate them.)
   - Do you have VPC endpoints for Bedrock today, or would that be new?
   - Is Bedrock enabled at all, and which models have been approved? (Model access is a
     request-and-approve flow; at some enterprises that takes weeks. Start it in week one.)

   **Data**
   - Where do the documents live *right now*? S3, SharePoint, a wiki, someone's laptop?
   - Is there existing lineage or classification you must respect?
   - Retention: how long may prompts and completions be stored? This determines your
     CloudWatch and Bedrock invocation-logging design, and it is a compliance answer, not a
     technical preference.

   **Cost and ownership**
   - Who sees the bill? Is there a chargeback or showback model? (This decides whether you need
     per-tenant cost attribution from day one — and it's much cheaper to build in than to add.)
   - Existing Savings Plans or Reserved commitments that should influence compute choices?
   - Who operates this after I leave? Do they have on-call today?

2. **Add two AWS-shaped hard conversations** to your Day 19 set. Rehearse both out loud:

   **"You don't need SageMaker."**
   > *"You've asked about hosting the model yourself. I ran the numbers on a g5.xlarge this
   > month — break-even against Bedrock's on-demand pricing is around a billion output tokens a
   > month at full utilisation, and realistically four to six times that once you account for
   > actual duty cycle. At your projected volume you'd be paying roughly twenty times more,
   > plus the ops burden. If the driver is data residency rather than cost, a Bedrock VPC
   > endpoint gets you that without the GPU. Which is it?"*

   **"Your quick-create just provisioned $350 a month."**
   > *"Before we go further — the knowledge base in your dev account is backed by an OpenSearch
   > Serverless classic collection. That bills a two-OCU minimum whether you query it or not,
   > about $350 a month. There's an S3 Vectors option that would cost you cents at your volume.
   > Want me to migrate it this week?"*

   That second one is a real conversation that happens constantly, and it's the fastest way an
   FDE demonstrates value in week one. **Finding money is more persuasive than building
   features.**

3. **Add an AWS column to the scoping canvas**: landing zone · egress posture · Bedrock model
   access status · who owns the bill · who operates it after handover.

---

## Day 20 — Capstone on AWS: the vertical slice, deployed · 60 min · ~$2

Same discipline as the core lane: **ugly and complete beats beautiful and partial.**

### Do

```bash
bash scripts/aws/lab_up.sh capstone     # KB + Lambda + HTTP API + log group, retention 7d
```

1. **Get the AWS path working end to end by lunch.** Carrier review generation, running on
   Lambda, retrieving from the Knowledge Base, generating on Nova Lite, writing output to S3.

2. **Nova Lite is your default. Claude only where the eval proves it's needed.**
   The discipline here is worth naming: run the whole thing on Nova Lite first, run your eval,
   and only promote specific steps to Claude where the score demands it. You will likely find
   that data lookup and computation are fine on Nova Micro, and only the final narrative
   writing benefits from a frontier model.

   **That per-step model routing is a real production pattern and a genuinely good demo** —
   most people pick one model for the whole system and never revisit it.

3. **Keep the local stack working.** The demo is *both*. A carrier review generated locally and
   the same review generated on AWS, side by side, same output, different cost line.

4. **Cost attribution from the start:** tag every resource, and emit the per-request cost
   metric with a `Tenant` dimension. When the Day 21 case study says "$0.04 per review," it
   should come from a metric you emitted, not a calculation you did afterwards.

---

## Day 21 — Harden on AWS, and the teardown drill · 60 min · ~$2

### Do

1. **Apply the Week 3 hardening on the AWS path:**
   - [ ] Guardrail attached, with only the policies this route needs (per-policy billing)
   - [ ] Bedrock invocation logging on, with the retention you decided on Day 16
   - [ ] X-Ray tracing end to end; `trace_id` in the generated document's footer
   - [ ] Per-generation cost cap enforced in code — partial document with a banner, not silence
   - [ ] Least-privilege execution role: specific model ARNs, one bucket, one KB
   - [ ] Reserved concurrency on the Lambda, so a runaway loop can't scale to your whole budget

   That last one is a small config change with a large blast-radius reduction, and it's the
   kind of thing a client's platform team notices you did without being asked.

2. **The teardown drill** — 20 minutes, and it belongs in the case study:

   > A client asks: *"if we don't proceed after the pilot, what does it cost us to stop, and
   > how long does it take?"*

   Answer it by doing it. Run `make aws-nuke`, time it, verify with `aws-cost`, then bring the
   whole stack back up with `lab_up.sh` and time that too.

   Write `capstone/service/TEARDOWN.md`: what gets deleted, what persists (S3 data, logs), what
   the residual monthly cost is if they keep the data but stop the service, and how long a
   restore takes.

   **Almost nobody can answer that question, and every enterprise buyer wants to ask it.** A
   pilot that can be cleanly stopped is a pilot that's easier to start — which means naming
   the exit is a way of getting to yes, not a sign of doubt.

3. **Add the AWS section to the case study:**
   - The architecture, with the managed-service trade named per box
   - Cost per review, measured, at pilot and production scale
   - The retrieval decision memo's conclusion (Day 14)
   - The self-hosting break-even (Day 18)
   - The teardown answer

---

## Day 22 — Curriculum: the AWS module · 45 min · no spend

Your learning log now has four weeks of AWS-specific confusions. Mine them the same way.

### Do

1. **Add AWS failures to your failure-organised curriculum**, in the same voice as the rest:

   ```
   Module 11  "The bill arrived and nobody could explain it"
                → cost attribution, per-request metrics, the never-leave-running list,
                  why a budget is not a cap
   Module 12  "It works on my laptop but not in their account"
                → IAM, VPC endpoints, model access approval, SSO expiry, architecture mismatch
   ```

2. **Build the AWS lesson's opening failure.** You have three strong candidates; pick the one
   with the best live demo:

   - **The $350 empty collection.** Show the quick-create form, show the pricing page, show
     the alternative. Visceral, and it has saved real money for real teams.
   - **The managed judge you can't calibrate.** Show Bedrock Evaluations returning 0.88, then
     show your κ of 0.51 against hand labels. Harder to grasp, more valuable once grasped.
   - **The prompt you can't see.** Ask a Knowledge Base a question, get a wrong answer, and
     demonstrate that you cannot inspect the assembled prompt to find out why.

   The third is my recommendation for a senior audience: it's the cleanest illustration of what
   a managed abstraction actually costs you, and it connects directly to Day 4's four-clause
   RAG contract.

3. **Write the build-vs-buy decision framework** — `teaching/build_vs_buy.md`. Not a
   preference; a set of questions with your own measured evidence attached:

   | Question | Buy managed when | Build when |
   |---|---|---|
   | Do you need to see the prompt? | no | yes — debugging, compliance, or you're teaching it |
   | Is the eval metric gate-worthy? | broad regression sweeps | you gate on it and need calibration |
   | Is quality sensitive to chunking? | defaults are fine | you've measured that they aren't |
   | What's the volume? | pilot / bursty | sustained and high enough to amortise |
   | Who operates it after you leave? | a small team | a platform team that wants control |
   | Is there a hard residency constraint? | VPC endpoint solves it | only if it doesn't |

   **This framework is a teaching asset and a consulting asset simultaneously.** It's the thing
   you hand a client architect, and it's a session on its own.

---

## Day 23 — Deliver the AWS segment live · 30 min within the live lesson

Fold a **10-minute AWS segment** into your 60-minute lesson. Don't bolt it on the end — put it
where it belongs, at the point where the audience is asking "but how would I actually run this?"

Structure:
1. **The failure** (2 min) — your chosen opener from Day 22, live.
2. **The frame** (2 min) — the build-vs-buy table, on screen.
3. **The evidence** (4 min) — your numbers. KB vs. hand-rolled recall. Guardrail false-positive
   rate. Self-hosting break-even. Real figures from your own account, not a vendor slide.
4. **The recommendation** (2 min) — *"start managed, here's the specific point at which you'll
   need to leave, and here's how to know you've reached it."*

The whole segment lands on that last sentence. **A trainer who says "use Bedrock" is repeating
marketing. A trainer who says "use Bedrock until X, and here's how I measured X" is teaching.**

Then handle the AWS questions in your hostile Q&A drill. Expect:

- *"Isn't Bedrock more expensive than calling OpenAI directly?"* (Same Claude, similar price.
  The difference is where the data goes and who your contract is with.)
- *"We're a Google shop."* (The seam. One env var. Show it.)
- *"Our security team won't approve any hosted model."* (VPC endpoint, then the self-hosting
  break-even. In that order — most objections dissolve at the first step.)
- *"How do we stop this becoming a runaway bill?"* (Reserved concurrency, per-request cost
  metrics, budgets, and the honest fact that AWS has no hard cap.)
- *"What happens when Bedrock has an outage?"* (Your Day 15 degradation path. If you did the
  stretch, show it.)

---

## Day 24 — The AWS portfolio, and closing the account cleanly · 45 min

### Do

1. **Publish the AWS artifacts.** These are the ones that read as senior:

   - `SELFHOST_ANALYSIS.md` — measured throughput, break-even, utilisation sensitivity
   - `day14_aws_retrieval_decision.md` — four options, priced at two scales, with a crossover
   - `ENTERPRISE_DEPLOYMENT.md` + `SECURITY_ANSWERS.md` — the VPC design and the eight answers
   - `TEARDOWN.md` — the question nobody else can answer
   - `build_vs_buy.md` — the framework

   **Written analysis with numbers travels further than code.** A hiring manager will skim your
   repo; they will *read* a two-page memo that answers a question they've been arguing about
   internally. Lead your portfolio with these, not with the repo tree.

2. **Write the short technical post** you drafted on Day 24. Strongest AWS candidate:
   *"I measured the SageMaker vs. Bedrock break-even so you don't have to"* — narrow, data-backed,
   contrarian to vendor messaging, and useful. That is exactly the shape of post that gets
   shared.

3. **Add AWS to the gap assessment.** You've now closed part of the self-hosted-serving gap
   (you deployed a GPU endpoint and measured its knee). Still open:
   - Fine-tuning / model customisation on Bedrock or SageMaker
   - Multimodal — Bedrock Data Automation on scanned freight paperwork (BOLs, PODs). **This is
     a genuinely unmet need in your domain** and would make a strong month-two project.

4. **Close the account down properly:**

   ```bash
   make aws-nuke
   make aws-nuke-dry        # must find nothing
   make aws-cost            # note the final number
   ```

   Then in the console, verify by hand — because a script is only as good as the resource types
   it knows about, and that limitation is worth internalising:

   - [ ] SageMaker → Endpoints: empty
   - [ ] OpenSearch Serverless → Collections: empty
   - [ ] Kendra → Indices: empty
   - [ ] Bedrock → Knowledge bases, Guardrails, AgentCore memories: empty
   - [ ] ECS → Services and clusters: empty
   - [ ] CloudWatch → Log groups: retention set on anything you keep
   - [ ] S3 → keep the vector bucket if you want (~cents), delete the rest
   - [ ] **Budget alerts: leave them on.** They cost nothing and they'll catch whatever you
         build next.

5. **Record the final number in `LEARNING_LOG.md`:** total AWS spend across 24 days, against
   the $50 budget, with the three biggest line items named.

   That number is a portfolio fact in itself. *"I built and deployed a production agentic
   system on AWS — Bedrock, S3 Vectors, AgentCore, Lambda, ECS, and a GPU endpoint — for
   thirty-one dollars, and here's the cost model"* is a better opening line than any list of
   services, because it demonstrates the discipline rather than claiming it.

---

## Week 4 AWS lane — done when

- [ ] Discovery guide extended with landing zone, egress, data, and cost-ownership questions
- [ ] Two AWS hard conversations rehearsed and recorded
- [ ] Capstone running on AWS end to end, with per-step model routing proven by eval
- [ ] Local and AWS stacks both working, demoed side by side with a cost line
- [ ] Full hardening applied, including reserved concurrency and least-privilege roles
- [ ] `TEARDOWN.md` written from an actual timed teardown-and-restore
- [ ] Two AWS modules added to the curriculum, with a chosen opening failure demo
- [ ] `build_vs_buy.md` framework written with your own evidence in it
- [ ] 10-minute AWS segment delivered inside the live lesson
- [ ] Five AWS written artifacts published and linked from the portfolio
- [ ] Account verified empty by hand, budget alerts left on
- [ ] Final spend recorded with the top three line items named
