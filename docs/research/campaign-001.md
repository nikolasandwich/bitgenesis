# Campaign 001 — Initial selection and lineage collapse

Run on Python 3.12.10, clean commit `0bb09425d4b988c96982fa89b6fa1ead7d3be8c4`.
Protocol: `experiments/v0/campaign-001.md`. Ten runs, 5,000 ticks each; every
tick passed energy and occupancy invariants. Raw local outputs: `data/campaign-001/`.
Reproduce with the committed campaign script and a new output directory.

| Treatment | Seed | Final population | Births | Final mean trait | Trait variants | Founder lineages | Max generation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Mutation | 0 | 73 | 7519 | 957.04 | 14 | 1 | 113 |
| Mutation | 1 | 95 | 7684 | 939.73 | 19 | 1 | 110 |
| Mutation | 2 | 84 | 7532 | 983.62 | 8 | 1 | 119 |
| Mutation | 3 | 78 | 7615 | 950.17 | 15 | 1 | 143 |
| Mutation | 4 | 60 | 7512 | 985.75 | 7 | 1 | 117 |
| No mutation | 0 | 97 | 7430 | 984.00 | 1 | 1 | 104 |
| No mutation | 1 | 76 | 7550 | 966.00 | 1 | 1 | 113 |
| No mutation | 2 | 88 | 7565 | 960.00 | 1 | 1 | 115 |
| No mutation | 3 | 92 | 7524 | 963.00 | 1 | 1 | 113 |
| No mutation | 4 | 77 | 7499 | 989.00 | 1 | 1 | 101 |

No run became extinct. Last-1,000-tick mean populations were 78.332–79.903 with
mutation and 78.389–80.205 without it. Founder direct offspring counts included
zero and ranged up to 4–12 depending on the run. These demonstrate turnover and
differential reproduction in this designed world, not equal success for all IDs.

Initial mean traits ranged from 444.39 to 524.16. Both treatments concentrated
near high movement. No-mutation controls still have initial genetic variation
and selection, so this is not evidence that mutation caused that shift. Mutation
maintained more terminal trait variants, but these observations do not establish
a demographic benefit from mutation.

All ten runs collapsed to one founding lineage. Do not confuse mutation-created
variants within that lineage with sustained ecological diversity. V0 currently
supports a narrow trait axis and limited novelty; it is not open-ended evolution.

Next: campaign 002 fixes founder traits and varies movement costs on held-out
seeds to test environmental dependence. Do not add a controller before checking
what these simple rules already explain.

Visual verification: baseline seed 0 replay loaded in a browser; slider end
showed tick 5,000, population 73, generation 113, matching raw metrics. Founder
color selection and playback changed the displayed world and tick as expected.
