# V4 local-unit experiment: remove group identity first

Status: local interaction kernel and connected-component observer implemented.
There is no reproduction, growth, movement, development or evolutionary result
in this first kernel. Earlier V0-V3 runtime files remain unchanged.

The remaining primitive is an explicit unit at a fixed lattice site, carrying
one of four material labels and nonnegative integer energy. Units and material
labels are engineered. No organism/group ID, shared genome or controller governs
a collection of units. Connected components are measurements, not agents.

## v4-local-1 rules

Use a rectangular periodic lattice with width/height at least3. Matching-material
orthogonal neighbors propose bonds. Each unit counts its matching neighbors and
checks whether its energy could pay bond_cost for all proposals. A bond forms
only when both endpoints pass this local check. Only realized bonds are charged;
the conservative reservation may leave affordable individual bonds unrealized.
This explicit rule avoids sequential edge priority and is not optimized behavior.

After charges, each bond transfers floor(abs(energy difference)/8) from its higher
energy endpoint to the lower. Compute all transfers from the same post-charge
state, then apply them simultaneously. Each site has at most four neighbors,
so outgoing transfers cannot exceed its energy. Total energy decreases only by
twice bond_cost per realized bond. No replenishment or energy creation occurs.

The exchange=False control keeps the same initial bond/charging rule but removes
transport. Later bonds can differ because energy states diverge. It is a transport
removal control, not a guaranteed non-organizing baseline. Bonds are recomputed
each step, with no stored bond memory. Zero-energy units remain explicit inert
units; connected-component counting does not label them alive.

## What can and cannot be measured

The observer returns all connected site sets, including isolated units. Group
indices are temporary output ordering, never inherited identities. Static site
occupancy and matching-label affinity heavily constrain possible components;
this first kernel cannot demonstrate spatial self-assembly, replication or novel
material synthesis. Apparent splitting can simply be loss of an energy-dependent
bond. It must not be reported as reproduction.

Next add bounded recorded sequences and independent energy/bond reconstruction,
then define persistence and perturbation measurements before experiments.
To study replication later, add a separately versioned local material/energy
conversion rule and an independent pattern detector; do not add a whole-organism
copy command and call it emergence. Report failed organization and detector
ambiguity, and keep the fixed-unit baseline runnable.

Engineering seed90000 covers random local energy accounting; deterministic
fixtures test periodic neighbors, transport removal, affordability and components.
