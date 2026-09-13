# Campaign 014: movement cost and reciprocal initial frequencies

Preregistered after campaign 013 and the retrospective campaign-001 trait-change
analyses. This extends campaign 003's endpoint comparison, without changing
`v0-darwin-1`. Question: how do intermediate movement costs and a reversal of the
initial trait majority change finite-window lineage outcomes?

## Fixed design

- Costs per movement attempt: 1, 2, 3, 4, including blocked attempts as in V0.
- Founder population: 80; B comprises the first 8 or 72 founder IDs (10% or 90%).
- Competition: A=250 and B=1000 movement probability per thousand.
- Neutral label control: A=B=250, with the identical founder grouping.
- Mutation disabled in every arm. All remaining parameters from `darwin-baseline.toml`.
- New seeds 1200–1209; every condition uses all ten seeds.
- All worlds run exactly 3000 ticks, including after extinction. No optional stopping.
- Total: 4 costs × 2 initial fractions × 2 treatments × 10 seeds = 160 executions,
  480000 new computed ticks. This is not a follow-up of a prior world.

World initialization precedes genome assignment, as in campaign 003. Ordinary
random placements and initial random draws remain unchanged. Founders' genomes
are assigned once; stale founder events are cleared. Group labels are inherited
through founder IDs and do not affect behavior. Matched seeds share initialization,
not guaranteed future random/environmental draws across treatments.

## Endpoints and reporting

Primary: A-only, B-only, both present, or whole-world extinction at tick 3000,
reported separately for every cost, initial fraction and treatment. Report all
seed rows, first A/B loss ticks, and extinction tick. A lost group cannot return
without immigration or mutation, but the sole remaining group may later go extinct.
Do not count that case as surviving fixation at the endpoint.

Secondary: population, group fraction, trait diversity, births/deaths and energy
metrics at every tick. The B fraction is undefined after extinction, not zero.
Store full per-tick metric/group CSVs and compact all-run summaries with metadata.
Check energy and spatial invariants each tick. Full event/death catalogs and
spatial frames are not retained; group accounting will be audited independently
from the saved series, not reconstructed from complete life histories.

Ten seeds yield descriptive frequencies only; no significance test, pooled
universal ranking or inferred critical cost is planned. Same-seed arms are paired
initializations, not independent observations. The two fractions reverse which
trait starts rare, but residents are not equilibrated before introduction: this
is not a formal rare-invasion or stable-coexistence experiment. The neutral control
uses trait 250 and does not isolate every demographic difference of mixed worlds.
If both labels survive 3000 ticks, call it endpoint persistence, not stable ecology.

Compare costs 1/4 qualitatively with campaign 003 while retaining separate seed
blocks and the changed 90% fraction. Do not pool historical and new samples.

```sh
python scripts/run_v0_frequency_cost.py --output data/campaign-014
```

Commit this protocol and runner before the first formal run. Use a new output
directory, preserve failed attempts and record source provenance. Formal research
totals are updated only after the complete grid and independent audit finish.
