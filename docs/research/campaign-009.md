# Campaign 009 — Equal starting energy does not imply equal establishment

Thirty preregistered runs / 300,000 ticks completed from clean source
`0639fd66271db72068733fba5bf105769c444dac`. All use fixed genome 250, no mutation,
regrowth 15/1000, 32×32 cells, 80 founders and seeds 800–809 for 10000 ticks.
See [protocol](../../experiments/v0/campaign-009.md) and [all outcomes](results/campaign-009.csv).

| Treatment | Initial food/cell | Initial energy/founder | Initial total | Alive 500 / 5000 / 10000 | Extinct-only tick range |
| --- | ---: | ---: | ---: | --- | --- |
| low | 0 | 24 | 1920 | 0 / 0 / 0 of 10 | 32–49 |
| food | 5 | 24 | 7040 | 9 / 3 / 1 of 10 | 218–8398 |
| stored | 0 | 88 | 7040 | 0 / 0 / 0 of 10 | 51–73 |

| Treatment | Mean births | Mean total supplied energy at 10000 | Mean population, ticks 9001–10000 |
| --- | ---: | ---: | ---: |
| low | 0 | 26779.6 | 0 |
| food | 2733.4 | 199383.2 | 3.8864 |
| stored | 215.4 | 32315.2 | 0 |

All means include extinction zeros and every seed. The one surviving food world
(seed 801) ends with 36 individuals and is right-censored at 10000.

## Interpretation

The equal-energy arms differ strongly in early establishment within this seed
block. Initial energy total alone is insufficient to describe these outcomes:
energy in organisms and distributed environmental food have different consequences
under the existing feeding and reproduction rules. Giving founders more energy
produces births but does not maintain these ten populations to tick 500.

This is an allocation intervention, not a clean isolation of spatial position.
Higher founder energy crosses the reproduction threshold sooner, changes offspring
numbers and energy division, and changes subsequent competition. These results
are consistent with an early reproduction/maintenance burden, but that mechanism
has not been isolated by a counterfactual or an event-level energy decomposition.
No reproduction rule was changed to force the result.

Equal initial totals do not imply equal total input over time. Regrowth is capped
by local food capacity; extinct worlds eventually stop consuming food and reject
more proposed input. Consequently the supplied-energy difference is partly an
outcome of the trajectories, not an independently assigned sustained subsidy.
Same-seed initialization matches, but later environmental random draws can diverge.

Ten seeds are descriptive, not proof that stored energy always fails. Food also
does not ensure maintenance: only one of ten remains at 10000. Comparison with
campaign 008's food level 8 uses a different seed block and is not a paired dose
response test. No new trait, controller, life origin or open-ended evolution is claimed.

## Verification

Every simulated tick checked engine invariants. A separate helper checked all
300,030 metric rows: fixed protocol and complete grid, initial energy components,
tick sequence, population/energy accounting, fixed trait, persistent extinction,
intermediate and final outcomes, late means and saved JSON summaries. The helper
does not replay dynamics or audit unexported lifecycle logs.

```sh
python scripts/summarize_v0_energy_allocation.py --input data/campaign-009 --output data/new-energy-allocation-summary
```

[Verification metadata](results/campaign-009-verification.json) records all CSV
hashes and helper hash. Preregistered source passed six-environment CI run
34778593278. Formal totals are now **400 runs / 2,040,000 ticks in nine campaigns**.
Existing eight-campaign visual pages and archives retain their declared scope.
