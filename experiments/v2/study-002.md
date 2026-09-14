# V2 study002: population inheritance under developmental costs

Preregistered before running these seeds. This descriptive population experiment
asks whether actual inherited changes occur, remain viable, and leave descendants.
It does not test developmental encoding superiority or certify adaptation.

Run ten independent source seeds84000..84009, each with mutation_per_thousand100
and0, in that order. All20 worlds use existing v2-world-1 developmental encoding,
intact sensing,16x16 sites,32 attempted random founders, initial energy640,
birth threshold1280, renewal15, and every other Config default. These parameters
come from pilot001's predeclared selection. Run3000 ticks including after
extinction. Never replace failed founders, extinct worlds, or unproductive seeds.
Paired arms must have identical initial states. Mutation streams and subsequent
trajectories may diverge; shared seeds do not imply paired individual histories.

Retain full attempts, events, lineage, states, actor records and source hashes.
Independently audit every world. Report all20 outcomes and ten paired contrasts,
with terminal population difference (mutation100 minus0) as the primary
descriptive contrast. Also report extinction tick, births, maximum generation,
founder and offspring development failure denominators/reasons, actual changed
offspring genotypes and their successful construction. A zero-mutation arm can
still undergo selection among initial genotypes; it is not a no-selection control.
Use source-level summaries, not offspring as independent experimental units.
No significance test or positive-result threshold is registered.

For each successful nonfounder, link its actual parent and founding ancestor.
Report genome changes relative to each and its own successful offspring count.
Keep unsuccessful attempts in separate unconditional denominators. A change
in realized controller may arise from different construction budgets even without
a genotype change; do not equate phenotype change with genetic mutation.
Any later fixed-budget behavioral assays or held-out competitions must be
separately defined and labeled exploratory unless registered before that phase.
Persistence or increased population alone is not evidence of improved information
use, and a mutation-arm difference does not isolate natural selection from drift.

Freeze clean source and protocol hashes before launch. Each run has a worst-case
768000 actor-record bound. Check8GiB total storage between runs; one bounded run
may exceed this soft threshold before the next check. Stop and label incomplete
on storage limit or error, preserving all records. Do not silently resume or
overwrite existing output. Publish complete-grid verification before conclusions.
