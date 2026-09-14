# V4 fixed-unit engineering runs

```console
python -m bitgenesis.v4 --seed 90102 --steps 100 --output data/my-v4-check
python -m bitgenesis.v4 --seed 90102 --steps 100 --no-exchange --output data/my-v4-control
```

Use new output directories. The same seed/configuration initializes identical
units across exchange conditions. Defaults:16x16 periodic sites, occupancy750/1000,
uniform material0..3 and uniform integer energy0..64 for occupied sites,
bond_cost1. One occupancy draw is made per site; material/energy draws occur only
for occupied sites. No randomness is consumed during subsequent interactions.
These are engineering settings, not a registered persistence experiment.

v4-run-1 saves initial/final units, initial RNG state, every synchronous transition,
transfers, costs, connected components and energy totals, plus version/configuration
and output hashes. Components refer to bonds used in that transition, based on its
pre-charge state. They are not bonds recomputed from the final energies. At zero
steps, last-transition bond/component counts are null. Isolated and zero-energy
units remain observations; counts do not represent living organisms.

The site-record preflight counts width*height*(steps+1) and defaults to one million.
This is a count limit, not an output byte guarantee. Independent reconstruction
of bonds, costs, transport and observer components is pending. Replay and energy
balance tests alone do not certify emergence or replication. Seeds90100..90102
are reserved for engineering; preserve90000 from the kernel tests as well.

Independent reconstruction is now available:

```console
python -m bitgenesis.v4.audit data/my-v4-check --output data/my-v4-audit.json
```

It uses four-neighbor sets and union-find rather than the runtime edge enumeration
and component traversal. It verifies initialization RNG, bonds, costs, transfers,
all recorded units/components and terminal accounting. Engineering001 passes;
its first zero-bond transition is51. Seeds90200/90201 cover controls and rehashed
observer corruption. See docs/research/v4-closed-system.zh-CN.md for the finite
activity bound of this closed positive-cost system; do not seek indefinite
persistence simply by increasing its horizon.

## Driven trajectories

```console
python -m bitgenesis.v4.driven_runner --seed 90402 --steps 100 --output data/my-v4-driven
```

Optional --no-drive removes input; --no-exchange removes transport. Initial units
use the same Random(seed) protocol as the closed runner. Input uses a separate
SHA256-derived stream named v4-driven-1:<seed>:drive. Every site draws one ticket
per step, even if empty or input disabled. Defaults propose8 energy with500/1000
probability per site, capacity64 and leakage1. These are engineering settings.

v4-driven-run-1 saves both initial random states, final drive state, proposals,
accepted/rejected inputs, leakage, local interactions and complete units/components.
The component observation uses the bonds actually employed in that transition.
Input and exchange controls share initial states and drive draw counts. Accepted
input may differ due to capacity and must not be inferred from proposal totals.
Independent driven-run audit is pending; the closed audit cannot verify this
new schema. Seeds90400..90402 are reserved for engineering.

Driven records now have independent verification:

```console
python -m bitgenesis.v4.driven_audit data/my-v4-driven --output data/my-v4-driven-audit.json
```

It reconstructs both random streams, all proposed/accepted/rejected input,
leakage and local interaction/component states. Engineering001 passes100 steps;
seed90500 tests rehashed input corruption. The [first activity study](study-001.md)
registers20 cases and fixed early/middle/late windows, without replication claims.

## Local material conversion

`python -m bitgenesis.v4.growing_runner --seed 90603 --steps 100 --output data/my-v4-growing`
records driven interactions followed by dissolution and local formation.
`python -m bitgenesis.v4.growing_audit data/my-v4-growing --output data/my-v4-growing-audit.json`
independently reconstructs the complete trajectory. Use new output paths.
Engineering001 ends with256 units after56 formations and5 dissolutions from205
initial units; conserved material461. Its independent audit is archived under
docs/research/results. Seeds90600..90603 and90700/90701 are engineering-only.
The [second study](study-002.md) preregisters formation/input/exchange controls
and spatial occupation measurements. Its scientific cases have not yet run.
