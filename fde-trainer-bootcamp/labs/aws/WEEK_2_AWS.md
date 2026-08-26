# AWS Lane — Week 2 (Sep 1–7)

**macOS. Est. AWS spend this week: $5–10. Est. added time: 4h 15m across six days.**

This is the week the AWS lane stops being "the same thing, on AWS" and starts being
capability you don't have locally. AgentCore Runtime, Gateway, and Memory are managed
primitives with no local equivalent — and they're what an enterprise client on AWS will
actually be running.

```bash
make aws-cost      # every morning
make aws-nuke      # after every AWS block. Memory especially — it bills monthly.
```

---

## Day 07 — Converse tool use, and the loop you already wrote · 45 min · ~$0.30

Core lane: you wrote the agent loop by hand. Today you point that same loop at Bedrock and
discover it needs about fifteen lines of change, not a rewrite.

### Do (30 min)

1. **Add a Bedrock adapter to your `Agent`** — not a second agent class. The registry, the
   step trace, the budget limits, the repeat detection all stay. Only the wire format changes:

   ```python
   from fdekit.bedrock import chat, tool_spec, extract_tool_uses, tool_result_message

   def _step_bedrock(self, messages):
       resp = chat(messages, system=self.system,
                   tools=[t.bedrock_spec() for t in self.registry.all()])
       uses = extract_tool_uses(resp)
       if not uses:
           return None, resp["output"]["message"]["content"][0]["text"]
       return uses, None
   ```

2. **Run all five Day 7 failure modes against Bedrock** and record where behaviour differs:

   | Failure | Local/OpenAI | Bedrock Converse |
   |---|---|---|
   | Bad arguments → ValidationError as observation | | |
   | Tool raises → structured error returned | | |
   | Infinite loop → repeat detection fires | | |
   | Budget exhausted → clean partial answer | | |
   | Stops too early | | |

   The self-correction one is the demo: Bedrock returns `toolUse.input` already parsed, so a
   pydantic ValidationError fed back via `tool_result_message(..., is_error=True)` produces the
   same self-healing behaviour. **Capture that trace** — it works on every provider and it's the
   single clearest way to show a room what a tool error actually is.

3. **`toolChoice` is worth knowing**: `{"auto"}`, `{"any"}` (must call something), or
   `{"tool": {"name": ...}}` (must call this one). Forcing a specific tool is how you get
   guaranteed structured output without a `response_format` parameter. Try all three.

### The thing to notice (15 min)

Your hand-rolled loop absorbed a new provider in fifteen lines. Ask yourself honestly: **how
long would that have taken if you'd started with a framework's prebuilt agent?**

Neither answer is wrong. But you now have a real, first-hand data point for the
build-vs-framework conversation, instead of an opinion. Write it in
`labs/day07/framework_comparison.md` as a third column.

---

## Day 08 — Knowledge Base retrieval inside your agentic patterns · 40 min · ~$0.60

### Do

1. Rebuild your **Day 4 Knowledge Base** (you nuked it) pointing at the S3 vector bucket.
   Then wire `bedrock-agent-runtime:retrieve` in as the retrieval step inside each of your four
   agentic patterns — routing, rewriting, decomposition, corrective.

2. **The interesting failure:** Knowledge Bases has its own query-reformulation and its own
   reranking. So when you add *your* query rewriting on top, you may be rewriting a query that
   was about to be rewritten. Measure it:

   | | KB retrieve, raw query | KB retrieve, your rewrite | KB with `orchestrationConfiguration` |
   |---|---|---|---|
   | Recall@5 | | | |
   | Latency | | | |
   | Cost | | | |

   **Layering your own logic on top of a managed service that does the same thing is one of
   the most common ways enterprise AI systems get slow and expensive for no benefit.** You are
   about to observe it in miniature. Note it — it becomes a strong Day 22 teaching point,
   because everyone has done it and few have measured it.

3. Add a row to your Day 8 strategy bake-off: **`KB-managed`** (retrieve_and_generate, no
   custom logic at all). Where does it land against your six strategies on quality, latency,
   and cost?

   If it beats three of your six on quality-per-dollar, say so out loud. Being willing to
   report that the managed service beat your hand-built pipeline is precisely the credibility
   that makes clients trust your recommendation when it goes the other way.

---

## Day 09 — AgentCore Runtime: multi-agent without the servers · 60 min · ~$1.50

Time trade: skip the Day 9 stretch (critic agent) — do it here on AgentCore instead.

**AgentCore Runtime** runs agents in microVMs at **$0.0895/vCPU-hour + $0.00945/GB-hour**,
billed per second, with **I/O wait and idle free**. A 1 vCPU / 2 GB agent costs $0.108 per
hour of *active compute*. Sessions persist up to 8 hours (Instances type: 14 days).

That "idle is free" clause is the whole product. An agent waiting on a tool call — which is
most of what agents do — costs nothing while it waits. Compare that to a Fargate task holding
a container open at ~$9/month minimum.

### Do

1. **Deploy your three workers as AgentCore runtimes.** Each worker is a container exposing
   `/invocations` and `/ping`:

   ```bash
   # Apple Silicon: AgentCore Runtime expects linux/arm64 — which is your native
   # arch, so no emulation needed. This is one of the rare times Apple Silicon is
   # the easy path rather than the awkward one.
   docker buildx build --platform linux/arm64 -t fde-bootcamp-policy-agent .
   ```

2. **Supervisor stays local**, workers run on AgentCore. Deliberate: it makes the handoff
   boundary a real network boundary, so context loss at handoff becomes visible rather than
   theoretical. Your typed `Handoff` model now has to survive serialisation — which is exactly
   the constraint that makes prose handoffs fail in production.

3. **Measure what changed**:

   | | All local | Workers on AgentCore |
   |---|---|---|
   | Wall clock, Ridgeline task | | |
   | Cold start per worker | | |
   | Active compute time (billed) | | |
   | Idle time (free) | | |
   | Cost per run | | |
   | Debuggability | full stack trace | logs + traces |

   Watch the **active vs. idle** split. In a typical multi-agent run, most wall-clock time is
   waiting. Being able to tell a client *"you pay for 4 seconds of a 22-second request"* is a
   surprisingly persuasive architectural point.

4. **The cost trap to note but not trigger:** AgentCore **Web Search is $7 per 1,000 queries**.
   Your deep-research agent could burn a fifth of the entire course budget in one afternoon.
   Use a stub search tool over your own corpus instead, and put the real number in your notes —
   it's a good example of a managed convenience that's fine at demo scale and ruinous at
   production scale.

```bash
make aws-nuke      # runtimes AND memories
```

---

## Day 10 — AgentCore Memory, and the recurring-cost lesson · 45 min · ~$0.75

Core lane: you built four memory types by hand. AgentCore Memory is short-term (events) and
long-term (extracted records) as a managed service.

### Do

1. Create a memory store and wire it into the supervisor. Run the 3-turn conversation from the
   core lane. Then restart and run turn 3 cold — same contrast, managed backend.

2. **Read the pricing carefully, because the shape is unusual:**

   | | Price | Shape |
   |---|---|---|
   | Short-term events | $0.25 / 1,000 new events | one-off |
   | Long-term, built-in extraction | **$0.75 / 1,000 records / month** | **recurring** |
   | Long-term, self-managed | $0.25 / 1,000 records / month | recurring |
   | Retrieval | $0.50 / 1,000 | per use |

   That recurring row is the lesson. **Memory is the only AWS GenAI primitive in this course
   that bills you monthly for something you created once.** A client who runs an agent for
   50,000 users and never prunes long-term memory has built a permanently growing bill.

3. **Do the arithmetic and put it in your cost model:** 50,000 users × 20 retained records
   = 1M records = **$750/month, forever, growing**. Then design the mitigation: TTL on records,
   relevance-based pruning, or self-managed extraction at 1/3 the price.

   **Then compare against your Day 10 hand-rolled semantic memory with dedupe.** Your dedupe
   on embedding similarity >0.9 exists precisely to stop this growth. You built the fix before
   you saw the bill — say that when you teach it.

4. Verify AgentCore's extraction against your own: does it preserve **negations**? Run the
   Day 10 negation-loss experiment against managed memory. ("Don't recommend intermodal for our
   reefer lanes.") Record whether the managed extractor keeps it.

```bash
make aws-nuke      # memories especially — they bill monthly
```

---

## Day 11 — MCP on AWS: Gateway and a Lambda-backed server · 60 min · ~$0.20

Time trade: drop the Day 11 stretch (streamable HTTP + auth design) — you're doing the real
version here, with actual auth.

**AgentCore Gateway** turns existing APIs, Lambda functions, and OpenAPI specs into MCP tools,
with auth handled for you. $0.005 per 1,000 invocations, plus $0.02 per 100 tools indexed
per month.

### Do

1. **Deploy your freight tools as Lambda functions:**

   ```bash
   bash scripts/aws/lab_up.sh day11        # creates fde-bootcamp-freight-tools
   ```

   Lambda is effectively free here — 1M requests and 400K GB-seconds are **always free**, every
   month, not just for new accounts. Every lab in this course fits inside that.

2. **Front them with AgentCore Gateway** as MCP tools. Then point *both* Claude Desktop (via
   the Day 11 stdio server) and your own agent (via the Gateway endpoint) at the same
   underlying Lambdas.

   Now you have the same capability exposed two ways. **That's the N×M → N+M argument made
   concrete** — and it's a much better demo than the diagram.

3. **Answer the two questions your Day 11 stretch asked**, with real infrastructure:
   - **Authentication:** Gateway uses inbound OAuth/JWT. Configure it. Who is calling?
   - **Tenancy:** whose data do they see? Enforce it in the Lambda from the caller's identity —
     **not** in the prompt. (Day 17 makes this a security answer; today you implement it.)

   Write `mcp_servers/AWS_GATEWAY_NOTES.md` covering both, plus the stdio-vs-HTTP trade.

4. **The macOS gotcha for Lambda packaging:** if any dependency has a compiled component
   (pydantic-core does), an `arm64` wheel built on your Mac will not run on an `x86_64`
   Lambda. Two clean options:

   ```bash
   # Option A — match the architecture (simplest, and ARM Lambda is cheaper)
   aws lambda create-function ... --architectures arm64

   # Option B — build for x86 in a container
   docker run --rm --platform linux/amd64 -v "$PWD":/var/task public.ecr.aws/sam/build-python3.12 \
     pip install -r requirements.txt -t python/
   ```

   The failure mode if you get this wrong is `Runtime.ImportModuleError` naming a `.so` file,
   which reads like a corrupt package. It isn't. It's architecture — and now you'll recognise
   it in three seconds instead of forty minutes.

---

## Day 12 — Capstone: the AWS-native architecture · 45 min · ~$1

### Do

1. Draw the **second architecture diagram** — the same Freight Ops Copilot, AWS-native:

   ```
   Chainlit / API Gateway (HTTP API)
        ↓
   Supervisor  →  AgentCore Runtime (workers)  →  AgentCore Gateway → Lambda tools
        ↓                    ↓
   AgentCore Memory    Bedrock Knowledge Base → S3 Vectors
        ↓
   Bedrock Guardrails  →  CloudWatch (traces, metrics, logs)
   ```

2. **Put both diagrams side by side** in your Day 12 architecture review. For each box, one
   line: *what the managed service does for you, and what it takes away.*

   This turns a 25-minute architecture review into something considerably more valuable: a
   **build-vs-buy analysis with numbers**, which is the actual conversation a client
   architect wants to have and rarely gets.

3. **Extend the trace viewer** to show which lane each node ran on, with per-node cost from
   both. Same request, two stacks, side by side:

   ```
   Request 7f3a · local stack  6.8s · $0.0071 · 11 calls
   Request 7f3b · aws stack    5.9s · $0.0038 · 11 calls   ← Nova Lite + prompt caching
   ```

4. **Week 2 AWS retro:**
   - AgentCore active-vs-idle split — what fraction of wall clock did you actually pay for?
   - The AgentCore Memory recurring-cost arithmetic at 50,000 users
   - Did managed memory preserve negations?
   - Did the KB-managed strategy beat any of your six hand-built ones?
   - `make aws-cost` — actual vs. the $5–10 estimate

```bash
make aws-nuke
make aws-cost
```

---

## Week 2 AWS lane — done when

- [ ] Hand-rolled agent loop absorbed Bedrock in ~15 lines; the diff is committed
- [ ] Five Day-7 failure modes re-run on Converse with differences recorded
- [ ] KB retrieval inside all four agentic patterns; double-rewriting effect measured
- [ ] `KB-managed` row added to the Day 8 bake-off
- [ ] Three workers running on AgentCore Runtime, with the active-vs-idle split measured
- [ ] AgentCore Memory recurring-cost arithmetic written into your cost model
- [ ] Negation-preservation tested against managed memory
- [ ] Lambda tools fronted by AgentCore Gateway, with auth and tenancy actually enforced
- [ ] `AWS_GATEWAY_NOTES.md` answering auth and tenancy
- [ ] Two architecture diagrams, box by box, with what each managed service takes away
- [ ] Every AgentCore memory and runtime torn down
