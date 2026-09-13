# Campaign 011: longer observation of high-threshold worlds

Preregistered follow-up before examining ticks beyond 10000. Campaign 010 found
17/20 high-threshold worlds alive at 10000 with late turnover. Test observation
horizon sensitivity by following both complete high-threshold cohorts to 100000.

Food-160 and stored-160, seeds 900–909, retain their exact campaign-010 settings:
32×32, 80 founders, initial total 7040; food/individual energy 5/24 or 0/88;
regrowth 15/1000, fixed genome 250, mutation off, birth threshold 160. All other
baseline parameters unchanged. Include the three early failures; do not select
only survivors or replace seeds. No new independent seed block is claimed.

Because campaign 010 did not save full world checkpoints, regenerate each prefix
and compare every saved snapshot at ticks 0–10000 against its original metric CSV.
Abort on any mismatch. Record reference-file hashes. This verifies recorded
observable prefixes, not a comparison with an unavailable original full RNG state.
The unchanged engine and initialization define deterministic continuation.

Twenty executions × 100000 ticks = 2000000 computational ticks, of which 200000
replay earlier trajectories and 1800000 extend their observation. These are twenty
follow-up executions, not twenty additional independent evolutionary replicates.
Continue even after extinction to preserve the stated execution horizon.

Primary: all-cohort survival at 10000, 50000, 100000 and first extinction time.
Secondary: births at those horizons, terminal population/energy, mean population
over ticks 99001–100000 including zeros. Save all per-tick metrics and source
provenance; check invariants every tick. Report additional extinctions even if
they contradict an impression of maintenance from the shorter experiment.

Prediction is deliberately unresolved: delayed failures may appear, or the
previous endpoint survivors may persist through this longer finite window. Either
outcome remains finite evidence, not proof of permanent survival or new function.
Do not extend the horizon or add replacement runs after looking at these outcomes.
Formal acceptance requires complete grid, matched prefixes and independent metric
verification. No engine changes or V1 code. Full events/replay are not exported.

```sh
python scripts/run_v0_long_horizon.py --reference data/campaign-010 --output data/campaign-011
```

Operational budget: 20 fixed executions, 100000 ticks each, one process, per-tick
CSV output and full in-memory lineage. Monitor progress output at 10000-tick
intervals. If interrupted or resource-limited, record partial completion; do not
silently shorten the declared horizon or count unfinished results as accepted.
