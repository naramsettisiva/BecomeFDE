# Day 19 · Learn — The FDE role, discovery, and eval-first scoping

**Read before `labs/DAY_19.md`. Budget 1:15.** Pen and paper for §3 — the volume-and-value arithmetic is the part clients actually change their mind about.

---

## 1. Where this sits

Eighteen days of mechanism. You can build retrieval that works, measure it honestly, harden it,
cost it, and put it in someone else's network. What you cannot yet do reliably is decide **what to
build**, in a room, with a busy executive who has already been pitched twice and has brought you
their own solution instead of their problem.

This is the day where your twenty-three years are worth more than anyone else's in the cohort, and
also the day where they mislead you in three specific places. So let's be precise about both.

You already know how to run discovery. You've done requirements elicitation on distributed systems
programmes, you know that the stated ask is never the real ask, you know how to find the dependency
that eats the schedule, and you know that "who signs off" is a harder question than any technical
one. None of that changes. What changes is:

| Instinct that transfers | What AI changes about it |
|---|---|
| Requirements are elicited, not received | Same — but the deliverable is a **distribution of behaviour**, not a feature list, so "the system shall" cannot be written |
| Integration is the schedule risk | No. **The data is the schedule risk.** Integration is a week; discovering the appointment field has no timezone is a month |
| Done = acceptance criteria signed off | Done = **a number on a named set of cases**, plus a stated policy for what the workflow does with the failures |
| Scope is defended by a change-control process | Scope is defended by having written down, in advance, what would make you *stop* |

That table is the whole day. Everything below is the mechanics of operating it.

The specific problem today solves: **converting a vague business complaint into a scoped,
evaluable, shippable engagement — fast, in the room, without designing the solution before you
understand the problem.** Nobody teaches this. Most people learn it by failing on two engagements.

---

## 2. The mechanism

### 2.1 What a Forward Deployed Engineer actually is

The title is doing real work, and the fastest way to see it is by contrast with the three adjacent
roles a client has already bought.

| Role | Optimises for | Leaves behind | Characteristic failure |
|---|---|---|---|
| **Consultant** | A recommendation the sponsor can act on | A deck, a roadmap, an assessment | The recommendation is unimplementable in that environment and nobody finds out for a quarter |
| **Solutions engineer** | Winning the technical evaluation | A demo, a POC, a reference architecture | Demo ran on clean sample data; the handoff to delivery loses everything that was learned |
| **Staff engineer (theirs)** | The long-term health of a system | The system, and the team that runs it | Correctly refuses to move at engagement speed, because they'll own the consequences for five years |
| **FDE** | A working thing in *their* environment that *their* team can run | Code, evals, runbook, a trained engineer | Becomes indispensable — which is the same as failing at enablement |

The one-sentence definition worth memorising, because you will say it in interviews and to clients:

> An FDE **builds in the client's environment, with their data, against their constraints, and
> leaves something their team can run.**

Every clause is load-bearing. *Their environment* rules out the demo that only runs on your laptop.
*Their data* rules out the sanitised extract. *Their constraints* rules out the architecture that
requires egress they'll never approve. *Their team can run it* rules out you.

**The TPM mapping.** The closest thing you have already done is owning an outcome without owning the
org — driving a launch across teams that don't report to you, where your only real instruments are
clarity, sequencing, and credibility. That is 70% of this job. The 30% that's new is that you now
also have hands on the keyboard, which changes the politics more than you'd expect: you can settle
an argument by building the thing in an afternoon instead of scheduling a design review about it.
That speed is the FDE's actual weapon, and §2.2 is about not letting it become the failure mode.

### 2.2 The four modes, and the failure of overdoing each

You switch between these within a single day, sometimes within a single meeting. The discipline is
knowing which one you're in and saying so out loud.

| Mode | What you're doing | Exit criterion | Failure if you overdo it |
|---|---|---|---|
| **Discovery** | Understanding the real problem behind the stated one | You can state the problem, the volume, the data, and the metric in four sentences | Analysis paralysis. They wanted something to look at in week one and you brought a questionnaire |
| **Prototyping** | Building the smallest thing that proves or kills the idea | The riskiest assumption is now measured, not argued about | Demo-ware that can't be productionised — and, worse, a sponsor whose expectations were set by it |
| **Hardening** | Evals, guardrails, tracing, deployment, cost caps | The scorecard is a number you'd sign, and the failure modes are documented | Gold-plating something nobody validated. Beautiful observability on a workflow no one uses |
| **Enablement** | Teaching their team to own it | Their engineer has deployed it, added an eval case, and resolved an alert — without you | You become the bottleneck you were hired to remove |

**The most common FDE failure is staying in prototyping**, because it is by a wide margin the most
fun mode and because the client keeps clapping. Take the applause seriously as a signal and it will
destroy your engagement, so understand mechanically why it's worthless:

A prototype demo is a **path you chose, on inputs you chose, with a narrative you wrote**. The
applause measures the demo. It measures nothing about the system, because the audience has no way
to sample the input distribution — they've seen one draw from it, selected by you, and humans do
not intuit a distribution from a favourable sample. This is the same reason a green build on the
tests you wrote yourself tells you very little; you've met that one before.

The second most common failure is **skipping discovery because the client already knows what they
want.** They know what they want the way a user knows they want a faster horse — the ask is a
solution, already committed to, usually because it's the thing they can picture. §2.3 is how you
get underneath it without telling anyone they're wrong.

There's a third failure that has no mode of its own: **oscillating.** Two days of hardening, then a
new capability because someone in the steering meeting mentioned it, then back. Name the mode in
your weekly note — *"we are in hardening this week; no new capability lands until Friday"* — and
you've converted a vague scope pressure into a visible, arguable decision. That move is pure TPM
and it works exactly as well here as it did at Amazon.

### 2.3 The six-area discovery framework

Run every discovery conversation through these six, **in this order**. The order is not
decorative — each area constrains the next, and doing them out of sequence is how you end up
designing a solution to a problem whose value you haven't measured.

---

**1 · The complaint, in their words.**

> *"Tell me about the last time this went wrong. Walk me through that specific day."*

Never accept the abstract version. This is the single highest-leverage rule in the framework, and
here's the reason, stated precisely:

> **Abstractions contain someone's guess at a solution. Incidents contain requirements.**

"We need better visibility into carrier performance" is not a problem statement. It is a solution
("a dashboard") with the solution word removed, and if you build against it you will build a
dashboard nobody opens. Compare what one dated incident gives you:

> *"Two weeks ago we had the quarterly review with Ridgeline. We told them their first-tender
> acceptance was 83%. They came back with 89% off their own system. We spent forty minutes arguing
> about which loads counted — they'd filed force-majeure on a weather event and we hadn't applied
> it. The meeting was supposed to be about moving volume off the Dallas–Chicago lane. We never got
> to it."*

Count what fell out of that in nine seconds of speech:

1. There must be a **shared, reproducible definition** of FTA, computed the same way on both sides.
2. Every number must decompose to **load-level evidence** — the argument is never about the
   aggregate, it's about which loads are in the denominator.
3. **Force-majeure exclusions** must be applied (filed within 5 business days, suspends measurement
   for the affected lanes plus 48 hours) and *visible* as an adjustment, not silently baked in.
4. The real business outcome is a **volume reallocation decision**, and it is being crowded out by
   reconciliation. That's the thing that's actually broken.
5. There is a **counterparty** who reads the output and is motivated to attack it — which sets the
   bar for citation and provenance far above "the model said so."
6. The meeting has a **date**, so there is a deadline shape to the workflow.

Six requirements, none of which were in "better visibility," and one of which (#4) reframes the
project entirely. That is why you demand the incident.

*Follow-ups that work:* "Who was in the room?" · "What did you do next?" · "What would have had to
be true for that meeting to go well?" · "Has that happened again since?" · "Show me the email."

*The failure of skipping:* you build against the abstraction, it demos fine, and nobody's Tuesday
gets shorter.

---

**2 · The current manual path.**

> *"Today, when that happens, who does what? How long does it take? What do they open?"*

You are looking for the process you're automating, in enough detail to know what the output has to
be. "What do they open" is the underrated part of that question — the answer is a list of your
data sources, given voluntarily, in priority order.

Then the test almost nobody applies: **if nobody does it manually today, ask why not.**

Often the answer is that it isn't actually valuable — someone would have found a way if it were —
and you have just saved everyone six weeks. Sometimes the answer is "because it's impossible at
this volume," which is the best answer you can get: a genuine capability gap with a demonstrated
appetite. Either way you learn something decisive in one question.

*The failure of skipping:* you automate a process that has an owner who wasn't consulted, and you
find out at UAT.

---

**3 · The volume and the value.**

> *"How many times a week? What does each one cost you in time or money when it goes wrong?"*

This is your **ROI numerator** and simultaneously your **cost budget**, and the second use is the
one people miss. Twenty events a week at thirty minutes each is not a $200,000 project. Knowing
that in meeting one is a gift to both sides — it stops you proposing something that can't pay back
and stops them expecting something they can't fund.

Two things to press on. First, **value concentrates**: the mandatory subset is usually much smaller
than the stated population, and the mandatory subset is where the money is. Second, ask for the
**cost of the failure**, not just the time — the forty minutes of a VP's meeting spent arguing
about a denominator is not on any timesheet and is worth more than the analyst hours.

*The failure of skipping:* you scope by ambition, and the project dies at the budget review with a
working system.

---

**4 · The data.**

> *"Where does that information live? Can I see a real example — not a sanitised one?"*

**Ask for real data in meeting one. Always.** Say it out loud in the meeting, and if the answer is
"we'll get you an extract next week," treat that as a finding rather than an answer.

> **The gap between the described data and the actual data is the single largest source of schedule
> overrun in this work.**

This is the place your TPM instincts *underestimate* the risk, because in a distributed-systems
programme the schema is usually knowable from a document and the risk lives in integration. Here it
doesn't. The system will produce fluent, confident, well-formatted output from bad data — there is
no type error, no failed join, no red build. A wrong number arrives looking exactly like a right
one.

From your own corpus, the traps you already know exist and a client will not mention:

- Appointment times stored in **facility local time**, delivery scans in **UTC**. Every OTIF claim
  is wrong at some facilities until that's resolved — and the grocery-DC window is `−30/+0 minutes`,
  so a one-hour offset doesn't degrade the metric, it *inverts* it.
- **Rescheduled appointments overwrite the original** in the TMS, which hides shipper-caused delay
  unless someone reads the appointment audit log.
- Detention evidence requires **ELD-derived timestamps**, which may live with the carrier, not you.

*Three questions that surface this fast:* "Can I see twenty real rows today?" · "Who owns this
field — who do I call when it's wrong?" · "What percentage of it is null?"

*The failure of skipping:* week five, and the reason it's fatal is that it lands after the sponsor
has told their boss the project is going well.

---

**5 · The constraints.**

> *"Can data leave your network? Who has to approve this? What's the security review process? Is
> there a system of record this has to write back to?"*

Ask about **egress in the first meeting** (Day 17). These are dependencies with lead times, most of
them non-technical, and you have spent two decades managing exactly this class of risk. The only
adjustment is knowing which four to ask about, because they're the ones that invalidate
architectures rather than delay them:

| Constraint | What it invalidates if discovered late |
|---|---|
| **Egress** | Your entire model choice and topology |
| **Approvals** | Your start date — and it's often 6–8 weeks of calendar you can run in parallel if you know on day one |
| **Security review** | Your deployment target, and sometimes your dependency list |
| **System of record** | Your output format — if it has to write back to a vendor portal, "generate a document" was the wrong shape |

*The failure of skipping:* you build the right thing and cannot deploy it.

---

**6 · The definition of done.**

> *"Six months from now, this worked. What's different? Who noticed? What number moved?"*

Push until there is a number attached to a named person's behaviour. "The team is less frustrated"
is not done. "In Q1, the eighteen mandatory carrier reviews go out on schedule with a number the
carrier doesn't dispute, and prep takes 45 minutes instead of four hours" is done.

And the rule that buys you the most trust in the whole framework:

> **If nobody can answer this, you don't have a project. You have an experiment — and it should be
> scoped and funded as one.**

Saying that in the room makes you *more* trusted, not less, because the alternative — accepting an
unmeasurable goal and discovering it in month four — is a failure both of you will own. An
experiment with a small fixed budget and a decision at the end is a perfectly respectable thing to
sell. A project with no definition of done is not.

---

**Three questions that surface a doomed engagement early**, worth asking somewhere in the middle:

- *"Who asked for this?"* — if the answer is a consultant's report or a board slide, the sponsor
  may not want it.
- *"What happens if we don't do it?"* — if the answer is "nothing much," believe them.
- *"Has this been tried here before?"* — the previous attempt's failure mode is your best available
  prior, and someone in that building is quietly waiting to watch it happen again.

### 2.4 Eval-first scoping — the move that distinguishes you

Here is the differentiator, and it's grounded in everything you've built since Day 5.

| | The proposal they've already seen twice | Yours |
|---|---|---|
| **Week 1** | Kickoff, architecture, environment setup | 50 real questions from your ops team; a scoring harness; a measured baseline |
| **Definition of done** | "An AI assistant for carrier performance" | "≥90% on the 50-case set at the stated rubric, 100% citation verification, refusal rate ≥95% on out-of-corpus questions" |
| **Progress visible as** | Demos, when there's something to demo | A number, weekly, that a sponsor who can't read code can read |
| **When the client says "it doesn't feel right"** | A debate | A list of failing cases |
| **When it isn't working** | Month three | Week one, cheaply |

Most proposals say *we'll build X and it'll take eight weeks.* Yours says: *before we build
anything, here are fifty real questions from your ops team. Here is how a system would be scored on
them. Week one we build the harness and measure a baseline. Then every week you watch the number
move.*

It does four things at once:

1. **Turns a vague ask into a measurable one** — and sometimes reveals the ask is *unmeasurable*,
   which is a finding worth more than the project would have been.
2. **Forces the client to produce real examples**, which surfaces the data problems in week one
   instead of week five. Collecting fifty real questions is a data-access request wearing a
   friendlier hat.
3. **Gives you a defensible definition of done**, so the last two weeks are not a negotiation.
4. **Makes progress legible to a non-technical sponsor**, which is the thing that actually keeps a
   project funded.

And it **de-risks you specifically.** When the sponsor's SME says "it doesn't feel right," you have
a number and a set of failing cases instead of a vibe you cannot argue with. You will use this at
least once per engagement and it is worth the entire week-one investment on its own.

**Where your TPM instinct needs adjusting.** You already write acceptance criteria. The adjustment
is that the criteria here are *statistical* and must be stated as such: a threshold, on a named
case set, at a stated rubric version, measured with a known noise floor (Day 13). "The system shall
correctly answer detention questions" is unfalsifiable and will be argued about forever. "≥90% on
`evals/detention_v2.jsonl`, judged by rubric v3, where five identical runs vary by ±2 points" is a
contract. Write the noise floor into the criterion — otherwise the first green-to-amber flicker
becomes a status meeting.

**The phase structure that makes it sellable:**

| Phase | Duration | Content | Commercial shape |
|---|---|---|---|
| **Phase 0** | 1 week | Eval harness, baseline, data assessment, findings memo | **Small, fixed fee, ends in a go/no-go** |
| **Phase 1** | 3–4 weeks | Build to the target metric | Priced against the metric, not a feature list |
| **Phase 2** | 2–3 weeks | Harden, deploy, hand over, enable | Includes the handover checklist as a deliverable |

Phase 0 is the whole trick. It is small enough to approve without a procurement cycle, produces a
decision rather than a deliverable, and gives *both* sides an honourable exit. A client who has
been burned by AI vendors will buy a decision far more readily than they'll buy a system.

Two fields on the scoping canvas that nobody else's has, and they belong to you:

- **Out of scope, explicit.** Written during the meeting, on screen, agreed out loud.
- **Kill criteria.** What would make you stop. *"If baseline retrieval on the fifty questions is
  below 40% and the failures are dominated by missing data rather than ranking, we stop and this
  becomes a data project."*

Writing down what would make you stop is the most senior thing on the page, and it is the sentence
that makes an experienced buyer decide you're different.

### 2.5 The week-one plan, and why you demo the failures

The plan itself is in the lab. One element deserves explaining here because it is
counter-intuitive and it works:

> **On day four of week one, you demo the baseline *and its failures* to the sponsor.**

Everyone's instinct is to show the best case. Show the failures instead, for three reasons. It sets
expectations honestly at the only moment when doing so is cheap. It makes every subsequent
improvement feel *earned* rather than expected — the number you move is a number they watched be
bad. And it converts the client's SME from a critic into a collaborator, because the fastest way to
get a domain expert engaged is to show them something wrong in their domain.

The version of this that fails is demoing failures without a diagnosis. "Here's what it gets wrong,
here's why, here's which of those are retrieval and which are data, and here's what I'd do about
each" is a status report. "Here's what it gets wrong" is an apology.

### 2.6 The four hard conversations

These are muscle memory, not knowledge. Rehearse them out loud; you will not compose them under
pressure.

---

**1 · "No, that won't work."**

> *"I want to flag something now rather than in week six: the appointment data doesn't carry a
> timezone, so any answer about on-time performance will be wrong for about 40% of facilities. We
> can fix it, but it's a data project before it's an AI project. Want me to scope that separately,
> or should we start with the accessorial questions where the data is clean?"*

The structure — and it is always this structure:

> **Name the problem → quantify it → offer two paths → let them choose.**

**Never "no" alone.** A bare no makes you an obstacle and invites them to route around you; a no
with two costed paths makes you the person who found the problem while it was still cheap. Note
also that both paths are acceptable to you. Don't offer a path you'd refuse.

---

**2 · "Not yet."**

> *"We could add that, and it'd take about a week. But we haven't validated that anyone uses the
> first thing yet. Can we put it on the list and revisit after the pilot has two weeks of usage
> data?"*

Three moves: **agree it's possible** (so this isn't a capability argument), **name the missing
evidence** (so the deferral has a reason that isn't your preference), and **name the trigger for
revisiting** (so it isn't a euphemism for no). The list has to be real and you have to bring it to
the next meeting, or you get one use of this sentence per client.

---

**3 · "That'll cost more than you think."**

> *"The build is four weeks. The part that surprises people is the security review and the data
> access — at your company that's historically taken six to eight weeks. I'd rather start that in
> parallel on day one than discover it in week five."*

The move is separating **build time** from **elapsed time**, which is the single most common
estimation error made by technical people talking to executives, and the one you already know
cold from twenty-three years of critical-path arguments. What's different here is *which*
dependency dominates: it's rarely the integration, it's almost always security review, data access,
and a DPA amendment nobody has read since 2023.

---

**4 · "It can't do that reliably."** — the most valuable sentence in this course.

> *"It'll be right about 85% of the time on that class of question, and it will be confident when
> it's wrong. So the question is what the workflow does with the other 15%. If a human reviews
> before anything is sent, 85% is a big win. If it's fully automated, 85% is a liability. Which is
> it?"*

Dissect it, because every clause is doing work:

| Clause | What it does |
|---|---|
| *"about 85%… on that class of question"* | Quantifies, and scopes the claim to a class — reliability is not a property of the system, it's a property of the system *on a distribution* |
| *"confident when it's wrong"* | Names the failure **mode**, which is the part they've never been told and the part that makes the risk real. Silent, fluent, well-formatted wrongness |
| *"what the workflow does with the other 15%"* | Moves the problem from model capability (where you'd be defending) to workflow design (where they have the authority and the domain knowledge) |
| *"Which is it?"* | Hands them a decision they are qualified to make, so the conversation ends in a design choice rather than a disappointment |

Almost nobody says this, and almost every failed AI project needed someone to. The reason people
avoid it is that it feels like admitting the technology is weak. It's the opposite: it's the
sentence that demonstrates you've deployed one of these before.

**The instinct it connects to.** You have run services with error budgets. Nobody promised 100%;
you promised a number, published it, and designed the operational response to the remainder. This
is that, moved from availability to correctness. The difference worth stating out loud is that an
availability failure is *loud* — a 503 is unmistakable — whereas this failure class is silent and
plausible, so the "operational response to the remainder" has to be a **human in a workflow**, not
an alert.

### 2.7 Two behaviours that predict a good discovery call

Both are measurable, which is why they're worth naming rather than gesturing at.

**Talk-time under 40%.** Time it. This is the most reliable single predictor of a discovery call
that produced anything, and it's a proxy for something real: every minute you talk is a minute you
are not learning, and most over-talking is the urge to demonstrate competence. You don't need to.
You're already in the room.

**Count the minutes until you first propose a solution.** You will feel the urge at about minute
six, when the first recognisable pattern appears. Write the idea down — physically, in the
notebook — and keep asking. The note costs you nothing and the discipline preserves the remaining
questions. Designing during discovery doesn't just risk the wrong design; it *changes the client's
answers*, because from the moment you propose, they start responding to your proposal instead of
describing their problem.

---

## 3. Worked example — on paper

> **Setup.** You have 30 minutes with **Dana Okonjo, VP of Transportation** at a $2B food
> distributor. 60 contracted carriers, 14 primary lanes. She has been pitched by two AI vendors
> already. Transcript excerpts, in the order they occurred:

> **Dana:** "Look, the honest version is my team spends too much time chasing carrier issues. What
> we want is a dashboard with AI in it — something where I can see who's underperforming without
> three people building slides."
>
> **Dana** *(after being asked for a specific day)*: "Two weeks ago, the Ridgeline review. We told
> them their FTA on Dallas–Chicago was 83%, they came back with 89% off their own system, and we
> spent forty minutes arguing about which loads counted. They'd filed force majeure on the
> February weather event; we hadn't applied it. The meeting was meant to be about moving volume off
> that lane and we never got there. Composite came out 78.5, which is Silver, which means the
> review is mandatory, which means we have to do it again next quarter."
>
> **Dana** *(on the current path)*: "An analyst pulls the scorecard out of the BI tool, pulls
> shipments and accessorials out of the TMS, opens the carrier's detention invoices — those are
> PDFs — reconciles it, writes the deck. Call it half a day each. We're supposed to do all sixty a
> quarter. Realistically we do the ones we're forced to."
>
> **Dana** *(on money)*: "Detention we were billed last year was about $412,000. Finance disputes
> maybe 20% of it and wins about 60% of what they dispute. There's probably another $60,000 a year
> we'd win if anyone looked in time, but the window closes."
>
> **Dana** *(on data)*: "It's all in the TMS."
>
> **Dana** *(on done)*: "The team would be less frustrated. And I'd stop losing forty minutes of
> every carrier meeting to arithmetic."

Assume a fully-loaded analyst cost of **$55/hour** and that **18** carriers currently sit below the
Gold band (composite < 80), so their quarterly business review is mandatory under the scorecard
spec.

**Q1.** Dana's opening sentence contains an abstraction *and* a proposed solution. Name both, and
say what each is hiding.

**Q2.** From the Ridgeline incident alone, list four requirements. Then name the one clause in the
incident that changes what you'd build, versus what she asked for.

**Q3.** Do the volume-and-value arithmetic. Labour value for all 60 versus the mandatory 18;
recoverable accessorial value; total annual value. What engagement size does that support, and what
does it imply about the *shape* of the proposal?

**Q4.** "It's all in the TMS." Write the three questions you ask next, and name the specific data
trap you expect to find given what this workflow measures.

**Q5.** Which of the six discovery areas has not been touched at all in the transcript? Give the
concrete cost of discovering it in week five rather than meeting one.

**Q6.** Rewrite Dana's definition of done as something you could put in a contract.

**Q7.** Write the Phase 0 proposal in six lines, including kill criteria. Then script the hard
conversation for the moment — and it will come — when Dana asks whether the system can just send
the review to the carrier automatically.

<details>
<summary><b>Answers — attempt Q3 with a pen before reading; the arithmetic is the part that changes the conversation</b></summary>

**Q1.** The abstraction is **"too much time chasing carrier issues"** — it hides *which* issues,
*who* chases them, and *what happens when they lose*. The proposed solution is **"a dashboard with
AI in it"**, which hides the actual job: nobody wants to look at a dashboard, they want the
argument in the carrier meeting to be shorter. Note that the solution has smuggled in an
architecture (a UI, always-on, browsable) that the real workflow (a quarterly document, produced on
a deadline, that a hostile counterparty will read) does not want. Build the dashboard and you'll
have built something correct and useless.

**Q2.** Any four of:

1. FTA must be **computed reproducibly** and be defensible line by line — accepted tenders over
   total offered, rolling 30-day window, per carrier per lane, with the definition stated.
2. Every aggregate must **decompose to load-level evidence**, because the dispute is never about
   the aggregate.
3. **Force-majeure exclusions must be applied and shown as an adjustment** — filed within 5
   business days, suspends measurement for affected lanes plus 48 hours. Silently applying it is
   nearly as bad as not applying it, because the carrier can't reconcile to it.
4. Output must **survive an adversarial read** by a counterparty with their own system — so
   citation and provenance, not fluency, is the bar.
5. The workflow is **deadline-shaped** (a scheduled meeting), not query-shaped.
6. Composite 78.5 → **Silver → the review is mandatory**, so there is a compliance driver, not just
   a convenience one.

The clause that changes what you build: *"the meeting was meant to be about moving volume off that
lane and we never got there."* The value isn't the time saved preparing. It's **the decision that
didn't get made.** That reframes the deliverable from a report to a document that ends in a
defensible recommendation — and it's the sentence you quote back to her when scoping.

**Q3.**

Labour, all 60: 60 × 4 hours = 240 hours/quarter → 960 hours/year × $55 = **$52,800/year**.
Labour, mandatory 18: 18 × 4 = 72 hours/quarter → 288 hours/year × $55 = **$15,840/year**.

Accessorials: currently disputed 20% of $412,000 = $82,400, winning 60% = $49,440 recovered today.
The stated missed opportunity is **$60,000/year** of never-disputed spend; recovering half of it is
**~$30,000/year**, and that number is more defensible than assuming you win it all.

Total defensible annual value ≈ **$53k labour + $30k recovery ≈ $83k**, plus an unquantified but
real fifth item: the carrier-meeting decisions that currently don't happen.

**What it supports:** an engagement in the **$60–80k** range pays back inside 12 months. It is not
a $200k project and you should say so. The arithmetic also tells you the *shape*: the labour value
is thin and spread across 60 carriers, while the recovery value is concentrated in the accessorial
path with a hard **30-day dispute window**. So the highest-value first slice is the detention
exposure section with dated events — not the general "carrier performance" surface she asked for.

Notice what just happened: **the volume-and-value question re-scoped the project**, and it took
four numbers and no technology.

**Q4.** The three questions: *"Can I see twenty real rows today — the actual export, not a
sample?"* · *"Who owns the appointment field; who do I call when it's wrong?"* · *"What percentage
of loads have no telematics feed?"*

The trap you expect: **appointment times are stored in facility local time and delivery scans in
UTC.** For a grocery DC the on-time window is `−30/+0 minutes`, so a one-hour timezone error doesn't
soften the metric, it inverts the verdict on a large share of loads. Two more you should expect from
the same corpus: **rescheduled appointments overwrite the original**, hiding shipper-caused delay
unless you read the audit log; and detention evidence requires **ELD-derived timestamps** that may
sit with the carrier rather than in the TMS at all. "It's all in the TMS" is never true, and it is
never a lie either — it is what the field looks like from a VP's chair.

**Q5.** **Constraints.** Nothing has been said about egress, approvals, security review, or the
system of record.

Concrete cost of finding out in week five: the TMS is vendor-hosted, so pulling shipment data to a
cloud model may need a **DPA amendment** (legal, weeks); enterprise security review at a company
this size historically runs **6–8 weeks**; and if carrier communications have to be written back to
a vendor portal, "produce a markdown document" was the wrong output shape entirely. Any one of
those in week five costs more than the whole of Phase 0. All three are free to ask about in
meeting one, and asking makes you look like you've done this before — which you now have.

**Q6.** *"By the end of Q1, all 18 mandatory quarterly business reviews are issued within 5
business days of scorecard publication. Each contains an FTA figure that reconciles to the
carrier's own number or shows the specific loads where it doesn't. Analyst preparation time drops
from ~4 hours to under 1 hour per review. Detention disputes are raised within the 30-day window on
at least 90% of disputable events."*

Four numbers, three of them already instrumented, all attached to someone's behaviour. Compare
"the team would be less frustrated."

**Q7.** Phase 0, one week, fixed fee:

```
1. Collect 50 real questions and 3 real past reviews from the analyst team (day 1–2).
2. Build the scoring harness: structural, factual-against-source, and a calibrated
   quality rubric. Baseline measured on all 50 (day 2–3).
3. Data assessment: 20 real rows per source, timezone/null/ownership audit, written up
   as a findings memo (day 3).
4. Demo the baseline AND its failures to Dana on day 4, with each failure classified
   as retrieval, data, or reasoning.
5. Deliverables: harness, baseline number, findings memo, Phase 1 plan with a metric
   target and a cost model.
6. KILL CRITERIA: if >40% of baseline failures are attributable to missing or
   unreconcilable source data (timezone, overwritten appointments, ELD not available
   to us), we stop. This is a data project before it is an AI project, and I will
   scope that instead.
```

The hard conversation, when she asks about sending it automatically:

> *"It'll be right about 85% of the time on this class of document, and it will be confident when
> it's wrong — it won't look uncertain, it'll look like the other 85%. So the question is what
> happens with the other 15%. This document goes to a counterparty who has their own numbers and a
> financial reason to attack it; one wrong detention figure and you're relitigating the whole
> review. If an analyst reviews it for fifteen minutes before it's sent, you've gone from four
> hours to fifteen minutes and the risk profile hasn't changed. If it sends itself, you've saved
> fifteen minutes and taken on a new category of dispute. Which do you want?"*

She will choose the review step. She would probably have chosen it anyway — but now she chose it,
knowingly, in a meeting, which means it is her design decision rather than your limitation. That
transfer is the entire technique.

</details>

---

## 4. What people get wrong

**"Discovery is asking what they want."**
Discovery is asking what happened. Wants are theories; incidents are evidence. Every question in
§2.3 is about the past for exactly this reason.

**"The client knows their own process."**
They know their description of it. The person who knows the process opens six tabs and has a
personal spreadsheet nobody has ever seen. Ask to sit with them for twenty minutes.

**"I'll get the real data once the contract's signed."**
Then you have signed a contract against a description. Ask in meeting one, and treat reluctance as
a measurement of the approval timeline rather than as a refusal.

**"Saying 'this might be an experiment, not a project' loses the deal."**
It loses the deals you'd have failed. It wins the buyers who have been burned, and that's most of
them by now.

**"Eval-first is slower — the client wants to see something in week one."**
Phase 0 *is* something in week one: a baseline, a failing-case list, and a data findings memo. It's
more than a demo, it's just less flattering. And the honest version is that a week-one demo built
without a harness is a week-one demo you cannot improve on purpose.

**"85% accuracy is a good result."**
It's not a result at all until you say *on what distribution* and *what the workflow does with the
remainder*. Reliability is a property of a system-on-a-distribution-in-a-workflow, never a property
of a model.

**"Scope is defended by change control."**
Change control defends scope in a programme with a signed spec. Here scope is defended by two
things written down while you were calm: the explicit out-of-scope list and the kill criteria.

**"Kill criteria make me look uncommitted."**
They make you look like someone who has been on a project that should have been stopped. Every
senior buyer has been on one.

**"If they clap at the demo, it's working."**
They're applauding a path you chose on inputs you chose. One favourable draw tells you nothing
about the distribution.

**"Enablement is the last week."**
Enablement is a mode you enter on day one by working *with* their engineer rather than in front of
them. A handover scheduled for the last week is a document, not a transfer.

---

## 5. The trainer's angle

**The analogy that lands, and it's yours already:** discovery is an **incident postmortem run
forwards**. In a postmortem you refuse the theory and demand the timeline — what happened, at what
time, who did what, what did they see. Discovery is identical, except the incident is ongoing and
the output is a scope rather than an action item. Rooms full of operations people get this
instantly, and it reframes "asking a lot of questions" from interrogation to a genre they already
respect.

**The demo that makes it click:** run a two-minute live discovery on a volunteer's own problem, on
stage, and get from their abstraction to a dated incident in four questions. Then read back the
requirements the incident contained and count them out loud. The room sees six requirements appear
from a story that was told in fifteen seconds, and nobody argues with the "demand an incident" rule
again.

**The second demo, and the one people quote afterwards:** put a stopwatch on screen during a
role-played discovery call and show the talk-time percentage climbing. Watching a competent
engineer discover they spoke for 60% of a discovery call is more persuasive than any amount of
telling them not to.

**The predictive question before the role-play:** *"You have thirty minutes with a VP. How many
minutes in do you think you'll first propose a solution?"* Everyone says fifteen or twenty. The
recording usually says six.

**The question a sharp student will ask:** *"What if the client just won't give me real data?"*
Have this ready:

> Then you've learned the most important thing available in that meeting, and it isn't about data.
> A refusal is one of three things: a policy you now know about eight weeks early, a person whose
> approval you didn't know you needed, or a quality problem someone is embarrassed about. All three
> are scope. So don't push on the refusal — ask what it would take. "What would have to be true for
> me to see twenty real rows?" gets you the approval chain, and the approval chain is the schedule.
> And if the answer is genuinely never, that's not a blocker, it's an architecture: you're building
> on-prem, and you've just saved yourself from proposing something you couldn't have delivered.

**The second sharp question:** *"Isn't 'kill criteria' just giving the client permission to cancel
me?"* — Yes, and that is the point. You are trading a small probability of an early, clean, paid
stop against a large probability of a slow failure that costs you the reference. Reference-ability
is the only currency in this work.

---

## 6. Self-check

Cover the answers.

1. Give the one-sentence definition of an FDE, and say what each clause rules out.
2. How does an FDE differ from a solutions engineer in what they leave behind?
3. Name the four modes, and the failure of overdoing each.
4. Why is applause at a prototype demo a worthless signal? Give the mechanical reason.
5. State the incident-versus-abstraction rule, and why it's true.
6. In area 2, what do you do if nobody performs the process manually today?
7. Volume and value gives you two things. Name both.
8. Why must you ask for real data in meeting one, and what's the *specific* reason bad data is more
   dangerous here than in a conventional integration project?
9. Name the four constraints to ask about, and what each one invalidates if found late.
10. What do you say when nobody can answer the definition-of-done question?
11. Describe eval-first scoping in two sentences, and name two of the four things it does at once.
12. What are the two fields on the scoping canvas that nobody else's has, and why do they matter?
13. Give the four-part structure of the "no, that won't work" conversation.
14. Recite the 85% sentence and explain what each of its three moves accomplishes.

<details>
<summary><b>Answers</b></summary>

1. *Builds in the client's environment, with their data, against their constraints, and leaves
   something their team can run.* Their environment rules out the laptop demo; their data rules out
   the sanitised extract; their constraints rules out the architecture that needs egress they won't
   approve; their team can run it rules out you.
2. An SE leaves a demo and a reference architecture, optimised for winning the evaluation. An FDE
   leaves working code in production plus evals, a runbook, and a trained engineer.
3. Discovery → analysis paralysis. Prototyping → unproductionisable demo-ware and mis-set
   expectations. Hardening → gold-plating something unvalidated. Enablement → becoming the
   bottleneck you were hired to remove.
4. The demo is one path, on inputs you chose, with a narrative you wrote. The audience cannot
   sample the input distribution from a single favourable draw, so the applause measures the demo,
   not the system.
5. Abstractions contain someone's guess at a solution; incidents contain requirements. An
   abstraction has already had the specifics — and therefore the constraints — compressed out of it.
6. Ask why not. Usually it isn't valuable enough for anyone to have bothered, and you've saved six
   weeks. Occasionally it's genuinely impossible at volume, which is the best answer available.
7. The ROI numerator, and your cost budget.
8. Because the gap between described and actual data is the largest source of schedule overrun. It's
   more dangerous than in a conventional integration because there's no type error and no failed
   join — the system emits fluent, confident, correctly-formatted output from wrong data, so the
   failure is silent.
9. Egress (invalidates model choice and topology); approvals (your start date, 6–8 weeks of
   parallelisable calendar); security review (deployment target and dependencies); system of record
   (your output shape).
10. That it's an experiment rather than a project, and it should be scoped and funded as one. Said
    plainly, this increases trust.
11. Instead of proposing to build X in N weeks, you propose to define — with real questions from
    their team — how a system would be scored, build the harness in week one, measure a baseline,
    and move the number weekly. Any two of: makes a vague ask measurable; forces real examples out
    early; produces a defensible done; makes progress legible to a non-technical sponsor.
12. Explicit out-of-scope, and kill criteria. The first prevents the silent expansion that eats
    fixed-fee work; the second converts a slow failure into an early, clean, paid stop.
13. Name the problem → quantify it → offer two paths → let them choose. Never "no" alone, and never
    offer a path you'd refuse.
14. *"It'll be right about 85% of the time on that class of question, and it will be confident when
    it's wrong — so the question is what the workflow does with the other 15%."* It quantifies and
    scopes the claim to a distribution; it names the failure mode as silent and plausible rather
    than loud; and it moves the decision to workflow design, where the client has both the
    authority and the domain knowledge to choose.

</details>

**Scored below 10?** Re-read §2.3 and §2.4. The lab's two hardest deliverables — a recorded
discovery that reaches a dated incident, and a phase-0 proposal with kill criteria — are exactly
those sections, and the lab will not re-explain either.

---

## 7. Going deeper

<!--reading:19-->

### If you read one thing this week

**[Shape Up — Part 1, Shaping](https://basecamp.com/shapeup)** — Ryan Singer (Basecamp) · docs · ~1h30

Read "Principles of Shaping" and "Set Boundaries" — appetite-before-estimate is precisely the move behind eval-first scoping, argued better than I argue it.

### Then, in the order I'd take them

- **[Product management at AWS: working backwards and the PR-FAQ](https://aws.amazon.com/executive-insights/content/product-management-at-amazon/)** — AWS Executive Insights · essay · ~20 min  
  Re-read the press-release-first mechanism as a DISCOVERY tool — the PR is a forcing function for "what changes, for whom", which is discovery area six.
- **[How to ask good questions](https://jvns.ca/blog/good-questions/)** — Julia Evans (Dec 2016) · essay · ~15 min  
  Short and unusually concrete on the mechanics of getting a real answer rather than a polite one — which is the whole skill in a first discovery call.

<!--/reading-->

### Also mentioned in this module

- *The Mom Test* — Rob Fitzpatrick, 2013. Short, and the best thing written on why you ask about
  the past rather than the future. His rule ("talk about their life, not your idea") is §2.3 area 1
  from a different direction.
- *Never Split the Difference* — Chris Voss, 2016. Read only the chapters on calibrated questions
  and on labelling. The "what would have to be true for…" move in §5 comes from that family.
- *Shape Up* — Ryan Singer, Basecamp, 2019. Free online. Fixed time, variable scope, and the idea
  of an "appetite" rather than an estimate — which is Phase 0's commercial logic stated in a
  product-development idiom.
- *Continuous Discovery Habits* — Teresa Torres, 2021. Opportunity-solution trees; useful mainly as
  a structured way to keep the problem space open while your hands itch to design.
- *Site Reliability Engineering* — Beyer et al., 2016. The error-budget chapters, re-read with §2.6
  conversation 4 in mind. The move — publish a number, design the operational response to the
  remainder — is identical; only the loudness of the failure differs.
- Palantir popularised the FDE title and writes publicly about the role; the material is
  recruiting-adjacent and worth reading with that in mind, but the operating description of
  building in the customer's environment is accurate to the job.

---

**Now go to `labs/DAY_19.md`.** The lab builds directly on §2.3 (the six areas become
`DISCOVERY_GUIDE.md`, and the role-play is graded on whether you reached a dated incident), §2.4
(the eval-first proposal template and the two canvas fields), §2.5 (the week-one plan, including
the day-four failure demo), and §2.6 (all four conversations, rehearsed out loud and recorded —
the fourth one twice).
