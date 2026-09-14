# V1 study-001: inherited information dependence

Status: preregistered before training or held-out outcomes. This is a bounded
first study, not a promise of a positive result or open-ended evolution.

## Frozen rules and independent units

Use v1-world-1 and v1-linear-1 with the documented schedule, 160 energy scale,
integer inputs/weights and seven RNG streams. Freeze clean source commit and
hashes at each phase launch. Revisions after launch must be recorded and preserve
semantics; any necessary semantic fix invalidates the affected phase for this
protocol and requires an explicit replacement study.

Ten independent training worlds use seeds72000..72009, each5000 ticks, including
resource updates after extinction. Config:16x16, capacity24, initial_food12,
founders32, initial_energy24, renewal15/1000 amount4, basal1, decision1,
movement0, feeding_limit8, threshold80, birth_cost0, mutation100/1000. Initial
weights are independent uniform integers[-100,100]. All train intact. This uses
the pilot's predeclared selected physiology, not a best-performing individual.

At tick5000 sample k=1 living individual without replacement from sorted IDs
with analysis seed74000+(training_seed-72000). No replacement for extinct worlds;
all ten remain the denominator for training survival. Trace actual founder
through the parent chain. Archive each initial genome pool. Separately generate
one unscreened randomized controller per training seed using Python Random seed
75000+(training_seed-72000),35 uniform integer weights[-100,100], even if training
is extinct. Extinct sources have no conditional evaluation, not zero effect.

## Held-out assays

For every available source evaluate three genomes: sampled descendant, its actual
founder, and its fixed randomized controller. Retain identical genomes without
deduplication. Each genome is tested intact versus blind (primary), shuffled
(secondary), and intact (neutral allocation control). Every comparison has both
allocation swaps, with16 founders per group and observer-only founder ancestry.

Five held-out seeds73000..73004 are crossed with renewal probabilities15 and30
per1000. All other physiology and initial state rules match training, except
mutation is disabled. Each world runs1000 ticks, including after extinction.
The higher renewal process is a bundled resource-regime robustness check, not a
new geometry or an isolated sensory effect. No held-out seed is used for tuning.
Maximum10 sources *3 genomes *3 controls *5 seeds *2 renewals *2 swaps =1800 runs.

## Endpoints, aggregation and interpretation

Primary per-run D=(N_intact-N_blind)/16. Preserve both counts, births/deaths,
living energy and four terminal statuses. Both-extinct D=0 and fraction=null.
For each source/genome/control, average swaps, then five seeds, then the two
renewal regimes with equal weights. Publish separate regime contrasts too.

Primary evolutionary contrast is descendant blind-D minus actual-founder
blind-D, averaged equally over available training worlds. Report every source
and all unavailable sources. Secondary: descendant blind-D itself, comparison
with randomized blind-D, shuffled versions, and birth/survival/turnover contrasts.
No alternate primary endpoint is selected after observing results.

Report an exploratory95% percentile bootstrap interval for the primary mean:
10000 cluster resamples of available training-world effects, Python Random76000,
nearest-rank2.5%/97.5% quantiles (one-based ranks250 and9750). Report null interval
with fewer than2 available worlds; do not resample actions or individual assays.
Minimum practically meaningful mean improvement is1/16. A bounded positive
interpretation requires primary mean>=1/16, lower interval>0, positive descendant
blind-D and descendant-minus-randomized blind-D, and nonzero mean fixed-probe
intact/blind responsiveness of descendants. Secondary contrasts are descriptive,
with no additional significance claims. Fewer than5 available training worlds
precludes a positive stage interpretation regardless of interval. Null/reversed
outcomes are retained and cannot be rescued by changing network size or memory.
These criteria do not establish selection over drift or universal adaptation.

For each archived genome, fixed-state probes cross post-charge energy{1,24,80,160}
with physical food patterns (current,E,W,S,N): all0; all12; current24/rest0;
one directional24 with other sites0 (four patterns); and (6,24,12,6,0).
Capacity24. Compute exact probabilities and total variation, average all32 states
equally. An additional occupied-east flag duplicates these states for reporting:
intended action probabilities must be unchanged because occupancy is not sensed.
Report these as synthetic probes, never as encountered training states.
Late turnover covers ticks501..1000. Retain counts of selected movement,
blocked attempts, intake and payment-phase deaths from actual records.

## Execution and preservation

Training max_actor_records=1280000 per run; evaluation256000 per run. Full
records, initial/final states, source metadata and independent audits are required.
Maximum worst-case actor count473600000 across training+evaluation. Dataset
budget16GiB, checked between runs; stop with incomplete status on reaching it,
retain records, and do not present partial evaluation as complete. No automatic
seed/horizon substitutions. Exclude engineering/pilot seeds70000..71999 from
training and held-out evaluation. Sampling/randomization/bootstrap streams are
analysis-only and must never enter simulation decisions.

Training and sampling may finish before the cohort analysis runner is implemented;
the decisions above cannot change after training starts. Any engineering failure
preserves failed output and reason; a same-input replacement needs a recorded link.
Before each launch require a clean tested source and exact protocol hash. V0
archives stay intact. V2 exploratory design may proceed after this study's
interpretation without falsely labeling a negative V1 result as graduation.
