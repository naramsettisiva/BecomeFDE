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
