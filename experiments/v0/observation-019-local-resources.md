# Retrospective local-resource observation of campaign 019

Status at registration: not executed. This is a supplementary replay protocol,
not campaign 020, a new independent sample, or an intervention on V0 rules.
It is motivated by post hoc evidence that all seven extinctions retain global food.

## Cohort and endpoint

Include all forty registered campaign-019 worlds: seeds 1600–1609, block food,
thresholds 40/160, birth costs 0/4, movement cost zero. Initial states must match
original food, founders, config and RNG digest. No selected subset or replacement.
For each world let endpoint be the recorded first extinction tick, or 10,000 for
right-censored survivors. Replay from initialization through that endpoint and
compare every metric row against the corresponding original prefix.

Retain local-resource, feeding, terminal and individual-energy rows for exactly
the last twenty action ticks: endpoint-19 through endpoint inclusive. Also retain
full food, occupancy, living-individual and RNG snapshots at the twenty-one tick
boundaries endpoint-20 through endpoint. This endpoint-aligned window deliberately
conditions on observed outcomes; it is not a prospective survival predictor and
is not a comparison at equal world age. Preserve all forty identities/statuses.
Do not change endpoints or window after seeing spatial results.

## Integrity gates

First verify each original initial/metric file against campaign-019 verification
hashes. Use the unchanged source-pinned observer. Test recording disabled versus
enabled if a capture-window switch is added, including transitions across a tick.
No mutation of world state or consumption of world RNG for observation is allowed.
Initial equality and all replayed metric prefixes must pass before interpretation.
Archive clean replay source, protocol hash, configuration, recorded window and
complete/failed status. A mismatch is a replay failure, not biological extinction.
Do not silently overwrite or rerun failed output. Engineering tests use other seeds.

Local rows must partition each tick's preexisting actor IDs and agree with energy,
feeding/terminal identity and position fields. Full boundary snapshots must match
aggregate energy/population and food capacity/occupancy invariants. The retained
boundary maps support later independent reconstruction of resource writes and
positions; claiming that stronger reconstruction requires implementing and passing
it, not merely recording maps. Later RNG states have no independent historical
reference, so prefix metric equality is not proof of historical actor-path equality.

## Descriptive outputs fixed before replay

Report per-world final living count/energy/global food and local stocks, plus
per-window action counts, immediate basal deaths, actors with positive food at
current site, and actors with food on an unoccupied neighboring site. Keep these
categories separate; the actor can have food in both categories. Summaries use
actor actions as descriptive denominators, never as independent experimental
replicates. Report distributions by treatment and observed endpoint status, with
explicit world counts. Do not infer unique causation from conditional differences.

Resource at the current site is measured before the actor's basal payment.
Neighbor food describes a possible site, not the randomly chosen destination.
No global distance/path claim is registered here. No additional world runs or
changes to movement, reproduction, resource renewal or basal cost are authorized
by this protocol. Original formal campaign totals remain unchanged; separately
report replayed prefix ticks and retained observation counts.
