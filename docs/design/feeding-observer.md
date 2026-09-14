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
and hashes. A later schema-3 replay of all forty early prefixes and its conditional movement
counts are documented in [campaign 017](../research/campaign-017.md#retrospective-movement-among-feeding-survivors).

## Pre-feeding terminal records

The observer now keeps a separate `pre_feeding_deaths` buffer, drained with
`drain_pre_feeding_deaths()`. These rows have their own `observation_schema=1` and
record individual/founder ID, tick, starting position and energy, final position,
phase (`basal` or `movement`) and whether movement was attempted. Feeding rows
remain schema 3 with unchanged meanings. A movement-payment death happens before
destination selection, so it must not be labeled an occupied-target block.

Every pre-tick living individual must appear exactly once in either that tick's
feeding rows or terminal rows, with no overlap. Tests enforce this partition
across all six reference configurations while retaining complete trajectory,
event and RNG equality. Directed cases distinguish basal death from movement
payment death, check zero-cost movement still counts as an attempt, and ensure
both buffers drain. All 126 local tests pass.

Consumers must drain both buffers to bound observation retention. The earlier
historical replay writer saved only feeding rows; its datasets do not gain death
phases automatically. A new writer/output and independent readback are needed
before reporting all-action movement fractions. This extension identifies the
terminal execution phase, not a biological cause such as starvation or a causal
effect of movement. The engine's state and rules remain unchanged.

## Complete early actor accounting

A new historical writer stores both streams under `data/action-replay-017/`.
Replay source `41144b6` matches all 4,040 original metric rows. The feeding stream
is byte-identical to the prior schema-3 stream for every world. Independent
readback starts from founder IDs 0–79 and reconstructs each tick's active IDs
from actual child IDs and terminal records; every active ID belongs to exactly
one stream, for all 4,000 observed transitions. Birth/death/population totals
match the original metrics at every tick, and newborns join only the next tick's
action population.

There are 3,413 basal-payment and 908 movement-payment terminal records across
these prefixes. These pooled counts describe execution phases, not independent
death samples or counterfactual causes. The fixed unit-cost check expects energy
one before a basal death and two before a movement-payment death. It also checks
unchanged death position, since destination choice follows surviving movement
payment. [All-world checks and hashes](../research/results/action-replay-017.json).

Reproduce with `python -I -S scripts/verify_v0_action_replay.py --output data/new-action-check`.
These replayed observations do not increase the formal campaign count and remain
outside the fixed seventeen-campaign archive. Earlier conditional movement
fractions retain their original definitions; this dataset permits a separate
analysis with all attempted-movement phases included.

## Separate per-action energy ledger

`EnergyWorld` in `scripts/observe_v0_energy.py` layers on `FeedingWorld` without
changing its feeding schema 3 or terminal schema 1. It emits a separate energy
schema 1 record for each pre-tick actor, including actors dying before feeding.
Fields are tick/ID, energy before and after action, actual basal/movement/birth
payments, food eaten, child ID and transferred child energy, and death status.

The per-action identity is:

`energy_before + eaten = energy_after + basal_paid + movement_paid + birth_paid + child_energy`

Payments are observed energy differences around the original payment method,
not the nominal configured costs. A lethal request greater than remaining energy
therefore records only what was paid. Child transfer is observed at the original
birth call, after the parent has split its energy. The final parent balance is
read before the next actor's first payment, or after the final actor completes.
This relies on the pinned sequential V0 engine: later actors cannot transfer
energy into earlier actors. The existing engine-source guard still applies.

After each successful step, call `drain_energy()`, `drain_feeding()` and
`drain_pre_feeding_deaths()`. Buffers are separate; all three must be drained to
bound observation retention. An exception interrupts the step and leaves partial
buffers; discard that failed run's observations rather than treating them as a
complete tick. This observer does not support checkpoint restoration. Underlying
V0 lineage/event retention remains unchanged.

Targeted checks compare six configurations for 100 steps against the existing
feeding observer: snapshots, complete lineage, food, events, RNG, and both old
observation streams agree. Ledger sums match global dissipation and food uptake;
ending parent energy plus child transfers equals living energy. Separate examples
cover zero costs, odd division and capped lethal basal/movement payments. These
checks establish the tested cases, not arbitrary future engine compatibility.

The historical energy replay is now complete for all forty campaign-017 worlds,
ticks 1–100, from clean source `be4ad5a`. All 4,040 original metric rows agree;
feeding and terminal files retain their previous SHA-256 values. The new ledger
has 171,207 records, one for each actor (166,886 feeding plus 4,321 terminal).

`python -m scripts.replay_v0_energy --output data/new-energy-replay` generates the
bounded dataset from original inputs and requires a clean committed checkout.
`python -I -S scripts/verify_v0_energy_replay.py --output data/new-energy-check`
reads the saved dataset without importing or running the engine. From initial
individual energies, it reconstructs payments, intake, birth splits and ending
energy using the already verified feeding/terminal observations and configuration.
All 4,000 actor steps reconcile with original population and energy totals.
See the [complete verification report](../research/results/energy-replay-017.json).

This is independent arithmetic over retained observations, not an independent
historical action reference. The fixed observation supplement predates this tool
and dataset; earlier feeding/terminal bytes and world rules remain unchanged.
