# Campaign 010 — Reproduction threshold changes finite-horizon survival

All 40 preregistered runs / 400,000 ticks completed from clean source
`6a1d4fa624ea99f75da16dc9d99a07ccd29ed72d`. Both energy allocations start with
total 7040; only allocation and birth threshold vary. Other V0 parameters remain
fixed, including genome 250 and no mutation. Seeds 900–909 are shared across arms.
See [protocol](../../experiments/v0/campaign-010.md) and [all-seed outcomes](results/campaign-010.csv).

| Allocation | Threshold | Alive 500 / 5000 / 10000 | Extinct-only ticks | Mean births by 10 / 100 |
| --- | ---: | --- | --- | --- |
| food | 40 | 9 / 5 / 1 of 10 | 159–9496 | 1.1 / 13.5 |
| stored | 40 | 0 / 0 / 0 of 10 | 44–95 | 215 / 215 |
| food | 160 | 10 / 10 / 10 of 10 | none observed | 0 / 0 |
| stored | 160 | 7 / 7 / 7 of 10 | 167–214 | 0 / 0 |

| Allocation | Threshold | Mean total births | Mean supplied energy at 10000 | Mean population, ticks 9001–10000 |
| --- | ---: | ---: | ---: | ---: |
| food | 40 | 3991.1 | 280337.8 | 5.5001 |
| stored | 40 | 215 | 32266.4 | 0 |
| food | 160 | 865.2 | 516104.7 | 41.1231 |
| stored | 160 | 592 | 369614.0 | 28.8633 |

All means include every seed and extinction zeros. Surviving worlds are
right-censored at tick 10000, not assumed immortal. Stored-160 failures are seeds
901, 906 and 908; these were retained in every group summary.

## What the intervention establishes

Raising the existing threshold suppressed the early stored-energy birth burst
and improved observed endpoint survival in both allocations. The stored arm went
from 0/10 to 7/10 and the food arm from 1/10 to 10/10 at tick 10000. Thus campaign
009's early stored-energy failures depend on reproduction parameters, rather than
showing that storing initial energy in organisms universally prevents persistence.
Food still has more surviving worlds in both threshold conditions in this block.

This is a controlled parameter intervention within the model. It estimates neither
a precise survival probability nor an isolated effect of early births. Threshold
160 is applied for the entire run and changes reproduction timing, energy division,
maintenance demands and competition together. No separate birth-cost or temporary
threshold intervention was performed. Resource draws can diverge after the matched
initialization; realized supplied energy also depends on food capacity and consumption.

Higher threshold groups have fewer total births but more surviving worlds at the
endpoint. Lifetime birth count alone is therefore insufficient as a measure of
population maintenance in these treatments. The result comes from a designer-set
parameter, not an evolved reproductive strategy. No controller or new trait arose.
Existing baseline configurations remain unchanged; this experiment does not select
a new universal default or demonstrate open-ended evolution.

## Verification

### Exploratory late turnover

An additional accounting check asks whether higher-threshold survival merely
resembles the no-turnover crowded state in campaign 004. Subtracting cumulative
births/deaths at tick 9000 from tick 10000 gives the following group means over
all ten worlds per arm, including extinct zeros:

| Allocation | Threshold | Births, ticks 9001–10000 | Deaths, same window |
| --- | ---: | ---: | ---: |
| food | 40 | 114.9 | 113.4 |
| stored | 40 | 0 | 0 |
| food | 160 | 84.1 | 93.8 |
| stored | 160 | 57.6 | 58.6 |

All seventeen higher-threshold endpoint survivors record both births and deaths
within this window. Thus the observed persistence includes late turnover, unlike
the full-occupancy arrest previously observed under extreme regrowth. This does
not prove replacement of every individual, permanent viability or innovation;
genomes still encode the same fixed movement trait. Population changes match
births minus deaths in every run. Group means are not survivor-conditioned rates.

The [per-run turnover sidecar](results/campaign-010-turnover.json) includes the
window, all forty pairs of counts and input/helper hashes. The updated verification
command below emits these additional retrospective fields. The original
verification sidecar remains preserved at its earlier helper revision.

### Original run verification

Engine invariants ran each tick. Independent verification checked all **400,040
metric rows** against the preregistered grid, initial energy components, complete
tick sequence, energy/population identities, fixed-trait constancy, extinction
persistence, all declared intermediate birth/population values, final summaries
and late-window means. No unexported lifecycle records were audited.

```sh
python scripts/summarize_v0_reproduction_threshold.py --input data/campaign-010 --output data/new-threshold-summary
```

The [verification sidecar](results/campaign-010-verification.json) contains input
and helper hashes. Preregistered source passed six-environment CI run 34779261990;
verification helper source passed run 34779319289. Formal totals are now ten
campaigns / **440 runs / 2,440,000 ticks**. Nine-campaign review pages and archives
remain fixed snapshots and do not yet include this campaign.
