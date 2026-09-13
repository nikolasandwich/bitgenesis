# Campaign 009: equal initial energy, different allocation

Preregistered before seeds 800–809. Campaign 008 changes both initial food and
total initial energy. Compare two allocations with equal total energy to ask
whether the total alone describes establishment in this V0 regime.

All treatments use 32×32 cells, 80 founders, regrowth probability 15/1000, fixed
genome 250 assigned after normal initialization, no mutation, and other baseline
rules. No new biology or engine changes.

| Treatment | Food per cell | Energy per founder | Initial total energy |
| --- | --- | --- | --- |
| low | 0 | 24 | 1920 |
| food | 5 | 24 | 7040 |
| stored | 0 | 88 | 7040 |

The equal-energy contrast is food versus stored: 1024×5 + 80×24 = 80×88.
The low arm measures the lower-energy baseline in the same new seed block.
Founder count, positions and initialized RNG state match within each seed.
Later random-number consumption and environmental draws may diverge.

This intervention changes availability and spatial distribution of energy.
Stored energy also permits earlier reproduction under the existing threshold;
it is not a pure spatial-position intervention independent of reproduction.
Regrowth accepts less input when cells are near capacity, so equal initial totals
do not guarantee equal realized cumulative resource input. Report that input.

Run seeds 800–809 for 10000 ticks each, even after extinction: 30 runs / 300000
ticks. Primary descriptive outcomes: alive at 500, 5000 and 10000; first extinction
tick. Secondary: terminal population, cumulative births/deaths, supplied energy,
and mean population in ticks 9001–10000 including extinction zeros. No replacement
seeds, horizon extension or filtering based on establishment after observing data.
Survivors are administratively right-censored at 10000. No infinite survival claim.

Prediction: distributing added energy directly among founders may improve early
establishment relative to low, but differences versus environmental food may go
either way because early reproduction and access competition also change. Report
all three arms and null/opposite outcomes. Ten seeds per arm are descriptive.

```sh
python scripts/run_v0_energy_allocation.py --output data/campaign-009
```

Save per-tick metrics, full protocol/provenance and all-run summaries. Existing
energy and occupancy invariants run every tick; pending events are drained and
full lineage remains in memory. No full lifecycle or replay artifacts are exported.
Independently verify the run grid, initial accounting and summaries against raw
metrics before treating results as accepted research or updating campaign totals.
