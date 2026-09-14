# V3 minimal ecology: resource-mediated interaction

Status: resource kernel, inherited metabolic trait and in-memory population world
implemented. Persisted runner, independent world audit and ecological experiments
are pending. V2 remains unchanged.
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

## Implemented world: v3-world-1

The world now uses an EcologyGenome: ten V2 development coordinates plus allocation
in0..16. Initialization draws development first, allocation second. Each offspring
first draws a mutation ticket out of1000, then (if selected) one of11 coordinates
uniformly. Amplitude/threshold coordinates use a uniform delta−10..10; all others
use−1..1, clipped to bounds. Zero and clipped changes remain possible. Adding the
allocation coordinate changes the marginal developmental mutation rate relative
to V2; this is a new kernel, not a matched V2 intervention.

Separate v3-world-1 random stream namespaces preserve older runs. Initial B defaults
to zero; recycling is a configuration integer0/1, default1. A retains the internal
field name food; B uses substrate_b. Total food sensing is normalized by twice the
per-substrate capacity. Initial founder sampling, failed development losses and
sequential birth/death order follow the explicit copied V2 schedule; V2 files are
unchanged. Only developmental ecological encoding is currently supported.

Actor feeding records contain site, pre-feeding stocks, allocation, both intakes,
energy gain, retained B and dissipation. intake means organism energy gain, not
raw substrate consumption. World spent includes substrate dissipation; individual
energy accounting does not charge that environmental loss a second time.
Engineering seeds85000..85003 are reserved and excluded from held-out studies.
