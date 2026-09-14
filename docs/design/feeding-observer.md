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
All 120 local tests pass at this checkpoint.

This is only the feeding component of the proposed mechanism observer. It does
not yet record unsuccessful movement, occupied-neighbor counts or birth
eligibility without birth. It therefore does not meet the entire observer gate
in the [decision note](../roadmap/next-decisions.md). No historical trajectory has
yet been replayed with these individual records, and no mediation claim follows
from the unit-test comparisons. Fixed seventeen-campaign archives are unchanged.
