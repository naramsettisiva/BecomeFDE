# Day 12 · Learn — Integration, system-level evaluation, and the architecture review

**Read before `labs/DAY_12.md`. Budget 0:45.**

---

## 1. Where this sits

You have six working pieces: retrieval, an agent loop, agentic-RAG patterns, a supervisor with
workers, memory, and an MCP server. Each was measured on its own and each passed.

Today they become one system, and **integration is where the problems you haven't met yet live.**
That sentence is not new to you — you've spent twenty-three years on the fact that a distributed
system fails in ways none of its services do. What's new is which specific failures this stack
produces, and that the debugging surface is a probabilistic component whose behaviour changes when
the input changes by four hundred tokens.

The second half of today is the teaching format that goes with it. Day 6's lesson was a **tutorial** —
you taught someone to build. Today is an **architecture review**: you walk a senior audience through
a system that exists and justify every decision in it. Different format, harder, and the one you'll
use most often with the people who sign contracts.

---

## 2. The mechanism

### 2.1 Four problems that only exist at the seams

**State that doesn't flow.** Each component was tested with its inputs handed to it. Wired together,
something upstream has to *produce* those inputs. The supervisor resolves "what about for reefer?"
using episodic memory — but only if the memory layer is read before the router runs, and the router
was built on Day 8 when memory didn't exist. Day 9 §2.3's context loss at handoff is this failure
in its most common form.

**Cost that compounds.** Every component multiplied its predecessor's call count. Routing (1 call) →
supervisor (1 plan) → three workers (2–4 steps each, each re-sending its own transcript) →
verification. You don't add costs across a system like this; you **multiply call counts and sum
quadratics** (Day 9 §2.5). A system of individually cheap parts is routinely 10× the naive baseline.

**Latency that stacks.** Sequential nodes add. A 400 ms router in front of a 6-second supervisor
looks free until you learn the router misroutes 6% of queries into a path that costs another four
seconds. Only nodes on the **critical path** matter, and parallel workers cost you `max`, not `sum` —
which is the single biggest structural latency lever you have.

**Failures that surface far from their cause.** The one that will actually cost you an evening: a
retrieval in step 4 returns a chunk severed from its condition (Day 3 §2.6), the analyst in step 9
uses it, and the answer is a confidently wrong dollar figure with a verified citation attached. The
symptom is in the answer. The defect is five nodes upstream. **Without a trace this is
unfalsifiable**, which is why the trace viewer is not a nice-to-have.

### 2.2 You evaluate the system, not the parts

Component metrics are all **conditional**, and integration breaks the conditions.

Retrieval recall of 0.91 means *given this query, the right chunk is in the top k.* End to end, the
query reaching retrieval is one the rewriter produced from a question the router classified from a
turn that memory resolved. Each stage has its own accuracy, and **the stages multiply**:

```
end-to-end ceiling = router_acc × rewrite_acc × recall × generation_faithfulness
```

Four stages at 0.94, 0.97, 0.91 and 0.95 give a ceiling of **0.79** — with no component below 0.91.
Nobody shipped a bad part. The system is worse than any of them, necessarily, and that arithmetic
is the whole argument for system-level evaluation.

So the golden set needs cases that **cannot exist at the component level**: multi-turn references
that require episodic memory, questions needing policy *and* data in one answer, and questions that
must be refused *after* a retrieval attempt rather than instead of one.

And expect the finding the lab asks you for: **integration usually regresses something.** Routing
sends some class of query down a worse path than the single best component would have taken. Find
it, name it, and quantify it — it's the most credible thing you'll say in the review.

### 2.3 p50, p95, and which one blows what

Two numbers, two different jobs, and mixing them up is the most common quantitative error in this
kind of review.

| | Driven by | Governs |
|---|---|---|
| **mean** | everything, dragged upward by the tail | **the monthly bill** |
| **p50** | the typical request | what a demo feels like |
| **p95** | retries, extra agent steps, big retrievals | **SLOs, timeouts, and budget-limit hit rates** |

**The cost distribution is right-skewed**, because the step count is decided at runtime and the
quadratic in Day 7 §2.5 punishes long runs. A handful of 12-step requests sit far from the median,
so p50 understates the mean, sometimes by 2×. Budget from the mean; set limits from p95.

**And p95 is where the failures cluster.** Every request over the p95 latency is a candidate for a
client-side timeout, and every request over the p95 cost is a candidate for tripping your own
`max_cost_usd` and returning a partial answer. If more than ~5% of requests hit a limit, either
your limits are wrong or your agent is inefficient — and the lab asks you to determine which,
because they have opposite fixes.

**The tail gets worse as you add nodes**, which is the Dean & Barroso result (*The Tail at Scale*,
2013) applied to your supervisor. If each of three workers independently has a 5% chance of being
slow, the request is slow when *any* of them is: `1 − 0.95³ = 14.3%`. **Fan-out amplifies the tail.**
Your workers made the p50 better and the p95 worse, and you should be able to say so out loud.

### 2.4 Attribution: per-node latency and cost

*"The LLM is slow"* is not a finding. It names the only component you can't change, and it's usually
wrong — a meaningful share of wall clock in these systems is retrieval, tool I/O, and serialisation.

Attribute everything to a node:

```
Request 7f3a · 6.8s · $0.0071 · 11 LLM calls
├─ route              120ms   $0.0000  → "multi_hop" → supervisor
├─ supervisor plan    890ms   $0.0012  → 3 sub-tasks
├─ ▸ policy           2.1s    $0.0028  → 2 retrievals, 4 chunks, 2 citations
├─ ▸ data             980ms   $0.0009  → mcp:carrier_scorecard(Ridgeline, 2026-08)
├─ ▸ analyst          2.4s    $0.0019  → band=Silver, composite 78.5
└─ verify               8ms   $0.0000  3/3 citations verified ✓
```

Two questions this makes answerable, and neither is answerable without it:

**What's on the critical path?** Here, policy + data + analyst run sequentially: 5.5 s of the 6.8 s.
Run policy and data in parallel and you pay `max(2.1, 0.98) = 2.1` instead of `3.08` — about a
second, for a scheduling change and no quality cost. Note that this helps p50 modestly and helps
p95 much more, because the tail is where one slow node was serialising behind another.

**Where does the money go?** "The analyst is 27% of spend and most of it is a duplicate policy
search" is a finding with a fix attached. "It costs seven-tenths of a cent" is trivia.

### 2.5 What a trace must capture

The test of a trace is simple: **can you answer "why did it say that?" without re-running the
request?** If not, it's telemetry, not a trace.

| Field | Why you need it |
|---|---|
| request id, span id, parent span id | Reconstruct the tree; correlate with the client's report |
| node name and type | Attribution (§2.4) |
| start / end timestamps | Latency, and whether nodes actually ran in parallel |
| model id **and version** | Provider version changes silently; "it got worse on Tuesday" needs this |
| input / output token counts, cost | The only honest cost attribution |
| the exact prompt (or its hash) | The answer to "why did it say that." Sample the full text; hash always |
| tool name, arguments, result size | Day 7's failure modes are all visible here |
| retrieval scores and doc ids | Distinguishes a retrieval miss from a generation miss |
| citation verification result | Clause 4 of the RAG contract, per request |
| `stop_reason` | `complete` vs `budget` vs `max_steps` vs `repeat_detected` — different bugs |
| error class | Retryable / user-correctable / fatal (Day 7 §2.6) |

Two practical notes. **Keep metadata for everything, full prompts for a sample** — prompt text
dominates storage, and 1–5% is enough to debug with. And **the trace is a client-facing artefact,
not just a debugging tool**: in a room full of people demoing chat boxes, putting the machinery on
screen with timings and dollars attached is what makes a technical buyer trust you.

### 2.6 The architecture review is a different format from the tutorial

Day 6 taught you a lesson's six beats. Today's format shares almost none of them.

| | **Tutorial** (Day 6) | **Architecture review** (today) |
|---|---|---|
| Goal | They can build it | They can **decide** about it |
| Audience | Practitioners | Senior — architects, VPs, a security lead |
| Earns trust by | A measured fix, live | **Naming your own weaknesses, unprompted** |
| Core content | Mechanism, built up | **Decisions, with their alternatives** |
| Numbers | Illustrative | **Specific and sourced** |
| Fatal error | No measured fix | Presenting a diagram without a decision in it |
| First thing to cut | The third example | The build detail nobody asked for |

The trap is that a review *feels* like a tour: here's the router, here's the supervisor, here are
the workers. A tour is not a review. **A review is a defence of choices**, and the boxes are only
there to give the choices somewhere to live.

### 2.7 The three things that make a review credible

**1 · Every decision comes with its alternative and its cost.** The format is one sentence:

> *"We route before the supervisor because 60% of queries are single-hop lookups and the supervisor
> costs 3× on those. The alternative was sending everything to the supervisor, which is simpler and
> has one fewer failure mode. What we gave up: the router misclassifies about 6% of queries, and a
> misroute is worse than no route because it answers confidently from the wrong path."*

Claim, alternative, and what you gave up. Do that three times — for us: routing before the
supervisor, MCP instead of direct function calls, and verifying citations rather than trusting them —
and you've spent five minutes and established that the system was designed rather than accreted.
**A decision with no named alternative reads as an accident.**

**2 · Name real weaknesses before anyone asks.** This is the segment that separates a consultant
from a vendor, and it's counter-intuitive enough that most people skip it. Four sentences each:

> *"p95 latency is 11 seconds, against a p50 of 4.2. It's the supervisor fan-out — three workers,
> and the request is only as fast as the slowest. I'd parallelise policy and data, which the trace
> says buys about a second, and cap the analyst at two steps. Two days of work, and I'd want a
> re-run of the 80-case set before believing the number."*

Named, quantified, with a fix and a cost. No hedging, no apology. A senior audience has already
guessed where it's weak; hearing you say it first is what makes the rest of your numbers believable.

**3 · Numbers are specific and sourced.** "About 90%" is worth nothing. **"86% on the 80-case golden
set, run September 7 against Claude Sonnet — the 20 integration cases score 71%, and that gap is the
regression I mentioned"** is worth the whole talk. Sourced means: what set, how many cases, which
model, when. If you can't source a number, don't say it — say you'd need to measure it, which costs
you nothing and buys you the credibility of the numbers you *can* source.

---

## 3. Worked example — on paper

> **Setup.** The integrated copilot. Per-node figures from §2.4. A 20-request cost sample, sorted
> (dollars): 0.0031, 0.0034, 0.0038, 0.0041, 0.0044, 0.0047, 0.0051, 0.0055, 0.0058, 0.0062,
> 0.0066, 0.0071, 0.0078, 0.0084, 0.0093, 0.0110, 0.0140, 0.0190, 0.0280, 0.0410.

**Q1.** From the §2.4 trace: total wall clock, the sequential worker time, and the saving from
running policy and data in parallel. Which percentile benefits more, and why?

**Q2.** From the sample: p50, p95, and mean. Which do you use to project a monthly bill at 10,000
queries, and which to set `max_cost_usd`?

**Q3.** With `max_cost_usd = 0.02`, what fraction of this sample trips the limit? Is that a limits
problem or an agent problem, and how would you tell?

**Q4.** Router 0.94, rewrite 0.97, retrieval recall 0.91, faithfulness 0.95. End-to-end ceiling? What
does that mean for a client who was quoted "91% retrieval accuracy"?

**Q5.** Each of three workers independently has a 5% chance of exceeding 4 seconds. Probability the
request exceeds 4 seconds? What if you add a fourth worker?

**Q6.** From §2.4's cost lines, express the analyst's share as a finding a client can act on.

**Q7.** A 25-minute review at Day 6's pace of ~125 spoken words per minute. Total words. The
decisions segment is minutes 5–10 — how many words, and how long per decision if you cover three?

<details>
<summary><b>Answers</b></summary>

**Q1.** Total **6.8 s**. Workers sequential: 2.1 + 0.98 + 2.4 = **5.48 s**, or 81% of the request.
Parallelising policy and data: `max(2.1, 0.98) = 2.1`, saving **0.98 s** → ~5.8 s. **p95 benefits
more than p50**: at the median both nodes are near their typical times, but in the tail one slow
node was serialising behind another, and `max` truncates that where `sum` accumulated it.

**Q2.** p50 = mean of the 10th and 11th values = (0.0062 + 0.0066)/2 = **$0.0064**. p95 = the 19th
value ≈ **$0.0280**. Mean = **$0.009915**. **Project the bill from the mean**: 10,000 × $0.009915 =
**$99.15/month**. Using p50 would say $64 — a 35% miss, entirely from five requests. **Set
`max_cost_usd` from p95**, not the mean, or you truncate a fifth of your traffic.

**Q3.** Two of twenty exceed $0.02 → **10%**. That's above the 5% threshold, so something's wrong.
Tell them apart from the traces: if the expensive requests are legitimately hard (multi-hop,
several retrievals, a real answer at the end) the limit is too tight; if they're repeated tool calls,
oversized observations, or a worker looping, it's an agent problem and raising the limit just buys
more of the same. Look at `stop_reason` and the repeat-detection fingerprints.

**Q4.** 0.94 × 0.97 × 0.91 × 0.95 = **0.788**. Roughly **79%** end to end, with no component below
0.91. The client who heard "91% retrieval accuracy" will read a 79% system as a broken promise —
which is why you quote **end-to-end numbers on the integrated set**, and use component numbers only
to explain where the loss is.

**Q5.** 1 − 0.95³ = **14.3%**. With four: 1 − 0.95⁴ = **18.5%**. Each additional parallel worker
raises the probability that *something* is slow. Fan-out improves throughput and typical latency; it
degrades the tail, monotonically.

**Q6.** Analyst = $0.0019 of $0.0071 = **27% of request spend**, for a node that runs no retrieval.
The actionable form: *"the analyst is 27% of spend and its trace shows a duplicate policy search the
policy agent already ran — passing the policy result through the handoff removes it."* Compare with
"it costs seven-tenths of a cent," which permits no action.

**Q7.** 25 × 125 ≈ **3,125 words**. The decisions segment is 5 minutes ≈ **625 words**, so three
decisions is **~208 words each, about 100 seconds.** That's claim, alternative, and what you gave up —
and nothing else. If your notes for one decision run past 200 words you will overrun or rush, and
rushing is the most common failure on a recording.

</details>

---

## 4. What people get wrong

**"Every component passed, so the system works."**
Stages multiply (§3 Q4). Four components above 0.91 give a 79% system.

**"Integration is wiring."**
It creates four problem classes that didn't exist in any part: state flow, compounded cost, stacked
latency, and failures that surface far from their cause.

**"Report the median cost."**
The median describes a demo. The mean pays the bill and p95 sets your limits.

**"The LLM is the slow part."**
Sometimes. Attribute per node before you say it — retrieval, tool I/O and serialisation are often a
third of wall clock, and they're the parts you can actually fix.

**"Adding parallel workers makes it faster."**
Faster at p50, slower at p95 (§3 Q5). Fan-out amplifies the tail.

**"A trace is for debugging."**
It's also the artefact that sells the system, and the only way to answer "why did it say that"
after the fact.

**"An architecture review is a walkthrough of the diagram."**
A tour is not a review. A review is a defence of decisions; the boxes just give them somewhere to
live.

**"Don't volunteer weaknesses — it undermines confidence."**
Backwards for a senior audience. They've already guessed; saying it first is what makes your other
numbers credible.

**"Round numbers are fine in a summary."**
"About 90%" is unsourced and reads as guessed. Name the set, the size, the model, and the date.

---

## 5. The trainer's angle

**The analogy that lands:** this is a distributed system and you already know how those fail —
except that one of the services is non-deterministic and its behaviour changes when its input grows
by four hundred tokens. For an infrastructure audience that lands hard, because it reframes
everything they're seeing as familiar problems with one unfamiliar component, rather than a new
discipline.

**The demo that makes it click:** the trace viewer, live, on a real question — *"Ridgeline's FTA is
83% and their composite is 78.5. What happens next?"* Point at the timings and the dollars as you
narrate. Then click into one node and show the exact prompt. The room understands in fifteen seconds
that you can debug this system, and that is the entire purpose of the artefact.

**The beat that earns the room:** minutes 16–20, the weaknesses. Rehearse it more than any other
segment, because the instinct to soften is strong and softening is what ruins it. Name it, quantify
it, say the fix, say the cost. Four sentences, no hedging.

**The predictive question:** *"Router 0.94, rewrite 0.97, recall 0.91, faithfulness 0.95 — what does
the system score end to end?"* Almost everyone guesses around 0.90, near the weakest link. Then show
0.79. That single number reframes system evaluation better than any argument, and it takes twenty
seconds.

**The question a sharp student will ask:** *"If the integrated system regressed against my best
single component, why ship the integration?"*

> Because they're not answering the same question. The single-shot RAG path wins on the 60% of
> traffic that's a simple lookup, and it can't answer the multi-hop questions at all — it doesn't
> regress on them, it's absent. What the integrated numbers show is that routing sends some queries
> down a worse path than they'd have taken, and that's a real regression I'd fix by tightening the
> router rather than by removing the supervisor. The honest framing for a client is: we bought
> coverage of a question class we previously refused, and it cost us a few points on a class we
> already served plus 3× on cost. Whether that's worth it depends on how much of their traffic is
> the new class — which is a question about their data, not about my architecture. Nobody should
> ship an agent because agents are good; you ship it when the question shape requires it.

---

## 6. Self-check

Cover the answers.

1. Name the four problem classes that appear only at integration.
2. Why can't you infer system quality from component quality? Give the arithmetic.
3. What three kinds of case must a system-level golden set contain that a component set can't?
4. Which statistic drives the monthly bill, and which sets your budget limits? Why the difference?
5. Why does fan-out make p95 worse, and what's the formula?
6. What's on the critical path in §2.4's trace, and what does parallelising buy?
7. Name six fields a trace must carry, and what each answers.
8. What's the one-sentence test for whether a trace is useful?
9. State the three-part shape of a decision in an architecture review.
10. What's the four-sentence shape for naming a weakness?
11. What makes a number "sourced"?
12. Give three differences between the tutorial format and the architecture-review format.

<details>
<summary><b>Answers</b></summary>

1. State that doesn't flow between components; cost that compounds; latency that stacks; failures
   that surface far from their cause.
2. Component metrics are conditional on inputs the integrated system now produces, and stages
   multiply: 0.94 × 0.97 × 0.91 × 0.95 = 0.79.
3. Multi-turn references needing episodic memory; questions needing policy and data together;
   questions that must be refused after a retrieval attempt.
4. The **mean** drives the bill (it includes the tail); **p95** sets limits and SLOs. The cost
   distribution is right-skewed because step count is decided at runtime, so p50 understates the
   mean.
5. The request is only as fast as its slowest branch: `1 − (1−p)ⁿ`. Three workers at 5% → 14.3%.
6. Policy → data → analyst, 5.48 s of 6.8 s. Parallelising policy and data pays `max` instead of
   `sum`, saving ~1 s, and helps p95 more than p50.
7. Any six of: request/span/parent ids (tree), node name (attribution), timestamps (latency and
   real parallelism), model id and version (silent provider changes), token counts and cost
   (attribution), exact prompt or hash ("why did it say that"), tool name/args/result size,
   retrieval scores and doc ids (retrieval vs generation miss), citation verification, `stop_reason`,
   error class.
8. Can you answer "why did it say that?" without re-running the request?
9. Claim, the alternative you rejected, and what you gave up by choosing yours.
10. Name it, quantify it, say what you'd do, say what that costs.
11. It names the set, the number of cases, the model, and the date the run happened.
12. Any three: goal (build vs decide); audience (practitioners vs senior); what earns trust (a
    measured fix vs naming weaknesses); core content (mechanism vs decisions); numbers
    (illustrative vs sourced); fatal error (no measured fix vs a diagram with no decision in it).

</details>

**Scored below 9?** Re-read §2.3 and §2.7. Block 2 of the lab is the percentile analysis and Block 3
is the review itself, and neither re-explains the other.

---

## 7. Going deeper

<!--reading:12-->

### If you read one thing this week

**[Building A Generative AI Platform](https://huyenchip.com/2024/07/25/genai-platform.html)** — Chip Huyen · essay · ~45 min

The closest thing in print to the architecture review you're being asked to produce — context enhancement, guardrails, router/gateway, three cache layers, observability and orchestration, built up one layer at a time with the failure each layer answers.

### Then, in the order I'd take them

- **[The Tail at Scale](https://www.barroso.org/publications/TheTailAtScale.pdf)** — Jeffrey Dean & Luiz André Barroso · paper · ~30 min  
  You almost certainly know this one, and today is when to re-read it with agents in mind: an LLM pipeline is a fan-out of slow, variable-latency components, so the tail-amplification argument applies directly to §2.3's p50-vs-p95 split.
- **[How NOT to Measure Latency](https://www.infoq.com/presentations/latency-response-time/)** — Gil Tene (QCon San Francisco) · video · ~55 min  
  The definitive demolition of averaging percentiles and of measuring only what your load generator managed to send — watch it before you put a single latency number in front of a client, because the coordinated-omission trap is easy to fall into with agent traces.
- **[Token & Cost Tracking](https://langfuse.com/docs/observability/features/token-and-cost-tracking)** — Langfuse · docs · ~15 min  
  Shows what per-node cost attribution actually requires — usage captured per generation, prices resolved per model version, costs rolled up the trace — which is the plumbing behind §2.4's per-node cost table.

<!--/reading-->

### Also mentioned in this module

- The **Google SRE book**, the chapters on SLOs and on monitoring distributed systems. You have the
  instincts already; this gives you the vocabulary a client's platform team will use back at you.
- OpenTelemetry's **GenAI semantic conventions** (still evolving) — worth skimming for the field
  names, so your trace schema matches what a client's observability stack expects rather than
  needing a translation layer later.
- Any hosted LLM-tracing product's trace view — Langfuse, LangSmith, Phoenix. Not to adopt one, but
  to steal the interaction design for your own viewer. Look specifically at how they show a prompt
  diff between two runs.
- *Building Effective Agents* — Schluntz & Zhang, Anthropic engineering blog, 2024. Re-read it now
  that you've built the thing. It reads completely differently after Week 2, and its argument for
  the simplest architecture that works is the one you'll be defending in the review.

---

**Now go to `labs/DAY_12.md`.** The lab builds on §2.1 and §2.2 (the integration, and the regression
you're required to find), §2.3 and §2.4 (Block 2's p50/p95 and per-node attribution), §2.5 (the
trace viewer's field list), and §2.6–§2.7 (Block 3's 25-minute review and the rubric it's graded
against).
