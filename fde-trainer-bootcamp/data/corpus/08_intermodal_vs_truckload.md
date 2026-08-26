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
