# FDE Trainer Bootcamp — 24 Days

> ## ▶ Open `fde-bootcamp.html`
>
> **That one file is the whole course.** Double-click it — every learn module, every lab,
> the AWS lane and the guides are embedded in it. Dark theme, works offline, works from a
> USB stick, works on your phone. Sidebar navigates day by day, search covers all 184,000
> words, and your progress saves in the browser.
>
> It also runs your flashcards. Click **Warm-up drill** in the sidebar for everything due
> from the days you've finished, or **Flashcards** on any day page for that day's deck.
> Space flips, `1` missed, `2` got it.
>
> The learn modules are **set like a book** in there: serif text at a readable measure, a
> chapter opener stating what you'll be able to do by the end, a section rail that tracks
> where you are on the page, and an S/M/L size control. Read them there, not in a markdown
> viewer.
>
> Everything below is the same content as markdown, for reading on GitHub or editing.

**Student:** Siva
**Trainer:** Claude
**Dates:** Thu Aug 27 → Tue Sep 29, 2026
**Load:** 5 hours/day × 24 weekdays = **120 hours**
**Target:** be a working AI Forward Deployed Engineer who can teach the material — with a deployed system, a measured eval suite, a portfolio, and a lesson you've delivered live.

This course is **self-contained**. It does not depend on any external programme, cohort, or
certification. It ends with you holding the artifacts and the skills, not a place on a waitlist.

---

## The contract

You show up 5 hours a day. Every day has two halves — **learn, then build**:

1. A **warm-up drill** (~20 min) — spaced repetition of what you'd forget otherwise. The
   navigator deals it for you: **288 flashcards**, one deck per day, scheduled in Leitner
   boxes (miss it and it returns tomorrow; know it and it goes 1 → 2 → 4 → 8 → 16 days out).
2. A **learn module** (~1:15) — `learn/DAY_NN_LEARN.md`. Actual instruction: what the thing
   is, how it works underneath, where it breaks, what people get wrong, worked examples done
   on paper, a self-check, and a link-checked reading list that names **one** thing to read if
   you read nothing else. You read this *before* you touch the keyboard.
3. A **hands-on lab** (~2:30) — code you type, run, break, and fix. Every lab ships something.
4. A **teach-back** (~40 min) — you explain today's idea out loud, recorded, to an imaginary
   room. This is the trainer muscle. It is not optional.
5. A **ship + retro** (~25 min) — commit, log, note what confused you.

The order matters twice over. You learn faster — and **you can only teach the part you were
taught.** A trainer who learned entirely by doing can demonstrate. One who understands the
mechanism can answer the question nobody prepared them for, which is the whole job.

`learn/README.md` explains the module format and how to work them. Every day still sums to
exactly 5:00 — the modules were traded against lab time, not added on top.

---

## Rules of the bootcamp

| Rule | Why |
|---|---|
| **Build it by hand before you import it.** You write cosine similarity before you touch a vector DB. You write the agent loop before you touch LangGraph. | An FDE debugs other people's stacks under time pressure. Framework-only knowledge collapses the moment the framework does something weird. A trainer who only knows the wrapper cannot answer the good questions. |
| **Everything is committed.** `git commit` at the end of every day, no exceptions. | Your GitHub history over these 24 days *is* the portfolio artifact. |
| **Teach-backs get recorded.** QuickTime screen recording, 5–10 min, saved in `teaching/recordings/`. | You cannot become a trainer by reading. You become one by hearing yourself be unclear and fixing it. |
| **Log every confusion in `LEARNING_LOG.md`.** | Your confusions are the exact places your future students will get stuck. This file becomes your FAQ. |
| **Cost discipline.** Local models by default (Ollama). Paid API only where the lab says `[PAID]`. | FDEs get asked "what will this cost in production?" on day one of every engagement. |

---

## Two lanes

The course runs a **core lane** and an **AWS lane** side by side.

| | Core lane | AWS lane |
|---|---|---|
| What | Build it from scratch — numpy, your own agent loop, your own eval harness | Rebuild the same capability on Bedrock, S3 Vectors, AgentCore, Lambda |
| Why | You cannot teach what you have only imported | You cannot deploy at a client without it |
| Cost | ~$0 (Ollama, local) | ~$25–48 over four weeks, with discipline |
| Time | 5 hrs/day | ~45 min/day, **traded** from the core lane's stretch goals — not added |

The AWS lane exists to earn one sentence, which you will say in a client meeting within a
month of starting an engagement:

> *"Bedrock Knowledge Bases will get you 80% of this in an afternoon. Here's the 20% it
> doesn't do, here's what it costs at your volume, and here's the failure mode you'll hit with
> your document set. Let's decide deliberately rather than by default."*

Nobody can say that who has only used one of the two lanes.

Start at **`labs/aws/AWS_LANE.md`**, then `AWS_SETUP.md` and `AWS_COST_DISCIPLINE.md`.

**Platform: macOS.** Every command is written for a Mac — Homebrew, zsh, BSD `date` and `sed`,
bash 3.2-safe scripts, and Apple Silicon notes where architecture matters (Lambda packaging,
Docker builds for Fargate and AgentCore).

---

## Repo map

```
fde-trainer-bootcamp/
├── fde-bootcamp.html  # ◀ THE WHOLE COURSE IN ONE FILE — start here
├── learn/             # 24 teaching modules — read BEFORE each lab
│                      #   DAY_01_LEARN.md ... DAY_24_LEARN.md (~120k words)
│                      #   _reading_*.json — 107 verified external sources
│                      #   _chapter_meta.json — objectives + key terms per chapter
│                      #   FLASHCARDS.csv — 288 cards, Anki/Quizlet importable
├── labs/              # 24 daily lab guides — DAY_01.md ... DAY_24.md
│   └── aws/           # the AWS lane — AWS_LANE.md, AWS_SETUP.md,
│                      #   AWS_COST_DISCIPLINE.md, WEEK_1..4_AWS.md
├── src/fdekit/        # shared helper library you build up over the course
│   ├── llm.py         #   one chat()/embed() seam — local, OpenAI, Anthropic, Bedrock
│   ├── bedrock.py     #   Converse API, tool use, guardrails
│   └── s3vectors.py   #   the cheap managed vector store
├── infra/lambda/      # freight tools as a Lambda, fronted by AgentCore Gateway
├── scripts/
│   ├── setup.sh       #   one-time local setup
│   ├── git_setup.sh   #   one-time git + GitHub setup (macOS SSH + Keychain)
│   ├── doctor.py      #   environment check (local + AWS)
│   └── aws/           #   preflight · budget · cost · lab_up · nuke
├── data/corpus/       # the freight document corpus your RAG systems index
├── evals/             # golden datasets, eval runs, scorecards
├── teaching/          # lesson plans, slide outlines, recordings
├── capstone/          # Week 4 capstone application
├── portfolio/         # README, case studies, demo scripts, FDE toolkit
├── Makefile           # make help
├── GIT_GUIDE.md       # git on macOS, from zero — setup, daily loop, panic section
├── LEARNING_LOG.md    # your daily confusion log
└── PROGRESS.md        # daily checkboxes
```

## The commands you'll live in

```bash
make setup             # one time — venv, deps, .env
make git-setup         # one time — git identity, editor, SSH key, GitHub remote
make doctor            # environment check
make aws-preflight     # AWS lane readiness — green before Day 1

make aws-cost          # every morning, 30 seconds
make aws-nuke          # after EVERY aws lab — the only zero-latency cost control
make aws-login         # when something starts 403ing

make html              # rebuild fde-bootcamp.html after editing any markdown
make schedule          # slipped a day? re-anchor the whole plan around where you are
make git-check         # before your first push: is .env tracked? anything oversized?
make ship M="Day 07"   # lint, test, commit, push
```

**When the schedule slips** — and it will — don't recompute anything by hand. Either click the
date range at the top of `fde-bootcamp.html`'s sidebar and say which day you're actually on, or
run `python scripts/schedule.py` to re-date the markdown files too. Both recompute all 24 days
around your anchor, backwards and forwards, skipping whichever days you don't work.

New to git from the Mac terminal? **`GIT_GUIDE.md`** is the full walkthrough — the mental
model, SSH keys with Keychain, the daily loop, and a panic section covering the things that
actually go wrong (including how to get out of vim).

---

## Day zero (do this tonight, ~75 min total, before Day 1)

**Core lane, ~30 min:**

```bash
# 1. Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Core tooling
brew install git uv ollama
brew install --cask visual-studio-code

# 3. Pull a local model so Day 1 has something to talk to (~4.7GB)
ollama serve &        # leave running
ollama pull llama3.1:8b
ollama pull nomic-embed-text

# 4. Accounts to create (free tiers are fine to start)
#    - github.com          (portfolio lives here)
#    - platform.openai.com (add $20 credit — used sparingly, marked [PAID])
#    - console.anthropic.com (add $20 credit)
#    - huggingface.co      (free — models + Spaces deploys)
#    - smith.langchain.com (free tier — tracing, Week 3)
```

Then on Day 1 morning:

```bash
cd fde-trainer-bootcamp
bash scripts/setup.sh
source .venv/bin/activate
python scripts/doctor.py
```

`doctor.py` tells you exactly what's missing. Do not start Day 1 until it's all green.

**AWS lane, ~45 min** — full instructions in `labs/aws/AWS_SETUP.md`:

```bash
brew install awscli jq

#  1. Create the account on the FREE PLAN (auto-closes when credits run out —
#     the closest thing AWS has to a hard spending cap)
#  2. IAM Identity Center → admin user → aws configure sso  (profile: fde)
#  3. make aws-budget EMAIL=you@example.com     # alerts at $5/$15/$30/$45
#  4. Console → Billing → Cost Anomaly Detection → AWS Services monitor (free)
#  5. Console → Bedrock → Model access → request Nova Micro, Nova Lite,
#     Titan Embeddings V2, Claude Sonnet
#  6. make aws-preflight                        # green before Day 1
```

**Do step 5 tonight, not tomorrow morning.** Bedrock model access is not granted by default
and approval is not always instant.

---

## Curriculum at a glance

| Week | Dates | Theme | Ships | AWS lane |
|---|---|---|---|---|
| **1** | Aug 27 – Sep 3 | Foundations: environment, Python for AI, embeddings, RAG, first evals | A working, evaluated RAG app with a UI | Bedrock as a fourth backend · Titan embeddings · S3 Vectors · Knowledge Bases · Bedrock Evaluations |
| **2** | Sep 4 – Sep 11 | Agents: tool calling, agentic RAG, multi-agent, memory, MCP | A multi-agent research assistant + your own MCP server | Converse tool use · AgentCore Runtime, Memory, Gateway · MCP tools on Lambda |
| **3** | Sep 14 – Sep 21 | Production: evals at depth, advanced retrieval, serving, observability, deploy, security | A deployed, traced, guardrailed API with a cost model | Guardrails · Lambda + HTTP API · CloudWatch + X-Ray · ECS Fargate · IAM/VPC · **SageMaker GPU + break-even** |
| **4** | Sep 22 – Sep 29 | The FDE + Trainer craft: discovery, capstone, curriculum design, demo day | Capstone app + a 60-min lesson you can actually deliver | AWS-shaped discovery · capstone on AWS · teardown drill · build-vs-buy framework |

Full day-by-day breakdown is in the course hub and in `labs/`.

---

## Coverage benchmark

Nothing here depends on enrolling anywhere. But it's worth checking your coverage against a
published industry syllabus, so you can say — accurately, to an employer or an audience —
that you've covered the standard body of knowledge. The AI Makerspace *AI FDE Certification*
(v1.1, 2026) is a reasonable yardstick because its module list is public and current:

| Benchmark module | Covered here |
|---|---|
| 01 Retrieval Foundations | Days 3–4 |
| 02 Agentic RAG | Days 7–8 |
| 03 Multi-Agent Systems | Day 9, 12 |
| 04 Memory & Context | Day 10 |
| 05 Evals | Days 5, 13 |
| 06 Advanced Retrieval & Skills | Days 11, 14 |
| 07 End-to-End Systems | Days 6, 12, 20–21 |
| 08 Production I (servers, guardrails, caching) | Days 15–17 |
| 09 Production II (cost vs. performance) | Day 18 |
| 10 The Edge (simulation, emerging tools) | Days 18–19 |

Every row is covered by something you **built and measured**, not something you watched. That
distinction is the whole argument for hiring you — and, if you ever choose to approach a
training programme, for letting you teach it rather than take it.

Where this course goes further than the benchmark: discovery and scoping (Day 19), curriculum
design and live delivery (Days 22–23), and the FDE handover discipline (Day 17). Where it
deliberately doesn't go: fine-tuning, self-hosted GPU serving, and multimodal. Those are named
as gaps in your Day 24 plan rather than skipped silently.
