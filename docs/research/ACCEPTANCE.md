# V0 acceptance checkpoint

Current research: eight campaigns / 370 runs / 1,740,000 ticks; see the
[research index](README.md). Latest report: [initial food and establishment](campaign-008.md).
Visual review entry `data/review-v0-6.html` and archive `data/bitgenesis-v0-review-6.zip`
cover the preceding six campaigns (290 runs / 1,240,000 ticks).
Earlier archive descriptions below refer to preserved historical snapshots.

## What runs now

Python 3.12+ package and CLI, original scaffold compatibility, finite toroidal
world, explicit organisms, inherited random-movement trait, resource regeneration,
feeding, reproduction, mutation, death, exact energy accounting, and local RNG.
No later-stage runtime or built-in food-seeking policy has been added.

```sh
python -m pip install -e .
python -m unittest discover -s tests -v
bitgenesis v0 --config experiments/v0/darwin-baseline.toml --steps 1000 --output data/my-review
```

Open `data/my-review/index.html` for replay and `lineage.html` for individual
inspection. Inspect a newborn ID, navigate to its parent, and compare recorded
genomes, generations and offspring counts. Both pages work without external
services. Use a new output path each time.

## V0 graduation evidence

| Criterion | Evidence | Status |
| --- | --- | --- |
| Birth/action/feed/reproduction/death loop | Engine plus campaign lifecycle logs | Met |
| Boundaries, energy/resource bounds, inheritance | Tests and per-tick invariants | Met |
| Same-seed repeatability | Events, spatial state and lineage replay test | Met on tested Python/runtime |
| Genomes, parent IDs, birth/death, offspring, metrics | JSONL/JSON/CSV outputs and metadata | Met |
| Five seeds, heritable variation, differential reproduction, no-mutation control | Campaign 001, ten runs | Met within stated scope |
| Basic world view and lineage inspection | Replay + clickable ancestry inspector | Met |
| Explain designed rules | `docs/design/v0-rules.md` and emergence note | Met |

Twenty-five checks passed at this checkpoint. Campaigns 001–005 cover 990,000
simulation ticks. Campaign 001 finds lineage collapse; campaign 002 shows that
the trait supporting more individuals in a fixed-trait assay need not match the trait favored in
mixed populations; campaign 003 directly tests competition with neutral-label
controls and confirms dependence on movement cost. Campaign 004 separates
extinction, turnover and crowded persistence without reproduction. Campaign 005
shows how finite world size and observation time qualify founder-loss conclusions.
Read the reports before
interpreting animations. An installed wheel and its provenance were also tested.
GitHub CI verified Windows/Linux and Python 3.12/3.13, including the frozen replay:
[run 34774116377](https://github.com/nikolasandwich/bitgenesis/actions/runs/34774116377).
All four jobs ran and passed the 25-check suite.

The read-only `bitgenesis audit` command independently reconciled all ten full
campaign-001 runs and the acceptance demonstration, plus a sampled extinction
run. It catches corrupted energy accounting, missing lifecycle events and broken
parent references. This checks artifact consistency, not biological validity.

The current Chinese entry point is `data/review-v0-5.html`. The local five-campaign
archive is `data/bitgenesis-v0-review-5.zip`, source checkpoint `54078bf`; its
398 files were read back and matched against their manifest hashes. A refreshed
documentation checkpoint can be packaged with `--output data/bitgenesis-v0-review-5b.zip`.
Earlier three/four-campaign pages and archives remain preserved. Existing archives
are never overwritten; use a new `--output` for each later checkpoint.

V0's minimal milestone is reached. Continue V0 mechanism/robustness experiments
before deciding whether a V1 controller adds a useful research question. Meeting
this checklist does not certify realism or open-ended evolution.

## Limits and next work

Since the five-campaign archive, state-only checkpoint recovery was added at
`0ad9f86`. All 30 tests passed locally, and all four CI jobs passed in
[run 34774790013](https://github.com/nikolasandwich/bitgenesis/actions/runs/34774790013).
A 1,000 + 1,500 tick continuation produced a byte-identical complete state file
to a continuous 2,500 tick run. See the [recovery guide](../design/checkpoints.md)
for its compatibility requirements and limits; this does not resume replay/CSV
recording. Existing review archives retain their earlier source snapshots.

- Organisms, inheritance, reproduction, resource rules and trait meaning are
  designed assumptions. No abiogenesis claim.
- Stochastic treatments share initialization, not guaranteed identical future
  environmental events. The frozen test matches on the four tested platform/
  interpreter combinations; this is not a guarantee for every run or future version.
- Complete lineage remains in memory; replay and chart retention are now bounded.
- Trait mutation clamps at boundaries. Exact calibration found inward one-birth
  mean drift near the edges; it does not predict the selected population distribution.
- Whole-population fixed-trait results do not replace direct competition tests.

Direct competition, a frozen replay regression, and installed-package provenance
are now checked, as are longer-horizon/resource regimes, independent artifact
auditing and portable review bundles. A V1 proposal is documented,
but V0 remains the only runtime. Preserve existing rules and preregister experiments.
