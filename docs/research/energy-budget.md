# Retrospective energy accounting for campaign 002

This reanalysis uses existing fixed-trait metric tables. It is not a preregistered
new campaign and adds no formal simulation runs or ticks. All 100 runs are included,
including extinction zeros, over the charge window ticks 1501–2000.

## Exact decomposition under the recorded rules

With basal cost exactly one, every individual alive immediately before a tick pays
one basal unit that tick. Energy is a positive integer while alive; no other
individual kills it, and newborns wait until the next tick to act. Therefore:

```text
basal energy        = sum(population at ticks 1500..1999)
reproduction energy = 4 × (births at 2000 − births at 1500)
movement energy     = increase in dissipation − basal − reproduction
actual energy input = basal + reproduction + movement + change in stored energy
stored energy       = food energy + living-organism energy
```

Reproduction always has enough energy to pay its full cost before dividing.
Movement energy includes blocked moves and a possible partial last payment before
death. It is not the number of successful moves. This reconstruction deliberately
rejects basal costs other than one: a dying organism could otherwise pay less than
the nominal cost, so population counts alone would not recover the charge.

## Results

Each entry is the ten-seed mean energy per tick. Negative storage change means
the window consumed some previously stored energy. Values are rounded here;
the [per-run budgets](results/energy-budget-001.csv) retain exact integer totals.

| Move cost | Trait | Basal | Movement | Reproduction | Actual input | Storage change |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| 1 | 250 | 114.7674 | 28.3956 | 7.5416 | 149.3776 | -1.3270 |
| 1 | 500 | 102.5706 | 50.6556 | 6.6040 | 159.9256 | 0.0954 |
| 1 | 750 | 89.2956 | 66.2766 | 6.1968 | 161.3960 | -0.3730 |
| 1 | 1000 | 78.4452 | 77.9058 | 5.9520 | 162.5624 | 0.2594 |
| 4 | 0 | 0 | 0 | 0 | 0 | 0 |
| 4 | 250 | 49.3892 | 47.8692 | 5.3728 | 103.7128 | 1.0816 |
| 4 | 500 | 29.9132 | 58.3728 | 4.1232 | 92.4960 | 0.0868 |
| 4 | 750 | 22.9066 | 67.1756 | 3.3096 | 94.5544 | 1.1626 |
| 4 | 1000 | 4.5064 | 17.7616 | 0.6096 | 22.8880 | 0.0104 |

Basal energy per tick equals the mean *pre-tick* population. Campaign 002 reported
post-tick population over 1501–2000. The small difference is the endpoint shift,
not an inconsistency: pre-tick mean minus post-tick mean equals
`(population[1500] − population[2000]) / 500`.

At movement cost one, trait 1000 spends substantially more on movement than trait
250, despite receiving only modestly more actual input. The smaller basal share
is consistent with its smaller population. This is a conservation-based explanation
of energy allocation, not an independent prediction of population dynamics or an
explanation of every spatial effect. It does not establish competitive superiority;
direct competition remains a different experiment.

Actual input varies even though the nominal regrowth probability is fixed. Food
regrowth is capped by free storage at each site. In extinct worlds the food field
eventually fills and further proposed additions are discarded; zero late input
does not mean the configured regrowth probability changed. The capped resource
process and the organisms' consumption interact.

## Checks and reproduction

All 200,100 source metric rows passed population/energy accounting checks. The
500-tick allocation closes exactly for every run, with nonnegative reconstructed
movement expenditure. An instrumented simulation test records actual `_pay`
charges using distinct basal/movement/reproduction costs and independently matches
the reconstructed totals. Tests reject unsupported basal costs and corrupted
dissipation. The full local suite now passes 37 tests; core engine code is unchanged.

```sh
python scripts/analyze_v0_energy_budget.py --input data/campaign-002 --output data/new-energy-budget
```

The [summary sidecar](results/energy-budget-001.json) records input and script
hashes. These are retrospective observations on existing campaign data, with no
additional significance testing or open-ended evolution claim.
