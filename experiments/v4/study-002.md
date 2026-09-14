# V4 study002: local formation and bounded spatial occupation

Register before running seeds 92000..92004. Cross five sources with energy drive
0/500 per thousand, formation threshold 16/65, and exchange false/true: 40 cases.
Use v4-growing-1, 300 steps, 16x16 sites, occupancy 250 per thousand, initial
energy uniform 0..64, capacity 64, initial_raw 1 at every site, drive_amount 8,
leak 1, bond_cost 1 and construction_cost 4. No source replacements, selection
on survival, changed horizons or extra parameter cells.

The lower initial occupancy leaves space for local growth, deliberately differing
from the engineering default. Threshold 65 exceeds capacity and disables formation
while retaining dissolution, input and interaction. All eight cases of a source
share initial units/raw material and initial/final drive and direction RNG states.
This is a control for an engineered formation rule, not evolved reproduction.

Windows are inclusive ticks 1..100 and 101..300. Primary endpoint: late-window
mean occupied-site fraction, including zeros after extinction. The source is the
comparison unit. Report formation-enabled minus disabled at every fixed drive/
exchange combination (20 contrasts), drive-on minus off at fixed formation/
exchange (20), and exchange-on minus off at fixed drive/formation (20). Report
all individual contrasts and exact rational means, without significance claims.

Secondary observations per window: formation and dissolution totals, accepted
and rejected input, leakage, bond costs and construction costs; mean number of
represented material labels; mean largest same-material spatial component size;
mean count of these spatial components. Also report first zero-population tick
(including tick 0, null if never), final population and all material stocks.

The spatial graph is an observer-only graph on post-conversion occupied sites.
Join orthogonal periodic neighbors exactly when their material labels agree,
regardless of energy or paid interaction bonds. Include singleton units; an empty
world has zero components and largest size zero. Labels range over 0..3, so this
is finite material diversity, not evolutionary novelty. Spatial adjacency must
not be substituted for the pre-conversion interaction graph saved by the engine.

This study asks whether local formation expands occupied space under these input
conditions and how transport changes that response. It does not test structural
replication, repair after perturbation, group heredity or open-ended evolution.
Connected-component counts or their increase cannot establish reproduction.
No-drive cases may remain nonempty at tick 300: the finite-energy extinction bound
can exceed this horizon, so record them without extending individual runs.

Freeze source and protocol hashes at a clean commit before execution. Each run
must pass independent initialization, input, direction, interaction and material
audit. The cohort verifier must check exact 40-case coverage, configurations,
matched streams, full windows and independently derive spatial observations.
Use 77056 site records per run (256 * 301). Check a 2 GiB cohort-output soft bound
between runs; a bounded run can overshoot. Stop incomplete on errors or the limit,
retain records and report missing cases. Do not silently replace or drop cases.
