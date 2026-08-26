# AWS Setup — macOS, 45 minutes, before Day 1

Everything here is written for macOS (Apple Silicon or Intel). Where a command differs from
the Linux version you'd find in most tutorials, it's called out — those differences are a
recurring source of copy-paste failures, and knowing them is useful when you're pairing with
a client engineer on a Mac.

---

## 1. Tooling (10 min)

```bash
brew install awscli jq
brew install --cask session-manager-plugin   # only if you do the ECS lab on Day 17

aws --version     # want aws-cli/2.x — v1 is missing SSO and half the Bedrock commands
jq --version
```

If `aws --version` reports 1.x, you have a pip-installed v1 shadowing brew's v2:

```bash
which -a aws                    # note: `which -a`, not `which` — you want ALL matches
pip3 uninstall awscli           # then reopen your terminal
```

**Apple Silicon note.** Homebrew installs to `/opt/homebrew` on Apple Silicon and
`/usr/local` on Intel. If `aws` isn't found after install, your `PATH` is missing the ARM
prefix:

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
exec zsh -l
```

**macOS ships bash 3.2** (from 2007, for licensing reasons) as `/bin/bash`. Every script in
this repo is written to run on it — no associative arrays, no `${var,,}`, no `mapfile`. If
you write your own, either stay 3.2-compatible or `brew install bash` and use
`#!/usr/bin/env bash` with `/opt/homebrew/bin` ahead on your PATH.

---

## 2. The account — choose the Free plan (10 min)

AWS changed the Free Tier to a credit model on 15 July 2025. At signup you pick a plan, and
**the choice matters enormously for a hard-budget course**:

| | **Free plan** ← choose this | Paid plan |
|---|---|---|
| Charges | None unless you upgrade or activate a paid-only service | Pay beyond credits |
| Credits | Up to $200 ($100 at signup + up to $100 for completing activities), valid 6 months | Same |
| Services | Limited to select services | All services |
| When credits run out | **Account closes automatically** | You keep being billed |

That auto-close is the closest thing AWS has to a hard spending cap, and it's why the Free
plan is the right choice here even though it restricts services.

> **Check this yourself, first thing:** confirm that **Bedrock, S3 Vectors, and AgentCore** are
> available on the Free plan in your account. If any of them are paid-only, you'll need the
> Paid plan — in which case the budget guardrails in section 4 become the only thing standing
> between you and an unpleasant invoice. Either way, know which situation you're in before
> Day 1 rather than discovering it mid-lab.

If you already have a personal AWS account, use it — but assume none of the credits and set
the budgets in section 4 today.

---

## 3. Identity — stop using root (10 min)

```bash
# In the console: IAM Identity Center → Enable
# Create a user (your email), add to a group, attach AdministratorAccess for now.
# Then, on the Mac:

aws configure sso
#   SSO session name:        fde-sso
#   SSO start URL:           https://d-xxxxxxxxxx.awsapps.com/start
#   SSO region:              us-east-1
#   Registered scopes:       (accept default)
#   → browser opens, approve
#   CLI default client Region: us-east-1
#   CLI default output format: json
#   CLI profile name:        fde

aws sso login --profile fde
aws sts get-caller-identity --profile fde
```

Add to `~/.zshrc` so every terminal is already pointed at the right profile:

```bash
export AWS_PROFILE=fde
export AWS_REGION=us-east-1
```

**Region: use `us-east-1`.** Not because it's best — it usually isn't — but because it gets
new Bedrock models first, and this course cares about model availability more than latency.
When you do this at a client, region choice is a data-residency conversation, not a default.

SSO sessions expire (typically 8–12 hours). When a lab suddenly 403s mid-morning, it's almost
always this: `aws sso login --profile fde`. Put it in your muscle memory now — it will happen
on Day 1 and you should recognise it instantly rather than debugging your code.

---

## 4. Budget guardrails (10 min) — do this before anything else costs money

Run the script, which creates four thresholds and an SNS topic that emails you:

```bash
bash scripts/aws/budget.sh you@example.com
```

It sets alerts at **$5 / $15 / $30 / $45** on a $50 monthly budget, both actual and forecast.

Then, in the console: **Billing → Cost Anomaly Detection → create an AWS Services monitor.**
Free, and it catches the shape of problem a threshold misses — a service that suddenly starts
costing money it never did before.

### The uncomfortable truth to internalise now

**AWS has no hard spending cap.** Budgets and Cost Anomaly Detection both read Cost Explorer,
which has **up to 24 hours of latency**. A forgotten `ml.g5.xlarge` endpoint can bill roughly
**$34 before your budget even notices**. Budget *Actions* can apply a restrictive IAM policy
or SCP, or stop EC2/RDS instances — but applying a deny policy does not terminate a running
Fargate task, SageMaker endpoint, or OpenSearch collection. Those keep billing.

So the real guardrail is not a service. It is:

1. The Free-plan account (auto-closes when credits are exhausted)
2. Budget alerts, so you find out in a day rather than a month
3. Cost Anomaly Detection, for the shape you didn't predict
4. **`make aws-nuke` at the end of every AWS lab** — the only mechanism with zero latency
5. Explicit CloudWatch log retention on every log group you create

Say all five out loud when you teach this. Engineers who believe a budget is a cap are
the ones who get the surprise invoice, and correcting that belief is genuinely useful.

---

## 5. Bedrock model access (5 min) — do this tonight, not tomorrow morning

Console → **Bedrock → Model access → Modify model access**. Request:

- **Amazon Nova Micro** and **Nova Lite** — your default workhorses ($0.08/$0.24 and $0.30/$0.90 per 1M)
- **Amazon Titan Text Embeddings V2** — embeddings, fractions of a cent at this scale
- **Anthropic Claude Sonnet** (current version) — for judging and demos only
- **Anthropic Claude Haiku** — cheaper judge alternative if Sonnet strains the budget

Access is not granted by default and approval isn't always instant. Requesting the night
before is the difference between starting Day 1 and waiting on Day 1.

Verify from the Mac:

```bash
aws bedrock list-foundation-models --region us-east-1 \
  --query 'modelSummaries[?contains(modelId,`nova`)||contains(modelId,`claude`)].modelId' \
  --output table
```

---

## 6. Preflight

```bash
bash scripts/aws/preflight.sh
```

Green across the board before Day 1. It checks: CLI version, SSO session validity, region,
caller identity, Bedrock model access, S3 Vectors availability, budget existence, and that
`make aws-nuke` is wired up.

---

## The three commands you will run constantly

```bash
make aws-cost     # every morning, before the lab — 30 seconds
make aws-nuke     # end of every AWS lab — every time, even when you're sure
aws sso login     # when something 403s for no reason
```

---

## macOS gotchas that will bite you in these labs

These are the ones that actually come up. Most AWS blog posts are written on Linux.

| Thing | Linux | **macOS** |
|---|---|---|
| In-place sed | `sed -i 's/a/b/' f` | `sed -i '' 's/a/b/' f` — the empty string is required |
| Date arithmetic | `date -d '-7 days' +%F` | `date -v-7d +%F` |
| ISO timestamp | `date -Is` | `date -u +%Y-%m-%dT%H:%M:%SZ` |
| base64 no-wrap | `base64 -w0` | `base64` (already unwrapped) |
| Resolve a path | `readlink -f p` | `python3 -c 'import os,sys;print(os.path.realpath(sys.argv[1]))' p` |
| Stat file size | `stat -c%s f` | `stat -f%z f` |
| `bash` version | 5.x | **3.2** — no assoc arrays, no `${v,,}`, no `mapfile` |
| Default shell | bash | **zsh** — `~/.zshrc`, and unquoted globs error instead of passing through |

All the scripts in `scripts/aws/` already handle these. The table is here because you will
copy a command off an AWS blog post at some point and it will fail confusingly, and because
it's a nice small thing to know when pairing with a client's Mac-using engineer.

**Docker on macOS** (Day 17): Docker Desktop on Apple Silicon builds ARM64 images by default.
ECS Fargate supports ARM64 and it's ~20% cheaper — so prefer it. But if you ever need x86:

```bash
docker buildx build --platform linux/amd64 -t myimg .
```

An ARM image deployed to an x86 task definition fails with an exec-format error that reads
like a corrupt binary. It isn't. It's architecture, and now you'll recognise it.
