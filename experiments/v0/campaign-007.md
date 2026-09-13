# Campaign 007: founder traits and mutation under scarce resources

Preregistered before seeds 600–609 are run. Campaign 006 found mixed extinction
and finite-horizon persistence at resource regrowth 15/1000. Test whether continued
mutation is necessary for persistence under this condition, and how founder trait
initialization changes outcomes.

Factorial design: founder genomes ordinary uniform-random, all 250, or all 1000;
mutation probability 0 or 100/1000 births. Hold other baseline values fixed,
including 32×32, 80 founders, energy 24, initial food 8, movement cost 1 and resource
regrowth 15/1000. Each combination uses seeds 600–609 for 5000 ticks: 60 runs /
300,000 ticks. Run through the horizon even after extinction.

Initialize normally to retain the same seed-specific founder positions and RNG
state, then replace all founder genomes for the fixed-initial-trait groups before
any step. Clear pending founder events because this metric-only assay does not
export events. With mutation on, fixed *initial* traits can subsequently change.
With mutation off, random founders still provide standing heritable variation and
can undergo selection; disabling mutation does not disable evolution generally.

Primary: extinct fraction by 5000, first extinction tick per run, and survival
status at tick 500. Secondary: terminal population, mean population over ticks
4001–5000 including extinction zeros, and mean trait at tick 500 and termination.
Survivors are right-censored at the horizon. Preserve all seeds, conditions,
per-tick metrics and provenance. No discarded outcomes or replacement seeds.

Prediction: persistence may occur without new mutations, depending on founder
traits; mutation is not presumed beneficial. Comparisons of fixed and random
founders change the trait distribution, not only its variance. Mutation consumes
additional RNG draws, so same-seed treatments do not have identical later resource
realizations. These small-group frequencies are descriptive, not proof of equal
probabilities or a formal causal decomposition of all establishment mechanisms.
No intelligence or open-ended evolution claim is part of the experiment.

```sh
python scripts/run_v0_establishment.py --output data/campaign-007
```
