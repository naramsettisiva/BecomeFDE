# Day 07 — Tool Calling and the Agent Loop, From First Principles

**Tue Sep 1, 2026** · Week 2 · Maps to: **Module 02 — Agentic RAG** · Backend: **local** + `[PAID]` · Est. cost: **$1–2**

> **Before you start — read `learn/DAY_07_LEARN.md` (1:15).**
> What a tool call really is, the loop, three wire formats. The lab below assumes it and does not re-explain it.


---

## Why today matters

**FDE lens.** "Agent" is the most abused word in the industry and the thing every client
will ask for by name. Your job on an engagement is often to talk someone *out* of an
agent — a well-scoped tool call inside a deterministic workflow beats an autonomous loop
in nine out of ten enterprise use cases, and being the person who says that (with a
reason) makes you the adult in the room.

**Trainer lens.** Agent frameworks hide the loop. A trainer who has only used LangGraph
teaches syntax. A trainer who has written the while-loop teaches the mental model, and
can then explain LangGraph in four sentences instead of a whole session.

**Rule of the day: no agent framework until 3:30.** You write the loop.

---

## Objectives

1. Write a tool-calling agent loop by hand: schema → model → parse → execute → observe → repeat.
2. Explain the wire format of a tool call in both OpenAI and Anthropic shapes, and why they differ.
3. Handle the five hard parts: bad arguments, tool errors, loops, budget, and termination.
4. State the decision rule for when *not* to use an agent.

---

## Schedule (5:00)

| Block | Time | What |
|---|---|---|
| 0 | 0:30 | Warm-up |
| 1 | 1:15 | **Learn** — `learn/DAY_07_LEARN.md` |
| 2 | 2:30 | Lab: `agent.py` from scratch, five hard parts, then LangGraph comparison |
| 3 | 0:30 | Teach-back #7 |
| 4 | 0:15 | Ship |

---

## Block 0 — Warm-up (0:30)

Flashcards from your Day 6 miss list, then:

1. Which bucket of your golden set scores worst, and what's your hypothesis?
2. What does the lost-in-the-middle reordering actually do to the chunk order?
3. Cohen's κ for your judge — what was it, and is it good enough?

---

## Block 1 — Learn (1:15)

**Read `learn/DAY_07_LEARN.md` and work its examples on paper before continuing.**
Take the self-check at the end. Anything you miss goes on a flashcard and into tomorrow's
warm-up. The material below consolidates the module — it is not a substitute for it.

### 1.1 A tool call is a constrained generation, not a function call

The model does not call anything. It emits **structured text** that your code parses and
acts on. Everything else is convention. Internalise this and the whole category
demystifies.

The loop, in full:

```
1. You send: messages + tool schemas (JSON Schema per tool)
2. Model emits either final text, or a tool_call block: {name, arguments, id}
3. YOUR CODE parses, validates, and executes the function
4. You append a tool_result message keyed to that id
5. Go to 2
```

Two wire formats you must know because clients use both:

```python
# OpenAI: tools live in a `tools` array; calls come back on message.tool_calls
{"role":"assistant","tool_calls":[{"id":"call_1","type":"function",
  "function":{"name":"lookup_rate","arguments":"{\"lane\":\"DAL-CHI\"}"}}]}
{"role":"tool","tool_call_id":"call_1","content":"{\"rate\":2.14}"}

# Anthropic: content blocks, tool_use / tool_result
{"role":"assistant","content":[{"type":"tool_use","id":"toolu_1",
  "name":"lookup_rate","input":{"lane":"DAL-CHI"}}]}
{"role":"user","content":[{"type":"tool_result","tool_use_id":"toolu_1",
  "content":"{\"rate\":2.14}"}]}
```

Note `arguments` is a **JSON string** in OpenAI and a **parsed object** in Anthropic.
That difference has caused more integration bugs than any other detail in this space.

### 1.2 ReAct, and what actually makes a loop work

ReAct = Reason → Act → Observe, repeated. The published version prompts for an explicit
"Thought:" before each action. Modern tool-calling models do this internally, so you
rarely hand-roll ReAct text anymore — but the *shape* is unchanged.

What separates a working loop from a demo:

| Concern | Naive | Production |
|---|---|---|
| **Termination** | `while True` | max_steps, max_tokens, max_wall_clock, max_cost — all four |
| **Bad arguments** | crash | validate with pydantic, return the validation error *to the model* as the tool result |
| **Tool errors** | crash or swallow | return a structured error the model can reason about, distinguish retryable from fatal |
| **Repetition** | infinite same call | detect identical consecutive calls, inject a nudge, then abort |
| **Observability** | print statements | a step trace you can replay and show a client |

The second row is the elegant one: **when a tool call fails, the error message is the
next observation.** The model reads "ValidationError: lane must match ^[A-Z]{3}-[A-Z]{3}$"
and corrects itself. Self-healing for free, if you don't swallow the exception.

### 1.3 When NOT to use an agent

Write this decision table into `teaching/when_not_to_agent.md`. You will use it in
client conversations constantly.

| Situation | Use instead | Why |
|---|---|---|
| Fixed sequence of steps, known in advance | A pipeline / DAG | Determinism, testability, 10× cheaper |
| One tool, one call | A function call, no loop | The loop adds latency and failure modes for nothing |
| Sub-second latency requirement | Retrieval + single generation | Agent loops are multi-round by definition |
| Regulated decision (credit, pricing, safety) | Deterministic rules + LLM for explanation only | You must be able to justify the output |
| Cost-sensitive at high volume | Pipeline with a small model | Each agent step is a full context re-send |

**Use an agent when the sequence genuinely depends on intermediate results.** That's the
whole rule. Query decomposition where the second query depends on the first answer:
agent. "Extract fields then summarise": pipeline.

Having a crisp answer to "do we need an agent here?" is a large part of what an FDE
actually gets paid for.

---

## Block 2 — Lab (2:30)

### 2.1 `src/fdekit/agent.py` — the loop, by hand (75 min)

```python
@dataclass
class Tool:
    name: str
    description: str
    args_model: type[BaseModel]      # pydantic — gives you JSON Schema for free
    fn: Callable[..., Any]
    def schema(self) -> dict: ...    # -> OpenAI tools[] entry

class ToolRegistry:
    def register(self, name, description, args_model): ...   # decorator
    def schemas(self) -> list[dict]: ...
    def execute(self, name: str, raw_args: str | dict) -> ToolResult: ...
        # validate with args_model; on ValidationError return
        # ToolResult(ok=False, content=str(exc)) — do NOT raise

@dataclass
class Step:
    n: int; thought: str | None; tool: str | None
    args: dict | None; observation: str | None; tokens: int; ms: float

class Agent:
    def __init__(self, registry, system, max_steps=8, max_cost_usd=0.25,
                 max_seconds=60, backend=None): ...
    def run(self, task: str) -> AgentRun:
        """Returns final answer + full step trace + usage + stop_reason."""
```

Tools to build (against the freight corpus and a small synthetic ops dataset):

```python
search_policy(query: str, k: int = 4)          # your Day 4 RAG retrieval
compute_detention(arrive_iso, appt_iso, free_minutes=120, rate_usd_per_hour=65.0)
lookup_shipment(shipment_id: str)              # synthetic TMS lookup
calculate(expression: str)                     # safe arithmetic — NOT eval()
current_date()                                 # yes, really. models don't know today.
```

`calculate` must not use `eval`. Use `ast.parse` with a whitelist of node types, or
`simpleeval`. **A client's security review will ask about this specific line.** Being
able to say "we AST-whitelist, here's the code" in the first meeting is worth a lot.

### 2.2 The five hard parts (45 min)

Force each failure and record the trace in `labs/day07/AGENT_FAILURE_MODES.md`:

1. **Bad arguments.** Ask something that makes it call `compute_detention` with a
   malformed timestamp. Confirm the ValidationError goes back as an observation and the
   model corrects on the next step. Screenshot the trace — this is a great demo.
2. **Tool error.** Make `lookup_shipment` raise on an unknown ID. Does the agent
   recover, or does it hallucinate a shipment? Fix the tool's error message until it
   recovers. **Error message wording is prompt engineering.** Most people miss this.
3. **Infinite loop.** Ask a genuinely unanswerable question. Watch it call the same tool
   repeatedly. Implement repeat-detection: hash (tool, args), and after 2 identical
   calls inject "You have already called this with these arguments and got the same
   result. Try a different approach or answer with what you have."
4. **Budget.** Set `max_cost_usd=0.02` and give it a task needing 8 steps. It must stop
   cleanly and report a partial answer with `stop_reason="budget"` — not crash, not
   silently truncate.
5. **Termination ambiguity.** Find a task where the agent stops too early with a partial
   answer. This is the subtlest one and the hardest to fix. Note what you tried.

### 2.3 Now LangGraph — and the honest comparison (30 min)

Rebuild the same agent with LangGraph's prebuilt ReAct agent. Then fill in
`labs/day07/framework_comparison.md`:

| | Hand-rolled | LangGraph |
|---|---|---|
| Lines of code | | |
| Time to first working version | | |
| Where's the step trace? | | |
| How do you add a cost budget? | | |
| How do you inspect the exact prompt sent? | | |
| What happens on a tool ValidationError? | | |
| Could you debug it at a client site at 5pm? | | |

There's no correct answer — the point is having a defensible one. Frameworks win on
persistence, streaming, human-in-the-loop, and checkpointing (all real, all things
you'd otherwise build). They cost you legibility. **State the trade honestly, and you
sound like someone who has shipped both. Which, as of today, you have.**

---

## Block 3 — Teach-back #7 (0:30)

Record 10 min: **"An agent is a while-loop. Here's the loop."**
`teaching/recordings/day_07.mov`

Must: write the 5-line loop on screen before showing any framework. Then show the
ValidationError self-correction trace live — it's the moment the concept clicks for a
room, every time. End with the when-not-to-agent table.

Your Week 2 teaching focus (from the Day 6 retro) goes at the top of your notes. Check
yourself against it when you watch back.

---

## Block 4 — Ship (0:15)

```bash
pytest labs/ -q && git add -A
git commit -m "Day 07: agent loop from scratch, tool registry, five failure modes, LangGraph comparison"
git push
```

---

## Done when

- [ ] Hand-rolled agent completes a 3-tool task with a readable step trace
- [ ] All four termination limits enforced (steps, tokens, cost, wall clock)
- [ ] ValidationError → self-correction demonstrated and captured
- [ ] Repeat-detection stops an unanswerable task cleanly
- [ ] `calculate` uses AST whitelisting, not `eval`
- [ ] Framework comparison table filled in with your own numbers

---

## Trap list

- `eval()` in a calculator tool. Instant security-review failure.
- Raising on tool errors instead of returning them as observations.
- Only `max_steps` as a limit — a single step can burn your budget with a huge context.
- Not logging the *exact* messages array sent. When an agent misbehaves this is the
  only thing that tells you why.
- Letting the model see raw stack traces. Give it a clean, actionable error string.
- Assuming tool descriptions don't matter. They're the highest-leverage prompt surface
  in an agent system — rewrite one badly and watch the agent stop using the tool.

---

## Stretch

Add `parallel tool calls`: when the model emits two independent tool_use blocks in one
turn, execute them concurrently with `asyncio.gather` and return both results. Measure
the latency win on a task that needs three independent lookups. This is a real
production optimisation and a satisfying five-minute demo.
