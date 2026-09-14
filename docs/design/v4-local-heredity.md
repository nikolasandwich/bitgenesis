# Next mechanism: inherited local construction rules

Status: design decision after the information-erasure counterexample, not yet
implemented. Preserve existing local/driven/growing and intervention versions.

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
