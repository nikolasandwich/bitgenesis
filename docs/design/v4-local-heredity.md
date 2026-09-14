# Next mechanism: inherited local construction rules

Status: deterministic conversion primitive `v4-heredity-1`, composed driven
steps, bounded runner and independent hereditary audit are implemented. Existing
local/driven/growing and intervention versions remain unchanged. Study005 tested
variation persistence; studies006/007 measured frozen descendant/actual-founder
expansion and competition. See the [current evidence](../roadmap/stage-status.zh-CN.md).

Separate a unit's expressed material label from a small inherited construction
program. The first candidate program has four entries (east, west, south, north),
each selecting child material0..3. On a successful local formation the parent
expresses its entry for the chosen direction; the child inherits the program.
An explicitly ticketed mutation may replace one entry with another label. No
whole-world reference, target pattern, group ID or recovery score enters dynamics.

Keep raw tokens untyped. Specify an additional nonnegative program-copy cost and
include it in the successful formation energy charge; require sufficient energy
for both parent and child. Failed proposals should retain the previous conflict
and resource rules. Mutation must be applied at a declared point after expression,
so it is clear whether it affects the newborn's material or only future offspring.
Use new state/rules versions and fixed RNG ticket schedules for controls.

First verify immutable inheritance, all four directional expressions, exact
copy-cost accounting, mutation/no-mutation coupling and independently reconstructed
events. A constant four-entry program equal to the parent's material, zero copy
overhead and no mutation should supply a carefully scoped baseline comparison.
Do not claim general baseline equivalence after nonconstant expression changes.

The program is engineered hereditary information. Testing its capacity to retain
or express structure is separate from testing whether useful programs evolve.
With only4^4 possible programs this candidate is explicitly finite; any later
open-ended representation needs a separate design and bounded novelty measures.

## Implemented conversion semantics

`HeritableUnit(material, energy, program)` is immutable; program is exactly four
integer labels0..3. `heredity.convert` projects physical units into the unchanged
material conversion primitive, charging construction_cost + copy_cost for each
successful formation. Default costs4+1,threshold16. Validation requires threshold
at least total cost + 2. Failed proposals neither copy nor mutate. Programs on
exhausted units disappear at dissolution; raw material remains untyped.

For a successful source proposal, first express child material from the parent's
original program entry for that direction. Then copy the program and optionally
mutate one entry. This mutation changes future offspring expression, not the
current newborn label. The parent's program never changes. A newborn therefore
can differ both in material from its parent and in program from both its parent
and its currently expressed label.

Supply a `(chance, entry, offset)` tuple for every site, even empty ones, with
chance0..999,entry0..3,offset1..3. Mutation occurs iff chance is below the configured
per-thousand probability (default10). The chosen entry changes by offset modulo4,
so a mutation always changes it. No random draws occur inside this primitive.
Future runners must generate all tickets with a fixed independent stream and
retain them for unused as well as used sites to permit matched controls.

Successful event records include parent/child programs, expressed material,
mutation ticket/outcome and copy/construction charges. Energy and material totals
are inherited from the physical conversion ledger. Programs themselves are
engineered information fields, not additional material tokens; the fixed copy
charge is an explicit modeling assumption, not a physically derived bit cost.

Tests cover four directions, deferred mutation expression, unchanged parents,
constant-program zero-overhead baseline projection, collisions and invalid tickets.
The composed driven interaction below preserves survivor programs and has an
independent inheritance/expression/mutation audit. Mutation availability alone
is not adaptation.

## Driven hereditary trajectories

`v4-hereditary-growing-1` projects expressed material and energy into the existing
driven interaction, then preserves each survivor's program through input, leakage
and transport before hereditary conversion. Pre-conversion interaction records
include programs; bonds/components still depend only on expressed material and
energy. A newborn cannot act until the next step.

`v4-hereditary-run-1` saves complete hereditary states, per-site mutation tickets,
events and copy/mutation totals. Physical initialization, drive and direction
streams retain the ordinary growing runner's schedules. Independent SHA256-seeded
streams `v4-heredity-1:{seed}:program` and `v4-heredity-1:{seed}:mutation` supply
programs and mutations. Initialization draws four program entries for every site,
even empty sites and constant-program controls. Each step draws chance, entry,
offset for every site, including when mutation probability is zero. Constant
program mode discards sampled entries and uses the initial unit's material in
all four entries. Random mode uses sampled entries. Physical initial states and
random stream consumption therefore remain matched across these controls.

Run an engineering trajectory with
`python -m bitgenesis.v4.hereditary_runner --seed 95004 --steps 100 --output data/v4-hereditary-engineering-001`.
Default copy cost1 and mutation10/1000 are engineering settings. Python arguments
expose program mode, copy cost and mutation probability; the CLI retains output,
seed, steps, no-drive and no-exchange controls. Seeds95000..95004 are engineering.
Ordinary growing audits do not accept this new schema. Use the independent
hereditary reconstruction below; full-state replay alone is not that gate.


Independent reconstruction is now available through v4.hereditary_audit. It
rebuilds physical initialization and program/mutation streams, uses independent
local/material reconstruction, and derives child expression and mutation from
serialized parent programs. It checks every recorded state and cost. Engineering
95004 passes100 steps,79 formations,79 copy-energy spent and1 mutation. Tests
reject rehashed child-program and mutation-ticket corruption; seed95005 is
reserved. Study005 completed its preregistered bounded variation-persistence
experiment. This dynamics gate itself does not claim adaptive value or lineage
identity; the separate passive lineage observer and matched assays supply those
additional measurements with the limitations stated in their reports.
