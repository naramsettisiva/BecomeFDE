# Day 01 · Learn — What you are actually calling, and what it costs

**Read before `labs/DAY_01.md`. Budget 1:15. Pen and paper for §3.**

---

## 1. Where this sits

You've spent 23 years on systems where a request goes to a service, the service does something
deterministic, and a response comes back. Today's system breaks two of those assumptions and
keeps one, and knowing exactly which is which is the difference between debugging effectively
and debugging by superstition.

The problem today solves: **you are about to build twenty-three days of software on top of a
component you have never called.** Before you write a line of it, you need an accurate model of
what that component is, what the request/response cycle actually looks like, and what each call
costs — because cost is a first-class design constraint here in a way it isn't for a database
query.

---

## 2. The mechanism

### 2.1 What a language model actually does

Strip away the chat interface and a language model does exactly one thing:

> Given a sequence of tokens, produce a probability distribution over what the next token is.

That's it. Everything else — conversation, reasoning, tool use, code generation — is that one
operation applied repeatedly, with scaffolding around it.

Concretely, for the input `"Detention accrues at $65 per"`:

```
the model outputs a score for EVERY token in its vocabulary (~100k-200k entries)

  " hour"    →  0.71
  " day"     →  0.09
  " week"    →  0.04
  " event"   →  0.03
  " mile"    →  0.01
  ...        →  (the other ~150,000 tokens share the remaining 0.12)
```

A **sampler** then picks one. Append it to the input. Run again. Repeat until the model emits a
special stop token or you hit your `max_tokens` limit.

This is called **autoregressive generation**, and three consequences fall straight out of it —
each of which will bite you in a lab this month:

**Consequence 1 — output is generated one token at a time, so latency scales with output
length, not input length.** A 4,000-token prompt with a 20-token answer is fast. A 200-token
prompt with a 2,000-token answer is slow. This is why streaming exists, and why "make the
answer shorter" is a real latency optimisation.

**Consequence 2 — the model cannot revise.** Once a token is emitted it's part of the input for
the next step. There is no backspace. If it starts a sentence badly it will finish it
consistently-badly rather than stopping. (This is also why "think step by step" works at all —
it gives the model tokens to compute *with* before committing to an answer.)

**Consequence 3 — the model has no memory between calls.** None. Every "conversation" is you
re-sending the entire history each time. When you build memory on Day 10, you are not unlocking
a feature; you are deciding what to re-send.

### 2.2 Temperature — how the sampler picks

The model gives you a distribution. Temperature controls how you sample from it.

```
temperature = 0     → always take the highest-scoring token         (greedy)
temperature = 1     → sample proportionally to the scores
temperature = 2     → flatten the distribution, rare tokens get a real chance
```

Mechanically, temperature divides the raw scores before they're normalised. Low temperature
exaggerates the gaps between candidates; high temperature compresses them.

**The practical rule, which most people get wrong by leaving the default at 0.7:**

| Task | Temperature | Why |
|---|---|---|
| Extraction, classification, tool calls, structured output | **0.0** | You want the most likely token. Variation is pure downside. |
| RAG answers over retrieved context | **0.0–0.2** | The answer is in the context; you want it reported, not embellished. |
| Summarisation | 0.0–0.3 | |
| Marketing copy, brainstorming, creative writing | 0.7–1.0 | Variation is the point. |

**And the caveat that matters professionally:** `temperature=0` is *not* a determinism
guarantee. Floating-point non-associativity under GPU batching means identical inputs can
produce different outputs depending on what else was in the batch. Providers also update models
behind stable-looking names. **Never promise a client bit-identical reproducibility.** Promise
them a measured consistency rate — which you'll learn to measure on Day 5.

### 2.3 Tokens — the unit of everything

Models don't see characters or words. They see **tokens**: sub-word chunks produced by a
tokeniser that was trained (usually with an algorithm called Byte-Pair Encoding) to give
frequent character sequences their own single token.

Roughly, for English prose: **1 token ≈ 4 characters ≈ 0.75 words.**

But "roughly" hides the part that costs you money:

| Text | Tokens | Why |
|---|---|---|
| `the` | 1 | Extremely common — its own token |
| `detention` | 1–2 | Common enough in English |
| `SHP-202608-0041729` | **~11** | Rare string; splits into fragments and digits |
| `détention` | 3–4 | The accented character costs extra bytes |
| `電子ログデバイス` | ~12 | Non-Latin scripts are poorly compressed by English-trained tokenisers |

**Why the ID costs 11 tokens:** the tokeniser never saw `SHP-202608-0041729` in training, so it
falls back to splitting into the largest known pieces — `SH`, `P`, `-`, `202`, `608`, `-`, `004`,
`17`, `29` or similar. Every rare string pays this tax.

**Why this is a design constraint, not trivia:** if you build a prompt that embeds 200 shipment
IDs, you've spent ~2,200 tokens on identifiers alone. At scale that's real money, and it
displaces context you'd rather spend on actual content. The fix — which you'll reach for in
Week 3 — is to pass a compact reference and let a tool fetch the detail.

### 2.4 The four layers people conflate

This is the section to actually memorise, because almost every "it doesn't work" question in a
client meeting resolves to someone confusing two of these.

| Layer | Examples | What changes when you swap it |
|---|---|---|
| **Model** | `llama3.1:8b`, `gpt-4o-mini`, `claude-sonnet`, `amazon.nova-lite` | Quality, latency, cost, context window size, tool-calling fidelity, training cutoff |
| **Provider** | Ollama (local), OpenAI, Anthropic, AWS Bedrock, Azure | Auth mechanism, rate limits, data residency, SLA, billing relationship, which models exist |
| **API shape** | OpenAI `/v1/chat/completions`, Anthropic Messages, Bedrock Converse | Request/response schema, how tool calls are encoded, how streaming frames arrive |
| **SDK** | `openai`, `anthropic`, `boto3`, `langchain` | Ergonomics only — and it should never leak into your business logic |

The subtle one is **model vs. provider**. Claude Sonnet accessed through Anthropic and the same
Claude Sonnet accessed through Bedrock is the *same weights producing the same outputs*. What
differs is who you have a contract with, where the data goes, and how you authenticate. When a
client says "we can't use Claude, our data can't leave our VPC," the correct response is not
"then use a different model" — it's "then use Bedrock with a VPC endpoint, same model." You'll
prove this to yourself on Day 1's AWS lane.

### 2.5 Why one seam matters

Given those four layers, here is the single most consequential architectural decision you make
on day one of any engagement:

```python
# ❌ The provider leaks into every file
from openai import OpenAI
client = OpenAI()
resp = client.chat.completions.create(model="gpt-4o-mini", messages=[...])

# ✅ One seam. Business logic never names a provider.
from fdekit import chat
answer = chat("How much detention for a 5-hour wait?")
```

The first version is fine in a notebook and a two-week refactor in a codebase. When the client's
security team mandates Bedrock in month two — and they will, roughly half the time — version two
is one environment variable.

You already know this pattern. It's the same argument as a repository interface over a database
driver, or an abstraction over a cloud provider's SDK. The reason to be explicit about it here is
that **the LLM ecosystem changes faster than any of those**, so the seam pays off sooner.

### 2.6 The failure mode with no error

This one deserves its own section because it's the most dangerous property of the whole stack.

Traditional systems fail loudly: exception, 500, timeout, constraint violation. LLM systems have
a large class of failures that raise nothing at all:

- **Truncation.** You set `max_tokens=100`, the answer needed 300, you get a confident-looking
  answer that stops mid-reasoning. No exception. The response has `finish_reason: "length"` and
  almost nobody checks it.
- **Hallucination.** The model states a number that doesn't exist. Status 200.
- **Silent context drop.** Your prompt exceeded the window and something got trimmed. Depending
  on the provider you may get an error — or you may not.
- **Wrong-but-plausible.** The answer is well-formed, confident, and wrong.

**Half of production LLM debugging is noticing that nothing errored.** This is why Days 4–5
build citation verification and an eval harness before you build anything sophisticated: they
are how you convert silent failures into loud ones.

---

## 3. Worked example — do this on paper

Don't run code. Do the arithmetic by hand; you'll need to do exactly this in a client meeting
one day, on a whiteboard, without a laptop.

> **Scenario.** You're scoping a RAG assistant for a 3PL's operations team. Each query sends
> the system prompt plus five retrieved document chunks and gets back a short answer.
>
> - System prompt + instructions: **600 tokens**
> - 5 retrieved chunks at ~900 tokens each: **4,500 tokens**
> - The user's question: **40 tokens**
> - The answer: **350 tokens**
>
> Volume: 40 users × 12 queries/day × 22 working days.

**Q1. Input and output tokens per query?**

**Q2. Total monthly tokens?**

**Q3. Monthly cost on `gpt-4o-mini` ($0.15 per 1M input, $0.60 per 1M output)?**

**Q4. Monthly cost on `gpt-4o` ($2.50 / $10.00)?**

**Q5. Monthly cost on `amazon.nova-lite` ($0.30 / $0.90)?**

**Q6.** The client says "we'll roll this out to all 500 users next year." Redo Q3 at 500 users.

**Q7.** Which line dominates the bill — input or output? What does that tell you about where to
optimise first?

<details>
<summary><b>Answers — work them first</b></summary>

**Q1.** Input = 600 + 4,500 + 40 = **5,140 tokens**. Output = **350 tokens**.

**Q2.** 40 × 12 × 22 = **10,560 queries/month**.
Input: 10,560 × 5,140 = **54.3M tokens**. Output: 10,560 × 350 = **3.7M tokens**.

**Q3.** Input: 54.3 × $0.15 = $8.15. Output: 3.7 × $0.60 = $2.22. **≈ $10.37/month**.

**Q4.** Input: 54.3 × $2.50 = $135.75. Output: 3.7 × $10.00 = $37.00. **≈ $172.75/month**.

**Q5.** Input: 54.3 × $0.30 = $16.29. Output: 3.7 × $0.90 = $3.33. **≈ $19.62/month**.

**Q6.** 500/40 = 12.5×. So $10.37 × 12.5 ≈ **$130/month** on `gpt-4o-mini`.

**Q7.** **Input dominates — roughly 4:1 here**, because RAG sends a lot of context to get a
short answer. So the first optimisation is *retrieval*, not generation: fewer, better chunks.
Cutting k from 5 to 3 with a reranker (Day 14) removes ~1,800 input tokens per query, about a
third of the bill, and often *improves* quality. Shortening the answer saves almost nothing.

This ratio is characteristic of RAG and it surprises people who expect output — the "expensive"
per-token side — to dominate. Notice also that all five numbers are small. At pilot scale the
token cost is a rounding error against the fixed infrastructure cost, which is the single most
useful thing you can tell a client who wants to optimise prematurely.

</details>

---

## 4. What people get wrong

**"Temperature 0 makes it deterministic."**
No — it makes the *sampler* greedy. GPU batching non-determinism and provider-side model updates
both still apply. Say "consistent", measure the rate, never promise identical.

**"The model remembers our conversation."**
It doesn't. You re-send the history every call. Every "memory" feature is a decision about what
to re-send and what to summarise or drop. This reframing makes Day 10 obvious rather than magical.

**"A bigger context window means I should use it."**
It means you now have to *decide* what goes in. Attention degrades toward the middle of long
contexts (you'll measure this yourself on Day 10), and you pay for every token on every step of
an agent loop. Bigger windows made context engineering more important, not less.

**"Tokens are words."**
They're sub-word fragments, and the mismatch is worst exactly where your domain data lives —
IDs, codes, part numbers, non-English text.

**"The model is reasoning."**
Careful here, because it's genuinely contested and you'll be asked. What's *observable* is that
producing intermediate tokens before an answer measurably improves accuracy on multi-step
problems. Whether that constitutes reasoning is a live argument with serious people on both
sides. The defensible position for a trainer: describe the mechanism and the measured effect,
flag the interpretation as disputed, and don't stake your credibility on either side.

**"Cheaper models are worse."**
Frequently untrue for extraction, classification, routing, and RAG-over-clean-context — the
tasks that make up most production traffic. Nova Lite at $0.30/1M is 8× cheaper than `gpt-4o-mini`
and 30× cheaper than Claude Sonnet, and on Day 1's lab you'll test whether that gap buys you
anything on freight questions. **Measure before you assume.**

---

## 5. The trainer's angle

**The analogy that lands:** autocomplete that has read a very large fraction of the internet and
can be steered by everything you put before the cursor. It's imperfect — it undersells
instruction-following — but it correctly kills the "it looks things up" and "it thinks then
writes" misconceptions in one move, which are the two most expensive ones to leave in place.

**The demo that makes it click:** show the token probabilities. Most tooling can surface
logprobs. Watching `" hour"` at 0.71 and `" day"` at 0.09 for `"Detention accrues at $65 per"`
converts an abstraction into an observation in about ten seconds.

**Your opening failure for this topic:** set `max_tokens=30` on a question needing a long answer.
Show the confident, truncated, wrong-looking response. Ask the room what went wrong. Someone will
say "the model doesn't know." Then show `finish_reason: "length"`. That five-second reveal is the
best possible introduction to *the failure mode with no error*, and it's the frame for the whole
course.

**The question a sharp student will ask:** *"If it's just predicting the next token, how can it
follow instructions?"* Have this answer ready — it's the most common genuinely good question in
the topic:

> Base models trained purely on next-token prediction follow instructions badly. The models you
> use have had a second training stage — instruction tuning on examples of instructions and good
> responses, then a preference-optimisation stage where humans (or a model trained on human
> judgements) rank candidate responses. That shifts the distribution so that "helpful response to
> the instruction" becomes the high-probability continuation. The mechanism is still next-token
> prediction. What changed is what the distribution favours.

---

## 6. Self-check

Cover the answers.

1. In one sentence, what operation does a language model perform?
2. Why does output length affect latency more than input length?
3. What does temperature actually modify?
4. Give two reasons `temperature=0` isn't a determinism guarantee.
5. Why does `SHP-202608-0041729` cost ~11 tokens when `detention` costs 1–2?
6. Name the four layers, and give one thing that changes when you swap each.
7. Is Claude-via-Bedrock a different model from Claude-via-Anthropic? What *is* different?
8. Name three LLM failures that raise no exception.
9. In a RAG workload, which side of the bill usually dominates, and where do you optimise first?
10. Why is "just use a bigger context window" not a complete answer?

<details>
<summary><b>Answers</b></summary>

1. Given a token sequence, produce a probability distribution over the next token. Everything
   else is that, repeated.
2. Output is generated autoregressively — one forward pass per token. Input is processed in a
   single largely-parallel pass.
3. How the sampler draws from the distribution — it scales the scores before normalisation.
   Low temperature exaggerates gaps; high temperature flattens them. It does not change what the
   model knows.
4. GPU floating-point non-associativity under batching; provider-side model updates behind a
   stable name. (Also: some providers don't expose a true 0.)
5. The tokeniser never saw that string in training, so it falls back to splitting into small
   known fragments — letters, punctuation, digit groups.
6. Model (quality/cost/latency/context/cutoff) · Provider (auth, residency, limits, billing) ·
   API shape (schema, tool-call encoding, streaming format) · SDK (ergonomics only).
7. Same model, same weights, same outputs. Different: contract, data residency, auth, rate
   limits, billing. This is the answer to "our data can't leave the VPC."
8. Truncation at `max_tokens`; hallucination; wrong-but-plausible answers; silent context
   trimming. (Any three.)
9. Input, typically ~4:1 in RAG. Optimise retrieval first — fewer, better chunks — which often
   improves quality at the same time. Shortening answers barely moves the bill.
10. You still have to decide what fills it; attention degrades toward the middle of long
    contexts; and you pay for every token on every step of an agent loop.

</details>

**Scored below 7?** Re-read §2.3 and §2.6 before starting the lab. Today's lab assumes all of
this and won't re-explain it.

---

## 7. Going deeper (optional)

- **Tokenisation, interactively** — OpenAI's tokeniser playground, or `tiktoken` locally. Ten
  minutes here is worth more than any article.
- *Attention Is All You Need* (Vaswani et al., 2017) — the transformer paper. Read the
  architecture diagram and §3.2; skip the rest on a first pass.
- *Training language models to follow instructions with human feedback* (Ouyang et al., 2022) —
  the InstructGPT paper. This is the answer to the "how does it follow instructions" question in §5.
- Your provider's pricing page. **Read it once properly today**, then re-read it monthly. Prices
  and model names drift faster than any other fact in this course, and a trainer quoting stale
  prices loses a room instantly.

---

**Now go to `labs/DAY_01.md`.** The lab assumes §2.4 (the four layers), §2.3 (tokens), and
§2.6 (silent failure) — those three are what the exercises are built on.
