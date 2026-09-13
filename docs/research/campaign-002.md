# Campaign 002 — Demographic productivity is not evolutionary success

Protocol: `experiments/v0/campaign-002.md`. Started from clean commit
`7b11541fa49668cac005521087279270ec87cb91`, Python 3.12.10. One hundred runs,
2,000 ticks each, held-out seeds 100–109. Engine invariants passed every tick.
Raw local output: `data/campaign-002/`. All treatments and failures are included.

The founder trait was experimentally fixed and mutation disabled. Each cell below
summarizes ten seeds. Population means cover the last 500 ticks, including zeros
after extinction. Trait 250 means a 25% chance of attempting movement each tick.

| Movement cost | Fixed trait | Mean late population | Seed range | Extinctions |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 0 | 0.00 | 0.00–0.00 | 10/10 |
| 1 | 250 | 114.78 | 111.50–116.31 | 0/10 |
| 1 | 500 | 102.58 | 99.59–104.27 | 0/10 |
| 1 | 750 | 89.29 | 87.96–91.11 | 0/10 |
| 1 | 1000 | 78.46 | 77.10–79.96 | 0/10 |
| 4 | 0 | 0.00 | 0.00–0.00 | 10/10 |
| 4 | 250 | 49.39 | 42.64–54.37 | 0/10 |
| 4 | 500 | 29.93 | 0.00–39.88 | 2/10 |
| 4 | 750 | 22.89 | 0.00–30.72 | 2/10 |
| 4 | 1000 | 4.51 | 0.00–23.33 | 8/10 |

Within these treatments, some movement supports persistence whereas complete
immobility does not. Greater movement does not monotonically increase population
size. Expensive movement sharply reduces population size and can cause extinction.

Campaign 001's mixed-trait populations concentrated near high movement, but the
fixed 250 treatment here supports more individuals than fixed 1000. Population
abundance is not a fitness function and is not what the simulator optimizes.
This contrast motivates a direct competition assay; it does not by itself show
that high movement invades a low-movement population, nor prove an evolutionary
tragedy of the commons.

The treatment changes a real behavioral parameter, but later random streams
diverge and the assay operates on whole populations with a fixed trait. These
results are bounded to the stated world, costs, seeds, and duration. They do not
establish sensing, learning, intelligence, ecological species, or open-endedness.

Next experiment: direct paired-trait competition with matched initial proportions
and held-out seeds, tracking descendant proportions and extinction. Keep trait
values fixed and mutation disabled so the ancestry/trait distinction is clear.
