# V0 acceptance checkpoint

Current research: fourteen campaigns / 710 executions / 6,220,000 computed ticks;
20 executions are longer follow-ups with 200,000 repeated prefix ticks, not new
independent seed replicates. See the [research index](README.md) and latest
[long-horizon report](campaign-011.md).
The latest [birth-cost report](campaign-012.md) adds eighty verified executions.
It is included in the current page, but not in the eleven-campaign fixed archive.
The newest [genome-coverage report](campaign-013.md) adds ten verified 50000-tick
worlds; it is included in the thirteen-campaign page and newest archive.
The [frequency-cost report](campaign-014.md) adds 160 independently verified worlds;
it is not yet included in the thirteen-campaign page or uploaded archive.
Visual review entry `data/review-v0-13.html` covers all thirteen campaigns, including
the allocation trajectories, threshold/cost survival curves, longitudinal follow-up
and cumulative versus living genome coverage.
It distinguishes executions from independent samples and identifies replayed prefixes.
Earlier pages remain preserved. The uploaded nine-campaign archive excludes 010–011.
Newest uploaded archive: `data/bitgenesis-v0-thirteen-campaigns.zip`, source
`1fc1c30dfcb6bcccbc929c0ba75ea5957272bc60`, 853 payload files / 86,150,042 bytes.
SHA-256: `ed6e90acda91f1b8e74f88acca5f246c03ee308c627cb611c3e2d180cd1383f2`.
It adds campaign 013 raw birth catalogs and metrics, the thirteen-campaign page,
and the corresponding verifier. Packaging reran eleven full-run audits and
metric verifiers for 005/009–013. Standalone expected-hash verification passed:
13 HTML pages and ten local targets. Source CI
[34785000803](https://github.com/nikolasandwich/bitgenesis/actions/runs/34785000803) passed.
The [thirteen-campaign draft](https://github.com/nikolasandwich/bitgenesis/releases/tag/untagged-507ea861ad4cf6ec9e02)
contains both archive and checksum. GitHub reports matching size and SHA-256.
An extracted copy recomputed the complete 013 verification JSON exactly,
including all input and script hashes, using Python 3.12 with `-I -S`.
This used the existing interpreter, not a new installation or a new simulation.
It checked 744901 birth rows and 500010 metric rows using archived code/data.

Previous uploaded archive: `data/bitgenesis-v0-twelve-campaigns.zip`, source
`11da88c6c19729b066a8ad4e30ca1362ae896c77`, 815 payload files / 70,481,664 bytes.
SHA-256: `121e11e56b22cd20c2f584b2989e9c25d9348042208ba02232cc4d1bdfad7cd4`.
It includes all twelve raw campaigns and the twelve-campaign review page. Packaging
reran eleven full-run audits and metric verifiers for 005/009/010/011/012;
the 012 report checks 800080 rows. Independent whole-archive verification passed.
The [twelve-campaign draft](https://github.com/nikolasandwich/bitgenesis/releases/tag/untagged-ef4c16aafc92a5c2bb8e)
now holds this archive and checksum. GitHub reports both uploaded with the
archive size and digest matching the local copy. Source CI
[34783294636](https://github.com/nikolasandwich/bitgenesis/actions/runs/34783294636) passed.

Portable research recomputation: extracted the verified twelve-campaign ZIP into
`data/portable-review-12/` and ran its archived campaign-012 verifier and early
budget script against its archived raw inputs. Both summary JSON values match
the archived reports exactly, including hashes; all eighty budget CSV rows are
byte-identical. The budget command ran with Python site-package loading disabled
(`-S`). This checks research recomputation using the existing Python 3.12
interpreter, not a new package installation or another simulation campaign.

The latest uploaded review archive is `bitgenesis-v0-twelve-campaigns.zip`, fixed
source `11da88c`, attached to the `v0.0.1-preview.4` GitHub draft release. The older
eight-, nine- and eleven-campaign drafts remain available. Draft attachments do not
track main and none is a published release. See the [Chinese guide](REVIEW.zh-CN.md) for access and
[archive verification](../design/review-verification.md) before using a snapshot.
Earlier archive descriptions below are explicitly historical.

The preserved eleven-campaign archive is `data/bitgenesis-v0-eleven-campaigns.zip`,
source `eba74b99cd77c323004dfbc743a7b697c341ff12`, 719 payload files / 62,325,938 bytes.
SHA-256: `9a67b9ad14fa66c6eeddbe11bbe0742672d1d8008d6a9da8262bcf3b5b8cf7f4`.
It includes all eleven raw campaigns and its eleven-campaign review page. Packaging reran
11 full-run audits plus the 005/009/010/011 metric verifiers and recorded the
follow-up workload in its manifest. Independent verification matched the expected
whole-file hash and checked 13 HTML pages / eight local targets. The [eleven-campaign draft](https://github.com/nikolasandwich/bitgenesis/releases/tag/untagged-83f2a58ad0f9613a370b)
holds this archive and checksum file. GitHub reports both assets uploaded, with
the archive size and digest matching the local result. Source CI
[34781902624](https://github.com/nikolasandwich/bitgenesis/actions/runs/34781902624) passed.

Fresh-install check of the eleven-campaign ZIP: verified before extraction into
`data/portable-review-11/`, then built and installed its wheel into a new virtual
environment. Imports resolved to that environment's site-packages. All 53 archived
tests and the inventory check passed. A new 1000-tick demo passed the independent
audit; metrics/events were byte-identical to the archived demonstration, and
lineage/summary JSON values matched. This checks this Windows/Python 3.12 setup,
not an offline installation or a rerun of all campaigns. Build dependencies were
resolved during installation.

The preserved local nine-campaign archive is
`data/bitgenesis-v0-nine-campaigns.zip`, source
`c5975cd5785e7f1ed784382810314545a9076b91`, 628 payload files / 32,997,186 bytes.
SHA-256: `8bf359d6f156ea71d0f15c6d5eee5f087e86af30e6d4db94562fe38c398895a6`.
It includes campaign 009, its raw metrics and the new page. Packaging reran 11
full-run audits plus campaign-005 and campaign-009 metric verification. Independent
ZIP verification passed. A separate [nine-campaign draft](https://github.com/nikolasandwich/bitgenesis/releases/tag/untagged-f053eec4d3332539ca25)
now holds this archive and checksum file. GitHub's uploaded asset digest matches
the hash above; the eight-campaign draft was not replaced.

Verified compatibility checkpoint: source `12982c7`, 56 tests passed on
Windows/Linux × Python 3.12/3.13/3.14 in
[run 34783952259](https://github.com/nikolasandwich/bitgenesis/actions/runs/34783952259).
The tracked campaign-inventory check also passed in all six jobs.
These counts describe named source checkpoints, not the test count of every archive.
This covers the frozen fixture and CLI/recovery contracts; it is not all research
campaigns replayed on six configurations. Checkpoint Python-version restrictions remain.

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

### Historical five-campaign checkpoint

Twenty-five checks passed at that checkpoint. Campaigns 001–005 cover 990,000
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

The historical Chinese entry point is `data/review-v0-5.html`. The local five-campaign
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
  environmental events. The frozen test matches on the six tested platform/
  interpreter combinations cited above; this is not a guarantee for every run or future version.
- Complete lineage remains in memory; replay and chart retention are now bounded.
- Trait mutation clamps at boundaries. Exact calibration found inward one-birth
  mean drift near the edges; it does not predict the selected population distribution.
- Whole-population fixed-trait results do not replace direct competition tests.

Direct competition, a frozen replay regression, and installed-package provenance
are now checked, as are longer-horizon/resource regimes, independent artifact
auditing and portable review bundles. A V1 proposal is documented,
but V0 remains the only runtime. Preserve existing rules and preregister experiments.

## Supplements on main

These analyses and engineering checks do not increase the formal campaign count:

- [Energy budgets](energy-budget.md): reconstruct expenditure from existing fixed-trait runs.
- [Retention benchmark](retention-benchmark.md): measured history and serialization memory limits.
- [Encoded behavior ceiling](../design/emergence.md): movement-trait diversity is not new controller structure.
- [Survival uncertainty](campaign-008.md#exploratory-uncertainty-supplement): pointwise, model-based intervals from ten worlds per treatment.
- [Checkpoint contract](../design/checkpoints.md): structural validation and continuation across empty, extinct, saturated and event-drained states.

The [continuous log](LOG.md) records source-specific validation and decisions.
V1 remains a [design proposal](../design/v1-proposal.md), with a separate
[experiment design](../design/v1-experiment-design.md), not an implemented runtime.
