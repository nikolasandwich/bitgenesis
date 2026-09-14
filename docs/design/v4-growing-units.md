# Driven material conversion

`v4-growing-1` composes the existing driven and material primitives in this order:

    external energy -> leakage -> local interaction -> dissolution -> formation

Input acceptance uses the starting occupied sites and their capacity. Consequently
an initially zero-energy unit can be rescued before dissolution. A new unit does
not receive input, pay leakage, interact or form another unit until the next step.
Units exhausted by leakage or bond costs dissolve unless synchronous transport
has replenished their energy. Dissolved material is immediately available to
the subsequent formation proposals. These choices are engineered update rules.

The exact energy ledger combines leakage, bond costs and construction costs.
Raw tokens plus occupied sites remain constant. Construction splits post-cost
parent energy, so it preserves the existing per-unit capacity bound. An exhausted
population cannot restart: empty sites reject input and there is no template.
With no input and positive integer leakage, any nonempty step spends at least
one unit of energy. Such a system must become empty within its initial total
energy in steps, even with local formation. Persistent activity requires input
under these conditions; it is not autonomous energy creation.

Interaction units, bonds and components are recorded before conversion. A bond
can have both endpoints dissolved later in the same step. Conversely, newborns
are not in that interaction graph. The record therefore names these observations
`interaction_units` and `interaction_components`; it does not present them as
connectivity of the final population. No component label controls dynamics.

The bounded `v4-growing-run-1` runner records initial/final raw material, complete
step states, proposals, direction tickets, conversion outcomes and cumulative
formation/dissolution counts. Site count times (steps + 1) is capped; this is a
record-count budget, not a byte guarantee. Existing output directories are rejected.
All V4 source hashes, configuration, Git state and output hashes are retained.

Initialization deliberately matches the fixed-site runner's `Random(seed)`
draw schedule. Drive tickets retain its `v4-driven-1:{seed}:drive` SHA256 seed
namespace. A separate SHA256 namespace `v4-growing-1:{seed}:directions` seeds
direction tickets. Each stream draws once per site per step even for empty
sites or disabled energy input. Control conditions thus preserve random ticket
schedules despite changing occupancy. Initial raw tokens are uniform (default 1)
at every site, including occupied sites, with no additional random draws.

Run an engineering trajectory with:

    python -m bitgenesis.v4.growing_runner --seed 90603 --steps 100 --output data/v4-growing-engineering-001

The CLI also supports `--no-drive` and `--no-exchange`. Python configuration
exposes material amount, threshold and construction cost. A threshold exceeding
capacity prevents formation while retaining dissolution, without changing RNG
consumption; this is a candidate formation-disabled control, not an experiment
already performed. Material conversion remains an explicit templating mechanism.

Next independently reconstruct inputs, interaction and conversion from saved
states before registering scientific comparisons. Replay equality and energy
tests alone do not certify independent reconstruction, structural reproduction,
evolution or open-ended novelty. Engineering seeds 90600–90603 are reserved.
