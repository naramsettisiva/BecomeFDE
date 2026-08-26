# Day 11 — MCP, Tools, and Skills: Making Capability Portable

**Sat Sep 5, 2026** · Week 2 · Maps to: **Module 06 — Advanced Retrieval & Skills** · Backend: **local** + `[PAID]` · Est. cost: **$1–2**

> **Before you start — read `learn/DAY_11_LEARN.md` (1:15).**
> MCP architecture, the three primitives, skills. The lab below assumes it and does not re-explain it.


---

## Why today matters

**FDE lens.** This is the most immediately marketable day in the bootcamp. MCP (Model
Context Protocol) is how a client's internal systems get exposed to any AI application
without rewriting integrations per vendor. Walking into an engagement able to say "I'll
wrap your TMS in an MCP server this week and it'll work in Claude Desktop, in your IDE,
and in whatever you build next" is a concrete, immediate deliverable. Very few people can
do it well yet.

**Trainer lens.** MCP is on every current AI-engineering syllabus and in almost nobody's
hands. Being fluent in it on both sides — server *and* client — is one of the fastest routes
to being asked to speak or teach, because the demand for the explanation currently exceeds
the supply of people who've built one.

---

## Objectives

1. Explain MCP's architecture: hosts, clients, servers, and the three primitives (tools, resources, prompts).
2. Build an MCP server exposing your freight tools, and connect it to Claude Desktop and Claude Code.
3. Build an MCP *client* so your own agent can consume any MCP server.
4. Understand "skills" as procedural capability, and write one.

---

## Schedule (5:00)

| Block | Time | What |
|---|---|---|
| 0 | 0:30 | Warm-up |
| 1 | 1:15 | **Learn** — `learn/DAY_11_LEARN.md` |
| 2 | 2:30 | Lab: build a server, connect it, build a client, write a skill |
| 3 | 0:30 | Teach-back #11 |
| 4 | 0:15 | Ship |

---

## Block 0 — Warm-up (0:30)

1. Four memory types, and which one is most often skipped.
2. Where did your needle heatmap start degrading? What's your reliability ceiling?
3. Which compaction strategy lost the negation, and what one sentence fixed it?
4. Why do tool schemas cost more than people expect?

---

## Block 1 — Learn (1:15)

**Read `learn/DAY_11_LEARN.md` and work its examples on paper before continuing.**
Take the self-check at the end. Anything you miss goes on a flashcard and into tomorrow's
warm-up. The material below consolidates the module — it is not a substitute for it.

### 1.1 Why MCP exists

Before: every AI app writes its own integration to every system. N apps × M systems = N×M
integrations. After: each system exposes one MCP server; each app implements one MCP
client. N + M.

That's the whole pitch, and it's the same argument as LSP for editors or ODBC for
databases. If you can make that analogy in one sentence to a client architect, you have
their attention.

### 1.2 The architecture

```
┌─────────────────────────────────────┐
│  HOST  (Claude Desktop, Claude Code,│
│         your own app)               │
│  ┌──────────┐  ┌──────────┐         │
│  │ Client 1 │  │ Client 2 │  one client per server
│  └────┬─────┘  └────┬─────┘         │
└───────┼─────────────┼───────────────┘
        │ JSON-RPC 2.0 over stdio or HTTP+SSE
   ┌────▼─────┐  ┌────▼──────┐
   │ Server A │  │ Server B  │
   │ (TMS)    │  │ (policy)  │
   └──────────┘  └───────────┘
```

Transports: **stdio** (local subprocess — simplest, what you'll use today) and
**streamable HTTP** (remote, multi-user, needs auth). Know that remote servers raise
auth and tenancy questions immediately; that's the first thing a client security team
will ask.

### 1.3 The three primitives

| Primitive | Controlled by | Analogy | Example |
|---|---|---|---|
| **Tools** | The *model* decides to call | POST endpoint | `compute_detention(...)`, `lookup_shipment(...)` |
| **Resources** | The *application* selects and injects | GET endpoint / file | `freight://policy/02_detention.md` |
| **Prompts** | The *user* invokes deliberately | Slash command / template | `/carrier-review carrier=Ridgeline` |

This three-way split is the part people get wrong. The distinction is **who is in
control**. A document your agent might want to search is a tool (`search_policy`). A
document the user explicitly attached is a resource. A workflow the user triggers is a
prompt.

Teaching that distinction clearly, with the "who decides?" framing, is worth ten minutes
of any curriculum — and it's the question that will come up in every design review.

---

## Block 2 — Lab (2:30)

### 2.1 Build the MCP server (75 min)

`mcp_servers/freight_ops/server.py`:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("freight-ops")

# --- TOOLS: model-invoked ---------------------------------------------------
@mcp.tool()
def search_policy(query: str, k: int = 4) -> str:
    """Search freight operations policy documents. Returns cited excerpts.
    Use for questions about detention, demurrage, OTIF, tender acceptance,
    scorecards, or bid process."""

@mcp.tool()
def compute_detention(arrive_iso: str, appt_iso: str,
                      free_minutes: int = 120,
                      rate_usd_per_hour: float = 65.0,
                      cap_usd: float = 650.0) -> dict:
    """Compute billable detention. Returns minutes, billable_hours, and USD,
    applying 15-minute increments and the per-event cap."""

@mcp.tool()
def lookup_shipment(shipment_id: str) -> dict:
    """Look up a shipment by ID (format SHP-YYYYMM-NNNNNNN) from the TMS."""

@mcp.tool()
def carrier_scorecard(carrier: str, month: str) -> dict:
    """Return a carrier's monthly composite score, component scores, and band."""

# --- RESOURCES: app-selected ------------------------------------------------
@mcp.resource("freight://policy/{doc_id}")
def policy_doc(doc_id: str) -> str:
    """A full policy document by id."""

@mcp.resource("freight://glossary")
def glossary() -> str: ...

# --- PROMPTS: user-invoked --------------------------------------------------
@mcp.prompt()
def carrier_review(carrier: str, quarter: str) -> str:
    """Generate a structured quarterly carrier business review."""

@mcp.prompt()
def detention_dispute(shipment_id: str) -> str:
    """Draft a detention dispute response with policy citations."""
```

Tool description quality is the whole game. Rewrite each description three times and,
for one of them, deliberately write a vague version and observe the model failing to
choose it. **That before/after is your teach-back demo.**

Test with the inspector before wiring anything up:

```bash
npx @modelcontextprotocol/inspector python mcp_servers/freight_ops/server.py
```

### 2.2 Connect it to real hosts (35 min)

**Claude Desktop** — `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "freight-ops": {
      "command": "/absolute/path/to/fde-trainer-bootcamp/.venv/bin/python",
      "args": ["/absolute/path/to/fde-trainer-bootcamp/mcp_servers/freight_ops/server.py"]
    }
  }
}
```

Restart Claude Desktop. Then ask it, in the chat: *"A truck arrived at 09:15 for an 08:00
appointment and left at 14:40. What detention do we owe, and what does our policy say
about the cap?"* It should call `compute_detention` **and** `search_policy`.

**Claude Code** — add the same server via its MCP configuration and confirm the tools
appear.

**Record this working.** A 90-second screen recording of your own tools running inside
Claude Desktop is one of the strongest portfolio artifacts in this entire bootcamp,
because it is immediately legible to a non-technical hiring manager or client.

Then break it deliberately, and note the diagnostics: wrong Python path, missing absolute
path, a server that writes to stdout (**this one silently corrupts the JSON-RPC stream —
log to stderr only**), an unhandled exception in a tool. Put all four in
`mcp_servers/TROUBLESHOOTING.md`. Every one of these will happen to a student.

### 2.3 Build an MCP client (35 min)

`src/fdekit/mcp_client.py` — so *your* agent can consume any MCP server:

```python
class MCPToolAdapter:
    """Connect to an MCP server; expose its tools through fdekit's ToolRegistry."""
    async def connect(self, command: list[str]) -> None: ...
    async def list_tools(self) -> list[Tool]: ...
    async def call(self, name: str, args: dict) -> ToolResult: ...
```

Then point your Day 9 supervisor at your own server *and* at one third-party server
(`@modelcontextprotocol/server-filesystem` is a good, safe one). Your agent now has
capability it didn't implement. That's the payoff, and it's worth pausing on: **this is
what "portable capability" means in practice.**

### 2.4 Write a skill (20 min)

A "skill" is procedural memory made portable: a folder with instructions the model loads
when relevant, plus optional scripts and references. Write
`teaching/skills/detention-dispute/SKILL.md`:

```markdown
---
name: detention-dispute
description: Draft a detention dispute response with policy citations and
  ELD evidence requirements. Use when a carrier disputes a detention charge
  or when preparing a rebuttal to a carrier's detention invoice.
---

# Detention Dispute Response

## When to use
...

## Procedure
1. Pull the shipment's arrive/depart geofence timestamps (never the batch
   `detention_minutes` column — it is computed nightly and is wrong for
   real-time disputes).
2. Verify arrival was within the appointment window; if the carrier arrived
   more than 30 minutes after the window closed, detention does not accrue.
3. Compute billable time in 15-minute increments after 2 hours free.
4. Apply the $650 per-event cap.
5. Cite the specific policy section for every assertion.
6. Note the 30-day dispute window if the invoice date is close to expiry.

## Output format
...

## Common errors
- Using appointment time in UTC against a local-time appointment field (see INC-4471).
- Forgetting the cap on long detentions.
- Asserting detention without ELD-derived timestamps.
```

Note what makes this a skill rather than a prompt: it encodes **procedure and traps**
learned from experience, it's discoverable by description, and it's portable across
applications. Your Day 10 procedural memory, packaged.

---

## Block 3 — Teach-back #11 (0:30)

Record 10 min: **"MCP in fifteen minutes: build a server, plug it into Claude Desktop."**
`teaching/recordings/day_11.mov`

This is your most portable teaching asset — record it well. Structure:
1. The N×M → N+M argument, 60 seconds, with the LSP analogy.
2. Tools vs. resources vs. prompts, with the "who decides?" framing.
3. Live: write one tool, run the inspector, add to config, restart, use it in Claude Desktop.
4. The stdout-corrupts-the-stream gotcha. Show it breaking. This one saves people hours.

---

## Block 4 — Ship (0:15)

```bash
git add -A && git commit -m "Day 11: MCP server + client, Claude Desktop integration, first skill" && git push
```

---

## Done when

- [ ] MCP server exposing 4 tools, 2 resources, 2 prompts, passing the inspector
- [ ] Working in Claude Desktop **and** Claude Code, with a screen recording
- [ ] `TROUBLESHOOTING.md` with four real failure modes and their diagnostics
- [ ] MCP client adapter letting your own agent consume external servers
- [ ] One skill written with procedure, traps, and output format
- [ ] Tool-description before/after captured showing selection improving

---

## Trap list

- **Printing to stdout in a stdio server.** Silently corrupts JSON-RPC. Log to stderr.
- Relative paths in the host config. Always absolute, always the venv's Python.
- Vague tool descriptions. The model's tool choice is downstream of your prose.
- Tools that raise instead of returning structured errors.
- Exposing a write/delete tool without confirmation semantics. Think about blast radius
  *before* a client asks.
- Forgetting to restart the host after a config change.

---

## Stretch

Add **streamable HTTP transport** and deploy the server so it's reachable remotely.
Then confront the two questions that immediately follow: authentication (who is calling?)
and tenancy (whose data do they see?). Write a one-page design note answering both. That
note is the thing a client's security architect will ask you for in week one of a real
engagement, and having written it once means you'll write it well under pressure.
