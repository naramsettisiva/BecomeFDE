#!/usr/bin/env bash
# Month-to-date AWS spend by service, against the $50 course budget.
# Run this every morning before the lab. Takes about 30 seconds.
#   bash scripts/aws/cost.sh [days_of_daily_detail]
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/_common.sh"
need_aws

BUDGET="${FDE_BUDGET_USD:-50}"
DETAIL_DAYS="${1:-7}"

START="$(month_start)"
END="$(tomorrow)"     # Cost Explorer End is exclusive

say "Month to date  $START → $(today)   (Cost Explorer lags up to 24h)"

MTD="$(aws ce get-cost-and-usage \
        --time-period Start="$START",End="$END" \
        --granularity MONTHLY --metrics UnblendedCost \
        --group-by Type=DIMENSION,Key=SERVICE \
        --output json 2>/dev/null)" || die "Cost Explorer call failed. Is it enabled? (Billing > Cost Explorer)"

TOTAL="$(printf '%s' "$MTD" | jq '[.ResultsByTime[].Groups[].Metrics.UnblendedCost.Amount|tonumber] | add // 0')"

printf '%s' "$MTD" | jq -r '
  [.ResultsByTime[].Groups[]
   | {svc: .Keys[0], amt: (.Metrics.UnblendedCost.Amount|tonumber)}]
  | map(select(.amt > 0.0001))
  | sort_by(-.amt)
  | .[]
  | [(.amt*100|round/100), .svc] | @tsv
' 2>/dev/null | awk -F'\t' '{ printf "  %8.2f   %s\n", $1, $2 }' || true

PCT="$(printf '%s %s' "$TOTAL" "$BUDGET" | awk '{ if ($2>0) printf "%.0f", ($1/$2)*100; else print 0 }')"
BAR="$(printf '%s' "$PCT" | awk '{n=int($1/5); s=""; for(i=0;i<n && i<20;i++) s=s "█"; for(i=n;i<20;i++) s=s "·"; print s}')"

printf '\n  %s  $%.2f of $%s  (%s%%)\n' "$BAR" "$TOTAL" "$BUDGET" "$PCT"

if awk -v t="$TOTAL" -v b="$BUDGET" 'BEGIN{exit !(t > b*0.8)}'; then
  warn "Over 80% of budget. Read labs/aws/AWS_COST_DISCIPLINE.md — drop the SageMaker lab to a design exercise."
fi

# ── daily detail, to spot the day a number changed shape ────────────────────
say "Last $DETAIL_DAYS days"
DSTART="$(days_ago "$DETAIL_DAYS")"
aws ce get-cost-and-usage \
  --time-period Start="$DSTART",End="$END" \
  --granularity DAILY --metrics UnblendedCost \
  --output json 2>/dev/null \
| jq -r '.ResultsByTime[]
    | "  \(.TimePeriod.Start)   $\(.Total.UnblendedCost.Amount|tonumber|.*100|round/100)"' 2>/dev/null || true

# ── the resources that would actually hurt ──────────────────────────────────
say "Expensive-if-forgotten check"

N="$(aws sagemaker list-endpoints --status-equals InService \
      --query 'length(Endpoints)' --output text 2>/dev/null || echo 0)"
[ "$N" = "0" ] && ok "SageMaker endpoints: none" || bad "SageMaker endpoints IN SERVICE: $N  (~\$1,000/mo each) → make aws-nuke"

N="$(aws opensearchserverless list-collections \
      --query 'length(collectionSummaries)' --output text 2>/dev/null || echo 0)"
[ "$N" = "0" ] && ok "OpenSearch Serverless collections: none" || bad "OpenSearch collections: $N  (classic = ~\$350/mo) → check type, then nuke"

N="$(aws kendra list-indices --query 'length(IndexConfigurationSummaryItems)' --output text 2>/dev/null || echo 0)"
[ "$N" = "0" ] && ok "Kendra indices: none" || bad "Kendra indices: $N  (~\$230+/mo) → make aws-nuke"

RUNNING="$(aws ecs list-clusters --query 'clusterArns' --output text 2>/dev/null | tr '\t' '\n' | while read -r c; do
  [ -z "$c" ] && continue
  aws ecs list-services --cluster "$c" --query 'serviceArns' --output text 2>/dev/null | tr '\t' '\n'
done | grep -c . 2>/dev/null || echo 0)"
[ "${RUNNING:-0}" = "0" ] && ok "ECS services: none" || warn "ECS services: $RUNNING  (~\$9/mo each at min size)"

printf '\n'
dim "If a number surprises you, chase it before writing code today."
