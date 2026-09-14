# Next gate: passive structure boundaries and continuity

Status: snapshot partition and surviving-member overlap primitives implemented
in `v4.structure`, following completed study008. Audited trajectory phase mapping
and scientific cohort observations remain pending. Do not interpret a positive
unit competition score as reproduction of a multi-unit organization. The next
implementation observes existing trajectories without changing their dynamics.

At each recorded state compare three explicitly different boundary conventions:

- Occupied orthogonal contact, regardless of material or energy.
- Occupied orthogonal contact with matching expressed material.
- Realized energy-dependent bonds from the recorded interaction phase.

Use the periodic geometry of the run. Include isolated units as singleton
components. Label each observation with its phase: realized bonds belong to the
interaction state before material conversion, while final occupation includes
newborns and excludes dissolved units. Never combine those states as if they
were simultaneous. For direct boundary comparison reconstruct all three on the
same interaction state; separately report final-state geometric components.

Use passive birth identities to measure component membership continuity. A
site vacated and refilled is a different unit, even with the same program.
Between comparable successive snapshots emit the full nonempty overlap graph
of old/new component memberships, with intersection counts and both component
sizes. Preserve split and merge ambiguity; do not greedily choose a single
parent component. Report components with no shared surviving members separately
from lineage-derived newborn relationships. No identity, boundary or score is
fed into the engine or random streams.

Also summarize size distribution, singleton fraction, component count and the
fraction of occupied units whose component membership differs between boundary
definitions. Give numerator and denominator, including empty-state conventions.
No component is called an organism solely because it is connected. Splitting a
connected set is not replication; a later hypothesis must specify maintained
organization and inherited variation across an independently observed event.

Engineering acceptance before scientific use:

1. Explicit fixtures for periodic contact, unlike-material neighbors, insufficient
   bond energy, isolates, empty states, merge, split and same-site replacement.
2. Correct phase mapping across dissolution and birth; reconstruct pre-conversion
   living identities from the previous final state and post-conversion identities
   from actual birth events. Fail on inconsistent occupancy or phases.
3. Independent component partition and overlap recomputation on fixtures and a
   bounded retained trajectory. Every live identity belongs to exactly one
   component under each convention; overlap cannot duplicate a surviving member.
4. Running the observer only reads input files: preserve their byte hashes, world
   state and random records. Record observer/version/input hashes separately.

Start with engineering fixtures and an already retained short trajectory, not a
new parameter sweep. Freeze descriptive windows and trajectory selection before
examining cohort structure outcomes. This gate establishes a measurement tool,
not self-organization, recovery or structural heredity by itself.

## Primitive implementation

`snapshot` consumes serialized units, unique birth identities and an explicit
interaction/final phase. Interaction requires supplied realized bonds; final
rejects them. It validates identity/occupation agreement and restricts supplied
bonds to matching-material periodic contacts. It does not infer bond eligibility
from post-charge energy: the trajectory audit must supply valid phase records.
Partitions include isolates, canonical member lists, size distributions and
exact disagreement numerators/denominators. Empty fractions are null.

`continuity` emits all surviving-member intersections and split/merge indices,
added/lost members and components without overlap. Indices are local to input
snapshots. No-overlap does not mean no genealogical relation, and overlap does
not establish structural reproduction. Four tests cover periodic/material/bond
differences, passive inputs, phase rejection, empty fractions, split/merge/site
replacement and partition comparison against independent union-find fixtures.
Seed102000 is engineering-only. Next implement audited phase mapping on a
retained trajectory and check immutable input hashes before any cohort claim.
