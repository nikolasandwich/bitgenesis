# Campaign 022: mutation from a monomorphic founder population under resource stress

Status at registration: not executed. Preserve v0-darwin-1, historical protocols,
archives and defaults. This protocol is committed before engineering and outcomes.
V1 remains design only.

## Question and distinction from earlier campaigns

Does enabling inherited variation in the existing scalar movement probability
change finite-horizon persistence when all founders start at genome 250 in the
block-food, low-threshold environment? Campaigns 001 and 013 used an initially
variable random founder pool and a different resource regime; campaign 021 fixed
all founders at 250 and disabled mutation. Neither supplies this paired assay.

The environment is selected using earlier evidence and is not an independently
selected universal challenge. Use fresh seeds and do not reuse the survival-selected
worlds from campaign 021. This is a mutation-treatment comparison, not a clean
isolation of selection, sensory information or adaptive genetic improvement.

Directional primary prediction: at tick 10,000, more seeds survive only with
mutation than survive only without it. Signed discordance <= 0 fails to support
this prediction. Any no-mutation-only survivor contradicts per-seed monotone rescue.
No significance threshold is specified. New trait values alone are an engineering
consequence permitted by mutation, not evidence that mutation improved fitness.

## Frozen grid and budget

Seeds 1900–1919, each with mutation_probability 0 or 100 per thousand births:
40 executions, exactly 10,000 steps each including empty worlds after extinction,
400,000 computed ticks. Twenty initial seed blocks, not forty independent initial
environments. No replacement, outcome-dependent stopping, additional rate arms,
seed extension or horizon change within this campaign.

Use darwin-baseline.toml with width=height=32, 80 founders at energy 24, genome 250
for every founder, food_capacity=24, feeding_rate=8, basal_cost=1, movement_cost=0,
birth_cost=0, birth_threshold=40, mutation_step=100, regrowth_probability=15 and
regrowth_amount=4. Construct with initial_food=0; apply the same block-map algorithm
as campaign 021, Random(1,000,000+seed), 213 sites with 24 and one with 8 food units.
Total food is 5,120 and total initial energy is 7,040 in both arms. Save and verify
exactly matching founder records, initial food vectors and initial RNG states;
configuration differs only in mutation_probability. Later RNG trajectories can
diverge because mutation perturbations consume draws and alter subsequent actions.
Do not change the frozen engine to force shared future environmental draws.

Mutation uses the existing rule: always draw the mutation decision at an eligible
birth, optionally add a uniform integer in [-100,100], then clip to [0,1000]. A
mutation attempt can leave the value unchanged. A child-parent difference is not
a count of mutation attempts, and clipping may affect the distribution near bounds.
The gene encodes random movement probability, not a food-directed action.

## Records and primary outcomes

Save initial config, founders, food and RNG; clean source provenance and protocol
hash; all 10,001 per-tick metric rows per world; complete compact birth and death
events and final full lineage records. Birth records must include id, parent_id,
birth_tick, genome and initial energy; retain death_tick and offspring information
in lineage so living trait counts can be independently reconstructed. Do not claim
full historical spatial replay from these records. No additional observer subclass
or unbounded all-action logging is required for this assay.

Primary per world: terminal population, first extinction tick and right censoring.
Primary per seed: both alive, mutation-only, no-mutation-only, both extinct. Report
all twenty pairs and signed mutation-only minus no-mutation-only count. No pooling
with earlier campaigns to change the primary result.

Secondary, predeclared checkpoints at 0, 100, 500, 1,000, 5,000 and 10,000:
population, births/deaths, living mean/variant count, complete living genome
histogram, number of ever-born genome values, count of births whose genome differs
from the parent's, surviving founder lineages, maximum living generation, food and
organism energy, supplied and dissipated energy. Save the complete ever-born
histogram separately from the living histogram, including founders. Empty means
and maximum living generations are null, living histograms empty, not missing
worlds. Whole-cohort reporting includes extinct worlds; no survivor-only adaptation
estimate. Genealogy depth is not synchronized generation count.

## Engineering and independent verification gates

Before launching use seed 23, outside the outcome cohort, to compare initialization
and 100 steps in both configurations against plain World, including full food,
metrics, events, lineage and RNG state. Instrumentation must not change dynamics.
Verify the founder reset also appears in initial birth records, not stale random
initial genomes. Record both arms' exact initial parity and energy checks.

Independent verification must check complete grid, source/protocol provenance,
initial map/config/founders/RNG, and all 400,040 metric rows. Reconcile energy,
population, cumulative births/deaths and contiguous tick sequences. Bound supplied
increments by 1024*4, food by 1024*24, basal expenditure by prior population,
uptake by 8*prior population and verify no return from extinction.

Reconstruct all births, deaths, final living identities and checkpoint trait
histograms from complete records; check contiguous unique IDs, 80 founders at
250, parents born earlier, parental survival at child birth, child genome bounds,
absolute parent-child difference <=100 and exact inheritance in the zero-mutation
arm. Distinguish birth changes from mutation attempts; do not infer the latter.
Reconcile event/lineage dates, child counts, all checkpoint summaries, extinction,
right censoring and primary pair classifications. Reject truncated records or
engineering errors as such, not as biological extinction. Record hashes of data
and analysis code. Formal totals change only after all gates pass.

## Decision after the result

If the primary difference is nonpositive, retain that result without adding rates
or choosing a favorable checkpoint. If positive, describe a finite-cohort effect
of enabling mutation; do not call it proof of adaptive evolution. A separate,
prospectively specified common-environment assay of sampled descendants and actual
ancestors would be needed to assess heritable performance improvement, with
sampling independent of the desired trait or survivor outcome. That assay is not
registered or launched by this protocol. No V1 controller follows automatically.
