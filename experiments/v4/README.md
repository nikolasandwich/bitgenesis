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
