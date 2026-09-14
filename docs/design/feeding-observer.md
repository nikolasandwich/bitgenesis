# Research feeding observer

The research-only `scripts.observe_v0_feeding.FeedingWorld` records each visit to
the feeding phase, including zero intake. It is a subclass around the existing
engine, not a new rules version or an instrumented copy of the stepping code.
There is no CLI or formal observational campaign yet.

Each row contains tick, individual and founder IDs, position, genome, food before
and after removal, intake, and individual energy immediately before feeding.
Individuals dying during basal or movement payment never reach this phase and
produce no feeding row; their existing lifecycle events remain available.
Energy after feeding is not separately observed by this tool.

The observer identifies the current actor through the preceding energy payment
and intercepts food-list writes. It clears actor context before regrowth and
after every tick. This depends on the precise V0 action order, so construction
requires a pinned, newline-normalized engine source hash. A changed engine fails
explicitly rather than silently reinterpreting writes. Initial food layouts may
be assigned in place while no tick is running; replacing the food list causes
an explicit failure on the next step.

Call `drain_feeding()` after each recorded tick and persist the returned records
before discarding them. Otherwise observer memory grows with feeding attempts.
This does not bound the engine's retained lineage. Checkpoints do not preserve
this observer or its buffered records; no observer resume support is claimed.

## Verification and limits

Six configurations cover three sparse-world seeds, full occupancy, immediate
basal death, and scarce-food/low-energy conditions over 100 ticks each. Observed
and ordinary worlds have equal snapshots, complete food maps, lineage, lifecycle
events and RNG state at every tick. Summed intake equals supplied-energy increase
minus food-stock increase. Rows have positive pre-feeding energy, at most one
feeding attempt per ID per tick, and no newborn feeding on its birth tick.
Separate tests distinguish zero intake from death before feeding, check draining,
and reject changed engine source or replacement of the observed list.
All 120 local tests passed at the initial feeding-only checkpoint.

The original feeding component is now extended with the schema-2 birth fields
below. It still does not record unsuccessful movement or deaths before feeding
as complete action observations. It therefore does not meet the entire observer gate
in the [decision note](../roadmap/next-decisions.md). The historical replay below adds feeding observations but no mediation claim
follows from the comparisons. Fixed seventeen-campaign archives are unchanged.

## Historical prefix replay

Source `0479c34` replayed all forty campaign-017 worlds through tick 100,
hash-checking the original initial states/metric files and confirming initial
founders/RNG. All 4,040 prefix metric rows match exactly. The observer recorded
166,886 feeding attempts; per-run intake equals the independently reconstructed
early total. A separate readback checks row counts, duplicate tick/ID pairs,
positive pre-feeding energy, feeding bounds, food changes and JSONL hashes.

[Replay verification and all-run counts](../research/results/feeding-replay-017.json).
Raw JSONL files are local under `data/feeding-replay-017/`. These 4,000 replayed
simulation steps add observations to existing trajectories and are excluded from
the formal campaign inventory. Original individual movement/feeding trajectories
were not saved, so the historical comparison is against aggregate metrics, not
an independent historical individual-path reference. No comparison of survival
mechanisms is inferred from the attempt counts alone.

## Schema 2: birth opportunity and actual birth

New feeding rows explicitly contain `observation_schema=2`. At food removal the
observer records `birth_eligible`, computed from pre-feeding energy plus intake
against the configured threshold, and `empty_neighbors_before_birth`. The pinned
engine changes no occupancy between this observation and its birth-space check.
`child_id` starts null and is filled only when the engine's actual birth method
creates a descendant. Thus an energetically eligible parent without space can be
distinguished from an actual birth. Founder creation is not a feeding event.

Tests verify full 2-by-2 occupancy with eligible parents and no birth, a lone
eligible parent producing a child that does not act that tick, and agreement of
observed child IDs with actual lineage and every tick's birth increment across
the six reference configurations. Complete world/event/RNG comparisons still
pass. All 122 local tests pass. Additional neighbor queries consume no randomness
and do not mutate the engine state.

The saved 166,886 feeding records from source `0479c34` predate these fields and
remain unchanged. Missing fields in that dataset must not be interpreted as false
eligibility or absent space. New schema-2 data requires a separate recorded replay. The completed replay
and its narrowly scoped adjacent-birth-space counts are reported in
[campaign 017](../research/campaign-017.md#retrospective-birth-eligibility-and-adjacent-space);
they do not test all forms of spatial competition.

## Schema 3: movement before feeding

New rows set `observation_schema=3` and include `position_before_action`,
`movement_attempted` and `moved`. The first payment identifies basal activity;
a second payment before feeding identifies a movement attempt. A payment after
feeding is reproduction cost and is not classified as movement. This uses the
pinned source's order, including when movement cost is zero.

For individuals surviving to feeding, an attempted move without a position change
means an occupied destination under these toroidal rules. No-attempt and successful
movement are separate outcomes. Individuals dying on a movement payment never
reach feeding and remain absent from these rows; the new fields therefore cannot
count all movement attempts or all movement-related deaths. Do not treat the
feeding-conditioned blocked fraction as a whole-population movement rate.

Tests force always-moving agents in full and single occupancy, a nonmoving parent
that still reproduces, and a lethal movement payment. They compare observed and
ordinary snapshots/events/RNG and verify outcome fields. The broader six-world
trajectory comparisons still pass; all 124 local tests pass. No source changes
were made to the engine. Existing schema-1/2 datasets retain their original fields
and hashes. No schema-3 historical replay has been analyzed at this checkpoint.
