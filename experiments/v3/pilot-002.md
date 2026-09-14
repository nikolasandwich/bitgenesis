# V3 pilot002: processing capacity versus external supply

Preregistered after pilot001 and its post-hoc energy diagnosis, before these
new source seeds are run. This is an exploratory viability calibration, not a
confirmatory ecological-benefit study. Retain pilot001's no-selection outcome.

Run40 worlds: seeds87000..87004 crossed with feeding_limit8/16,
renewal_per_thousand30/60, and recycling1/0. Use1000 ticks including after
extinction, v3-world-1 ecological encoding, intact sensing,16x16 sites,32 random
founder attempts, initial A12/B0, capacity24, initial energy640, threshold1280,
and every other V3 Config default. No preselection of viable founders. Paired
recycling arms must have identical initial states. Retain all failures and seeds.

The design separates changing processing capacity from changing external supply;
neither is an evolved trait improvement. Do not alter maintenance, construction,
mutation, yield or birth thresholds in this cohort. Recycling removal still
changes energy retention and cannot on its own identify cooperation.

Report every world's survival, extinction, births, maximum generation, all
founder/offspring failure reasons, and substrate flows. Include source-paired
contrasts for feeding-limit and renewal changes separately at fixed other
settings, retaining zeros and extinction. No significance or cooperation claim.

Use the same viability condition as pilot001: at least4/5 surviving worlds and
at least one successful nonfounder in every survivor. Select among recycling-on
cells in fixed order (feeding_limit,renewal): (8,30),(16,30),(8,60),(16,60).
If none qualifies, report no selection; do not silently add another grid.
Any future experiment will have a separate protocol and rationale.

Freeze clean launch commit and protocol hash. Retain full states, attempts,
lineage, events and actors; independently audit every run and verify exact40-case
coverage before selection. Each run has256000 worst-case actor records. Check8GiB
total output between runs, accepting one bounded-run overshoot of that soft
limit. Stop incomplete on error/limit, preserve outputs and never overwrite them.
