# AWS Lane — Week 1 (Aug 25–31)

**macOS. Est. AWS spend this week: $4–8. Est. added time: 3h 45m across six days.**

Read `AWS_LANE.md` and `AWS_COST_DISCIPLINE.md` first. Run `bash scripts/aws/preflight.sh`
before Day 1 — green or don't start.

Every AWS block ends the same way:

```bash
make aws-nuke      # every time, even when you're sure there's nothing
```

---

## Day 01 — Bedrock is a fourth backend, not a new course · 40 min · ~$0.05

**Core lane taught you** one `chat()` seam so swapping providers is one env var.
**Today you cash that in.**

```bash
export FDEKIT_BACKEND=bedrock
python labs/day01/hello_llm.py "How much detention for a 5-hour wait?" --backend bedrock
```

That's it. Your Day 1 CLI now runs on AWS. Nothing else changed. **Sit with that for a
minute** — it is the entire argument for the seam, and it's the demo you'll use when a client
asks "how hard is it to move off OpenAI?"

### Do (25 min)

1. **Run the same prompt across four backends** and build the table:

   ```bash
   for b in local openai anthropic bedrock; do
     python labs/day01/hello_llm.py "What is routing guide depth?" --backend $b
   done
   ```

   | backend | model | latency | in/out tokens | cost | answer quality 1-5 |
   |---|---|---|---|---|---|

2. **Then vary the Bedrock model only** — `amazon.nova-micro-v1:0`, `amazon.nova-lite-v1:0`,
   and your Claude model. Same prompt, same temperature.

   The finding you're looking for: **on a factual freight question with clear context, Nova
   Lite is often indistinguishable from Claude at 1/30th the price.** Confirm or refute it
   with your own numbers. Whichever way it lands, that measurement is the basis of every
   model-selection recommendation you'll make on an engagement.

3. **Read the Converse API** in `src/fdekit/bedrock.py`. Two things to internalise:
   - Converse gives you one message shape across every Bedrock model. `InvokeModel` is
     per-model JSON. You will meet `InvokeModel` in client code; know it, don't write it.
   - Converse rejects a `system` role inside `messages` — system is a top-level parameter.
     The error doesn't say so. `bedrock.py` rescues an inline system message; note *why*
     that rescue exists.

### Break it (10 min)

Add to `labs/day01/FAILURE_MODES.md`. These are the five AWS failures you'll actually hit:

| Break it by | You should recognise |
|---|---|
| Let the SSO session expire (or `aws sso logout`) | `UnrecognizedClientException` / 403 → `make aws-login`, not a code bug |
| Use a model ID you haven't requested access to | `AccessDeniedException` → console > Model access. **Listing a model ≠ having access** |
| Switch to `--region us-west-2` | Model not found — availability is regional |
| Put a `system` role inside `messages` | `ValidationException` that doesn't mention system |
| Pin `anthropic.claude-3-5-sonnet-*` | Works fine, costs **double** current Sonnet for a worse model |

That last one isn't an error — it's a bill. Legacy Claude 3.5 moved to "Public Extended
Access" in Dec 2025 at $6/$30 per 1M. **Finding a pinned legacy model ID in a client's
codebase is a free cost win in your first week**, and it's the kind of thing that gets an FDE
noticed. Grep for it as a reflex.

### Teach-back addendum (5 min)

Append 90 seconds to teach-back #1: *"and here's the same code on Bedrock, one env var."*
Show the four-backend table. This is the moment the seam stops being theory.

---

## Day 02 — Structured output the Bedrock way · 35 min · ~$0.10

Core lane built three levels of structured output. Bedrock's native level-3 is **tool use**,
not a `response_format` parameter — and the envelope differs from OpenAI's in a way that
causes real bugs.

### Do

1. Port `extractor.py` to Bedrock using forced tool use:

   ```python
   from fdekit.bedrock import chat, tool_spec, extract_tool_uses

   spec = tool_spec(
       "record_policy_rules",
       "Record every policy rule found in the document.",
       ExtractionResult.model_json_schema(),
   )
   resp = chat(doc_text, system=SYS, tools=[spec],
               toolConfig={"toolChoice": {"tool": {"name": "record_policy_rules"}}})
   rules = extract_tool_uses(resp)[0]["input"]     # already a dict
   ```

2. **Write the three-envelope table** into your notes — you'll draw it on a whiteboard within
   a month of starting an engagement:

   | | OpenAI | Anthropic direct | Bedrock Converse |
   |---|---|---|---|
   | Tools live in | `tools[].function` | `tools[]` | `toolConfig.tools[].toolSpec` |
   | Schema key | `parameters` | `input_schema` | `inputSchema.json` |
   | Call arrives as | `tool_calls[]` | `content[].tool_use` | `content[].toolUse` |
   | **Arguments type** | **JSON string** | parsed object | parsed object |
   | Result goes back as | `role: "tool"` | `tool_result` block | `toolResult` block |

   The bolded row is the one that bites. OpenAI hands you `arguments` as a **string** you must
   `json.loads`; the other two hand you an object. Code that works against Bedrock silently
   breaks against OpenAI, on a line that looks fine.

3. **Compare violation rates.** Run your Day 2 extractor 20 times on each path: prompt-and-
   parse (level 2) vs. forced tool use (level 3) on Nova Lite. Record schema-violation rate,
   repair-loop invocations, latency, cost.

   Forced tool use should be near-zero violations. **Note how much prompt you could delete** —
   that deleted prompt is the level-3 argument, expressed in tokens saved rather than adjectives.

---

## Day 03 — Titan embeddings, and the dimensions decision · 35 min · ~$0.05

### Do

1. Embed the corpus with Titan V2 at **three dimensionalities**: 256, 512, 1024.

   ```python
   from fdekit.bedrock import embed
   v256  = embed(chunks, dimensions=256)
   v1024 = embed(chunks, dimensions=1024)
   ```

2. Run your Day 3 chunking bake-off queries against each. Build:

   | dims | Recall@3 | MRR | storage/1M vectors | query cost/1M |
   |---|---|---|---|---|

   Storage scales linearly with dimensions: 1M × 1024 dims × 4 bytes ≈ 3.8 GB ≈ $0.23/month
   on S3 Vectors. At 256 dims it's $0.06.

   **The finding to look for: 256 dims often costs you very little recall for a 4× storage
   and query-scan reduction.** Whether that holds on *your* corpus is an empirical question —
   answer it. "We used 1024 because it's the default" is not an answer you want to give a
   client who's asking why their vector bill is what it is.

3. **The gotcha:** Titan has no batch endpoint. 2,000 chunks = 2,000 API calls. Sequential,
   that's slow. Apply Day 2's async fan-out with a semaphore and measure the difference.
   This is the first place the two lanes genuinely reinforce each other.

4. Cross-model check: compare Titan V2 (1024) against `nomic-embed-text` (local, 768) on the
   same queries. Different scale, different distribution — **their similarity scores are not
   comparable**, which is exactly the Day 3 trap list item, now demonstrated across providers.

---

## Day 04 — S3 Vectors, and the $350 click you didn't make · 60 min · ~$0.15

**Today has the highest chance of an expensive mistake in the whole course. Read before you
click.**

Time trade: drop the Day 4 core-lane stretch goal (the paid OpenAI comparison) — you're doing
a better version of it here.

### Part A — S3 Vectors by hand (30 min)

```python
from fdekit.s3vectors import S3VectorStore, estimate_cost
from fdekit.bedrock import embed

store = S3VectorStore(bucket=f"fde-bootcamp-vectors-{suffix}", index="corpus")
store.create()                       # non_filterable=("text",) — see below
store.add((c.id, v, {"text": c.text, "doc_id": c.doc_id, "heading": c.heading_path})
          for c, v in zip(chunks, embed([c.text for c in chunks])))

hits = store.search(embed("how much detention per hour")[0], k=5)
```

Three things to notice, each of which is a teachable point:

1. **`query_vectors` returns DISTANCE, not similarity.** For cosine, similarity = 1 − distance.
   Forget this and your ranking inverts — you confidently return the *worst* matches, with no
   error anywhere. Read how `s3vectors.py` handles it.
2. **`nonFilterableMetadataKeys` should include `text`.** You never filter on chunk text, it's
   large, and metadata is capped at 1 KB per vector. Put it in non-filterable and the cap is
   yours to spend on things you actually filter by.
3. **PUT bills a 128 KB minimum per request.** 2,000 one-at-a-time PUTs cost ~$0.05; batched,
   ~$0.002. Run `python -m fdekit.s3vectors` to see the arithmetic.

Then reconcile against ground truth: run the same 8 queries through your Day 3
`SimpleVectorStore` and through S3 Vectors. **Identical rankings?** If not, which query differs
and why? (Metric, normalisation, or approximation — determine which.)

### Part B — Bedrock Knowledge Bases, carefully (30 min)

Now the managed version. In the console: **Bedrock → Knowledge Bases → Create**.

> ### STOP before you click Create
>
> Read the vector-store section of the form and **write down exactly what it says it will
> provision.** Historically quick-create defaulted to an **OpenSearch Serverless collection**,
> which bills a 2-OCU minimum — roughly **$350/month** — whether you query it or not.
>
> OpenSearch Serverless **NextGen** went GA in May 2026 with **no OCU minimum** and
> scale-to-zero after 10 minutes idle. So there are three possible states, and you need to
> know which you're in:
>
> | What the form offers | What to do |
> |---|---|
> | S3 Vectors | Choose it. Cost is cents. |
> | OpenSearch Serverless **NextGen** | Acceptable — scales to zero. Note it and move on. |
> | OpenSearch Serverless **classic** | **Do not create.** Point the KB at your existing S3 vector bucket instead. |
>
> **Write what you actually saw into `labs/day04/AWS_KB_NOTES.md`.** If the default has moved
> to S3 Vectors or NextGen, the famous "$350 empty collection" warning is out of date — and
> being the person who knows that, with a screenshot, is worth more than repeating folklore.

Then:

1. Point the Knowledge Base at your S3 vector bucket. Sync the corpus.
2. Query it with `retrieve` and with `retrieve_and_generate`.
3. **Build the honest comparison** — `evals/day04_kb_vs_handrolled.md`:

   | | Your Day 4 RAG | Bedrock Knowledge Base |
   |---|---|---|
   | Time to working | | ~20 min |
   | Chunking control | full | fixed / semantic / hierarchical presets |
   | Can you see the assembled prompt? | yes | **no** |
   | Citation verification | your substring check | `citations[]` — verify it yourself anyway |
   | Recall@5 on your golden set | | |
   | Cost per query | | |
   | What happens when it's wrong? | you debug it | you file a support case |

   Row three is the one that matters. **The Knowledge Base will not show you the prompt it
   assembled.** After Day 4 of the core lane you know exactly why that's a problem — you spent
   a day proving that prompt assembly changes the answer. Write down what you'd tell a client
   who asks "should we just use Knowledge Bases?"

   The honest answer is usually: *yes, start there — and here's the specific point at which
   you'll need to leave.* Being able to name that point is the value you add.

```bash
make aws-nuke      # deletes the KB. Keep the vector bucket — it's ~$0.001/month and Day 14 uses it.
```

---

## Day 05 — Bedrock Evaluations vs. your own harness · 45 min · ~$2

You spent today building an eval harness and calibrating a judge. AWS sells that as a service.
**Run both on the same golden set and find out what you'd give up.**

### Do

1. Console → **Bedrock → Evaluations → Create**. Run an **LLM-as-a-judge** evaluation on your
   60-case golden set, plus a **RAG evaluation** (retrieve-and-generate) against your Knowledge
   Base if it's still up.

2. Note the pricing shape: **you pay on-demand token rates for the model under test AND the
   judge model** — token cost twice. Use Nova Lite as the model under test to keep this at a
   couple of dollars. Human evaluation adds $0.21 per task; skip it.

3. **The comparison that matters** — `evals/day05_bedrock_evals_vs_mine.md`:

   | | Your harness | Bedrock Evaluations |
   |---|---|---|
   | Setup time | a day | ~30 min |
   | Can you change the rubric? | fully | within the built-in metrics |
   | Can you measure judge κ against your own labels? | **yes** | **not directly** |
   | Runs in CI as a gate? | yes | via API, awkwardly |
   | Segments by your difficulty labels? | yes | not natively |
   | Cost per 60-case run | | |

4. **Do the thing the service can't do**: take Bedrock's per-case verdicts, hand-label the same
   25 cases, and compute Cohen's κ between Bedrock's judge and you.

   This is the day's real lesson. A managed eval service gives you a number. **It does not tell
   you whether that number agrees with your definition of correct** — and on a client
   engagement, their domain expert's definition is the only one that matters. Being able to say
   *"Bedrock Evaluations scored this 0.88; I measured its agreement with your ops team at
   κ=0.51, so I wouldn't act on that 0.88 yet"* is a genuinely senior thing to be able to say.

### Teach-back addendum

Add a segment to teach-back #5: *"managed evals give you a number, not a calibrated number."*
Show your κ. This is the strongest five minutes in the AWS lane's first week.

---

## Day 06 — Capstone: the same app, two stacks · 30 min · ~$0.50

### Do

1. Add a **backend switcher** to your Chainlit app: local · OpenAI · **Bedrock**. It should
   already work if you kept everything behind `fdekit.chat`. If it doesn't, find where you
   leaked a provider import into business logic — **that leak is the lesson**, and it's the
   single most common architectural mistake in client AI codebases.

2. Add an **AWS beat to the demo script** (30 seconds, slots in after the transparency panel):

   > *"This runs identically on Bedrock inside your VPC — same code, one environment variable.
   > If your data can't leave your account, that's not a rewrite, it's a config change."*

   Say it while switching the dropdown live. For an enterprise buyer this is often the single
   most important sentence in the demo, and almost nobody demonstrates it.

3. **Week 1 AWS retro** in `LEARNING_LOG.md`:
   - `make aws-cost` — what did the week actually cost? Against the $4–8 estimate?
   - Which surprised you: a service being cheaper or more expensive than expected?
   - What did the managed services hide that you'd need to explain to a client?
   - What did the Knowledge Base quick-create form actually offer? (The Day 4 note.)

```bash
make aws-nuke
make aws-cost
```

---

## Week 1 AWS lane — done when

- [ ] `preflight.sh` green; budget alerts confirmed by email
- [ ] Four-backend comparison table with your own latency and cost numbers
- [ ] Nova Lite vs. Claude quality finding, stated either way with evidence
- [ ] Three-envelope tool-use table written down
- [ ] Titan embedding dimensionality trade measured on your corpus
- [ ] S3 Vectors store working; rankings reconciled against local ground truth
- [ ] **`AWS_KB_NOTES.md` recording what quick-create actually provisions**
- [ ] Knowledge Base vs. hand-rolled comparison, including the prompt-visibility row
- [ ] Cohen's κ measured between Bedrock's judge and your own labels
- [ ] Demo script has the "same code, one env var" beat
- [ ] `make aws-nuke` run after every AWS block, and at week's end
