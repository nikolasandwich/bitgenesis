# Campaign 013: long-window coverage of the fixed V0 genome vocabulary

Preregistered before running fresh seeds 1100–1104. Follow the baseline V0
world for 50000 ticks with mutation probability 100/1000 versus zero. Keep the
ordinary random founder genome pool; all other darwin-baseline.toml parameters
are unchanged. Two arms × five seeds = ten executions / 500000 ticks. No
outcome-dependent seed replacement, stopping or horizon extension. Include
extinct worlds through the observation endpoint. Shared seeds match initial
conditions, not future environmental random draws after trajectories diverge.

Primary observations: distinct genome values ever born at ticks 0, 1000, 5000,
10000, 25000, 40000 and 50000; distinct values added in 40001–50000. Count a
value once at its first observed birth, including founders at zero. Also record
living genome diversity, founder count, population, mean trait, births/deaths,
extinction and maximum living generation at these horizons and at the endpoint.
Save all per-tick metrics with ever-seen diversity and a compact birth table
(id, parent_id, birth_tick, genome) for every individual. Keep the full engine
lineage internally but do not export full death events or spatial replay.

Prediction: mutation permits new scalar values beyond the founding pool, whereas
the no-mutation arm must never do so. The long-window rate of new scalar values
may decline or remain nonzero; neither outcome is defined as a functional
innovation. Do not force a plateau model or interpret an observed plateau as
proof that no new value can ever occur. These rules can encode exactly 1001
movement probabilities, not new sensors, memory, topology or action meanings.
The collective world state is much richer than that inherited vocabulary.

Report all five worlds per arm without survivor selection. New-value counts
are per-world observations, not independent counts of evolutionary innovations.
Generation depth is genealogical depth, not a synchronized population generation.
This is a longer assay with new seeds, not extension/replay of campaign 001.

Commit protocol and runner first, record clean provenance, check invariants each
tick and independently reconstruct first-seen values from complete birth tables.
Verify contiguous IDs, parent-before-child and earlier parental birth, inherited
genome closure in no-mutation worlds, complete tick sequences, energy/population
accounts, cumulative diversity and declared horizon/end-window summaries.
Do not add results to verified campaign totals until that check passes.

```sh
python scripts/run_v0_genome_coverage.py --output data/campaign-013
```

All outputs go to a new directory. This changes observations, not V0 rules or
existing defaults. Existing archives remain fixed.
