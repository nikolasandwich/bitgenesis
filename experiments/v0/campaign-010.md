# Campaign 010: allocation × reproduction threshold

Preregistered before executing seeds 900–909, motivated by campaign 009's
stored-energy birth burst and subsequent extinction. Test whether raising the
existing reproduction threshold changes finite-horizon survival, with both energy
allocations included so effects are not attributed only to one background.

Use four treatments: food-40, stored-40, food-160, stored-160. Food arms start with
5 food energy per cell and 24 per founder; stored arms with 0 and 88 respectively.
Each has total initial energy 7040, 80 founders and 32×32 space. The suffix is the
birth_threshold parameter (baseline 40, elevated 160). Regrowth 15/1000, fixed
genome 250 assigned after normal initialization, mutation probability zero, all
other baseline parameters unchanged. No engine or rules-version change.

Run ten fresh seeds 900–909 in each arm, 10000 ticks even after extinction:
40 runs / 400000 ticks. Preserve initialization matching within seed; do not claim
matched future resource draws after random-number consumption diverges.

Primary descriptive outcomes: survival at ticks 500, 5000, 10000 and first
extinction time. Mechanistic secondary observations: births and population at
10 and 100 (also save 500 and 5000), terminal births/deaths and energy accounts,
and mean population during ticks 9001–10000 including zeros. Retain all seeds,
null outcomes and extinctions; no replacement, outcome-dependent stopping, or
horizon extension. Surviving worlds are right-censored at 10000.

Prediction: threshold 160 suppresses the stored arm's early birth burst and may
delay extinction or improve establishment. It can also inhibit replenishment, so
long-run improvement is not guaranteed. Report changes in both allocation arms
and whether their ordering reverses. No precise probability or permanence claim.

Interpretation boundary: threshold changes reproduction timing, energy splitting,
population costs and subsequent competition jointly. It does not isolate birth
cost alone or prove a single causal pathway. The intervention acts throughout the
run, not only during the first ten ticks. Equal starting energy does not guarantee
equal realized input because resource capacity and consumption affect regrowth.

```sh
python scripts/run_v0_reproduction_threshold.py --output data/campaign-010
```

Commit this protocol and runner before execution. Save all per-tick metrics and
provenance, check engine invariants each tick, then independently verify the fixed
grid, initial components, intermediate/final summaries and accounting. Full events
and replay are not exported. Do not update accepted campaign totals before that
verification completes. This is a parameter intervention within V0, not V1.
