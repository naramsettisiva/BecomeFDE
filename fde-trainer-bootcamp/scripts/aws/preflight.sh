#!/usr/bin/env bash
# AWS lane preflight. Run before Day 1, and any time something behaves oddly.
#   bash scripts/aws/preflight.sh
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/_common.sh"

FAILS=0
WARNS=0
f() { bad "$1"; FAILS=$((FAILS+1)); }
w() { warn "$1"; WARNS=$((WARNS+1)); }

say "AWS lane preflight — profile=$AWS_PROFILE region=$AWS_REGION"

# ── 1. macOS + tooling ──────────────────────────────────────────────────────
if [ "$(uname -s)" = "Darwin" ]; then
  ok "macOS $(sw_vers -productVersion) on $(uname -m)"
else
  w "Not macOS. Course commands assume BSD date/sed; adjust as you go."
fi

if command -v brew >/dev/null 2>&1; then ok "homebrew $(brew --version | head -1 | awk '{print $2}')"
else f "homebrew missing — https://brew.sh"; fi

if command -v aws >/dev/null 2>&1; then
  V="$(aws --version 2>&1 | awk '{print $1}')"
  case "$V" in aws-cli/2*) ok "$V" ;; *) f "$V — need v2. brew install awscli, remove pip v1 (which -a aws)" ;; esac
else f "aws CLI missing — brew install awscli"; fi

command -v jq >/dev/null 2>&1 && ok "jq $(jq --version)" || f "jq missing — brew install jq"

if python3 -c 'import boto3,sys; sys.stdout.write(boto3.__version__)' >/dev/null 2>&1; then
  ok "boto3 $(python3 -c 'import boto3;print(boto3.__version__)')"
else
  w "boto3 not importable — activate .venv, then: uv pip install -r requirements.txt"
fi

# ── 2. identity ─────────────────────────────────────────────────────────────
if IDENT="$(aws sts get-caller-identity --output json 2>/dev/null)"; then
  ACC="$(printf '%s' "$IDENT" | jq -r .Account)"
  ARN="$(printf '%s' "$IDENT" | jq -r .Arn)"
  ok "account $ACC"
  case "$ARN" in
    *:root) f "You are using ROOT credentials. Stop. Set up IAM Identity Center (AWS_SETUP.md §3)." ;;
    *) ok "identity $(printf '%s' "$ARN" | sed 's#.*/##')" ;;
  esac
else
  f "No valid session. Run: aws sso login --profile $AWS_PROFILE"
fi

[ "$AWS_REGION" = "us-east-1" ] && ok "region us-east-1" \
  || w "region is $AWS_REGION — the course assumes us-east-1 for model availability"

# ── 3. bedrock model access ─────────────────────────────────────────────────
if MODELS="$(aws bedrock list-foundation-models --output json 2>/dev/null)"; then
  ok "bedrock reachable"
  for want in "nova-micro" "nova-lite" "titan-embed-text-v2" "claude"; do
    if printf '%s' "$MODELS" | jq -e --arg m "$want" \
        '.modelSummaries[] | select(.modelId | contains($m))' >/dev/null 2>&1; then
      ok "model visible: $want"
    else
      w "model not visible: $want — Bedrock console > Model access > Modify"
    fi
  done
else
  f "Cannot list Bedrock models. Check region and that Bedrock is enabled for this account."
fi

# Actually invoke the cheapest model — listing a model is not the same as being
# granted access to it, and that distinction costs people an hour on day one.
say "Invoking Nova Micro (costs about \$0.000002)"
# `converse` rather than `invoke-model`: one message shape across every Bedrock
# model, and no base64 body encoding to get wrong. This is the API the course uses.
if OUT="$(aws bedrock-runtime converse \
      --model-id amazon.nova-micro-v1:0 \
      --messages '[{"role":"user","content":[{"text":"Reply with exactly: pong"}]}]' \
      --inference-config '{"maxTokens":8,"temperature":0}' \
      --output json 2>/dev/null | jq -r '.output.message.content[0].text' 2>/dev/null)"; then
  [ -n "$OUT" ] && ok "nova-micro responded: $(printf '%s' "$OUT" | tr -d '\n' | head -c 30)" \
                || f "nova-micro returned an empty response"
else
  f "nova-micro invoke failed — model access not granted yet, or wrong region"
fi

# ── 4. s3 vectors ───────────────────────────────────────────────────────────
if aws s3vectors list-vector-buckets --max-results 1 >/dev/null 2>&1; then
  ok "s3vectors API available"
else
  w "s3vectors API not available — check CLI version (needs a recent v2) and region support"
fi

# ── 5. budget guardrails ────────────────────────────────────────────────────
if [ -n "${ACC:-}" ]; then
  if aws budgets describe-budgets --account-id "$ACC" --output json 2>/dev/null \
       | jq -e '.Budgets[] | select(.BudgetName=="fde-bootcamp-50")' >/dev/null 2>&1; then
    ok "budget 'fde-bootcamp-50' exists"
  else
    f "No budget set. Run: bash scripts/aws/budget.sh you@example.com"
  fi
fi

# ── 6. teardown wired up ────────────────────────────────────────────────────
[ -x "$HERE/nuke.sh" ] && ok "teardown script present" || f "scripts/aws/nuke.sh missing or not executable"

# ── verdict ─────────────────────────────────────────────────────────────────
say "Result"
printf "  %s fail · %s warn\n\n" "$FAILS" "$WARNS"
if [ "$FAILS" -gt 0 ]; then
  dim "Fix the failures before starting the AWS lane."
  exit 1
fi
dim "Green. Run 'make aws-cost' each morning and 'make aws-nuke' after every AWS lab."
