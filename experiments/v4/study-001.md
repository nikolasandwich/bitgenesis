# V4 study001: bounded driven connection activity

Preregistered before seeds91000..91004 are executed. Twenty runs cross these five
sources with drive_per_thousand0/500 and exchangeFalse/True. Use500 steps,16x16
sites,occupancy750,max_energy64,capacity64,drive_amount8,leak1,bond_cost1 and
v4-driven-1 rules. All four cases of a source must share initialization and drive
RNG draw counts. No source replacement, material filtering or changed horizon.

This measures activity of engineered fixed-site affinity bonds, not organism
persistence, replication, evolution or self-assembly. Unit/material positions
never change. With no input, positive leakage drains occupied units; driven
activity is expected to depend on energy supplied by the experimenter.

Predeclare windows1..100,101..250,251..500 inclusive. For each window report
fraction of transitions with at least one bond, mean bond count, mean largest
component size (zero if no units), and accepted/rejected input, leakage and bond
cost sums. Primary descriptive endpoint is the last window's active-transition
fraction. Report per-source drive-on minus off at fixed exchange, and exchange-on
minus off at fixed drive. Use sources as comparison units, retain zero activity,
and report no significance threshold or graduation criterion.

Full observations include all units, bonds, transfers and components. Require
independent initialization/input/local interaction audit and exact20-case coverage
before results. Source/protocol hashes must be frozen at a clean launch. Site
record bound is128256 per run (256*(500+1)). Check2GiB between runs; one bounded
run can overshoot. Stop incomplete on limit/error, retaining all records. No
additional parameter grid within this protocol. Any subsequent disturbance or
material-conversion experiment needs a separate specification.
