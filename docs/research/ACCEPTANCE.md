# V0 acceptance checkpoint

Current verified research: nineteen campaigns / 904 executions / 8,240,000 computed
ticks, including 24 follow-up executions and 212,000 repeated prefix ticks.
Use the [current Chinese review guide](REVIEW.zh-CN.md) for the latest instructions.

Latest [nineteen-campaign draft](https://github.com/nikolasandwich/bitgenesis/releases/tag/untagged-bd1c724e09502d74998e): source `eec26ab`,
1,961 payload files / 134,751,855 bytes. Fresh extraction reproduced all three
campaign-019 reports; a new noneditable installation passed 150 tests and a
1,000-tick demo audit with reference-equivalent records. Remote asset sizes and
SHA256 values match local files. The separate observation supplement supplies
campaign-017 retrospective observer data. Older archives remain unchanged.

Evidence: [extraction](results/portable-review-019.json), [installation](results/portable-wheel-019.json),
[remote assets](results/release-019.json), and [source CI](https://github.com/nikolasandwich/bitgenesis/actions/runs/34815145967).

## Preserved earlier checkpoint notes

The dated and version-specific statements below describe earlier deliveries.
Their references to "current" or "newest" apply to those historical checkpoints,
not the latest download above.

Current research: fourteen campaigns / 710 executions / 6,220,000 computed ticks;
20 executions are longer follow-ups with 200,000 repeated prefix ticks, not new
independent seed replicates. See the [research index](README.md) and latest
[long-horizon report](campaign-011.md).
The latest [birth-cost report](campaign-012.md) adds eighty verified executions.
It is included in the current page, but not in the eleven-campaign fixed archive.
The newest [genome-coverage report](campaign-013.md) adds ten verified 50000-tick
worlds; it is included in the thirteen-campaign page and newest archive.
The [frequency-cost report](campaign-014.md) adds 160 independently verified worlds;
it is included in the fourteen-campaign page and newest uploaded archive.
Visual review entry `data/review-v0-14.html` covers all fourteen campaigns, including
the allocation trajectories, threshold/cost survival curves, longitudinal follow-up
and cumulative versus living genome coverage, plus the complete frequency-cost grid.
It distinguishes executions from independent samples and identifies replayed prefixes.
Earlier pages remain preserved. The uploaded nine-campaign archive excludes 010–011.
Newest uploaded archive: `data/bitgenesis-v0-fourteen-campaigns.zip`, source
`6d98fb94dee3d07b09e5cd2edd1b9f383dd06c52`, 1044 payload files / 96,447,134 bytes.
SHA-256: `0501fd0c6cf4d947ee26fb3fc107b592adf5f9c66d854531b7ef364ff6b6240a`.
It contains all fourteen campaigns, the fourteen-campaign page and the newer
trait-change analyses and checkpoint validation code. Packaging reran eleven
full-run audits and the selected 005/009–014 metric checks. Standalone expected-hash
verification passed: 13 HTML pages and eleven local targets. Source
[CI 34786711417](https://github.com/nikolasandwich/bitgenesis/actions/runs/34786711417) passed.
The [fourteen-campaign draft](https://github.com/nikolasandwich/bitgenesis/releases/tag/untagged-5f2b766924cc208bb796)
contains the archive and checksum; GitHub asset size and digest match the local copy.
An extracted copy's archived 014 verifier ran under Python 3.12 with `-I -S` and
reproduced the complete stored verification JSON (480160 rows, all 160 outcomes,
input/script/metadata hashes). This reused an existing interpreter, not a fresh
installation or new simulation. Earlier draft assets remain unchanged.

Fresh-install check of the fourteen-campaign source: built and installed a
noneditable wheel in a new Python 3.12.10 environment, confirmed imports from its
site-packages, and passed all 78 archived tests. A new 1000-tick installed-CLI
run passed its full artifact audit. Metrics/events match the archived acceptance
demo byte for byte; lineage and summary JSON match structurally. Pip resolved build
dependencies, so this is not an offline-install guarantee or a fourteen-campaign
simulation rerun. [Recorded checks](results/portable-wheel-014.json).

Browser checks of that freshly installed demo also passed: blank and fractional
IDs clear stale details, valid Enter queries restore them, and parent navigation
1640 -> 1618 shows the expected parent and three children. The values match raw
lineage. [Manual browser evidence and limits](results/lineage-browser-014.json).
This is not cross-browser or screen-reader speech certification.

Previous uploaded archive: `data/bitgenesis-v0-thirteen-campaigns.zip`, source
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

## Fifteen-campaign local archive — 2026-09-14

`data/bitgenesis-v0-fifteen-campaigns.zip` contains source
`0344839a39bf943bc2634583b04ee2b496c94a13`, all fifteen campaigns, the
fifteen-campaign page, latest failure-status fix and 92 tests. This is a new local
snapshot; it does not change the uploaded fourteen-campaign draft.

- 1,071 payload files; 100,031,797 bytes.
- SHA-256: `a98e0f3427a21dc93376453063ad280cd930da00ca779eba2687ff3701a936df`.
- Eleven full recorded-run audits plus campaign-005 and 009–015 metric audits.
- Standalone standard-library verification with the expected hash passes:
  thirteen HTML pages and twelve local targets.
- Manifest workload: 714 executions / 6,340,000 ticks, including 24 follow-ups
  and 212,000 replayed prefix ticks.

Campaign 015's audit rechecks 120,004 metric rows and 12,004 reference-prefix
rows. This confirms consistency of recorded artifacts, not independent reruns
or a biological interpretation. Fresh extracted installation and upload remain
separate follow-up checks. The packaging command documentation was refreshed on
main after this fixed source snapshot; its included fourteen-campaign example
remains a valid older-scope command, while `--campaigns 15` is supported.

### Independent installation of the fifteen-campaign archive

Extracted the hash-verified archive into `data/portable-review-15`, created a new
virtual environment and installed a noneditable wheel from its source. Confirmed
imports come from that environment's site-packages. All 92 archived tests pass.
The new 1,000-tick demo passes the artifact audit: 83 living, 1,561 births,
1,558 deaths, 1,641 recorded individuals and 101 frames. Metrics/events match the
archived acceptance demo byte for byte; lineage/summary JSON agree structurally.
Installed metadata correctly does not attribute the enclosing checkout's Git ID.

Using extracted scripts and raw records, the campaign-015 verifier reproduces the
complete saved report, including all input and helper hashes. Its 120,004 metric
rows and 12,004 reference-prefix rows are checked. The script ran with `-S` and
its normal script-directory import path; the simulation demo ran with `-I`.
Build dependencies were resolved by pip, so this is not an offline-install claim.
These 1,000 engineering ticks do not increase formal experiment totals.
See [portable installation record](results/portable-wheel-015.json).

### Fifteen-campaign uploaded draft

[Draft v0.0.1-preview.7](https://github.com/nikolasandwich/bitgenesis/releases/tag/untagged-00e18fdc0b94307ac16e) (release 388062162)
remains a draft/prerelease targeting source `0344839`. Both assets are uploaded;
GitHub API archive size 100,031,797 and SHA-256 match the verified local file.
The 103-byte checksum asset also matches local SHA-256
`5b8c873fa74c84ce0d22332bd442376f2870a56b09d292829e5e9591eb54bb00`.
Source CI 34788400431 is successful. Prior draft assets remain unchanged.

## Sixteen-campaign local archive — 2026-09-14

`data/bitgenesis-v0-sixteen-campaigns.zip` fixes source
`8acb86c8c81f8a5ec7ed0ad29760a809999e53fa`, all sixteen raw campaigns and the
sixteen-campaign page. It includes 106 tests and the subsequent-to-fifteen-archive
provenance and audit corrections. The simulator rules are unchanged.

- 1,154 payload files; 101,914,494 bytes.
- SHA-256: `765f6995fc9ca7a03ea9c8e5d0d80779e93bb8b93faa89092b48885038b37c11`.
- Eleven full-run audits plus campaign-005 and 009–016 metric audits pass.
- Independent expected-hash verification confirms thirteen HTML pages and
  thirteen local targets. This is file integrity, not a simulation rerun.
- Manifest workload: 744 executions / 6,640,000 computed ticks, including
  24 follow-ups and 212,000 replayed prefix ticks.

Campaign-016 initialization and metric checks cover thirty initial states and
300,030 rows. Fresh extracted installation and remote upload are separate next
checks; the existing fifteen-campaign download remains unchanged.

### Independent installation and upload of the sixteen-campaign archive

Fresh extraction and noneditable installation passed all 106 archived tests.
The installed module resolves inside the new environment, and generated metadata
correctly records no Git commit. A new 1,000-tick demo passes the archived audit;
metrics/events match the archived acceptance run byte for byte, with lineage and
summary structurally equal. These demonstration ticks are not formal experiments.

The archived standalone campaign-016 verifier, run with isolated standard-library
Python, checks 30 initial states, ten matched seed triplets and 300,030 metric
rows. Its complete JSON report, including source/input hashes, equals the archived
report. Pip resolved build dependencies; offline installation and rerunning every
campaign are not claimed. See [installation record](results/portable-wheel-016.json).

[Draft v0.0.1-preview.8](https://github.com/nikolasandwich/bitgenesis/releases/tag/untagged-c526b608b2e4ff9bd666)
(release 388070091) targets source `8acb86c` and remains a draft/prerelease.
GitHub API confirms both assets uploaded with local sizes and SHA-256 values.
The 103-byte checksum asset hashes to
`452e631841435b54922e0559786e32f2c00bb6b936f6dd5e078cc8e472a9861d`.
See [remote asset record](results/release-016.json).
Source CI 34789953078 completed successfully. Earlier draft assets are unchanged.

## Seventeen-campaign local archive — 2026-09-14

`data/bitgenesis-v0-seventeen-campaigns.zip` fixes source
`8e4cf89d764b5fad3666498c4d66f6f97e547077`, all seventeen raw campaigns,
the seventeen-campaign review page and 117 tests. It also includes the later
parameter-domain audit correction and campaign-016 retrospective access/budget
analyses. V0 dynamics remain unchanged.

- 1,260 payload files; 106,192,281 bytes.
- SHA-256: `7c0e66bb1603dfa64a6e11416b5658f8ee8ff268fb8c447468b11edc7458ddac`.
- Eleven full-run audits plus campaign-005 and 009–017 metric audits pass.
- Standalone standard-library verification with the expected hash passes.
- Workload: 784 executions / 7,040,000 computed ticks, including 24 follow-ups
  and 212,000 replayed prefix ticks.

Extracted installation and remote upload remain separate next checks. The fixed
sixteen-campaign download and earlier archives are unchanged.

### Independent installation and upload of the seventeen-campaign archive

Fresh noneditable installation from the extracted archive passes all 117 tests.
A new 1,000-tick demo passes the archived audit and matches reference metrics and
events byte for byte, with lineage/summary structurally equal. Installed metadata
has no Git commit. The archived campaign-017 verifier and sibling helper recreate
the entire verification report, including hashes, from the extracted records.
Pip resolved build dependencies; no offline-install or all-campaign rerun claim.
See [installation record](results/portable-wheel-017.json).

[Draft preview.9](https://github.com/nikolasandwich/bitgenesis/releases/tag/untagged-817afa7dc5fa0391cfcc) (release 388158362) targets source `8e4cf89`.
Both uploaded assets match local size and SHA-256 according to the GitHub API.
See [remote asset record](results/release-017.json). Source CI 34808083099
completed successfully. Previous draft files remain unchanged.
