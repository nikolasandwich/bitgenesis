# Next mechanism: inherited local construction rules

Status: deterministic conversion primitive `v4-heredity-1` implemented after the
information-erasure counterexample. Existing local/driven/growing and intervention
versions are unchanged. No composed driven runner or scientific cohort yet.

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
Next compose driven interaction using expressed material, preserve programs on
survivors, and independently reconstruct inheritance/expression/mutation before
an evolutionary experiment. Mutation availability alone is not adaptation.
