# Day 07 · Learn — Tool calling and the agent loop, from first principles

**Read before `labs/DAY_07.md`. Budget 1:15.**

---

## 1. Where this sits

Week 1 built a pipeline: retrieve, assemble, generate, measure. Its shape was fixed by you at
design time — five chunks in, one answer out, always in that order. That's a DAG, and you have
spent twenty-three years making DAGs reliable.

Today's problem is the class of question that has no fixed shape. *"How much detention do we owe
on SHP-202608-0041729?"* You can't write a static pipeline for that: you don't know the arrival
timestamp until you've looked the shipment up, don't know whether the $650 cap applies until
you've computed the hours, and don't know whether the geofence exception in document 02 matters
until you've read the arrival record. **The sequence depends on intermediate results.** That is
the only condition that justifies an agent, and by tonight you should be able to say it in one
sentence to a client.

The second reason today matters is defensive. "Agent" is the most abused word in this industry
and the thing clients ask for by name. The fastest way to lose a room is to be unable to say what
one *is*. It's a while-loop. You're going to write it.

---

## 2. The mechanism

### 2.1 A tool call is generated text. The model calls nothing.

Everything today rests on this, and most tutorials obscure it.

When you enable "function calling," here is what physically happens. You put a JSON Schema
description of each tool into the request. The model — doing exactly what it did on Day 1,
predicting one token at a time — emits a span of text that the provider parses into a structured
block containing a tool name, an arguments object, and an ID. Then the API returns that block and
**the request ends.**

Nothing has been executed. No network call was made on your behalf. The model has no file
descriptors, no sockets, no runtime. What it produced is a *request for work*, serialised.

The framing that will stick: the model is a scheduler that emits a work order onto a queue, and
**your process is the only worker on that queue.** If you never pick the message up, nothing
happens. If you execute it wrongly, the model has no way to know. If you decide the work order is
unsafe and drop it, that's your prerogative — there is no enforcement channel. Every security
property of an agent system lives in your executor, not in the model.

Which answers the two questions every client asks. *"Can it reach our database?"* Only through a
tool you wrote, with credentials you supplied, in a process you control. *"What stops it calling
`delete_shipment`?"* The fact that you didn't write one, or that your executor checks a permission
before dispatching. Not the prompt. Never the prompt.

### 2.2 The loop, in five steps

```
1. Send:    messages[] + tool schemas[]
2. Receive: final text (done), or one-or-more tool_call blocks {id, name, arguments}
3. Execute: YOUR code validates the arguments and runs the function
4. Append:  a tool_result message keyed to that id, back onto messages[]
5. Goto 2
```

That's the whole mechanism. LangGraph is this loop with checkpointing and a state schema. CrewAI
is this loop with role prompts. The OpenAI Agents SDK is this loop with handoffs. When a framework
surprises you at a client site at 5pm, the move is always the same: find where it does step 3, and
log what went into step 1.

One detail in step 4 bites people: the result is keyed by **ID**, not by position or name. If the
model emits two calls in one turn you must return both results with matching IDs before the next
request, or the provider rejects the array as malformed. The error message is rarely helpful.

### 2.3 Three wire formats, and the one difference that causes real bugs

Clients run all three, and you will port code between them.

```python
# OpenAI (and everything OpenAI-compatible: vLLM, Ollama, Groq, most gateways)
{"role": "assistant", "tool_calls": [
  {"id": "call_1", "type": "function",
   "function": {"name": "lookup_rate", "arguments": "{\"lane\":\"DAL-CHI\"}"}}]}
{"role": "tool", "tool_call_id": "call_1", "content": "{\"rate\": 2.14}"}

# Anthropic — everything is a content block on a normal message
{"role": "assistant", "content": [
  {"type": "tool_use", "id": "toolu_1", "name": "lookup_rate",
   "input": {"lane": "DAL-CHI"}}]}
{"role": "user", "content": [
  {"type": "tool_result", "tool_use_id": "toolu_1", "content": "{\"rate\": 2.14}"}]}

# Bedrock Converse — request side: toolConfig.tools[].toolSpec
#   = {name, description, inputSchema: {"json": {...}}}
{"role": "assistant", "content": [
  {"toolUse": {"toolUseId": "tu_1", "name": "lookup_rate",
               "input": {"lane": "DAL-CHI"}}}]}
{"role": "user", "content": [
  {"toolResult": {"toolUseId": "tu_1",
                  "content": [{"json": {"rate": 2.14}}], "status": "success"}}]}
```

> **OpenAI's `arguments` is a JSON *string*. Anthropic's `input` and Bedrock's `input` are
> already-parsed objects.**

That single difference has caused more integration bugs here than any other detail, and they're
all the same bug wearing different hats:

| What you see | Cause |
|---|---|
| `TypeError: the JSON object must be str, bytes or bytearray` | OpenAI code calling `json.loads(args)`, ported onto Anthropic |
| Arguments arrive as `{"lane": "{\"lane\":\"DAL-CHI\"}"}` | You `json.dumps`'d an already-parsed object |
| `JSONDecodeError: Expecting value: line 1 column 1` | OpenAI returns `""` for a zero-argument tool, not `"{}"` |
| Sporadic truncated arguments under load | Streaming deltas arrive as argument *fragments*; concatenate before parsing |

Handle it once, at the seam: `ToolRegistry.execute` takes `raw_args: str | dict`, normalises to a
dict, and never lets the rest of the codebase know which provider it came from. Same discipline as
Day 1's provider seam, one layer up.

Two more landmines. The tool-result **role** differs — OpenAI uses a dedicated `"tool"` role,
Anthropic and Bedrock put the result in a **`user`** message. And the ID field is named three
things (`tool_call_id`, `tool_use_id`, `toolUseId`). Not conceptually interesting; costs an
afternoon if you meet it live.

### 2.4 ReAct, and why you rarely write it anymore

ReAct (Yao et al., 2022) is **Reason → Act → Observe**, repeated. The original was pure prompt
engineering against models with no tool support — you asked for a fixed text format and parsed it:

```
Thought: I need the arrival time before I can compute detention.
Action: lookup_shipment
Action Input: SHP-202608-0041729
Observation: {"arrive_iso": "2026-08-14T14:38:00-05:00", ...}
```

You regex-scraped `Action:`, ran it, appended `Observation:`, re-prompted. Brittle — a stray colon
in the reasoning broke the parser.

Modern tool-calling models have the loop baked in by post-training: they were trained on
transcripts of exactly this shape in the provider's serialisation, which is why the block comes
back reliably structured instead of as text you scrape. **The shape did not change. Only the
parsing moved from your regex into the provider.**

Do you still write "Thought:" prompts? Usually no — you get the reasoning for free. The exception
is a model with weak or no native tool support, which you will meet on an on-prem engagement.
Knowing ReAct-as-text still works when the API doesn't is the fallback that makes you useful in
month one.

The teaching point: ReAct is a *shape*, not a framework. When someone says "we use ReAct," ask
what their termination conditions are — that's where the engineering lives.

### 2.5 Termination: four limits, and why `max_steps` alone is negligent

The naive loop is `while True`. The slightly-less-naive one is `for _ in range(8)`. Both are
wrong, and the second is wrong in a way that's easy to defend and expensive to discover.

| Limit | Bounds | Catches |
|---|---|---|
| `max_steps` | Iterations | Repetitive loops, unanswerable questions |
| `max_tokens` (cumulative) | Total context processed across the run | One step with a monstrous observation |
| `max_cost_usd` | Spend | Everything, in the unit a client cares about |
| `max_seconds` | Wall clock | A hung tool, a degraded provider |

Why steps aren't enough has a clean form. Every step re-sends the entire prior transcript plus the
newest observation, so with base prompt `B` and observations of `o` tokens:

```
total_input ≈ n·B + o·n(n−1)/2
```

**Quadratic in the step count.** Doubling `max_steps` roughly quadruples worst-case spend. And the
quadratic term is driven by `o`, which the loop doesn't control — a tool returning `k=20` chunks
instead of `k=4` multiplies your bill without changing the step count at all. A step budget bounds
iterations. It bounds nothing a finance team recognises.

Two operational details. **Check the budget before issuing the call, on the projected input
size** — a post-hoc check tells you you're over budget after you've paid. And **stop cleanly with
a `stop_reason`** (`"budget"`, `"max_steps"`, `"repeat_detected"`, `"complete"`), returning the
partial answer and the trace; an agent that crashes at the limit discards every dollar it already
spent and can't tell a client why it stopped.

A fifth control that isn't a limit belongs here: **repeat detection.** Hash
`(tool_name, canonical_json(args))`; on the second identical call inject an observation saying so
and suggesting a different approach; on the third, stop. Six lines, eliminates the most common
runaway.

### 2.6 Tool errors are observations, not exceptions

The most elegant idea in the day, and the one people reflexively get wrong — twenty-three years of
instinct says *an error is an exception and exceptions propagate*. In an agent loop, invert it.

```python
# in ToolRegistry.execute
try:
    args = tool.args_model.model_validate(raw_args)
except ValidationError as exc:
    return ToolResult(ok=False, content=str(exc))   # <- NOT raise
```

What happens next is the demo that makes a room sit up. The model reads:

```
ValidationError: arrive_iso — Input should be a valid datetime,
invalid character in year, input_value='Aug 14 2026 2:38pm'
```

…and on the next step calls the tool again with `"2026-08-14T14:38:00-05:00"`. **Self-healing for
free, because you didn't swallow the exception.** You got a retry loop with a repair mechanism and
wrote none of it.

Three consequences most people miss.

**Error wording is prompt engineering.** `"lookup failed"` gets you a hallucinated shipment.
`"No shipment found with id SHP-202608-9999999. IDs have the form SHP-YYYYMM-NNNNNNN. Use
search_shipments if you only know the lane or date."` gets you a correct recovery. That string
sits in the context and conditions the next token exactly like any other prompt text — because it
*is* prompt text.

**Classify into three kinds**, because they want different observations: *user-correctable* (bad
arguments — return the validation detail), *retryable-transient* (a 503 from the TMS — "temporarily
unavailable, retry or proceed without it"), and *fatal* (permission denied — say the path is
closed, so it reports honestly instead of looping).

**Never return a raw stack trace.** A hundred tokens of file paths that teach the model nothing,
leak your directory structure into a transcript you may be shipping to a provider, and crowd out
the one line that matters.

### 2.7 Tool descriptions are the highest-leverage prompt surface you have

Every tool schema — name, description, and every field description in the args model — is in the
context on **every single step.** It is the most re-read text in your system.

The model's job each step is a routing decision, and your description is the only evidence it has.
A vague one (`"searches things"`) gets the tool used at random or not at all. One that omits the
*boundary* gets it called for questions it can't answer, burning a step. **The most valuable
sentence in a description is usually the negative one:**

```python
# bad
search_policy(query: str, k: int = 4)
"""Searches the documents."""

# good
search_policy(query: str, k: int = 4)
"""Semantic search over the shipper's transportation policy corpus: tender
acceptance, detention/demurrage rates, OTIF measurement, lane bidding,
carrier scorecards, intermodal guidance. Returns k passages with document
IDs for citation. Does NOT contain data about specific shipments or
carriers — use lookup_shipment for those."""
```

Seventy extra tokens per step, routinely saving two or three steps. Almost always worth it.

The corollary governs Day 9: **every additional tool is a permanent context tax and one more thing
to choose wrongly between.** Selection accuracy degrades as the list grows — the threshold is
model-dependent and I'd distrust anyone quoting a hard number, but the direction isn't in dispute.
Three sharp tools beat nine fuzzy ones.

### 2.8 When *not* to use an agent

Write this down. Talking a client *out* of an agent, with a reason, is a large part of the job.

| Situation | Use instead | Why |
|---|---|---|
| Fixed sequence, known in advance | A pipeline / DAG | Deterministic, testable, ~10× cheaper |
| One tool, one call | A plain function call | The loop adds latency and failure modes for nothing |
| Sub-second latency requirement | Retrieval + one generation | Agent loops are multi-round by definition |
| Regulated decision (credit, pricing, safety) | Deterministic rules; LLM for explanation only | You must be able to justify the output |
| High volume, cost-sensitive | Pipeline with a small model | Every step re-sends the full context (§2.5) |

**Use an agent when the sequence genuinely depends on intermediate results.** That's the rule.
Agent: "which carrier has the worst FTA on DAL→CHI, and what's their detention exposure?" —
you can't write query two until query one answers. Pipeline: "extract the fields, then summarise."

---

## 3. Worked example — on paper

> **Setup.** An agent answers *"How much detention do we owe on SHP-202608-0041729?"*
> **$3.00 / M input tokens, $15.00 / M output.** System prompt + five tool schemas = **900 tokens**;
> task message = **60**. Model latency **1.2 s** per step. The run takes 4 steps:
>
> | Step | Model output | Observation |
> |---|---|---|
> | 1 | `lookup_shipment` (40 tok) | 150 tok |
> | 2 | `search_policy` (40 tok) | 880 tok |
> | 3 | `compute_detention` (40 tok) | 60 tok |
> | 4 | final answer (180 tok) | — |

**Q1.** The record says appointment **09:00**, departed **14:38** same day. Free time 2 hours;
$65/hour in 15-minute increments **rounded up**; cap $650 per event. What's owed? Then a second
event: appointment 09:00, departed **06:00 next morning**.

**Q2.** Input tokens billed at each of the 4 steps, and the run totals. (Every step re-sends
everything before it.)

**Q3.** Cost of the run, versus a single Day 4 RAG call (960 + 880 input, 180 output). Multiple?

**Q4.** A bad run: same 960 base, `max_steps=8`, model loops on `search_policy` with `k=20` so
each observation is **4,400 tokens** and each output is 40. Total input? Cost? Ratio to Q3 — and
note `max_steps=8` was satisfied in both.

**Q5.** General formula for total input over `n` steps with base `B` and observation size `o`.
Growth order in `n`?

**Q6.** Wall clock for the good run if the tools take 40 ms, 180 ms and 1 ms. Versus the single
RAG call (1.2 s + 180 ms). Does a 2-second SLO survive?

**Q7.** Which limits stop the Q4 runaway, and at which step? Use `max_cost_usd = 0.25` and a
cumulative `max_tokens = 60,000`.

<details>
<summary><b>Answers — do the arithmetic first</b></summary>

**Q1.** Free time ends 11:00. 11:00 → 14:38 = **218 minutes**. 218/15 = 14.53 → **round up to 15
increments** = 225 min = 3.75 h × $65 = **$243.75**, under the cap.
Second event: 21 h − 2 h free = 19 h = $1,235, which exceeds the per-event cap → **$650**. Note
what the cap does to the shape of the answer: an agent that computes 19 × 65 and stops has
retrieved the rate and missed the rule.

**Q2.** 960 · 1,150 · 2,070 · 2,170. Input **6,350**, output **300**.

**Q3.** 6,350 × $3/M + 300 × $15/M = $0.01905 + $0.0045 = **$0.0236**. Single RAG call: 1,840 ×
$3/M + 180 × $15/M = **$0.0082**. The agent costs **≈2.9×** — the honest price of adaptivity on a
*well-behaved* run.

**Q4.** Step *k* input = 960 + 4,440(k−1): 960 · 5,400 · 9,840 · 14,280 · 18,720 · 23,160 ·
27,600 · 32,040 = **132,000**. Cost = $0.396 + $0.0048 = **$0.401**, which is **17× the good run
at the identical `max_steps` setting.** The step budget held perfectly and did nothing.

**Q5.** `n·B + o′·n(n−1)/2` where `o′` is observation plus assistant output. **O(n²)** — doubling
`max_steps` roughly quadruples the worst case, with the observation size as coefficient, and the
observation size is set by your tools, not your loop.

**Q6.** 4 × 1.2 + 0.221 ≈ **5.0 s**, versus **1.38 s**. **3.6× slower.** A 2-second SLO does not
survive and no tuning fixes it — four sequential round trips is structural. That's row 3 of §2.8
and the most common reason to say no.

**Q7.** Cumulative input: 960 · 6,360 · 16,200 · 30,480 · 49,200 · 72,360 · 99,960 · 132,000.
`max_tokens = 60,000` trips on the projection for step 6 (72,360) → **stops entering step 6** at
~$0.148. `max_cost_usd = 0.25`: spent $0.217 after step 6, projected $0.300 after step 7 →
**stops entering step 7**. Either caps the damage at roughly half, and both fire well before
`max_steps` would. That's the argument for four limits, in numbers.

</details>

---

## 4. What people get wrong

**"The model executes the tool."**
It emits structured text. Your code is the only thing that runs anything, which is where every
security property of the system lives.

**"Function calling is a special model mode."**
Next-token prediction with schemas in context and constrained decoding on the argument span —
Day 2's Level 3, pointed at a tool schema instead of your output model.

**"`arguments` is a dict."**
On OpenAI it's a JSON *string*, and `""` rather than `"{}"` for zero-argument tools. Normalise at
the seam and stop thinking about it.

**"Strict mode means the arguments are correct."**
It means *valid* — Day 2 §2.3 again. `{"shipment_id": "SHP-202608-0041730"}` is one digit from the
right answer and passes every check you wrote.

**"`max_steps` is enough."**
§3 Q4. Eight steps, seventeen times the cost, budget respected. Steps bound iterations; nothing
else.

**"Tool errors should be caught and retried silently."**
Then you've thrown away §2.6's self-healing, and your trace no longer shows what happened.

**"Tool descriptions are documentation."**
They're the most-re-read prompt in your system and the sole evidence for every routing decision.
Rewrite one badly and the agent stops using the tool.

**"More tools make the agent more capable."**
Up to a point, then selection degrades and every schema is a per-step context tax.

**"Temperature 0 makes the loop deterministic."**
No. Tool results vary, and even at temperature 0 you get run-to-run variation from batching and
hardware nondeterminism at the provider. Test with invariants, not exact-output snapshots.

**"An agent is a better RAG."**
An agent is a *more adaptive* RAG that costs 3× and runs 3.6× slower. Sometimes that's the right
trade; never automatically.

---

## 5. The trainer's angle

**The analogy that lands:** an agent is a workflow orchestrator whose DAG is generated one node at
a time, at runtime, by a component that cannot see the executor. Step Functions where the state
machine is emitted lazily and you learn the next state only after the current one returns. For an
infrastructure audience that does two things at once — it makes the loop obvious, and it makes the
*danger* obvious: you've given up static analysis of the workflow, the thing you'd normally never
trade away. Everything in §2.5 is buying back the guarantees you just lost.

For §2.1, use the work-order framing: **the model puts a message on a queue and your process is
the only consumer.** It answers the security question before anyone asks it.

**The demo that makes it click:** the ValidationError self-correction, live, with the raw step
trace on screen. The room watches the model receive a pydantic error and fix itself on the next
step. Ten seconds, no narration needed, and it converts §2.6 from advice into something people
have seen.

**The second demo, which is better and almost nobody does:** replace your good `search_policy`
description with `"""Searches things."""` and re-run the identical question. The agent stops using
the tool or calls it with a garbage query. Paste the good description back, re-run. Same code,
same model, same question — the only variable was seventy tokens of prose. Most efficient argument
for §2.7 in existence.

**The predictive question before you run anything:** *"This agent has `max_steps=8`. What's the
worst it can cost me?"* Take two guesses from the room — almost everyone answers with something
linear — then walk §3 Q4.

**The question a sharp student will ask:** *"If a tool call is just text the model emits, why do I
need a special API parameter? Why not prompt for JSON like Day 2?"*

> You can, and that's exactly what ReAct did in 2022 — regex over a text stream. Three things make
> the native path better. The model was post-trained on that specific serialisation, so the block
> comes back reliably instead of drifting into prose. The provider applies constrained decoding to
> the argument span against your schema, so you get Day 2's Level 3 guarantee on the shape. And
> the call/result pair is a first-class message shape, so the transcript stays in the distribution
> the model was trained on, which matters more than you'd expect over six steps. The prompt-only
> version still works and you'll need it the first time a client hands you a local model with no
> tool support. It's measurably worse and it's a fine fallback.

---

## 6. Self-check

Cover the answers.

1. What does the model actually produce when it "calls a tool"? Who executes it?
2. Write the five-step loop from memory.
3. What is `arguments` in the OpenAI format, and how does it differ from Anthropic and Bedrock?
4. Name two portability landmines beyond string-vs-object.
5. What does ReAct stand for, and why do you rarely hand-write it now? When would you?
6. Name the four termination limits and what each catches that the others don't.
7. Why is `max_steps` alone insufficient? Give the growth order and the coefficient driving it.
8. Should a budget check happen before or after the call, and why?
9. What should `ToolRegistry.execute` do on a `ValidationError`, and what do you get for free?
10. Name the three error classes and the observation each should return.
11. Why is a tool description higher-leverage per token than the system prompt?
12. State the rule for when an agent is justified, with one freight example each side of it.

<details>
<summary><b>Answers</b></summary>

1. Structured text — name, arguments, ID — parsed by the provider and returned to you. Your code
   executes it; the model has no runtime.
2. Send messages + schemas → receive text or tool_call → your code validates and executes →
   append tool_result keyed by ID → repeat.
3. A JSON **string** on OpenAI (`""` for no-args); an already-parsed **object** on Anthropic
   (`input`) and Bedrock (`input`).
4. Tool-result role (`"tool"` vs a `user` message); ID field name (`tool_call_id` /
   `tool_use_id` / `toolUseId`); streaming argument fragments needing concatenation. Any two.
5. Reason → Act → Observe. Models are post-trained on the loop and the provider parses the
   structure, so you don't scrape text. Hand-write it for a model with no native tool support.
6. `max_steps` (repetition/unanswerable), cumulative `max_tokens` (one enormous observation),
   `max_cost_usd` (spend in the client's unit), `max_seconds` (hung tool, degraded provider).
7. Each step re-sends the whole transcript: `n·B + o·n(n−1)/2`, **quadratic in n**, coefficient
   `o` — set by your tools, not your loop.
8. Before, on the projected input size. A post-hoc check tells you you're over after you've paid.
9. Return `ToolResult(ok=False, content=str(exc))`, don't raise. You get self-correction: the
   model reads the error as its observation and repairs the arguments next step.
10. User-correctable → the validation detail. Retryable-transient → "temporary, retry or proceed
    without it." Fatal → the path is closed, so it reports honestly instead of looping.
11. It's in context every step and is the only evidence for the routing decision made every step.
12. **Use an agent when the sequence genuinely depends on intermediate results.** Agent: "which
    carrier has the worst FTA on DAL→CHI, and what's their detention exposure?" Pipeline:
    "extract the accessorial rates from these ten documents and summarise."

</details>

**Scored below 9?** Re-read §2.5 and §2.6. The lab's five hard parts are exactly those two
sections, and it will not re-explain either.

---

## 7. Going deeper

<!--reading:07-->

### If you read one thing this week

**[Building Effective AI Agents](https://www.anthropic.com/engineering/building-effective-agents)** — Erik Schluntz & Barry Zhang (Anthropic engineering blog, 2024) · essay · ~35 min

The clearest published statement of workflow-versus-agent, and it argues §2.8 harder than the module does — the seven named patterns are the vocabulary you will use in every client scoping conversation from here on.

### Then, in the order I'd take them

- **[Tool use with Claude — overview](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)** — Anthropic · docs · ~30 min  
  §2.1 and §2.2 in primary-source form — `stop_reason: "tool_use"`, the `tool_use` block, and the `tool_result` block you send back — which is the exact round trip your loop has to implement, and reading it before you write the loop saves an hour of guessing.
- **[ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)** — Yao, Zhao, Yu, Du, Shafran, Narasimhan & Cao (ICLR 2023) · paper · ~35 min  
  Read §2 and Figure 1 and stop — the Thought/Action/Observation prompt format is obsolete now that tool calling is native, but the loop it describes is the one running inside every agent framework you will be handed.
- **[Amazon Bedrock — client-side tool use](https://docs.aws.amazon.com/bedrock/latest/userguide/tool-use-client-side.html)** — AWS documentation · docs · ~25 min  
  The `toolConfig` / `toolSpec` / `inputSchema.json` shape is the third wire format from §2.3 and it is the one your AWS clients will hand you — read it next to the Anthropic page above and the normalisation your registry needs becomes obvious.
- **[τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains](https://arxiv.org/abs/2406.12045)** — Shunyu Yao, Noah Shinn, Pedram Razavi & Karthik Narasimhan (2024) · paper · ~35 min  
  Multi-turn tool use with a rule-following requirement, and the pass^k consistency numbers are the antidote to single-shot benchmark optimism — useful the first time a client asks why the agent that worked in the demo is flaky in production.

<!--/reading-->

### Also mentioned in this module

- *Toolformer: Language Models Can Teach Themselves to Use Tools* — Schick et al., 2023. How tool
  use got into the post-training data in the first place.
- *Gorilla: Large Language Model Connected with Massive APIs* — Patil et al., 2023, and the
  Berkeley Function-Calling Leaderboard it produced. Read skeptically: benchmark tools aren't yours.
- Bedrock **Converse API** docs, the `toolConfig` section. Twenty minutes, and it's the format your
  AWS clients hand you.

---

**Now go to `labs/DAY_07.md`.** The lab builds on §2.2 (you write the loop), §2.3 (your registry
normalises all three formats), §2.5 (four limits plus repeat detection), §2.6 (the five hard parts
*are* this section, forced), and §2.8 (which you write up as `teaching/when_not_to_agent.md`).
