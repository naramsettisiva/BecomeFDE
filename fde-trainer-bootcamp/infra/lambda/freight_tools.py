"""Day 11 — freight operations tools as a Lambda, fronted by AgentCore Gateway.

One function, dispatching on a `tool` key. In production you would usually give
each tool its own function for independent scaling and least-privilege IAM; a
single dispatcher keeps the lab to one deploy, and knowing why you'd split it is
the more useful half of that trade.

Two things here matter beyond the lab:

1. TENANCY IS ENFORCED HERE, NOT IN THE PROMPT.
   `_caller_tenant()` reads identity from the Gateway/JWT context. A prompt
   instruction saying "only use tenant X's data" is not an access control. This
   distinction is the difference between a demo and something a security review
   will pass.

2. ERRORS ARE RETURNED, NOT RAISED.
   A tool error becomes the model's next observation. Raising gives the model a
   stack trace it cannot act on; returning {"error": "..."} with an actionable
   message gets you self-correction for free. Day 7 proved this locally; it is
   just as true across a network boundary.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone

SHIPMENT_RE = re.compile(r"^SHP-\d{6}-\d{7}$")

DETENTION_RATE_USD_PER_HOUR = 65.0
DETENTION_FREE_MINUTES = 120
DETENTION_CAP_USD = 650.0

# Stand-in for a TMS. On an engagement this is a database call — and the shape of
# the seam is the same.
SHIPMENTS = {
    "SHP-202608-0041729": {
        "shipment_id": "SHP-202608-0041729",
        "carrier": "Ridgeline Freight",
        "origin": "DAL",
        "destination": "CHI",
        "equipment": "DRY_VAN",
        "tender_seq": 1,
        "linehaul_usd": 2140.00,
        "status": "DELIVERED",
        "tenant": "acme-foods",
    }
}

SCORECARDS = {
    ("Ridgeline Freight", "2026-08"): {
        "carrier": "Ridgeline Freight",
        "month": "2026-08",
        "on_time_pickup": 17.2,
        "on_time_delivery": 19.8,
        "tender_acceptance": 16.1,
        "billing_accuracy": 13.0,
        "telematics": 12.4,
        "composite": 78.5,
        "band": "Silver",
        "fta_pct": 83.0,
        "tenant": "acme-foods",
    }
}


def _caller_tenant(event: dict) -> str | None:
    """Identity from the request context — never from the model's arguments.

    AgentCore Gateway puts verified JWT claims in requestContext.authorizer.
    If the model could supply this value, it could also fabricate it.
    """
    ctx = event.get("requestContext", {}) or {}
    claims = (ctx.get("authorizer", {}) or {}).get("jwt", {}).get("claims", {})
    return claims.get("custom:tenant") or os.environ.get("DEFAULT_TENANT")


def _ok(payload: dict) -> dict:
    return {"statusCode": 200, "body": json.dumps(payload)}


def _err(message: str, hint: str | None = None) -> dict:
    """Actionable errors. The model reads this and corrects itself."""
    body: dict = {"error": message}
    if hint:
        body["hint"] = hint
    return {"statusCode": 200, "body": json.dumps(body)}


# ── tools ───────────────────────────────────────────────────────────────────
def compute_detention(args: dict, tenant: str | None) -> dict:
    for field in ("arrive_iso", "appt_iso"):
        if field not in args:
            return {"error": f"missing required argument '{field}'",
                    "hint": "ISO 8601 UTC, e.g. 2026-08-24T09:15:00Z"}
    try:
        arrive = datetime.fromisoformat(args["arrive_iso"].replace("Z", "+00:00"))
        appt = datetime.fromisoformat(args["appt_iso"].replace("Z", "+00:00"))
        depart = (
            datetime.fromisoformat(args["depart_iso"].replace("Z", "+00:00"))
            if args.get("depart_iso")
            else datetime.now(timezone.utc)
        )
    except ValueError as exc:
        return {"error": f"could not parse timestamp: {exc}",
                "hint": "Use ISO 8601 UTC, e.g. 2026-08-24T09:15:00Z"}

    free_minutes = int(args.get("free_minutes", DETENTION_FREE_MINUTES))
    rate = float(args.get("rate_usd_per_hour", DETENTION_RATE_USD_PER_HOUR))

    # Policy: detention accrues from the LATER of arrival and appointment. A
    # carrier arriving early does not start the clock early. Getting this wrong
    # over-bills the shipper and is the single most disputed calculation in the
    # accessorial process.
    start = max(arrive, appt)
    held = (depart - start).total_seconds() / 60.0
    billable_min = max(0.0, held - free_minutes)

    # Billed in 15-minute increments, rounded up.
    increments = -(-billable_min // 15)
    usd = min(increments * 0.25 * rate, DETENTION_CAP_USD)

    return {
        "total_held_minutes": round(held, 1),
        "free_minutes": free_minutes,
        "billable_minutes": round(billable_min, 1),
        "billable_increments_15min": int(increments),
        "rate_usd_per_hour": rate,
        "billable_usd": round(usd, 2),
        "cap_applied": usd >= DETENTION_CAP_USD,
        "policy_note": (
            "Accrues from the later of arrival and appointment; 15-minute "
            f"increments; capped at ${DETENTION_CAP_USD:.0f} per event."
        ),
    }


def lookup_shipment(args: dict, tenant: str | None) -> dict:
    sid = (args.get("shipment_id") or "").strip()
    if not SHIPMENT_RE.match(sid):
        return {"error": f"'{sid}' is not a valid shipment id",
                "hint": "Format is SHP-YYYYMM-NNNNNNN, e.g. SHP-202608-0041729"}
    rec = SHIPMENTS.get(sid)
    if not rec:
        return {"error": f"shipment {sid} not found",
                "hint": "Verify the id, or the shipment may be outside the retention window."}
    # Tenant check AFTER lookup, and the response is identical to not-found —
    # otherwise the error message itself leaks which ids exist.
    if tenant and rec.get("tenant") != tenant:
        return {"error": f"shipment {sid} not found"}
    return {k: v for k, v in rec.items() if k != "tenant"}


def carrier_scorecard(args: dict, tenant: str | None) -> dict:
    carrier = (args.get("carrier") or "").strip()
    month = (args.get("month") or "").strip()
    if not carrier or not month:
        return {"error": "both 'carrier' and 'month' are required",
                "hint": "month format YYYY-MM, e.g. 2026-08"}
    rec = SCORECARDS.get((carrier, month))
    if not rec:
        return {"error": f"no scorecard for {carrier} in {month}",
                "hint": "Scorecards publish 5 business days after month close."}
    if tenant and rec.get("tenant") != tenant:
        return {"error": f"no scorecard for {carrier} in {month}"}
    return {k: v for k, v in rec.items() if k != "tenant"}


def current_date(args: dict, tenant: str | None) -> dict:
    """Models do not know today's date. This tool is unglamorous and prevents
    a whole category of confidently wrong answers about deadlines and windows."""
    now = datetime.now(timezone.utc)
    return {"utc_date": now.strftime("%Y-%m-%d"), "utc_datetime": now.isoformat()}


TOOLS = {
    "compute_detention": compute_detention,
    "lookup_shipment": lookup_shipment,
    "carrier_scorecard": carrier_scorecard,
    "current_date": current_date,
}


def handler(event, context):  # noqa: ANN001
    # Accept a direct invoke, an HTTP API proxy event, or a Gateway invocation.
    body = event
    if isinstance(event.get("body"), str):
        try:
            body = json.loads(event["body"])
        except json.JSONDecodeError:
            return _err("request body is not valid JSON")

    name = body.get("tool") or body.get("name")
    args = body.get("args") or body.get("input") or {}
    if name not in TOOLS:
        return _err(f"unknown tool '{name}'",
                    hint=f"Available: {', '.join(sorted(TOOLS))}")

    try:
        return _ok(TOOLS[name](args, _caller_tenant(event)))
    except Exception as exc:  # noqa: BLE001
        # Never hand a stack trace to the model — it cannot act on one.
        return _err(f"{type(exc).__name__} while running '{name}'",
                    hint="Check the argument types and retry once.")
