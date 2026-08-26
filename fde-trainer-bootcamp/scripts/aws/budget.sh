#!/usr/bin/env bash
# Create the $50 course budget with four alert thresholds, plus an SNS email topic.
#   bash scripts/aws/budget.sh you@example.com
#
# Read AWS_COST_DISCIPLINE.md before trusting this: budget alerts are NOTIFICATION,
# not a cap. Cost Explorer lags up to 24 hours. The only zero-latency control is
# `make aws-nuke`.
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/_common.sh"
need_aws

EMAIL="${1:-}"
[ -n "$EMAIL" ] || die "Usage: bash scripts/aws/budget.sh you@example.com"

ACC="$(account_id)"
BUDGET_NAME="fde-bootcamp-50"
LIMIT="${FDE_BUDGET_USD:-50}"
TOPIC="fde-bootcamp-budget-alerts"

# ── SNS topic ───────────────────────────────────────────────────────────────
say "SNS topic for alerts"
TOPIC_ARN="$(aws sns create-topic --name "$TOPIC" --query TopicArn --output text)"
ok "$TOPIC_ARN"

aws sns subscribe --topic-arn "$TOPIC_ARN" --protocol email --notification-endpoint "$EMAIL" >/dev/null
warn "Check $EMAIL and confirm the subscription — unconfirmed means no alerts."

# Budgets must be allowed to publish to the topic.
POLICY=$(cat <<JSON
{"Version":"2012-10-17","Statement":[{
  "Sid":"AllowBudgets","Effect":"Allow",
  "Principal":{"Service":"budgets.amazonaws.com"},
  "Action":"SNS:Publish","Resource":"$TOPIC_ARN"
}]}
JSON
)
aws sns set-topic-attributes --topic-arn "$TOPIC_ARN" \
  --attribute-name Policy --attribute-value "$POLICY" >/dev/null
ok "topic policy allows budgets.amazonaws.com"

# ── budget + notifications ──────────────────────────────────────────────────
say "Budget '$BUDGET_NAME' at \$$LIMIT/month"

BUDGET_JSON=$(cat <<JSON
{
  "BudgetName": "$BUDGET_NAME",
  "BudgetLimit": {"Amount": "$LIMIT", "Unit": "USD"},
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST",
  "CostTypes": {
    "IncludeTax": true, "IncludeSubscription": true, "UseBlended": false,
    "IncludeRefund": false, "IncludeCredit": false, "IncludeUpfront": true,
    "IncludeRecurring": true, "IncludeOtherSubscription": true,
    "IncludeSupport": true, "IncludeDiscount": true, "UseAmortized": false
  }
}
JSON
)

# Note IncludeCredit:false — you want to see REAL spend, not spend-after-credits.
# Credits run out; the habit of watching gross cost should not.

mk_notif() {  # mk_notif <threshold> <ACTUAL|FORECASTED>
  cat <<JSON
{"NotificationType":"$2","ComparisonOperator":"GREATER_THAN","Threshold":$1,"ThresholdType":"PERCENTAGE","NotificationState":"ALARM"}
JSON
}
SUBS="[{\"SubscriptionType\":\"SNS\",\"Address\":\"$TOPIC_ARN\"},{\"SubscriptionType\":\"EMAIL\",\"Address\":\"$EMAIL\"}]"

if aws budgets describe-budget --account-id "$ACC" --budget-name "$BUDGET_NAME" >/dev/null 2>&1; then
  aws budgets update-budget --account-id "$ACC" --new-budget "$BUDGET_JSON" >/dev/null && ok "budget updated"
else
  aws budgets create-budget --account-id "$ACC" --budget "$BUDGET_JSON" >/dev/null && ok "budget created"
fi

# $5 / $15 / $30 / $45 on a $50 budget = 10 / 30 / 60 / 90 percent
for pct in 10 30 60 90; do
  for kind in ACTUAL FORECASTED; do
    aws budgets create-notification \
      --account-id "$ACC" --budget-name "$BUDGET_NAME" \
      --notification "$(mk_notif "$pct" "$kind")" \
      --subscribers "$SUBS" >/dev/null 2>&1 \
      && ok "alert  ${kind}  ${pct}%  (\$$(awk -v l="$LIMIT" -v p="$pct" 'BEGIN{printf "%.0f", l*p/100}'))" \
      || dim "alert  ${kind}  ${pct}%  already exists"
  done
done

say "Next, in the console"
dim "Billing > Cost Anomaly Detection > create an 'AWS Services' monitor. It is free."
dim "It needs ~24h to activate and ~10 days of history to baseline."
printf "\n"
warn "Budgets NOTIFY, they do not CAP. Cost Explorer lags up to 24h."
warn "A forgotten ml.g5.xlarge bills ~\$34 before an alert fires. 'make aws-nuke' is the real control."
