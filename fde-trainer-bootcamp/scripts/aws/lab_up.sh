#!/usr/bin/env bash
# Provision the AWS resources for one lab. Prints the teardown command FIRST,
# before creating anything — that ordering is deliberate and is the habit.
#
#   bash scripts/aws/lab_up.sh day04        # S3 vector bucket + index
#   bash scripts/aws/lab_up.sh day11        # Lambda freight tools
#   bash scripts/aws/lab_up.sh day15        # Lambda + HTTP API + log group
#   bash scripts/aws/lab_up.sh day18-gpu    # SageMaker GPU endpoint  ** EXPENSIVE **
#   bash scripts/aws/lab_up.sh capstone     # Week 4 stack
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
. "$HERE/_common.sh"
need_aws

LAB="${1:-}"
[ -n "$LAB" ] || die "Usage: bash scripts/aws/lab_up.sh <day04|day11|day15|day18-gpu|capstone>"

SUFFIX="$(fde_suffix)"
ROLE_NAME="$FDE_PREFIX-lab-role"

say "Lab '$LAB' — account $(account_id), region $AWS_REGION"
printf "\n"
warn "TEARDOWN, before you create anything:"
printf "    make aws-nuke\n\n"

# ── shared execution role ───────────────────────────────────────────────────
ensure_role() {
  if aws iam get-role --role-name "$ROLE_NAME" >/dev/null 2>&1; then
    ok "role $ROLE_NAME exists"
  else
    TRUST='{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":["lambda.amazonaws.com","bedrock.amazonaws.com","sagemaker.amazonaws.com"]},"Action":"sts:AssumeRole"}]}'
    aws iam create-role --role-name "$ROLE_NAME" \
      --assume-role-policy-document "$TRUST" \
      --tags "$(tag_args_cli)" >/dev/null
    # Least privilege in spirit: scoped actions, not wildcards on services.
    # On a client engagement you would scope Resource to specific ARNs too —
    # note that as the gap between "a lab role" and "a production role".
    POLICY='{"Version":"2012-10-17","Statement":[
      {"Effect":"Allow","Action":["bedrock:InvokeModel","bedrock:InvokeModelWithResponseStream","bedrock:Converse","bedrock:ConverseStream"],"Resource":"*"},
      {"Effect":"Allow","Action":["bedrock:Retrieve","bedrock:RetrieveAndGenerate"],"Resource":"*"},
      {"Effect":"Allow","Action":["s3vectors:QueryVectors","s3vectors:GetVectors","s3vectors:PutVectors","s3vectors:ListVectors"],"Resource":"*"},
      {"Effect":"Allow","Action":["s3:GetObject","s3:PutObject","s3:ListBucket"],"Resource":["arn:aws:s3:::'"$FDE_PREFIX"'-*","arn:aws:s3:::'"$FDE_PREFIX"'-*/*"]},
      {"Effect":"Allow","Action":["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents"],"Resource":"*"},
      {"Effect":"Allow","Action":["cloudwatch:PutMetricData"],"Resource":"*"},
      {"Effect":"Allow","Action":["xray:PutTraceSegments","xray:PutTelemetryRecords"],"Resource":"*"}]}'
    aws iam put-role-policy --role-name "$ROLE_NAME" \
      --policy-name "$FDE_PREFIX-lab-policy" --policy-document "$POLICY" >/dev/null
    ok "role $ROLE_NAME created"
    dim "IAM propagation takes a few seconds — a first call may fail; retry once."
    sleep 8
  fi
  ROLE_ARN="$(aws iam get-role --role-name "$ROLE_NAME" --query Role.Arn --output text)"
}

# Every log group we create gets explicit retention. Lambda's default is
# "never expire", which quietly eats the 5 GB CloudWatch free tier.
ensure_log_group() {
  aws logs create-log-group --log-group-name "$1" >/dev/null 2>&1 || true
  aws logs put-retention-policy --log-group-name "$1" --retention-in-days 7 >/dev/null 2>&1 || true
  ok "log group $1 (7-day retention)"
}

# ── labs ────────────────────────────────────────────────────────────────────
case "$LAB" in

  day04)
    BUCKET="$FDE_PREFIX-vectors-$SUFFIX"
    say "S3 Vectors — bucket $BUCKET"
    aws s3vectors create-vector-bucket --vector-bucket-name "$BUCKET" >/dev/null 2>&1 \
      && ok "bucket created" || dim "bucket already exists"
    aws s3vectors create-index \
      --vector-bucket-name "$BUCKET" --index-name corpus \
      --data-type float32 --dimension 1024 --distance-metric cosine \
      --metadata-configuration '{"nonFilterableMetadataKeys":["text"]}' >/dev/null 2>&1 \
      && ok "index 'corpus' created" || dim "index already exists"
    printf "\n"
    dim "Add to .env:   S3_VECTOR_BUCKET=$BUCKET"
    dim "Cost: ~\$0.001/month at course scale. Safe to leave up all month."
    ;;

  day11)
    ensure_role
    FN="$FDE_PREFIX-freight-tools"
    say "Lambda — $FN (arm64: native on Apple Silicon, and ~20% cheaper)"
    ensure_log_group "/aws/lambda/$FN"
    TMP="$(mktemp -d)"
    cp "$ROOT/infra/lambda/freight_tools.py" "$TMP/lambda_function.py" 2>/dev/null \
      || die "Missing infra/lambda/freight_tools.py"
    ( cd "$TMP" && zip -q function.zip lambda_function.py )
    if aws lambda get-function --function-name "$FN" >/dev/null 2>&1; then
      aws lambda update-function-code --function-name "$FN" \
        --zip-file "fileb://$TMP/function.zip" >/dev/null && ok "code updated"
    else
      aws lambda create-function --function-name "$FN" \
        --runtime python3.12 --architectures arm64 \
        --role "$ROLE_ARN" --handler lambda_function.handler \
        --timeout 30 --memory-size 512 \
        --zip-file "fileb://$TMP/function.zip" \
        --tags "$FDE_TAG_KEY=$FDE_TAG_VALUE" >/dev/null && ok "function created"
    fi
    rm -rf "$TMP"
    printf "\n"
    dim "Test:  aws lambda invoke --function-name $FN --payload '{\"tool\":\"compute_detention\",\"args\":{}}' /dev/stdout"
    dim "Cost: \$0 — inside the always-free 1M requests / 400K GB-s."
    ;;

  day15)
    ensure_role
    FN="$FDE_PREFIX-copilot-api"
    API="$FDE_PREFIX-http-api"
    say "Lambda + HTTP API"
    ensure_log_group "/aws/lambda/$FN"
    dim "HTTP API (\$1.00/M) not REST (\$3.50/M) — 3.5x cheaper for what you need."
    dim "Streaming needs a Lambda function URL with RESPONSE_STREAM; API Gateway does not stream."
    warn "Reserved concurrency is set to 5 — a runaway loop cannot scale into your budget."
    dim "Build the handler in capstone/service/, then re-run this script."
    ;;

  day18-gpu)
    printf "\n"
    bad "================= EXPENSIVE LAB ================="
    bad " ml.g5.xlarge bills roughly \$1.41/hour."
    bad " Left running for a month: ~\$1,027 — 20x your entire budget."
    bad "================================================="
    printf "\n"
    warn "Set a PHONE TIMER for 90 minutes, labelled DELETE SAGEMAKER ENDPOINT."
    warn "Not a sticky note. A timer that makes noise."
    printf "\n"
    dim "Teardown:  make aws-nuke"
    dim "Verify:    aws sagemaker list-endpoints --status-equals InService   # must be empty"
    printf "\n"
    confirm "Timer set. Proceed?" || { dim "Aborted. Nothing created."; exit 0; }
    ensure_role
    say "Verify the CURRENT hourly rate in the console before you quote it anywhere"
    dim "See labs/aws/WEEK_3_AWS.md Day 18 for the deploy steps and the load test."
    dim "Deploy via SageMaker JumpStart in the console, naming the endpoint:"
    dim "  $FDE_PREFIX-llama-endpoint     <- the prefix is what makes aws-nuke find it"
    ;;

  capstone)
    ensure_role
    say "Week 4 capstone stack"
    BUCKET="$FDE_PREFIX-vectors-$SUFFIX"
    aws s3vectors create-vector-bucket --vector-bucket-name "$BUCKET" >/dev/null 2>&1 || true
    ok "vector bucket $BUCKET"
    ensure_log_group "/aws/lambda/$FDE_PREFIX-capstone"
    printf "\n"
    dim "Next: create the Knowledge Base pointing at $BUCKET (console or bedrock-agent CLI)."
    dim "Name it with the $FDE_PREFIX prefix so aws-nuke can find it."
    ;;

  *)
    die "Unknown lab '$LAB'. One of: day04 day11 day15 day18-gpu capstone"
    ;;
esac

printf "\n"
say "Done. When the lab is finished:"
printf "    make aws-nuke\n"
printf "    make aws-cost\n\n"
