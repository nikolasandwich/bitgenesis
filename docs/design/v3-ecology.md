# V3 minimal ecology: resource-mediated interaction

Status: resource kernel implemented; population world, inherited metabolic trait,
persisted records and ecological experiments are pending. V2 remains unchanged.
No coexistence or evolved specialization has been demonstrated.

Start with resource-mediated competition and potential cross-feeding. Avoid
assigning producer/consumer species or rewarding cooperation. Two energy-bearing
substrates A and B share the lattice but have separate per-site capacity bounds.
Planned external renewal supplies only A; digestion can release B locally.
This opportunity for cross-feeding is deliberately engineered, not emergent.
Whether inherited allocation patterns differentiate is an empirical question.

## Frozen resource kernel: v3-resources-1

An allocation value p in0..16 divides a processing limit L: A quota=floor(L*p/16),
B quota=L minus A quota. Intake is capped by the pre-feeding stock of each type.
Unused quota is lost, preventing a free generalist. At default L=8 some adjacent
allocation values have identical quotas; retain these neutral encodings.

Each consumed substrate converts floor(intake/2) units into organism energy.
A's remainder is released as B, limited by free B capacity after old B intake.
B's remainder and overflow dissipate. New B cannot be eaten in the same feeding
operation. The exact invariant is:

    old A + old B = new A + new B + energy gain + dissipation

All quantities use common energy units. This is an imposed yield and allocation
tradeoff, not a model of real chemistry. Integer rounding is per substrate and
per feeding event; it is part of the rule. Feeding may produce no usable energy.
There is no unexplained resource multiplication or replenishment in this kernel.

The removal control sets recycle=False: A's remainder dissipates rather than
entering B. It keeps the processing budget and conversion yield unchanged but
changes retained environmental energy. A later causal experiment must separate
that energy difference from partner-specific benefits (e.g. matched exogenous B
control). Removing recycling alone cannot demonstrate evolved cooperation.

## Integration contract

Add a V3 genome containing the V2 developmental genes and a heritable allocation
coordinate. Keep the old development mapping and construction charges; document
the new mutation kernel and source streams under a new world rules version.
Controllers initially sense total local substrate energy at the old five food
positions, with the same energy/bias interface. They do not receive a hand-coded
direction or ecological role. Total substrate sensing is an explicit information
restriction; stage comparisons will not pretend V2's food semantics are identical.

Record both substrate grids, external A renewal, intakes, energy gain, B release,
overflow/dissipation and metabolic allocation for every actor. Sequential actor
order permits later actors to access newly released B; that timing is deliberate.
Retain all failed construction attempts and extinct worlds. Independent audits
must reconstruct substrate transfers, occupancy and energy before a research run.

Begin with engineering fixtures for accounting and the recycle-removal control,
then preregister a bounded viability pilot. Before coexistence claims, define
trait-frequency and turnover observations across at least five seeds and fixed
windows, include perturbation controls and distinguish imposed resource niches
from evolved differentiation. No extra species labels or desired fitness scores.
