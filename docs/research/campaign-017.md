# Campaign 017 — Food layout and reproduction threshold

All twenty high-threshold worlds survived to tick 10,000. At the original
threshold, two dispersed worlds survived and no block world survived. Raising
the threshold also reduced early births and prevented the initial population
from exceeding its founder count in these twenty worlds.

| Food layout | Birth threshold | Alive at 500 | Alive at 5,000 | Alive at 10,000 | Extinction range among extinct worlds |
| --- | ---: | ---: | ---: | ---: | --- |
| Dispersed | 40 | 5/10 | 2/10 | 2/10 | 148–3,620 |
| Dispersed | 160 | 10/10 | 10/10 | 10/10 | None observed |
| Block | 40 | 2/10 | 0/10 | 0/10 | 119–3,903 |
| Block | 160 | 10/10 | 10/10 | 10/10 | None observed |

Within dispersed layouts, eight seed pairs changed from extinct at 10,000 under
threshold 40 to alive under 160, and two were alive under both. Within block
layouts all ten pairs changed from extinct to alive. These are endpoint paired
comparisons; right-censored high-threshold runs do not provide their eventual
extinction times. Twenty high-threshold executions are ten seed quadruplets,
not twenty independent seed blocks or evidence of permanent stability.

## Predeclared early observations

Ranges below are across ten worlds per treatment during ticks 0–100. Food uptake
covers ticks 1–100; population peaks include the initial 80 founders.

| Layout / threshold | Births by 100 | Peak population | Population at 100 | Food consumed by 100 |
| --- | ---: | ---: | ---: | ---: |
| Dispersed / 40 | 33–51 | 97–120 | 2–10 | 2,856–3,980 |
| Dispersed / 160 | 0 | 80 | 7–20 | 3,028–3,848 |
| Block / 40 | 100–120 | 116–157 | 1–15 | 5,484–6,164 |
| Block / 160 | 2–9 | 80 | 11–25 | 2,508–4,600 |

These windows and observations were fixed in the protocol before execution.
Higher threshold changes reproduction eligibility and timing, individual energy
storage, population size and subsequent interactions together. The experiment
therefore supports a threshold-dependent outcome in these settings, without
identifying birth cost, crowding or another mediator as the unique cause.
There is no evolved sensing or controller: all genomes remain fixed at 250.

The original-threshold block results also qualify campaign 016: that earlier
seed block went extinct by tick 169, whereas the new block seeds include
extinctions at 230, 645 and 3,903. Reported ranges belong to the sampled seeds;
the earlier range is not a bound on all V0 worlds. No old results were replaced.

## Controlled initialization and verification

The [preregistered protocol](../../experiments/v0/campaign-017.md) crosses layouts
dispersed/block with thresholds 40/160 for every seed 1400–1409, 10,000 ticks each.
All other specified settings match campaign 016. Initial energy is 7,040,
including 5,120 food units; maps share the same food-value multiset. Each seed
quadruplet has identical founder records and world RNG state. Threshold pairs
within each layout have identical food maps. Subsequent RNG draws and realized
replenishment can differ. These are new seeds, not extensions of old worlds.

Clean launch source: `05508f0fd1d933fbc318a80440e3990f698586b6`, Python 3.12.10,
rules `v0-darwin-1`. Execution completed all forty runs. The independent verifier
checks forty initial states, ten founder/RNG quadruplets, twenty threshold-map
pairs, **400,040 metric rows** and **4,000 early feeding transitions**. It rebuilds
all saved observations and endpoints and requires exact equality with result JSON.

The verifier checks actual threshold/configuration before reusing the independent
campaign-016 initial-map/founder/RNG checker. Its common metric bounds remain
valid at either threshold because birth cost, basal cost and movement cost do not
change. Full individual history and movement observations were not retained;
record consistency is not an independent dynamic replay or proof of mediation.

[All forty outcomes](results/campaign-017.csv) ·
[Verification, groups and hashes](results/campaign-017-verification.json).
The standard-library verifier imports its sibling helper via normal script path:

```sh
python -S scripts/summarize_v0_geometry_threshold.py --output data/new-geometry-threshold-check
```

All 117 local tests pass at this checkpoint. Launch source passed the six-platform
CI matrix ([run 34790910564](https://github.com/nikolasandwich/bitgenesis/actions/runs/34790910564));
that earlier CI covers the runner, not this later verification/report addition.
The new verification tests reject wrong thresholds, wrong RNG, missing early
observations and inconsistent feeding, and check earliest-tie peak selection.

This campaign adds forty executions / 400,000 computed ticks, no replay prefix.
Completed totals become seventeen campaigns / 784 executions / 7,040,000 computed
ticks, including the existing 24 follow-ups and 212,000 replayed prefix ticks.
The fixed sixteen-campaign download does not contain campaign 017.
