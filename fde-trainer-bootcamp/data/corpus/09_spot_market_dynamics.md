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
