#!/usr/bin/env bash
# Delete everything the bootcamp could have created. Run after EVERY AWS lab.
#
#   bash scripts/aws/nuke.sh          # interactive, shows what it will delete
#   bash scripts/aws/nuke.sh --yes    # no prompt (use in a lab teardown)
#   bash scripts/aws/nuke.sh --dry    # list only
#
# Scope: resources named with the 'fde-bootcamp' prefix, or tagged
# Project=fde-bootcamp. It will not touch anything else in the account.
#
# This script is deliberately verbose about what it finds. The habit you want is
# reading the list, not trusting it.
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/_common.sh"
need_aws

MODE="interactive"
case "${1:-}" in
  --yes|-y) MODE="yes" ;;
  --dry|-n) MODE="dry" ;;
esac

FOUND=0
note() { FOUND=$((FOUND+1)); printf "  %s· %s%s\n" "$C_WARN" "$1" "$C_0"; }

run() {
  # run <description> <command...>
  desc="$1"; shift
  if [ "$MODE" = "dry" ]; then
    dim "would: $desc"
    return 0
  fi
  if "$@" >/dev/null 2>&1; then ok "deleted: $desc"; else bad "failed:  $desc"; fi
}

say "Scanning for bootcamp resources — account $(account_id), region $AWS_REGION"

# ── 1. SageMaker: endpoints first, they are the expensive ones ──────────────
EPS="$(aws sagemaker list-endpoints --output json 2>/dev/null \
        | jq -r '.Endpoints[]?.EndpointName' | grep "^$FDE_PREFIX" || true)"
for e in $EPS; do note "SageMaker endpoint $e  (~\$1,000/mo)"; done

ECFGS="$(aws sagemaker list-endpoint-configs --output json 2>/dev/null \
        | jq -r '.EndpointConfigs[]?.EndpointConfigName' | grep "^$FDE_PREFIX" || true)"
for c in $ECFGS; do note "SageMaker endpoint-config $c"; done

SMODELS="$(aws sagemaker list-models --output json 2>/dev/null \
        | jq -r '.Models[]?.ModelName' | grep "^$FDE_PREFIX" || true)"
for m in $SMODELS; do note "SageMaker model $m"; done

# ── 2. OpenSearch Serverless ────────────────────────────────────────────────
COLLS="$(aws opensearchserverless list-collections --output json 2>/dev/null \
        | jq -r '.collectionSummaries[]?.name' | grep "^$FDE_PREFIX" || true)"
for c in $COLLS; do note "OpenSearch Serverless collection $c  (classic = ~\$350/mo)"; done

# ── 3. Kendra ───────────────────────────────────────────────────────────────
KIDX="$(aws kendra list-indices --output json 2>/dev/null \
        | jq -r '.IndexConfigurationSummaryItems[]? | select(.Name|startswith("'"$FDE_PREFIX"'")) | .Id' || true)"
for i in $KIDX; do note "Kendra index $i  (~\$230+/mo)"; done

# ── 4. Bedrock knowledge bases + agents ─────────────────────────────────────
KBS="$(aws bedrock-agent list-knowledge-bases --output json 2>/dev/null \
        | jq -r '.knowledgeBaseSummaries[]? | select(.name|startswith("'"$FDE_PREFIX"'")) | .knowledgeBaseId' || true)"
for k in $KBS; do note "Bedrock knowledge base $k"; done

GRDS="$(aws bedrock list-guardrails --output json 2>/dev/null \
        | jq -r '.guardrails[]? | select(.name|startswith("'"$FDE_PREFIX"'")) | .id' || true)"
for g in $GRDS; do note "Bedrock guardrail $g"; done

# ── 5. AgentCore (runtimes, gateways, memories) ─────────────────────────────
# Memory is the one with recurring monthly storage cost — always clear it.
ACR="$(aws bedrock-agentcore-control list-agent-runtimes --output json 2>/dev/null \
        | jq -r '.agentRuntimes[]? | select(.agentRuntimeName|startswith("'"$FDE_PREFIX"'")) | .agentRuntimeId' || true)"
for a in $ACR; do note "AgentCore runtime $a"; done

ACM="$(aws bedrock-agentcore-control list-memories --output json 2>/dev/null \
        | jq -r '.memories[]? | select(.id|startswith("'"$FDE_PREFIX"'")) | .id' || true)"
for m in $ACM; do note "AgentCore memory $m  (recurring \$0.75/1K records/mo)"; done

ACG="$(aws bedrock-agentcore-control list-gateways --output json 2>/dev/null \
        | jq -r '.items[]? | select(.name|startswith("'"$FDE_PREFIX"'")) | .gatewayIdentifier' || true)"
for g in $ACG; do note "AgentCore gateway $g"; done

# ── 6. ECS ──────────────────────────────────────────────────────────────────
CLUSTERS="$(aws ecs list-clusters --output json 2>/dev/null \
        | jq -r '.clusterArns[]?' | grep "$FDE_PREFIX" || true)"
for c in $CLUSTERS; do note "ECS cluster $(basename "$c")"; done

# ── 7. Lambda + API Gateway ─────────────────────────────────────────────────
FNS="$(aws lambda list-functions --output json 2>/dev/null \
        | jq -r '.Functions[]?.FunctionName' | grep "^$FDE_PREFIX" || true)"
for f in $FNS; do note "Lambda function $f"; done

APIS="$(aws apigatewayv2 get-apis --output json 2>/dev/null \
        | jq -r '.Items[]? | select(.Name|startswith("'"$FDE_PREFIX"'")) | .ApiId' || true)"
for a in $APIS; do note "HTTP API $a"; done

# ── 8. S3 Vectors + S3 (cheap, but tidy) ────────────────────────────────────
VBS="$(aws s3vectors list-vector-buckets --output json 2>/dev/null \
        | jq -r '.vectorBuckets[]?.vectorBucketName' | grep "^$FDE_PREFIX" || true)"
for b in $VBS; do note "S3 vector bucket $b  (cheap — keep unless done)"; done

# ── 9. CloudWatch log groups (retention safety) ──────────────────────────────
LGS="$(aws logs describe-log-groups --output json 2>/dev/null \
        | jq -r '.logGroups[]? | select(.logGroupName|contains("'"$FDE_PREFIX"'")) | .logGroupName' || true)"
for l in $LGS; do note "Log group $l"; done

# ── decide ──────────────────────────────────────────────────────────────────
if [ "$FOUND" -eq 0 ]; then
  say "Nothing found. Clean."
  dim "Run this even when you expect nothing — that is how it becomes reflex."
  exit 0
fi

printf "\n"
say "$FOUND resource(s) above"

if [ "$MODE" = "dry" ]; then dim "Dry run. Nothing deleted."; exit 0; fi
if [ "$MODE" = "interactive" ]; then
  confirm "Delete all of the above?" || { dim "Aborted. Nothing deleted."; exit 0; }
fi

say "Deleting"

for e in $EPS;    do run "endpoint $e"        aws sagemaker delete-endpoint --endpoint-name "$e"; done
for c in $ECFGS;  do run "endpoint-config $c" aws sagemaker delete-endpoint-config --endpoint-config-name "$c"; done
for m in $SMODELS;do run "model $m"           aws sagemaker delete-model --model-name "$m"; done
for c in $COLLS;  do run "collection $c"      aws opensearchserverless delete-collection --id "$(aws opensearchserverless list-collections --query "collectionSummaries[?name=='$c'].id" --output text)"; done
for i in $KIDX;   do run "kendra index $i"    aws kendra delete-index --id "$i"; done
for k in $KBS;    do run "knowledge base $k"  aws bedrock-agent delete-knowledge-base --knowledge-base-id "$k"; done
for g in $GRDS;   do run "guardrail $g"       aws bedrock delete-guardrail --guardrail-identifier "$g"; done
for a in $ACR;    do run "agentcore runtime $a" aws bedrock-agentcore-control delete-agent-runtime --agent-runtime-id "$a"; done
for m in $ACM;    do run "agentcore memory $m"  aws bedrock-agentcore-control delete-memory --memory-id "$m"; done
for g in $ACG;    do run "agentcore gateway $g" aws bedrock-agentcore-control delete-gateway --gateway-identifier "$g"; done
for f in $FNS;    do run "lambda $f"          aws lambda delete-function --function-name "$f"; done
for a in $APIS;   do run "http api $a"        aws apigatewayv2 delete-api --api-id "$a"; done
for l in $LGS;    do run "log group $l"       aws logs delete-log-group --log-group-name "$l"; done

for c in $CLUSTERS; do
  name="$(basename "$c")"
  for s in $(aws ecs list-services --cluster "$name" --query 'serviceArns[]' --output text 2>/dev/null); do
    run "ecs service $(basename "$s")" aws ecs delete-service --cluster "$name" --service "$s" --force
  done
  run "ecs cluster $name" aws ecs delete-cluster --cluster "$name"
done

# S3 vector buckets need their indexes removed first.
for b in $VBS; do
  for ix in $(aws s3vectors list-indexes --vector-bucket-name "$b" --output json 2>/dev/null | jq -r '.indexes[]?.indexName'); do
    run "vector index $b/$ix" aws s3vectors delete-index --vector-bucket-name "$b" --index-name "$ix"
  done
  run "vector bucket $b" aws s3vectors delete-vector-bucket --vector-bucket-name "$b"
done

say "Done. Verify with: make aws-cost"
dim "Cost Explorer lags up to 24h — a deleted resource can still show yesterday's charge."
