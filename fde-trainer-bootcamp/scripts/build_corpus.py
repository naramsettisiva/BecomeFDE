#!/usr/bin/env python3
"""Generate the working corpus for Days 3-24.

The domain is deliberately freight / supply-chain operations. Two reasons:

1. You already know this domain cold. When a retrieval result is subtly wrong,
   you will *notice* — which you would not with a corpus about, say, immunology.
   Domain knowledge is how you learn to evaluate a RAG system by feel before you
   learn to evaluate it by metric.
2. It is the domain you will pitch from. An FDE who demos "chat with my PDFs"
   is one of ten thousand. An FDE who demos a carrier-performance agent that
   speaks the language of tender acceptance and detention is memorable.

    python scripts/build_corpus.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "corpus"

DOCS: dict[str, str] = {
    "01_tender_acceptance_policy.md": """
    # Carrier Tender Acceptance Policy — Revision 7

    ## Scope
    Applies to all contracted asset-based carriers operating under a Master
    Transportation Agreement (MTA) on North American truckload lanes.

    ## Definitions
    - **Tender**: an electronic load offer transmitted via EDI 204 or API.
    - **Tender Acceptance Rate (TAR)**: accepted tenders / total tenders offered,
      measured on a rolling 30-day window per carrier per lane.
    - **First Tender Acceptance (FTA)**: acceptance by the primary carrier before
      the load routes to backup.

    ## Service standards
    Carriers must respond to a tender within **60 minutes** during business hours
    (06:00-20:00 local shipper time) and within **120 minutes** otherwise. A
    non-response after the response window is recorded as a decline.

    Primary carriers are expected to maintain FTA >= 92% per lane per quarter.
    Carriers falling below 85% for two consecutive quarters enter Lane Review and
    may be removed from primary position at the next bid cycle.

    ## Exceptions
    Force majeure events (declared weather emergency, port closure, federal
    hours-of-service waiver) suspend TAR measurement for the affected lanes for
    the duration of the event plus 48 hours. Exceptions must be filed within
    5 business days with the Transportation Operations Center.
    """,
    "02_detention_and_accessorials.md": """
    # Detention, Demurrage, and Accessorial Charges

    ## Detention (driver + power unit held at facility)
    Free time is **2 hours** from scheduled appointment time at both origin and
    destination. After free time expires, detention accrues at **$65 per hour**,
    billed in 15-minute increments, capped at **$650 per event**.

    Detention does not accrue if the carrier arrives more than 30 minutes after
    the appointment window closes. Arrival time is established by geofence entry
    recorded in the carrier's ELD, or by signed gate ticket where no telematics
    feed exists.

    ## Layover
    A layover charge of **$250 per 24-hour period** applies when a driver is held
    overnight through no fault of the carrier.

    ## Truck Order Not Used (TONU)
    **$150** flat when a tendered load is cancelled after the driver has been
    dispatched but before arrival. **$250** if cancelled after arrival at origin.

    ## Demurrage (intermodal container held at ramp/port)
    Distinct from detention. Free time is **4 calendar days** at inland ramps,
    **5 calendar days** at marine terminals, then $150/day escalating to $300/day
    after day 10. Weekend days count toward free time at marine terminals but not
    at inland ramps.

    ## Dispute window
    All accessorial disputes must be raised within **30 days** of invoice date.
    Supporting evidence must include ELD-derived arrival/departure timestamps.
    """,
    "03_otif_measurement.md": """
    # On-Time In-Full (OTIF) Measurement Standard

    ## The metric
    OTIF = shipments delivered on time AND complete / total shipments, measured
    at the purchase-order line level, not at the shipment level. A single short
    line fails the entire PO.

    ## On-time definition
    Delivery is on time if the truck is checked in at the receiving facility
    within the appointment window. Standard windows:
    - Grocery/retail DC: **-30 / +0 minutes** relative to appointment
    - Manufacturing plant inbound: **-2 hours / +0 minutes**
    - E-commerce fulfilment centre: **-1 hour / +15 minutes**

    Early arrival outside the window is a failure. This surprises new analysts
    constantly: arriving four hours early at a grocery DC is an OTIF miss, not
    a service win, because the receiving dock has no labour scheduled.

    ## In-full definition
    Quantity delivered must be within **-0% / +0%** of the PO line quantity for
    ambient goods. Catch-weight categories (meat, produce) tolerate **+/- 2%**.

    ## Attribution
    Failures are attributed in order: carrier fault, shipper fault (late load
    ready), receiver fault (dock congestion), or force majeure. Attribution
    drives chargebacks, so it is the most disputed field in the entire dataset.

    ## Known data quality traps
    - Appointment times are stored in facility local time, delivery scans in UTC.
    - Rescheduled appointments overwrite the original in the TMS, which hides
      shipper-caused delays unless you read the appointment audit log.
    """,
    "04_lane_bidding_process.md": """
    # Annual Lane Bid Process (RFP)

    ## Timeline
    - **Week 0**: lane file frozen. Historical volume by lane, equipment type,
      and seasonality published to bidders.
    - **Weeks 1-3**: carrier round 1 pricing submitted.
    - **Weeks 4-5**: optimisation run and scenario analysis.
    - **Weeks 6-7**: round 2 for lanes with insufficient coverage.
    - **Week 8**: award, primary/backup/tertiary assignment.
    - **Week 10**: rates effective.

    ## Award logic
    Award is not lowest-cost. The optimiser weights:
    - Linehaul cost (55%)
    - Historical service — FTA and OTIF (25%)
    - Capacity commitment stability (10%)
    - Network fit / continuous move opportunity (10%)

    A carrier bidding 8% below market on a lane where they hold a 71% historical
    FTA will usually lose to a carrier 3% higher with 96% FTA, because the cost
    of routing to backup — routing guide depth — exceeds the linehaul delta.

    ## Routing guide depth
    Depth is the average tender position at which a load is accepted. Depth of
    1.0 is perfect. Depth above 1.8 on a lane means the primary is failing and
    spot exposure is imminent. Depth is the single best leading indicator of
    cost overrun in the next quarter.
    """,
    "05_tms_data_dictionary.md": """
    # TMS Data Dictionary (extract)

    ## SHIPMENT
    | Field | Type | Notes |
    |---|---|---|
    | shipment_id | string | Primary key. Format `SHP-<yyyymm>-<7 digits>` |
    | tender_ts_utc | timestamp | When the 204 was transmitted |
    | accept_ts_utc | timestamp | Null if declined or expired |
    | tender_seq | int | 1 = primary, 2 = first backup, etc. |
    | origin_facility_id | string | FK to FACILITY |
    | dest_facility_id | string | FK to FACILITY |
    | equipment | enum | DRY_VAN, REEFER, FLATBED, INTERMODAL |
    | linehaul_usd | decimal | Excludes fuel and accessorials |
    | fuel_surcharge_usd | decimal | Derived from DOE weekly index |
    | status | enum | TENDERED, ACCEPTED, DISPATCHED, IN_TRANSIT, DELIVERED, CANCELLED |

    ## STOP
    | Field | Type | Notes |
    |---|---|---|
    | stop_id | string | |
    | shipment_id | string | FK |
    | seq | int | 1-based |
    | appt_start_local | timestamp | **Facility local time, no tz stored** |
    | arrive_ts_utc | timestamp | Geofence entry |
    | depart_ts_utc | timestamp | Geofence exit |
    | detention_minutes | int | Computed nightly, not real time |

    ## Gotchas that have caused production incidents
    - `appt_start_local` has no timezone column. You must join FACILITY.tz.
      Two DST-boundary incidents in the last three years trace to this.
    - `detention_minutes` is a batch field. Any real-time detention alerting
      must recompute from arrive/depart, not read this column.
    - `tender_seq` resets when a load is re-tendered after cancellation, so
      routing-guide depth computed naively double-counts.
    """,
    "06_carrier_scorecard_spec.md": """
    # Carrier Scorecard Specification

    Published monthly, 5 business days after month close.

    ## Composite score (0-100)
    - On-Time Pickup: 20 pts
    - On-Time Delivery: 25 pts
    - Tender Acceptance (FTA): 25 pts
    - Billing accuracy (invoice matches rate confirmation first pass): 15 pts
    - Telematics compliance (share of loads with continuous tracking): 15 pts

    ## Bands
    | Score | Band | Consequence |
    |---|---|---|
    | 90-100 | Platinum | Eligible for volume growth and dedicated awards |
    | 80-89 | Gold | Maintain current allocation |
    | 70-79 | Silver | Quarterly business review required |
    | 60-69 | Bronze | Improvement plan, 90-day cure period |
    | < 60 | Review | Volume reallocation begins immediately |

    ## Appeals
    A carrier may appeal individual load-level events, not the composite. Appeals
    require the event id and evidence. The scorecard is restated only if appeals
    change the composite by more than 1.5 points.

    ## Why scores drift without anyone changing behaviour
    Telematics compliance is measured against loads where the shipper *requested*
    tracking. When a shipper turns on tracking requirements for a new lane, a
    carrier's denominator changes overnight and their score falls even though
    their operations are identical. Every scorecard conversation should start by
    checking whether the denominator moved.
    """,
    "07_incident_postmortem_dst.md": """
    # Post-Incident Review: Appointment Times Shifted One Hour (INC-4471)

    ## Summary
    On the first Sunday of November, 1,840 delivery appointments across 62
    facilities displayed one hour earlier than scheduled in the carrier portal.
    214 carriers arrived an hour early; 38 loads were refused at the dock and
    rescheduled, producing $71K in detention and layover exposure.

    ## Root cause
    The appointment service stored `appt_start_local` as a naive timestamp and
    the portal rendered it by applying a **fixed** UTC offset per facility, cached
    at facility creation time. When DST ended, the cached offset was stale for
    facilities in observing timezones. Facilities in Arizona and most of
    Saskatchewan were unaffected, which is why the bug survived two prior DST
    boundaries in a partial rollout.

    ## Contributing factors
    - No integration test crossed a DST boundary.
    - The offset cache had no TTL and no invalidation event.
    - Monitoring alerted on appointment *volume*, not appointment *time deltas*,
      so the shift was invisible until carriers called.

    ## Corrective actions
    1. Store IANA timezone identifier per facility; render via tz database. Done.
    2. Add DST-boundary cases to the integration suite. Done.
    3. Alert when >5% of appointments in a facility shift by exactly 60 minutes
       between consecutive snapshots. Done.
    4. Backfill audit of historical OTIF attribution across prior DST windows.
       In progress — expected to restate 3 quarters of carrier scores.
    """,
    "08_intermodal_vs_truckload.md": """
    # Choosing Intermodal vs. Truckload

    ## Rule of thumb
    Intermodal becomes cost-competitive above roughly **700 miles** of length of
    haul, with the crossover moving shorter when diesel is expensive and longer
    when rail service is degraded.

    ## Trade-offs
    | Dimension | Truckload | Intermodal |
    |---|---|---|
    | Transit | Faster, predictable | 1-3 days longer, higher variance |
    | Cost per mile | Higher | 10-25% lower on long haul |
    | Capacity in peak | Tight, spot-exposed | More stable |
    | Emissions | Higher | ~60-70% lower per ton-mile |
    | Damage/claims | Lower | Higher (extra lifts, ramp handling) |
    | Suitability | Time-sensitive, high-value, short haul | Dense freight, long haul, stable demand |

    ## What actually decides it in practice
    Not the rate. It is whether the receiving facility's inventory policy can
    absorb 2 extra days of transit variance. If safety stock is thin, the
    theoretical savings are consumed by expedite events on the tail of the
    distribution. Any conversion analysis that models mean transit and ignores
    P95 transit is wrong.

    ## Conversion candidates
    Best candidates: lanes >800 miles, weekly volume >5 loads, non-perishable,
    destination has >7 days of inventory cover, no appointment window tighter
    than 4 hours.
    """,
    "09_spot_market_dynamics.md": """
    # Spot Market Dynamics and When Contracts Break

    ## The cycle
    Truckload capacity oscillates on a roughly 3-year cycle. Carriers add trucks
    when spot rates are high; the added capacity depresses rates; marginal
    carriers exit; capacity tightens; rates rise again.

    ## Contract compliance is a function of the gap
    When spot rates exceed contract rates, contracted carriers reject tenders and
    volume falls into the spot market at a premium. When spot falls below
    contract, carriers accept everything and shippers over-pay relative to market.

    A shipper's routing guide is therefore only as good as the *gap*. A guide with
    99% FTA in a loose market tells you almost nothing about resilience.

    ## Leading indicators worth instrumenting
    - Tender rejection rate, weekly, by region
    - Routing guide depth trend
    - Spot-to-contract spread by lane cluster
    - Dry van load-to-truck ratio
    - Diesel price change, 4-week trailing

    ## Why this matters for an AI system
    A model trained on a loose-market year will systematically under-predict
    rejection in a tight-market year. Any carrier-behaviour model needs the
    market regime as an explicit feature, or it needs to be retrained on a
    rolling window short enough to track the cycle. This is the single most
    common failure mode in freight ML systems.
    """,
    "10_glossary.md": """
    # Freight Operations Glossary

    - **BOL** — Bill of Lading. Legal document of carriage and title.
    - **Deadhead** — Empty miles driven to reach a pickup.
    - **Drayage** — Short-haul move between port/ramp and warehouse.
    - **EDI 204** — Load tender transaction set.
    - **EDI 214** — Shipment status message.
    - **EDI 210** — Freight invoice.
    - **ELD** — Electronic Logging Device; source of truth for hours and geofence.
    - **FTL / LTL** — Full / Less-than truckload.
    - **HOS** — Hours of Service. Federal driver duty-time limits.
    - **Linehaul** — Base transport charge, excluding fuel and accessorials.
    - **MTA** — Master Transportation Agreement.
    - **OTIF** — On-Time In-Full.
    - **POD** — Proof of Delivery.
    - **Routing guide** — Ordered list of carriers per lane.
    - **Spot** — Transactional, non-contracted capacity purchase.
    - **TONU** — Truck Order Not Used.
    - **TAR / FTA** — Tender Acceptance Rate / First Tender Acceptance.
    - **TMS** — Transportation Management System.
    - **Yard jockey** — Vehicle that repositions trailers within a facility.
    """,
}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, body in DOCS.items():
        (OUT / name).write_text(dedent(body).strip() + "\n", encoding="utf-8")
    total = sum(len(dedent(b)) for b in DOCS.values())
    print(f"Wrote {len(DOCS)} documents ({total:,} chars) to {OUT}")
    print("\nDay 4 note: 10 documents is deliberately small. You want a corpus you")
    print("can hold in your head, so that when retrieval returns the wrong chunk")
    print("you can see *why*. You scale it up on Day 14.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
