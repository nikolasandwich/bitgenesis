# Campaign 007 — Persistence does not require new mutation here

Sixty preregistered runs / 300,000 ticks completed from clean source
`0b73705a69db36d57665b4f85fc2172ea06fe8ea`. All use resource regrowth 15/1000,
32×32 worlds and 80 founders, with seeds 600–609 and a 5000-tick horizon.
See [protocol](../../experiments/v0/campaign-007.md) and
[all seed outcomes](results/campaign-007.csv).

The strongest result is a counterexample to necessity: some populations with
identical founder traits and no mutation persisted to tick 5000. Thus persistence
over this horizon does not require new trait variants, or even initial variation
in the encoded movement trait. This does not establish indefinite persistence.

| Founder genomes | Mutation attempt per birth | Alive at 500 | Alive at 5000 | Extinct-only tick range | Late group mean population |
| --- | --- | --- | --- | --- | --- |
| Random | 0% | 9/10 | 7/10 | 127–1198 | 22.9116 |
| Random | 10% | 10/10 | 9/10 | 3897 | 27.6514 |
| All 250 | 0% | 10/10 | 7/10 | 2054–4120 | 27.5463 |
| All 250 | 10% | 10/10 | 7/10 | 576–959 | 22.2580 |
| All 1000 | 0% | 4/10 | 4/10 | 63–87 | 11.7818 |
| All 1000 | 10% | 3/10 | 2/10 | 83–3169 | 5.7636 |

250 and 1000 mean 25% and 100% probability of attempting random movement per
step. They specify initialization; mutation-enabled populations can change later.
Late means average ticks 4001–5000 and include all seeds and extinction zeros.
Survivors are right-censored at 5000. Extinct-only time ranges exclude survivors.

## Why the intermediate checkpoint matters

All initially-250 runs were alive at tick 500, but only seven per treatment were
alive at 5000. High initial movement lost most runs before tick 500. Equal terminal
counts for the two 250 treatments conceal different observed extinction timings;
neither establishes equal underlying probabilities or identical mechanisms.

Mutation-enabled random founders survived in nine of ten runs versus seven without
mutation. The high-initial-trait group showed the opposite numerical direction,
two versus four. These ten-seed differences are descriptive. They neither prove
mutation beneficial/harmful in general nor justify a significance claim. The same
seed does not hold later environmental draws fixed after the random streams diverge.

The no-mutation random group still allows selection among pre-existing heritable
variants. The no-mutation fixed-trait groups retain exactly one encoded trait in
every surviving population; demographic and spatial randomness remain. Comparing
fixed and random founders changes the whole trait distribution, not just diversity.

This experiment narrows the explanation of persistence. It does not isolate every
mechanism of establishment or measure intelligence, innovation or learning.

## Verification

Engine invariants ran every tick. A separate script, without importing the engine,
read all 300,060 metric rows, checked the complete treatment grid and tick ranges,
population/energy accounting, initial fixed traits, no-mutation trait constancy,
absence of population reappearance after extinction, and every terminal metric
plus the declared intermediate/late summaries against saved JSON outcomes.
This is accounting and summary consistency, not dynamics replay or lifecycle audit.

```sh
python scripts/summarize_v0_establishment.py --input data/campaign-007 --output data/new-establishment-summary
```

The [verification sidecar](results/campaign-007-verification.json) includes all raw
CSV hashes and analysis script hash. Raw data remain in `data/campaign-007/`.
CI passed for the preregistered source in run 34775566923. Core rules were unchanged.

Formal totals now: 350 runs / 1,540,000 ticks. The six-campaign HTML and archive
remain the preceding review snapshot; this report and its all-seed CSV add the
seventh campaign without altering earlier results.
