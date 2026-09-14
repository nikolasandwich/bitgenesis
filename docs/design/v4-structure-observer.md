# Next gate: passive structure boundaries and continuity

Status: snapshot partition and surviving-member overlap primitives implemented
in `v4.structure`, following completed study008. Audited trajectory phase mapping
is implemented in `v4.structure_trace`; scientific cohort observations remain
pending. Do not interpret a positive
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

## Audited trajectory adapter

`structure_trace.trace` supports hereditary, explicit-program and competition
schemas through their respective independent dynamics audits. Before conversion,
interaction identities equal the previous final identities; material/program
and occupation must match. After dissolution/formation the passive lineage
observer assigns final birth identities. Continuity compares consecutive final
states (including initialization) and consecutive interaction states separately;
the first interaction has no preceding interaction comparison.

All input-directory file hashes are checked before and after observation; the
CLI requires an exclusive output outside that directory. Observations record
input, dynamics-audit and observer hashes. Two tests check audited phase mapping,
independent event identity assignment, cross-product overlap counts, immutable
files and zero horizon. Seeds102001/102002 are engineering-only.

The retained100-step hereditary engineering trajectory95004 passes this adapter:
182 founders,79 births,5 deaths,256 final living units. Independent cross-product
overlap recomputation matches497 phase/definition transitions. Its final contact
partition has one component while the material partition has129; this illustrates
boundary dependence, not129 organisms. A compact engineering record is archived
under `docs/research/results/v4-structure-engineering-001.json`. Independent
retained-trajectory partition reconstruction and cohort selection remain next;
overlap checks alone do not complete the full measurement gate.

Independent retained-trajectory partition reconstruction is now implemented in
`structure_audit`: all occupied pairs determine geometric edges, union-find
reconstructs partitions, identical member sets determine boundary agreement,
and cross-product intersections reconstruct continuity. Event-order birth
identity assignment is separate from the runtime lineage observer. The retained
100-tick engineering trace passes502 partition and497 transition checks; input
and observation bytes are unchanged. Metric and birth-ID corruption tests reject
altered observations, including valid JSON with otherwise intact source binding.
The audit relies on the existing independent dynamics audit for physical events;
it does not authenticate external Git identities or establish group ancestry.
Study009 freezes all twenty retained study005 sources and descriptive windows
before cohort structure observations. It adds measurements, not new trajectories.
