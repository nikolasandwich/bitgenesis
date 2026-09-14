# Research log

## 2026-09-14 — Autonomous cycle 1

User authorized continuous independent progress until stop or acceptance review.
Prioritize a measured V0 before adding V1. Preserve original scaffold semantics.

Decisions:

- Implement a scalar inherited random-movement probability instead of a neural
  controller; the latter belongs to V1. Do not write food-seeking behavior.
- Use integer energy and an explicit external regrowth supply to allow exact
  accounting and meaningful invariants at every tick.
- Keep new dynamics under `bitgenesis.v0` and `v0-darwin-1`; keep empty-world
  commands and definitions unchanged.
- Record provenance, raw lifecycle events, metrics, lineage and replay artifacts.
- Test matched initial seeds with and without mutation before asserting adaptation.

Validation so far: 13 unit/integration tests pass, including deterministic replay,
energy accounting across five seeds, inheritance, mutation, newborn scheduling,
torus boundaries, extinction without resources, and output preservation.

Campaign 001 completed: ten 5,000-tick runs, no extinction; all converged to one
founder lineage. Mutation and no-mutation treatments both concentrated near high
movement probabilities. See `campaign-001.md`; do not interpret mutation as
necessary for this initial selection. Replay controls and terminal values checked
in a browser. Next: the preregistered fixed-trait/cost assay (campaign 002).

## 2026-09-14 — Autonomous cycle 2

Campaign 002 completed: 100 runs / 200,000 ticks, no invariant failures. Fixed
trait 250 supported larger populations than 1000 under both costs; expensive
movement at trait 1000 caused extinction in 8/10 seeds. Report all outcomes in
`campaign-002.md`. Do not confuse demographic productivity with individual
reproductive success. Next causal question: direct trait competition.

Added standalone lineage inspection: ID lookup, ancestry navigation, direct
children and founder outcomes. Browser check: individual 1640 -> parent 1618,
founder 24, generation 23; parent showed children 1624, 1631, 1640. New replay
at `data/acceptance-v0/` uses clean commit `27b2137` and records 1,000 ticks.

V0 minimal graduation conditions now have bounded evidence; see `ACCEPTANCE.md`.
Keep exploring V0 mechanisms and hardening reproducibility before adding V1.

## 2026-09-14 — Autonomous cycle 3

Campaign 003 completed: 80 direct-competition/neutral-control runs, 240,000 ticks.
Low movement cost: high trait won 20/20 competition runs. High movement cost:
low trait won 17/20, high trait won 1/20, whole-world extinction in 2/20. Neutral
controls separately show label drift. Report finite frequencies, not universal
optimality. See `campaign-003.md` and its compact CSV evidence.

Added a frozen V0 replay checksum covering lifecycle events, lineage, resources
and metrics. Fourteen tests pass. Built a regular wheel in an isolated build
environment, installed into a fresh environment, and ran its CLI. Fixed installed
package provenance to hash actual source and avoid claiming an enclosing repo's
Git revision. A first no-build-isolation attempt lacked setuptools in the test
environment; standard isolated build succeeded without changing runtime deps.

Next: assemble a concise Chinese acceptance entry point; then continue robustness
and mechanism experiments while preserving the initial V0 rules and results.

Chinese acceptance page generated at `data/review-v0.html` and visually checked;
its statistics are computed from campaigns 001–003. Source generator and Chinese
review guide are committed. This is a fixed checkpoint, not a live experiment.

Campaign 004 preregistered: 20 longer runs across scarce, baseline, abundant and
guaranteed-per-tick regrowth. Measure late birth/death activity to distinguish
demographic persistence from evolutionary turnover. Do not add aging or energy
caps mid-experiment if crowding freezes reproduction.

Recorder hardening: output schema 2 caps retained replay frames and chart samples
while keeping every raw metric tick. Exact frame metrics remain available even
when charts are thinned. Interrupted runs record `interrupted` rather than a
false successful status. Sixteen tests pass, including the unchanged V0 dynamics
fingerprint. Full lineage memory remains an explicit limitation.

## 2026-09-14 — Autonomous cycle 4

Campaign 004 complete: 20 runs / 200,000 ticks. Scarce supply extinguished all
five populations by tick 136; baseline retained turnover with one founder;
abundant stochastic supply retained 3–4 founders at 10,000 ticks. Guaranteed
supply filled all sites by tick 24, then produced no turnover; all original
founders survived while energy accumulated. Preserve this counterexample.

Total formal campaigns: 210 runs / 690,000 ticks. Reports and compact CSVs are
committed; the Chinese review HTML remains the earlier three-campaign checkpoint.

CI run 34773024529 succeeded on Ubuntu/Windows with Python 3.12/3.13, including
installed-package CLI and frozen V0 replay. Sampled long-run viewer also checked
in-browser: final tick 10,001, zero population and no defined generation, matching
its recorded data. Sixteen current tests pass.

Read two primary research publications to contextualize the next decision;
`docs/design/research-context.md` separates their claims from our interpretations.
Added a V1 proposal focused on sensory ablation and held-out reproductive outcomes.
No V1 runtime implemented. Next useful work: independent artifact auditing and
a reproducible local review bundle; retain counterexamples rather than tuning them away.

## 2026-09-14 — Autonomous cycle 5

Added a read-only artifact auditor independent of the stepping engine. It checks
energy and population identities, chronology, inheritance, parent/child counts,
lifecycle completeness, summary equality, replay occupancy/resources and terminal
lineage agreement. Corruption tests cover wrong energy, missing events and orphan
parents. Twenty local checks pass. All ten campaign-001 runs, acceptance-v0 and
sampling-check pass auditing, supporting both legacy and current recording schemas.

Generated the updated Chinese entry point `data/review-v0-4.html` from all four
campaigns. Packaged 348 tracked/source/artifact files into
`data/bitgenesis-v0-review.zip` (14,760,677 bytes), source checkpoint `925b031`.
SHA-256: `68ca58ac879549b4d5754332515942530fe5dd4ebc7f12cebd3a6c5577c02322`.
The packager audited 11 complete runs and verified every archived file hash after
writing. It excludes virtual environments, build intermediates and unrelated data.

Next: check current CI, inspect malformed/partial artifact handling, and improve
operational usability without changing the frozen V0 dynamics. Do not interpret
a successful integrity audit as external validation of the scientific model.

Auditor now independently reconstructs every tick's mean trait, variant count,
founder count and maximum generation from lifecycle records; it no longer merely
compares duplicated aggregate fields. All 12 saved full runs pass the stronger
check. Added malformed/partial artifact tests; 23 local checks pass. CI run
34773495978 passed the preceding 20-check suite on all four platform combinations.

Campaign 005 preregistered: world size at fixed initial density, evolving versus
phenotype-neutral founder controls, 30 runs / 300,000 ticks. This asks whether
founder collapse in small worlds is a finite-horizon demographic effect, without
treating founder labels as species. Existing review bundle remains a frozen
four-campaign checkpoint; do not overwrite it with unfinished experiments.

## 2026-09-14 — Autonomous cycle 6

Campaign 005 completed all 30 runs / 300,000 ticks without extinction or invariant
failures. Small and medium worlds reached one founder under both treatments;
64×64 worlds retained 1–3 founders with evolving traits and three in all neutral
runs. Absolute counts and fractions tell different stories; report both.
Neutral and evolving conditions also differ in realized population size, so their
time differences are not a clean estimate of selection strength.

Total formal experiments: 240 runs / 990,000 ticks. Added a six-panel trajectory
figure with all seeds and pointwise medians, inspected visually. Optional Matplotlib
analysis dependencies do not change the dependency-free engine. Figure provenance
records library version, script hash and every input/output hash.

Added atomic JSON replacement to the main run recorder; failed replacement tests
preserve the preceding valid checkpoint. Twenty-five local tests pass. Earlier
campaign scripts remain available exactly at their recorded commits; a saved
`running` metadata flag must never substitute for a live process check.

Next question: calibrate the bounded mutation kernel separately from selection,
so clamping bias is explicit rather than an untested explanation of high traits.

## 2026-09-14 — Autonomous cycle 7

Exact mutation calibration enumerated all 1,001 genomes and 201 perturbations.
The one-birth mean shift is zero for traits 100–900 and inward near endpoints,
with exact reflection symmetry. At endpoints actual changes occur in about 4.975%
of births despite a 10% attempt rate. This is a calibration, not an added world
experiment; it does not determine long-run selected trait frequencies.

Five-campaign Chinese review page generated and checked visually, including the
trajectory figure. The fifth-campaign review archive at source `54078bf` contains
398 files and 21,227,566 bytes. SHA-256:
`460fea04f1f2ba2769d788c042a15da2c9b9ef173dfb03bcec757367b83a81c8`.
All archive file hashes were verified and 11 full run artifacts audited. Current
documentation now reflects 240 runs / 990,000 ticks and 25 tests.

CI run 34774116377 passed all 25 tests on each of Windows/Linux × Python 3.12/3.13.
Consolidated local preview into one server rooted at the repository so relative
figure links work; old preview processes were stopped. All formal campaigns are
finished; no experiment process remains to be awaited or restarted.

Next: improve experiment recovery/operational ergonomics where evidence warrants
it; keep the V1 proposal as design until a new runtime stage is deliberately scoped.

## 2026-09-14 — Autonomous cycle 8

Added versioned, checksummed JSON state checkpoints with periodic atomic saving
and exact continuation in a new output directory. The existing engine is unchanged.
Recovery retains RNG state and dictionary ordering, and requires matching engine
source and Python major/minor version. An interrupted partial tick is discarded;
the preceding successfully saved complete state remains recoverable.

This is explicitly a state-only command. Existing replay/CSV runs are not resumed
or repaired, and full lineage/event memory remains unbounded. A separate-process
CLI comparison supplements state equivalence, interruption, corruption and
no-overwrite tests. Earlier research bundles remain immutable and represent their
recorded source revisions, before this feature.

All 30 local tests passed, including unchanged frozen-engine regression. The
preceding source revision `13a7b7a` also passed CI run 34774421613 on all four
OS/Python combinations; the checkpoint revision will receive its own CI run.

Checkpoint source `0ad9f86` subsequently passed all four CI jobs in run
34774790013. A baseline seed-42 demonstration used separate processes for 1,000
then 1,500 ticks versus a continuous 2,500 ticks. Both final state files have
SHA-256 `fb3b3bd325df3304d5337ae8f2fc55d658799af5b2646225390c1a0fa0779d41`.
Final population is 81, with 3,780 births and 3,779 deaths. These are operational
validation runs, not additional independent research trials. Local outputs are
preserved under `data/checkpoint-validation/`.

## 2026-09-14 — Autonomous cycle 9

Added an independent read-only verifier for campaign 005's metric-only artifacts.
It does not import or step the engine. All 30 runs / 300,030 rows passed: complete
tick ranges, accounting identities, cumulative counters, diversity bounds, neutral
trait invariance, and recomputed terminal/late-window/fixation/extinction summaries
agree with both saved summary formats. No reported result needed correction.

The verifier checks the metadata-declared run grid; that grid was also inspected
against the preregistration (three widths, two treatments, five seeds, 10,000 ticks).
It cannot validate unavailable lifecycle records or establish biological truth.
Corrupted intermediate energy, altered summary mean and a truncated CSV are rejected
by tests. All 34 local tests pass. Future portable review archives include this
additional metric audit separately from their 11 full-lifecycle run audits.

Archive `data/bitgenesis-v0-review-9.zip` was built from committed source `4cabc6b`:
403 files, 21,239,792 bytes, SHA-256
`6452f736682589de618cd4d3b14901cc003d30d8be3797ab78ea9733b7979be9`.
All archived file hashes were read back and checked, with 11 full-run audits and
the separate 30-run metric audit recorded in its manifest. It retains the existing
five-campaign visual review page; later documentation updates are in Git.

Source `4cabc6b` passed CI run 34775013482 across the four OS/Python combinations.
The current suite has 34 tests. No formal campaign was rerun or added this cycle.

## 2026-09-14 — Autonomous cycle 10

Preregistered and completed campaign 006 from clean source `d692b09`: 50 new runs,
250,000 ticks, seeds 500–509, regrowth 10/15/20/30/40 per 1000. Extinction by tick
5000 was respectively 10/10, 4/10, 0/10, 0/10, 0/10. At 10/1000 extinction ranged
93–1806 ticks, extending the earlier five-seed observed range. At 15/1000 early
extinction coexisted with persistence to the horizon. Surviving times are censored,
not proof of permanence. No infinite-time threshold claim is made.

The plot helper independently recomputed key outcomes and accounting from all
250,050 metric rows. Committed compact CSV and a visually inspected two-panel
figure preserve every seed, including extinct worlds. Formal totals now 290 runs
/ 1,240,000 ticks. Existing five-campaign review archives remain untouched; their
scope is explicitly historical. CI for preregistered source passed in 34775144877.

Next useful mechanism question: distinguish founder establishment effects from
later adaptation under scarce resources, with an explicitly controlled treatment
rather than attributing mixed outcomes to either cause from this assay alone.

## 2026-09-14 — Autonomous cycle 11

Integrated campaign 006 into the Chinese static review: `data/review-v0-6.html`
now shows all 290 runs / 1,240,000 ticks, the extinction table and figure, and
explicit finite-horizon language. Browser inspection confirmed the displayed
totals, new table and rendered figure; replay and lineage destinations remain
the original acceptance demonstration.

Built `data/bitgenesis-v0-review-6.zip` from clean source `02419ac`. It contains
464 files / 25,673,634 bytes. SHA-256:
`d8d6a923b5eed8c831c4b01d1b19524b2017fc5628f832ec18dc5d8611776972`.
Every archived file was read back and hash-checked. All four local targets from
the entry page (replay, lineage, two figures) resolve within the archive without
requiring an absolute workspace path. The manifest records 11 full-run audits
and the separate campaign-005 metric audit. Previous archives remain preserved.

## 2026-09-14 — Autonomous cycle 12

Preregistered and completed campaign 007 from clean source `0b73705`: founder
genomes random/250/1000 × mutation attempt 0/100 per 1000 births, regrowth 15/1000,
seeds 600–609, 5000 ticks. All 60 runs completed (300,000 ticks). Final survivors
per ten runs: random 7 without / 9 with mutation; initially 250, 7 / 7; initially
1000, 4 / 2. Intermediate survival and extinction times differ substantially even
where terminal counts match. No significance or general mutation benefit claim.

Fixed-trait, mutation-free populations supply direct counterexamples to the claim
that new or standing movement-trait variation is necessary for 5000-tick persistence
in this condition. They do not prove indefinite persistence. All 300,060 metric
rows were independently checked for accounting and declared outcomes; a sidecar
records raw CSV and script hashes. Formal totals: 350 runs / 1,540,000 ticks.
Source CI passed in 34775566923. Six-campaign review artifacts remain historical;
the seventh report and all-seed CSV are tracked alongside them.

## 2026-09-14 — Autonomous cycle 13

Added a Chinese research index linking all seven protocols, reports and compact
datasets. Recomputed counts from the seven saved result CSVs: 350 runs / 1,540,000
ticks. The index separates observations, bounded interpretations and unsupported
claims, and gives a concise replication route. All 29 index links resolve locally.

Simplified the root README to one current total and an index link. Acceptance and
Chinese review guides now distinguish current seven-campaign research from the
preserved six-campaign visual archive. This avoids interpreting older bundle scope
as the latest research state. No simulation rules, tests or experimental data changed.

## 2026-09-14 — Autonomous cycle 14

Campaign 008 completed from clean preregistered source `ff63d73`: initial food
0 versus 8/cell, fixed genome 250, mutation off, regrowth 15/1000, seeds 700–709,
10,000 ticks. Empty-food runs all died by tick 65 (range 30–65). Baseline-food
survival was 10/10 at 500, 8/10 at 5000, 3/10 at 10000; extinct-only times ranged
3053–8685. Initial resource supply helps establishment here but not permanence.

All 200,020 metric rows were independently checked for initial conditions,
accounting, fixed traits and declared outcomes. Compact results and hash sidecar
are tracked. Total formal research: 370 runs / 1,740,000 ticks. Source CI passed
in 34775932916. No runtime-stage or engine change; historical archives are preserved.

## 2026-09-14 — Autonomous cycle 15

Eight-campaign review page and archive now cover all 370 runs / 1,740,000 ticks.
Archive `data/bitgenesis-v0-review-8.zip`, source `1202f61`, contains 563 files /
31,397,908 bytes; SHA-256
`c0905b233a635a383d0321cccca31a63cdcbdac079f19d94f7f7112d5928c38b`.
All archived hashes were checked. Browser inspection confirmed the new totals and
initial-food results. Prior review pages and archives remain preserved.

Extracted into `data/portable-review-8/`, created a fresh Python 3.12 environment,
built/installed the archived source as a wheel, and verified the loaded module
came from that environment's site-packages. All 34 tests passed there. A new
1000-tick baseline run passed independent audit: 83 survivors, 1561 births,
1558 deaths, 1641 total recorded organisms. CSV metrics and JSONL events match the
original acceptance demonstration byte-for-byte; lineage and summary JSON have
equal values (historical formatting differs). Installed provenance correctly
reports Git unavailable, rather than borrowing the enclosing repository commit.

The extracted entry page's four local links resolve. Core installation did not
require the optional plotting libraries; initial wheel build obtained its declared
build dependency, so this is not an offline-installation claim. The fresh run is
operational validation and does not increase formal experiment totals.

## 2026-09-14 — Autonomous cycle 16

Extended CI to Windows/Linux × Python 3.12/3.13/3.14. Source `9c1ac4b` passed all
six jobs in run 34776314237. The frozen engine fingerprint was unchanged. This
fixture-level compatibility evidence does not mean all campaigns were rerun on
all interpreters; cross-minor checkpoint loading remains deliberately rejected.

CI emitted Node 20 deprecation notices for its old pinned actions. Queried official
GitHub release/tag/action metadata and pinned [checkout v7.0.1](https://github.com/actions/checkout/releases/tag/v7.0.1)
at `3d3c42e5aac5ba805825da76410c181273ba90b1` and
[setup-python v7.0.0](https://github.com/actions/setup-python/releases/tag/v7.0.0)
at `5fda3b95a4ea91299a34e894583c3862153e4b97`; both declare Node 24.
Source `4039b54` passed run 34776427675 on all six jobs. Inspected logs confirm
34 tests in every job and no preceding Node 20 deprecation message. Core engine,
research outcomes and eight-campaign archive remain unchanged.

## 2026-09-14 — Autonomous cycle 17

Retrospectively decomposed campaign-002 energy over ticks 1501–2000. Basal cost
one permits exact reconstruction from pre-tick populations; reproduction is the
known birth cost times births, and movement is remaining dissipation. Every one
of the 100 allocations closes, using 200,100 source metric rows. Actual charged
energy was independently matched in an instrumented test with distinct costs.
All 37 local tests pass. No engine changes or new formal world trials.

At movement cost one, trait 250 spends 28.3956 energy/tick on movement versus
77.9058 for trait 1000, while actual inputs are 149.3776 versus 162.5624. The
allocation supports the cost explanation of lower fixed-trait population, without
predicting mixed competition. The report explains capped input and pre/post-tick
mean differences, preserves extinction zeros, and identifies the analysis as
retrospective rather than preregistered. Counts remain 370 runs / 1,740,000 ticks.

## 2026-09-14 — Autonomous cycle 18

The preceding 37-test suite passed all six CI jobs in run 34776692127. Measured
retention with clean source `1afd161`, baseline seed 42, two separate event-drained
/ event-retained processes through 10000 ticks. Complete lineage reached 14,993
records despite only 68 survivors; retained events reached 29,918.

Inspection showed the atomic writer built the entire formatted JSON in memory.
Changed it to stream encoder chunks into the temporary file (`f0befe4`), preserving
sync/replace behavior. Repeating the same benchmark reduced traced serialization
peaks from 34.774 to 12.836 MB drained and 74.166 to 25.157 MB retained at tick 10000.
All six new/old checkpoint files are byte-identical; the two modes' non-event state
matches. This is traced Python allocation, not RSS, and timings include tracing.

Full local tests passed (38); strengthened nonfinite-write cleanup assertion also
passed focused artifact tests. The report preserves exact measurements and hashes.
Full historical-state growth remains unresolved; no bounded-memory or ultra-long
capacity claim. Operational benchmarks do not alter formal experiment totals.

## 2026-09-14 — Autonomous cycle 19

Consolidated a V0-informed V1 design contract without implementing another stage.
The candidate is a 35-integer-weight linear food/energy-to-action controller with
explicit matched decision costs. Controls distinguish directional information,
all-food information, initial variation, within-lineage change and direct competition.
Sampling uses an observer-only RNG and independent training worlds as replicate
units; failed training worlds remain in reporting. A separate viability pilot and
future preregistration are required before outcome interpretation.

The six design constraints link directly to completed V0 analyses; all links resolve.
No training seeds are selected or reused for hypothetical results. V0 remains the
only runtime. The 38-test source `0fca4d9` passed CI run 34776989101; logs confirm
38 tests in each Windows/Linux × Python 3.12/3.13/3.14 job.

## 2026-09-14 — Autonomous cycle 20

Added a standard-library-only ZIP verifier that executes/extracts nothing. It checks
member paths, exact manifest coverage, payload sizes/hashes and static local HTML
targets, with an optional externally recorded archive SHA-256. The distinction
between internal consistency and identity/authenticity is explicit in the guide.

Verified existing eight-campaign archive against its recorded external hash:
563 payload files, 13 HTML pages, six local targets. Corrupt payload, missing HTML
target, unlisted payload and wrong expected archive hash are detected in tests.
All 42 local tests passed. Future packaging invokes the helper; prior archives
remain immutable. This operational verification adds no formal experiment runs.

Rebuilt the eight-campaign bundle with the integrated verifier from clean source
`f389047`: `data/bitgenesis-v0-review-8b.zip`, 576 files / 31,425,729 bytes,
SHA-256 `cc81e02cae90d8d72117d41310bc85c5051a7697391f96bb097f0210e510832d`.
The integrated packaging path passed, including 11 full-run audits and the
campaign-005 metric audit. It now includes energy/retention analysis, streamed
JSON code and the standalone verifier; earlier `review-8.zip` remains preserved.

## 2026-09-14 — Autonomous cycle 21

Clarified V0's inherited controller vocabulary directly from engine code: exactly
1001 scalar movement settings, with no genotype mechanism for adding sensing,
memory, actions or topology. This is not a bound on total world states or collective
patterns. It distinguishes genealogical growth, scalar variation and new functions.

Retrospectively counted all campaign-001 lineage genomes. Mutation-enabled runs
visited 241–303 values, retained 7–19 at the endpoint and reached living generations
110–143. No-mutation runs visited only their initial 76–79 values, retained one and
reached generations 101–115. Bounds, unique IDs, terminal counts and no-mutation
closure passed; raw input hashes and ten seed records are tracked. No new formal
world runs. Earlier archive-verifier source passed CI in 34777333414.

## 2026-09-14 — Autonomous cycle 22

Prepared GitHub draft prerelease `v0.0.1-preview.1` (release ID 388008482), targeting
the archive's exact source `f389047f38e3329b010a566ae49b3ca94d5000ce`. Uploaded the
eight-campaign `bitgenesis-v0-review-8b.zip` and its SHA-256 text file. The draft
notes state scope, review instructions, provenance, checks and scientific limits.
No release was published; draft and prerelease flags were verified true through
the GitHub API.

Server-reported archive asset size is 31,425,729 bytes, state `uploaded`, digest
`sha256:cc81e02cae90d8d72117d41310bc85c5051a7697391f96bb097f0210e510832d`,
matching the local verified archive. Draft page:
https://github.com/nikolasandwich/bitgenesis/releases/tag/untagged-25033c66c4d616cc9048
Later main commits are explicitly outside this fixed snapshot. Existing local
archives and formal experiment counts are unchanged.

## 2026-09-14 — Autonomous cycle 23

Found and reproduced a checkpoint validation gap: a recomputed checksum could
allow self-parent references, inconsistent generations/founders/offspring counts,
invalid dead-record genomes/energy or fractional positions. Added regression
cases first; all eight malformed examples were previously accepted.

The loader now validates all historical lineage scalars, ancestry and chronology,
single reproduction per parent/tick, offspring counts and integer member IDs.
Format and engine rules are unchanged. Full local suite passed 43 tests; focused
checkpoint tests also pass with Python optimization enabled. Fifteen historical
checkpoint files (original continuation demonstrations and retention measurements)
still load successfully, and existing exact-resume tests remain green.
This checks structural plausibility, not full historical transition replay.

## 2026-09-14 — Autonomous cycle 24

Verified cycle 23 on all six Windows/Linux and Python 3.12–3.14 CI jobs
(run 34777990358; documentation follow-up 34778040879 also passed).
Extended the continuation contract to four boundary states: initially empty,
extinct, fully occupied without turnover, and ongoing turnover. Each scenario
checks both retained and explicitly drained pending-event buffers. After saving
at tick 40 and continuing for 60 ticks, resumed and uninterrupted checkpoints
are byte-identical in all eight cases. Drained historical events stay drained;
external event-log durability is explicitly outside this state-only contract.

No new engine behavior or scientific campaign was added. Full local suite passed
44 tests. These cases complement the previous interruption and separate-process
checks; they do not establish that every possible configuration was tested.

## 2026-09-14 — Autonomous cycle 25

Added an explicitly exploratory uncertainty supplement to campaign 008, using
the previously verified compact outcomes. Pointwise 95% Wilson intervals are
0/10: [0, 0.277533], 10/10: [0.722467, 1], 8/10: [0.490162, 0.943318],
and 3/10: [0.107791, 0.603222]. The same worlds recur across horizons; no pooled
replicate count, treatment-effect test or permanent-survival probability is claimed.
The report states the independent-world Bernoulli assumption and the limitation
of a deterministic consecutive seed block. Method checked against NIST's binomial
interval documentation; numerical endpoints tested against the score equation.

The helper checks the campaign's complete 20-run grid and survival/extinction
consistency, records input and script hashes, and refuses to overwrite output.
No new simulation or engine change. Full local suite passed 46 tests.

## 2026-09-14 — Autonomous cycle 26

Reviewed the acceptance documents against current repository and release state.
Corrected a stale claim naming the five-campaign visual page as current; marked
that section as historical and distinguished the eight-campaign main working
tree from the uploaded fixed-source 8b draft archive. Linked the later energy,
memory, expressive-ceiling, survival-uncertainty and checkpoint supplements without
counting them as new formal campaigns. V1 is still explicitly design-only.

Source 1b8a2fd passed all six Windows/Linux × Python 3.12/3.13/3.14 jobs in
CI run 34778435637, including the 46-test suite. Acceptance guides now cite this
specific source and run instead of implying historical archive test counts are
current. No runtime or experiment data changed.

## 2026-09-14 — Autonomous cycle 27

Preregistered campaign 009 and its runner at clean 0639fd6 before executing seeds
800–809. Compared initial food/energy allocations low (0/24), food (5/24), stored
(0/88), with the latter two sharing initial total 7040. Other V0 rules unchanged.
All 30 × 10000-tick runs completed; independent metric verification checked
300030 rows and accepted all saved summaries. Source CI 34778593278 passed.

Alive at 500/5000/10000: low 0/0/0, food 9/3/1, stored 0/0/0 (each of ten).
Stored worlds produced mean 215.4 births yet all went extinct at ticks 51–73.
Report distinguishes allocation effects from an unisolated reproduction mechanism
and documents capacity-limited resource-input feedback. All-seed results and hash
sidecar are tracked. Formal totals become nine campaigns / 400 runs / 2040000 ticks;
the existing eight-campaign visual pages, packager and release remain historical.

## 2026-09-14 — Autonomous cycle 28

Reconstructed first-100-tick energy budgets and population peaks from campaign
009's existing metrics, explicitly as a post-experiment analysis. Stored-energy
worlds had mean peak population 295.4 at mean first-peak tick 3.9 and mean 215.4
births by tick 10; at tick 100 all were extinct with mean 5496 food energy left.
The food arm had mean peak 84.7 and 13.8 births by tick 100. Reused the exact
basal/movement/reproduction accounting helper; its three contract tests passed.

All-seed budgets and input/helper/script hashes are tracked. The report avoids
equating world food totals with individual access or treating the observed early
burst as an isolated causal explanation. No new simulations or changes to rules.

## 2026-09-14 — Autonomous cycle 29

Added a reproducible PNG/SVG figure of all thirty campaign-009 early population
trajectories, with per-arm means, shared axes and explicit initial energy labels.
It preserves seed variation and distinguishes the low-energy baseline from the
equal-energy contrast. Raw trajectory hashes and plotting source hash accompany
the figure. Visual inspection found an initial shared-axis clipping issue; fixed
the common upper bound using the maximum across all traces, regenerated and
visually verified the complete peaks and readable labels before committing.
The figure is an exploratory first-100-tick view; no new simulations were added.

## 2026-09-14 — Autonomous cycle 30

Extended the review builder with explicit eight/nine-campaign scope. Default
eight-campaign behavior remains compatible with the existing packager; passing
--campaigns 9 builds a new review-v0-9.html without replacing old pages. The new
section contains all three allocation arms, finite-horizon counts, the early
trajectory figure and causal limitations. Browser inspection verified the rendered
Chinese section and table. Acceptance guides now point to the nine-campaign page
and continue to identify the uploaded draft/archive as eight-campaign snapshots.

## 2026-09-14 — Autonomous cycle 31

Extended packaging with explicit eight/nine-campaign scope while retaining the
default eight-campaign path. Nine-campaign packaging includes raw campaign 009,
selects review-v0-9.html, and reruns its independent metric verifier into a temporary
directory before recording the result in the manifest. Full local suite: 46 passed.

Created data/bitgenesis-v0-nine-campaigns.zip from clean
c5975cd5785e7f1ed784382810314545a9076b91: 628 payload files, 32997186 bytes,
SHA-256 8bf359d6f156ea71d0f15c6d5eee5f087e86af30e6d4db94562fe38c398895a6.
Eleven full-run audits and both metric-campaign checks passed. Independent ZIP
verification passed, including an explicit expected whole-archive hash. Existing
local archives and the GitHub draft attachment were not replaced.

## 2026-09-14 — Autonomous cycle 32 (running)

Preregistered campaign 010 at 6a1d4fa before executing seeds 900–909. Crossed
food/stored allocation (equal initial energy 7040) with birth thresholds 40/160:
four arms, 40 runs planned, 10000 ticks each. Engine unchanged. The intervention
is active throughout each run and jointly changes reproduction timing, division
and population demands; the protocol does not claim single-pathway identification.

Started the campaign from the clean preregistered commit. Prepared an independent
metric verifier for the fixed grid and all intermediate birth/population endpoints.
Full existing local suite passed 46 tests. Execution is still live at this entry;
accepted formal totals remain nine campaigns / 400 runs / 2040000 ticks until
completion and metric verification. No partial outcomes have been accepted.

## 2026-09-14 — Autonomous cycle 33

Campaign 010's original process completed all 40 runs. Independent verification
passed all 400040 metric rows and declared intermediate/final summaries. At tick
10000, food-40/stored-40/food-160/stored-160 survival was 1/0/10/7 of ten each.
Raised-threshold arms had zero births through tick 100; stored-40 averaged 215.
Stored-160 failures (901, 906, 908) are retained; surviving lifetimes are censored.

Reported the threshold's total intervention effect without claiming a single
causal pathway, evolved strategy or universal parameter optimum. Baseline rules
and defaults unchanged. All-seed outcomes and verification hashes committed;
formal totals become ten campaigns / 440 runs / 2440000 ticks. Existing nine-
campaign portable snapshot remains explicitly historical. Source and verifier
CI runs 34779261990 and 34779319289 both passed six environments.

## 2026-09-14 — Autonomous cycle 34

Checked campaign 010's late turnover from existing cumulative counts (ticks
9001–10000), preserving the original verification sidecar. All seventeen
threshold-160 endpoint survivors had both births and deaths in this window.
All-seed mean births/deaths: food-40 114.9/113.4, stored-40 0/0, food-160
84.1/93.8, stored-160 57.6/58.6. Net population changes reconcile in every run.

This distinguishes the observed persistence from campaign 004's crowded arrest,
without claiming permanent survival or new functions. Forty per-run count pairs,
input hashes and the extended helper hash are saved in a separate sidecar. No
simulation or engine change; accepted campaign totals remain unchanged.

## 2026-09-14 — Autonomous cycle 35

Fed campaigns 009–010 back into the design-only V1 contract. Sensory controls must
match initial food and organism energy separately, reproduction parameters and
all costs/schedules. Any later sensory × threshold robustness experiment needs a
declared factorial grid; information effects are compared within one physiology.
Pilot choices remain separate from held-out outcome trials.

Identified a design coupling: energy-input normalization previously used the birth
threshold, so a threshold intervention would also change controller input meaning.
Replaced that with a separately declared fixed scale (candidate 160), matched
across arms and not presented as empirically optimized. Added birth tempo and late
turnover reporting alongside survival and competition. No V1 code or V0 change.

## 2026-09-14 — Autonomous cycle 36

Created a separate GitHub draft prerelease v0.0.1-preview.2 (release 388019032),
fixed to c5975cd5785e7f1ed784382810314545a9076b91, and uploaded the already verified
nine-campaign archive plus checksum file. GitHub reports uploaded state, 32997186
bytes and SHA-256 8bf359d6f156ea71d0f15c6d5eee5f087e86af30e6d4db94562fe38c398895a6,
matching the local archive. Source CI 34779146296 passed all six environments.

Draft URL: https://github.com/nikolasandwich/bitgenesis/releases/tag/untagged-f053eec4d3332539ca25
Notes explicitly exclude campaign 010 and later main changes. The eight-campaign
draft remains untouched, and neither release has been published. Acceptance
guides distinguish current ten-campaign research from the downloadable snapshot.

## 2026-09-14 — Autonomous cycle 37

Added a full-horizon survival figure for campaign 010, paired with an early-window
zoom of the same forty observations. Each arm retains ten worlds, step locations
come directly from recorded extinction times, and endpoint survivors are marked
as administratively censored. Line styles distinguish reproduction thresholds;
colors distinguish allocation. Overlaps are retained and disclosed.

The plot helper checks the compact grid and survival/time consistency and saves
curve coordinates with input/source hashes. PNG and SVG were generated and visually
inspected for labels, legends, range and endpoint display. No new simulation,
probability fitting or changes to accepted experiment totals.

## 2026-09-14 — Autonomous cycle 38

Extended the static review builder to optional ten-campaign scope, retaining
eight-campaign defaults and older output files. Added threshold outcome table,
survival figure and interpretation limits. Before rendering campaigns 009/010,
the builder now validates their complete treatment/seed grids, rejecting duplicates
even when the total count is unchanged. Two regression tests cover reordered
complete data and same-count duplicate/wrong-seed failures; all 48 local tests pass.

Generated review-v0-10.html and inspected the new table and figure in the browser.
Current acceptance links now point to that page while the nine-campaign uploaded
archive remains a fixed historical snapshot. No new experiment or engine change.

## 2026-09-14 — Autonomous cycle 39 (running)

Preregistered campaign 011 at a843547 before observing beyond tick 10000. Follow
both complete threshold-160 cohorts (seeds 900–909, including early failures) to
100000 ticks. Twenty follow-up executions require 2000000 computational ticks:
200000 repeated prefix ticks and 1800000 later observations. They are not new
independent seed replicates. Existing V0 rules and parameters are preserved.

The runner compares every tick-0–10000 snapshot with campaign 010 before proceeding
and records reference CSV hashes. First-world prefix check passed and execution
is live. Accepted totals remain ten campaigns / 440 runs / 2440000 ticks pending
complete execution and independent metric verification. No partial survival claim.

## 2026-09-14 — Autonomous cycle 40 (running)

Prepared a streaming verifier for campaign 011. It compares the saved observable
prefix, checks every tick's accounting and cumulative-counter monotonicity,
retains extinction failures and recomputes observation/late-window summaries.
Its report distinguishes computational ticks, repeated prefixes, later observations
and zero new independent seed replicates. Four regression cases cover a complete
fixture, altered reference, post-prefix intermediate corruption and truncated end.
All 52 local tests passed. An already completed 100000-tick food-160/900 run also
passed the streaming check against its original prefix. The remaining campaign
process is still live; this is not full-cohort acceptance or a survival conclusion.

## 2026-09-14 — Autonomous cycle 41 (running)

Strengthened the pending long-horizon verifier's protocol checks: fixed world size,
population, capacity, regrowth amount, feeding and energy costs must match the
declared design, alongside rules version, mutation setting and fixed trait.
Counts and accounting alone could otherwise accept metadata describing a different
experiment. A regression test rejects changed movement cost, dimensions, resource
probability and a boolean disguised as an integer parameter. All 53 local tests
passed. Campaign 011's original process remains live; no runner or engine change.

## 2026-09-14 — Autonomous cycle 42

Waited on the original campaign process until terminal completion; no restarts or
extra seeds. All twenty follow-ups reached 100000 ticks. Independent streaming
verification passed 2000020 rows and 200020 historical prefix rows. Food/stored
survival at 10000, 50000 and 100000 stayed 10/10 and 7/10; the three early failures
were retained. No additional extinction occurred in the extended interval.

Report, all-run CSV and hash sidecar are committed. Computation is explicitly
2000000 ticks, including 200000 repeated prefixes and 1800000 later observations;
these twenty executions introduce zero independent seed replicates. Project totals
become eleven campaigns / 460 executions / 4440000 computed ticks with that caveat.
No permanence or adaptation claim. Preregistered source CI 34780086318 and verifier
CI 34780384606 passed; existing pages and archives retain their prior scope.

## 2026-09-14 — Autonomous cycle 43

Compared recorded founder counts and living-generation depth across the long
follow-up. All seventeen survivors have one founder at 100000; sixteen already
did at 10000. Food-160/905 changes from two to one at 18651. Terminal maximum
living depth ranges 224–287 (food) and 221–268 (stored), with the same fixed genome.
Two extinct worlds had also passed through one-founder states, so founder fixation
is not equated with maintenance or superiority.

Saved every world's comparison and hash sidecar. Streaming checks cover complete
ticks, count bounds/monotonicity and fixed-variant consistency; unavailable full
genealogy was not reconstructed. This retrospective view adds no new executions.

## 2026-09-14 — Autonomous cycle 44

Added a retrospective machine-readable campaign inventory and compact-CSV counting
checker. It verifies counts, horizons, balanced seed coverage, unique run identities
and declared follow-up references/prefix lengths. Result: eleven campaigns, 460
executions, 4440000 computed ticks, twenty follow-ups and 200000 replayed prefixes;
excluding declared replay work gives 4240000 computed ticks. None is labelled an
independent replicate count. Protocols remain the source of scientific design.

All eleven committed CSVs passed. Disposable-copy checks rejected a duplicate row
with unchanged total count and an incorrect replay-prefix declaration. Inventory,
input and helper hashes are recorded. No original data or engine was changed.

## 2026-09-14 — Autonomous cycle 45

Added the compact campaign-inventory check to every existing CI environment after
the contract suite. Future edits now automatically check declared execution counts,
unique/balanced identities, horizons and follow-up prefixes against tracked CSVs.
This requires no private/local raw artifacts and does not rerun scientific worlds.
The step remains a counting check, not validation of every research conclusion.

CI run 34781320417 completed successfully for source 7f8fd4d in all six
Windows/Linux × Python 3.12/3.13/3.14 jobs: 53 tests, the new inventory check,
installed CLI smoke run and independent artifact audit. Acceptance guides now
cite this specific checkpoint without changing historical archive test counts.

## 2026-09-14 — Autonomous cycle 46

Extended the Chinese review builder through campaign 011. Expected execution
counts and horizons now come from the tracked campaign inventory. The follow-up
table retains all twenty worlds, including the original three early extinctions.
The page explicitly separates execution workload, replayed prefixes and independent
seed samples; no extra independent replication is claimed.

Generated a new local review-v0-11.html without overwriting earlier snapshots.
Browser inspection confirmed the workload notice and the 10/10 versus 7/10
survival table through 100000 ticks. All 53 local tests passed. Acceptance guides
now point to the eleven-campaign page while the uploaded nine-campaign archive
retains its named source and scope. Engine rules are unchanged.

## 2026-09-14 — Autonomous cycle 47

Extended portable packaging through campaign 011 while preserving the default
eight-campaign mode and existing archives. The manifest now separates selected
raw campaign workload from tracked source, and selected 009–011 metric verifiers
run during packaging; 011 also verifies its 010 prefixes. Existing outputs are
rejected before expensive work. All 53 local tests passed. A packaging smoke run
found a text-encoding syntax error missed by the contract suite; corrected it,
compiled the helper and completed the real packaging path successfully.

Source eba74b99cd77c323004dfbc743a7b697c341ff12 produced the eleven-campaign ZIP:
719 payload files, 62325938 bytes, SHA-256
9a67b9ad14fa66c6eeddbe11bbe0742672d1d8008d6a9da8262bcf3b5b8cf7f4.
Eleven full-run audits and 005/009/010/011 metric verifiers passed. Standalone
verification matched the external hash and checked 13 HTML pages / eight local
targets. The manifest records 460 executions, twenty follow-ups and 200000 replay
ticks explicitly. This new local archive is not yet uploaded; existing GitHub
drafts remain unchanged.

## 2026-09-14 — Autonomous cycle 48

Uploaded the fixed eleven-campaign ZIP and checksum as draft prerelease
v0.0.1-preview.3 (release 388031251), target
eba74b99cd77c323004dfbc743a7b697c341ff12. GitHub reports both assets uploaded,
the archive size 62325938 and SHA-256 matching the independently checked local
copy. The source CI 34781902624 completed successfully. Notes identify the twenty
follow-ups, repeated prefixes, finite observation and fixed-trait limitations.

Acceptance entries now link to this draft. The eight- and nine-campaign drafts
and their fixed assets remain unchanged. No release was published and no new
scientific executions were added by this delivery step.

## 2026-09-14 — Autonomous cycle 49

Closed the syntax-check gap exposed during packaging: CI now compiles all src,
scripts and tests before the existing contract suite. This checks unimported
research helpers without executing their experiments or requiring local datasets.
CONTRIBUTING includes the same local command and current Python matrix.

Local compilation and 53 tests passed. A disposable copy of the historical broken
packager from 1affa17 was rejected by this command, confirming coverage of the
actual observed failure. Source 694fd9c45f9fea86b676efac916940a94708ff35 passed
CI 34782162578 in all six Windows/Linux and Python 3.12/3.13/3.14 jobs, including
the new syntax step. This closes a syntax gap only, not behavioral coverage for
every research helper. Existing archive source and evidence remain fixed.

## 2026-09-14 — Autonomous cycle 50

Verified the eleven-campaign ZIP against its external hash, extracted into a
new portable-review-11 directory and installed its wheel into a new virtual
environment. Confirmed imports resolve to that environment's site-packages.
All 53 archived tests and the compact inventory check passed. A newly generated
1000-tick baseline passed independent artifact audit: 83 living, 1561 births,
1558 deaths and 1641 recorded organisms. Metrics and events match the archived
acceptance demo byte-for-byte; lineage and summary JSON values match.

This exercises the delivered snapshot in Windows/Python 3.12, not all research
campaigns or offline dependency installation. Installation resolved build
dependencies. New disposable outputs remain ignored; the ZIP and draft assets
were not modified. Acceptance notes record the scope of this check.

## 2026-09-14 — Autonomous cycle 51

Updated the research index to the actual eleven-campaign page and uploaded draft.
Added a prioritized unresolved-mechanism decision alongside the existing evidence
table: cross existing birth-threshold and direct birth-cost parameters in both
allocation backgrounds. This remains a design candidate, not a preregistered or
executed campaign. Checked engine reproduction: zero direct birth cost still
splits parental energy and adds an individual with basal/movement and space costs.

Specified what persistence of early failure under zero direct cost would falsify,
and why a survival improvement would not isolate all indirect mechanisms. Any
execution requires a new protocol, seed block and verification plan. No scientific
counts, runtime rules or archive assets changed.

## 2026-09-14 — Autonomous cycle 52

Preregistered campaign 012 and its runner at source b963348 before execution:
eight allocation × threshold × direct-cost arms, fresh seeds 1000–1009, 10000
ticks each. Confirmed the seed block was absent from prior registered campaigns.
Specified survival contrasts, early peak/births and late turnover, including
all failures and the limits of zero direct cost. No engine changes.

Compilation and 53 tests passed. Started the actual run from clean source;
metadata confirms git_dirty false and the registered source. The live process
is producing per-seed outputs. Results are pending and are not yet included in
validated totals or archives. Next: independently recompute declared observations
from all raw metric tables once execution completes.

## 2026-09-14 — Autonomous cycle 53

Added the campaign-012 independent full-metric verifier while the original
experiment process remains live. It validates the declared grid, fixed parameters,
initial ledger, per-tick accounting/bounds, extinct living metrics, early peak,
late turnover and summaries, then computes preregistered descriptive contrasts.
Compilation and 53 contract tests passed.

Disposable inputs confirmed rejection of a falsely completed empty grid, altered
intermediate energy, an incorrect early-peak summary and a truncated first run.
An unchanged completed first run advanced to the intentionally absent second
file, distinguishing its validation from later missing-input failure. These are
focused corruption probes, not verification of all eighty unfinished runs. Raw
data and running engine were untouched; accepted totals remain eleven campaigns.

## 2026-09-14 — Autonomous cycle 54

Campaign 012 completed all eighty runs in the original process. Independent
verification checked 800080 metric rows and all declared observations. Stored/40
worlds all fail at either direct cost; cost zero failures span ticks 37–59, cost
four 46–63. Stored/160 survives 9/10 at both costs; food/160 10/10 at both.
Food/40 ends 0/10 at cost zero and 1/10 at cost four. All results and descriptive
contrasts, including null/reversed differences, are retained in report and CSV.

This rejects positive direct birth deduction as necessary for the observed early
stored/40 failures; it does not isolate indirect costs or imply universal optimal
parameters. Verified totals now twelve campaigns, 540 executions, 5240000 computed
ticks, including the existing twenty follow-ups and 200000 replayed prefixes.
Inventory check passed. Original source CI 34782507452 and verifier CI 34782708374
passed. Eleven-campaign pages/draft archives remain fixed and explicitly exclude
this new campaign.

## 2026-09-14 — Autonomous cycle 55

Added a reproducible campaign-012 survival figure: allocation separated by row,
full horizon and early-window zoom by column, threshold by color and direct
cost by line style. All eighty seeds are represented. Explicitly notes that
overlapping high-threshold survival curves do not establish identical dynamics.
Saved PNG/SVG and curve values with input/script hashes; visually checked axes,
legend, censor markers and annotations. The helper checks the complete grid and
survival/extinction consistency before plotting. Compilation passed. No new
worlds or scientific endpoints were added.

## 2026-09-14 — Autonomous cycle 56

Reconstructed the first hundred ticks of campaign 012 with the tested exact
basal-cost-one budget helper, using each arm's actual direct birth cost rather
than the baseline value. All eighty raw hashes match the committed verification
report. In stored/40, zero direct cost removes 864.8 mean birth units but basal
plus movement rises by 885.6; total dissipation rises 20.8. Both groups are
extinct at 100 while world food remains. This accounting is not a unique causal
path or proof of local resource access.

Saved all-run budgets and hashes and marked the window analysis retrospective.
Also noted that cumulative spending is affected by time alive: high-threshold
worlds spend more basal/movement energy in this window while retaining organisms.
No new scientific executions were added.

## 2026-09-14 — Autonomous cycle 57

Added a meaningful zero-direct-birth-cost regression for the budget helper used
in campaign 012. Instrumented actual World._pay deductions in a world with
confirmed births and deaths, separate basal/movement charge amounts, initial
stored energy and sparse resources. Reconstructed category totals match actual
deductions exactly; zero-cost payment calls match births while reproduction
spending remains zero and other spending remains positive. Engine code unchanged.

All 54 local tests and source/script compilation passed. This new regression
extends direct accounting evidence to the zero-cost branch; it is an engineering
check, not an extra scientific replicate. Historical archives still contain
their previously recorded test suites.

## 2026-09-14 — Autonomous cycle 58

Extended the local Chinese review page through campaign 012 with its complete
eight-arm grid, finite-horizon survival figure and bounded mechanism conclusion.
The follow-up counting notice remains present for the inherited 011 cohort.
Generated review-v0-12.html as a new file and checked its browser content and
rendering. All 54 local tests passed. Acceptance and index entries now distinguish
the twelve-campaign current page from the fixed eleven-campaign downloadable
archive. Earlier pages and draft assets were not overwritten.

## 2026-09-14 — Autonomous cycle 59

Extended portable packaging to twelve campaigns with the 012 metric verifier.
Compilation and 54 local tests passed. Clean source 11da88c6c19729b066a8ad4e30ca1362ae896c77
produced 815 payload files / 70481664 bytes. SHA-256:
121e11e56b22cd20c2f584b2989e9c25d9348042208ba02232cc4d1bdfad7cd4.
Eleven full-run audits and 005/009/010/011/012 metric checks passed during
packaging; the manifest includes the 800080-row campaign-012 verification.
Independent ZIP verification matched the external hash. The twelve-campaign
archive and checksum are local; existing draft assets remain unchanged.

## 2026-09-14 — Autonomous cycle 60

Uploaded twelve-campaign ZIP and checksum to draft prerelease v0.0.1-preview.4,
release 388038285, fixed source 11da88c6c19729b066a8ad4e30ca1362ae896c77.
GitHub reports both assets uploaded; archive size 70481664 and digest
121e11e56b22cd20c2f584b2989e9c25d9348042208ba02232cc4d1bdfad7cd4 match
the local verified copy. Source CI 34783294636 passed. Notes retain follow-up
counting, bounded mechanism claims and retrospective-analysis labels. Updated
current download entries; all older drafts/assets remain unchanged and no
release was published.

## 2026-09-14 — Autonomous cycle 61

Verified and extracted the twelve-campaign ZIP into a fresh portable-review-12
directory. Ran the archived 012 verifier against archived raw metrics, and the
archived early-budget tool with Python -S (site packages disabled). Both JSON
reports match their archived counterparts exactly, including script/input hashes;
all eighty budget CSV rows match byte-for-byte. This uses the existing Python
3.12 interpreter and does not claim a fresh package installation. No unarchived
analysis files or simulation reruns were needed. Acceptance evidence updated;
draft assets and scientific counts remain unchanged.

## 2026-09-14 — Autonomous cycle 62

Profiled a baseline 2000-tick loop with invariants, snapshots and event draining,
plus one unprofiled comparison. Selected final-state digests match. Observed
1.3141 seconds unprofiled and 4.5793 profiled; these are single local operational
samples, not before/after optimization. Random sampling is prominent and neighbor
queries modest. Recorded methods, raw profile summary and limitations.

Decision: retain the engine rather than change random draws or add caching for
an unproven gain. Exact historical streams and checkpoint compatibility matter;
any optimization needs repeated representative measurement and replay evidence.
No code behavior or scientific count changed.

## 2026-09-14 — Autonomous cycle 63

Improved newly generated replay timelines with aria-valuetext containing actual
tick, population and saved-frame position, plus keyboard/sampling help connected
through aria-describedby. This distinguishes sampled frame indices from model
time. Existing generated pages and fixed archives are unchanged.

A fresh 100-tick demo was checked in the browser: Home then Right selects tick
10/population 144; End selects tick 100/population 56. All 54 tests passed.
This verifies keyboard behavior and page updates, not independent screen-reader
speech output. No simulation rules or recording schema changed.

## 2026-09-14 — Autonomous cycle 64

Fixed stale individual details after an invalid lineage query. Failed lookup
now clears the previous detail row, ancestry and child controls, labels the
selection empty and marks the input invalid with its message linked. Successful
lookup restores details and removes the invalid state.

Verified in a fresh browser demo: ID 0 initially visible, nonexistent 99999
clears the old record, then ID 1 restores its details and child 179. All 54
tests passed. Only newly generated lineage pages change; historical artifacts
and simulation rules remain fixed.

## 2026-09-14 — Autonomous cycle 65

Replayed the first hundred ticks of all twenty stored/40 worlds at costs 0/4
with a read-only death observer around the original removal routine. All 2020
metrics match verified prefixes. Observed 3175/2962 deaths; 45/53 respectively
had food on the current cell, and 1166/1110 had food in cardinal neighbors.
Counts are nested death events, not independent samples. Existing charge-before-
feeding order explains how local food can coexist with a zero-energy death; no
counterfactual benefit from changing order was tested.

Tracked all-world counts, reference hashes, method and limits. The retrospective
diagnostic adds 2000 replay computation ticks and zero new independent seeds,
reported separately from formal campaign workloads. Engine and archives unchanged.

## 2026-09-14 — Autonomous cycle 66

Added boundary contracts for the execution-order interpretation raised by death
observations. A one-energy resting organism and a two-energy always-moving
organism both die before feeding despite food everywhere; food remains untouched
and dissipation matches the initial energy. A three-energy always-moving control
survives the charges, feeds and ends with nine energy. These distinguish zero
from positive post-charge energy and cover both death paths.

All 56 local tests, including the frozen historical trajectory, and compilation
passed. No engine behavior changed. This records an intentionally designed rule,
not a claim that this schedule is biologically correct or optimal.

## 2026-09-14 — Autonomous cycle 67

Connected the death-site evidence to the explicit V0 action-order rules and
boundary examples. Clarified that feed-before-charge would be a separately
versioned intervention, not a bug fix, and that future information comparisons
must match action order. Updated the storage note to distinguish bounded replay
sampling from growing lineage/raw records.

Source 12982c715964a57109493dcbbcf1e3e9f3955bdc passed all six CI environments
in run 34783952259, including the 56-test suite. Current acceptance guides cite
this checkpoint; archived source/test counts remain historical. No runtime or
experimental observations were changed.

## 2026-09-14 — Autonomous cycle 68

Preregistered campaign 013 and runner, then launched from clean source
f3f35e5850b1a358dc7b9c94692d5f1686057e1d. Fresh seeds 1100–1104, mutation 100/1000
versus zero, 50000 ticks each, ordinary random founders and unchanged V0 defaults.
Records every birth genome plus per-tick ever-seen diversity so first appearance
can be reconstructed independently. Explicitly distinguishes scalar vocabulary
coverage from functional novelty and does not force a saturation conclusion.

Compilation and 56 tests passed. Original process is live; outcomes are pending
and excluded from validated campaign totals. Next: verify birth-table ancestry,
first-seen coverage, energy accounts and declared horizon summaries.

## 2026-09-14 — Autonomous cycle 69

Extended campaign-013 verifier tests from birth catalogs to metric reconstruction:
a real short world passes; an invented intermediate discovery, energy mismatch
and truncated window are rejected. All 64 local tests pass. Independently checked
the first completed full run (mutation/1100): 74704 birth records, 371 ever-seen
values and two first appearances during the final 10000 ticks; all declared
horizon observations match. This is a per-run check, not a final group result.

The original experiment process remains live and continues the no-mutation arm.
No restart, new seed or observation-window change; validated totals still exclude
campaign 013 pending the complete-grid audit.

## 2026-09-14 — Autonomous cycle 70

Campaign 013 completed in the original process. Independent verification checked
744901 birth records and 500010 metric rows. Mutation worlds reach 340–371
ever-seen values, adding 0/2/7/12/22 during the final ten thousand ticks; four
of five add values. No-mutation worlds stay at the initial 77–78 values. All
ten survive 50000, each with one founder lineage. Neither permanent saturation
nor functional novelty is inferred. Report preserves all seeds and horizons.

Committed compact results, verification hashes and limitations of missing full
death/spatial records. Inventory now validates thirteen campaigns / 550 executions
/ 5740000 computed ticks, retaining twenty follow-ups and 200000 prefix replays.
Preregistered-source CI 34784159894 and 64-test verifier CI 34784386963 passed.
Twelve-campaign pages and downloadable archive retain their explicit scope.

## 2026-09-14 — Autonomous cycle 71

Added a two-panel genome-coverage figure from verified raw metrics: exact
cumulative change points versus living diversity sampled every hundred ticks.
All ten worlds are included; different vertical scales and sampling omissions
are explicit. The 1001 reference bounds the inherited movement vocabulary only.
No plateau fit or future extrapolation. Input hashes match the independent
verification report. Saved PNG/SVG, curve data and hash sidecar, and visually
checked axes, labels and legend. No new simulation or hypothesis test.

## 2026-09-14 — Autonomous cycle 72

Extended the optional review builder to thirteen campaigns, keeping its default
at eight and all earlier pages immutable. Added the full ten-world coverage
table and figure, with cumulative versus living diversity, late-window novelty,
sampling and finite-controller limitations stated explicitly. Browser inspection
confirmed the new section and every seed row. Updated current entry guides;
the downloadable twelve-campaign archive retains its original scope.
All 64 local tests passed. No new simulation or V1 runtime change.

## 2026-09-14 — Autonomous cycle 73

Extended packaging to thirteen campaigns, preserving the default and existing
archives. Committed source 1fc1c30 then packaged all selected raw records, with
the 013 birth-catalog/metric verifier included. Eleven full-run audits and the
selected metric audits passed. New archive: 853 files / 86150042 bytes, SHA-256
ed6e90acda91f1b8e74f88acca5f246c03ee308c627cb611c3e2d180cd1383f2.
Independent expected-hash verification checked 13 HTML pages and ten local
targets. Local 64 tests and source CI 34785000803 passed. Archive remains local;
the published download instructions still identify the twelve-campaign draft.
Next: recompute campaign 013 from an extracted archive before uploading a new draft.

## 2026-09-14 — Autonomous cycle 74

Revalidated the thirteen-campaign archive hash before extracting a new portable
copy. Ran its archived 013 verifier with the existing Python 3.12 interpreter
using -I -S: no site packages or working-directory imports. All 744901 birth
records and 500010 metric rows passed. Recomputed JSON equals the archived
verification JSON exactly, including every run, observation and input/script
hash. This was a record reanalysis, not a new simulation or fresh Python install.

Uploaded the archive and checksum to draft prerelease v0.0.1-preview.5, release
388046564, targeting 1fc1c30. API confirms both assets uploaded, 86150042 archive
bytes and matching SHA-256. Draft remains unpublished; older drafts are unchanged.
Updated acceptance and research download entries to the new thirteen-campaign
snapshot while preserving historical archive scopes and hashes.

## 2026-09-14 — Autonomous cycle 75

Found a checkpoint validation gap: an in-range child genome impossible under the
configured inheritance rule was accepted after recomputing the checksum. Added
a reproducing test with mutation disabled, zero mutation step, and positive
mutation bounded at 100; all three cases failed before the fix. Loading now
checks every child's change against its parent's genome and configured mutation
bounds, including historical dead descendants and drained event buffers.

All 65 tests pass after the fix; all eight checkpoint tests also pass under -O.
Existing continuation tests compare RNG, events, lineage, space and complete
checkpoint bytes. No engine source, rules, random draws or checkpoint schema
changed. This strengthens consistency checks, not authenticity or exhaustive
history reconstruction. The fixed thirteen-campaign archive predates this fix.

## 2026-09-14 — Autonomous cycle 76

Extended the checkpoint review to pending events. Eleven corruption cases were
accepted by the prior loader: unsupported event kind, inconsistent birth/death
fields, invalid birth position/energy, duplicate events and reverse chronology.
Each case recomputed the envelope checksum, isolating structural validation.
The new event validator rejects these while retaining empty/drained buffers.
Birth ancestry/genome/tick and death energy/location/tick match lineage; founder
birth energy matches configuration. Child birth energy and historical birth
location are only bounded because full transition reconstruction is unavailable.

All 66 local tests pass, including exact continuation comparisons; all nine
checkpoint tests pass under -O. Engine source, rules and checkpoint schema remain
unchanged. No claim of buffer completeness or authenticity. The fixed uploaded
thirteen-campaign snapshot predates this validation improvement.

## 2026-09-14 — Autonomous cycle 77

Added a retrospective exact decomposition of campaign-001 living mean-trait
change into birth sorting, death sorting and parent-to-child transmission.
All ten artifact audits pass; all 50000 tick identities and cumulative telescoping
sums hold with rational arithmetic, and reconstructed means match raw metrics.
Five mutation runs all increase mean trait while cumulative direct transmission
is negative (-142.47 to -77.35). The no-mutation term is exactly zero. Birth sorting
is positive in every run; death sorting is negative for mutation seed 1.

Report derives the identity and distinguishes trajectory bookkeeping, stochastic
sorting and counterfactual mutation effects. No new simulations or independent
replicates; no adaptation or significance claim. Four hand-computed tests added;
all 70 tests pass. Committed all-run CSV and input/script hashes. Fixed archive
contains the necessary old raw events, but predates this new analysis.

## 2026-09-14 — Autonomous cycle 78

Added a signed contribution chart for the ten campaign-001 trait decompositions.
Both panels share axes; births, deaths and transmitted mutation are separate
components, and diamonds mark the net mean change. Mutation seed 1's negative
death component remains visible rather than being hidden by treatment averages.
Validated complete seed grid, finite values and rounded decomposition totals
before plotting. Saved PNG/SVG and the plotted data/input/script hashes; visual
inspection confirms readable axes, labels and legend. No new simulation or test
of statistical significance. The diagram is linked from the derivation/report.

## 2026-09-14 — Autonomous cycle 79

Evaluated the exact one-birth mutation-kernel expectation at each observed
campaign-001 parent, then weighted it using the recorded post-tick population.
Raw hashes match the prior audited decomposition; its observed mutation terms
are reproduced exactly. All five mutation reference sums are negative, and the
observed-minus-reference differences have both signs. Most births come from
parents above 900. All no-mutation reference and observed terms are exactly zero.

Report states that observed parents and denominators are trajectory-dependent:
this is neither an unbiased full-path expectation nor a clipping counterfactual.
Saved every run, unweighted increments and input/reference/script hashes. Added
hand-enumerated kernel boundary and disabled-mutation tests. No new simulations.

## 2026-09-14 — Autonomous cycle 80

Partitioned each of ten campaign-001 trajectories into all five contiguous
1000-tick windows, using the tested exact decomposition helper. All fifty window
identities telescope and their component sums equal each prior full-run result.
Raw hashes match the audited analysis. First windows all rise; final mutation
windows decline in three worlds and rise in two. Final control windows have zero
trait change despite each retaining over 1400 births and deaths.

Preserved every window, raw/helper/reference/script hashes, and explicit start
boundary semantics. Report distinguishes whole-run direction from late trends,
trait fixation from demographic arrest, and repeated windows from independent
replicates. No new simulation, stationarity or equilibrium claim. Existing
73-test analysis-source CI 34785743212 passed.

## 2026-09-14 — Autonomous cycle 81

Consolidated the Chinese review entry instead of appending another status block.
Removed stale contradictory claims calling the nine-campaign draft "latest" and
corrected main README's eleven-campaign label against the inventory (thirteen,
550 executions, 5740000 ticks). Historical archives remain documented in the
full acceptance checkpoint and unchanged on disk/GitHub.

The shorter guide distinguishes the fixed 64-test archive from newer main
validation/analyses, gives an explicit review path and three evidence/limitation
comparisons, and links every deeper report. Confirmed all six jobs of 73-test
source CI 34785743212 passed. Inventory recount agrees. V1 remains design only.

## 2026-09-14 — Autonomous cycle 82

Loaded three actual historical checkpoints with the strengthened current loader:
tick 1000 (1641 lineage records, 3199 events), and two tick-2500 files (3860
records, 7639 events each). Same engine hash and Python 3.12 minor as required.
Resumed the preserved tick-1000 state through the CLI for 1500 more ticks into a
new directory. Its complete 2219615-byte result is byte-identical to both older
tick-2500 files, SHA-256 fb3b3bd325df3304d5337ae8f2fc55d658799af5b2646225390c1a0fa0779d41.

Recorded source/runtime and all input/result hashes. No historical file modified;
engineering replay only, outside formal counts. This validates acceptance of real
compatible old records alongside rejection of malformed ones, not unrestricted
cross-version compatibility. Documented the local-input and archive limits.

## 2026-09-14 — Autonomous cycle 83

Preregistered campaign 014 before running: costs 1/2/3/4, B initial fraction
10%/90%, competition 250 versus 1000 and neutral 250/250 labels, mutation off,
new seeds 1200–1209, 3000 ticks each. Planned 160 worlds / 480000 new ticks.
The reversed majority tests finite-window frequency dependence; it is explicitly
not equilibrated-resident invasion or a stable-coexistence assay. All endpoints,
extinctions and matched-seed limitations are specified in advance.

Committed protocol/runner as 7fabace and launched once from clean source into
new data/campaign-014. The original process is active. Per-tick full metrics and
group counts are retained, with runtime invariants; independent group/metric
audit remains to be built before conclusions. Local 73 tests pass. Current formal
inventory stays at thirteen campaigns until complete-grid verification succeeds.

## 2026-09-14 — Autonomous cycle 84

Built campaign-014's independent verifier while the original run continued.
Checks complete parameters/grid, initial state, contiguous ticks, group and
population accounting, trait means/diversity, no lost-group return, cumulative
and per-tick energy/birth/death bounds, loss times and exact terminal summaries.
Partial checking exposed the verifier's incorrect assumption that extinct
max_generation is zero; the established engine uses None. Corrected the verifier
and added a real extinction fixture without changing the experiment or engine.
All 78 local tests pass; verifier source d6c06f5 committed.

The original process then completed normally, all 160 worlds. Full independent
verification passed for 480160 metric rows. Results are saved locally under
campaign-014-analysis; next step is the complete report, compact data and formal
inventory update. No run restarted, dropped or extended. Group membership is
checked for consistency with saved trait summaries, not reconstructed from
unsaved full individual histories; this limitation remains explicit.

## 2026-09-14 — Autonomous cycle 85

Committed campaign-014's full report, 160-row compact results and independent
480160-row verification. Costs 1/2 yield all B-only competition endpoints at
both initial fractions. Cost 3 gives mixed outcomes; cost 4 with initially common
B includes five extinctions. All six total extinctions are reported individually,
including first group loss and later total loss; no survivor-only denominator.
All neutral and competition endpoints remain separate. No critical-cost,
stable-coexistence or rare-invasion conclusion.

Inventory now validates fourteen campaigns / 710 executions / 6220000 computed
ticks, including the same twenty follow-ups and 200000 historical prefix ticks.
Current guides updated; fixed thirteen-campaign page/archive explicitly exclude
014. Verifier CI 34786356370 passed. Original experiment process was terminal;
no active simulation remains from this campaign.

## 2026-09-14 — Autonomous cycle 86

Added a four-panel tile chart for all 160 campaign-014 endpoints. Costs and seed
labels remain explicit; competition and neutral labels are separate panels at
both initial fractions. A/B/AB/X symbols supplement colors. All six extinctions
and four neutral both-present endpoints are included. No survivor-only filtering
or uncertainty interval. The plotter validates the complete identity grid and
reconciles tile outcomes with verified group totals.

Saved PNG/SVG and outcome/input/script hashes; visually inspected titles, seed
labels, symbols and legend. Linked figure and regeneration command from the full
report. No new simulation or changed interpretation of finite endpoint survival.

## 2026-09-14 — Autonomous cycle 87

Extended the review builder to fourteen campaigns while preserving default eight
and all existing pages. The new section checks the full 160-key grid and includes
the sixteen condition totals, all-seed figure and explicit extinction/endpoint
limitations. Generated review-v0-14.html as a new file. Browser inspection confirmed
the complete section and the cost-4 majority-B extinction count; all 78 tests pass.

Updated local page entries to fourteen. Download instructions still identify
the fixed thirteen-campaign source and archive, which has not been replaced.
Retrospective trait decompositions remain report-only, separately distinguished
from the numbered formal experiment sections. No new simulation.

## 2026-09-14 — Autonomous cycle 88

Added explicit fourteen-campaign packaging, including the 014 verifier, while
retaining default eight and exclusive output paths. Committed source 6d98fb9,
then generated a new archive: 1044 files / 96447134 bytes, SHA-256
0501fd0c6cf4d947ee26fb3fc107b592adf5f9c66d854531b7ef364ff6b6240a.
All eleven full-run audits and selected 005/009–014 metric checks passed.
Standalone expected-hash verification checked 13 HTML pages and eleven targets.
Source CI 34786711417 passed. The packaging process completed normally.

Recorded local snapshot scope and checksum. Thirteen-campaign uploaded draft
remains unchanged. Next: independent reanalysis of archived 014 inputs from an
extracted copy before uploading this new draft. No new simulation.

## 2026-09-14 — Autonomous cycle 89

Revalidated the fourteen-campaign archive hash, extracted a new copy, and ran
its archived 014 verifier using Python 3.12 -I -S. All 480160 metric rows passed;
the complete report equals its archived reference, including all 160 outcomes
and raw/metadata/script hashes. Existing interpreter, no new installation or
simulation. The reanalysis output is retained under portable-recomputed-014.

Uploaded archive/checksum to draft prerelease v0.0.1-preview.6, release 388054596,
targeting 6d98fb9. GitHub reports both assets uploaded with matching archive
96447134 bytes and SHA-256 0501fd0c6cf4d947ee26fb3fc107b592adf5f9c66d854531b7ef364ff6b6240a.
Draft remains unpublished. Updated current download guides and snapshot/test
scope; all earlier archives are unchanged.

## 2026-09-14 — Autonomous cycle 90

Created a fresh Python 3.12.10 venv beside the extracted fourteen-campaign source
and installed its noneditable wheel. Confirmed imports resolve to the new
site-packages rather than the development tree. All 78 archived tests pass.
The installed CLI generated a new 1000-tick demo, and its full audit passed:
1641 individuals, 1561 births, 1558 deaths, 83 final population, 101 frames.
Metrics/events are byte-identical to the archived acceptance demo; lineage and
summary JSON equal structurally. Recorded hashes and exact scope.

Pip resolved build dependencies, not an offline guarantee. This adds only 1000
engineering replay ticks outside formal campaign totals. Archived files and
draft assets unchanged. Fresh installation complements the earlier raw-data
reanalysis rather than claiming every formal simulation was rerun.

## 2026-09-14 — Autonomous cycle 91

Checked the neutral-label invariance implied by campaign 014's design. At each
cost/seed, B=8 and B=72 runs have identical all-250 genomes and differ only in
observer labels. All 40 pairs / 120040 paired rows exactly match every saved
non-label field; nested founder-group counts also hold. Inputs match prior
independent-audit hashes. No unsaved spatial/RNG comparison or new simulation.

Report now explicitly distinguishes eighty neutral executions from independent
physical trajectory samples. Saved paired-check hashes and added tests rejecting
changed physical metrics, truncated pairs and reversed subset counts; all 81
local tests pass. The supplement postdates the fixed fourteen-campaign archive.

## 2026-09-14 — Autonomous cycle 92

Manually checked input boundaries on the lineage page generated by the fresh
fourteen-campaign installed package. Blank Inspect clears the prior individual;
valid 1640 plus Enter restores its detail/ancestry; fractional 1.5 plus Enter
clears that populated view; valid re-entry restores again. Parent-button
navigation to 1618 displays parent 1609 and children 1624/1631/1640, matching
raw lineage. The existing behavior passed, so no UI code change was necessary.

Recorded artifact hashes and manual-check limits. This is new browser evidence,
not added automated test coverage, cross-browser testing or screen-reader speech
verification. The browser remains on the valid parent record for continued work.

## 2026-09-14 — Autonomous cycle 93

Review of failure reporting found two concrete defects in recorded runs:
initialization exceptions escaped the status handler, leaving metadata "running";
and exceptions inside a step could count the already-incremented world tick as
completed. Reproducing tests failed for both. Moved world construction inside
the handler and track completion only after the loop's record handling finishes.
Initialization failures now report failed/zero, and a partial third tick after
two completed ticks reports failed/two. Original errors are re-raised.

All 83 tests pass, including frozen engine replay and prior interruption cases.
No engine source, random draws or successful-run schema changed. Documented
that retained partial files are diagnostic and not crash-safe/resumable records.
The fourteen-campaign fixed archive predates this runner-status correction.

## 2026-09-14 — Autonomous cycle 94

Recomputed all three trait-change supplements from the extracted fourteen-campaign
archive using its installed wheel and saved raw records. Full-run decomposition,
local mutation reference and five-window decomposition all reproduce complete
archived JSON reports exactly, including their input/script/helper/reference
hashes, and CSVs byte for byte. Recorded comparison hashes and invocation modes.

The kernel reference ran -I -S with standard library only; full decomposition
used -I plus the installed package audit; windows used normal script mode for
the sibling helper and installed package. Dependency scope is explicit. No new
simulation, changed source or broad cross-platform portability claim.

## 2026-09-14 — Autonomous cycle 95

Preregistered and completed campaign 015 from clean source b575054: all four
neutral campaign-014 endpoints retaining both labels at tick 3,000, followed
to 30,000 without early stopping. All lose one group at ticks 3,625–4,765;
remaining groups survive to the endpoint. This is a selected conditional cohort,
not new independent seeds or an estimate of stable coexistence.

Independent verification checks 120,004 rows and matches all 12,004 historical
prefix rows to the previously hashed reference. Added tests for truncated and
changed prefixes, incomplete follow-ups and sparse inventory seed counts.
Inventory now records 15 campaigns / 714 executions / 6,340,000 computed ticks,
including 24 follow-ups and 212,000 replayed prefix ticks. Raw observation
extension is 108,000 ticks for this campaign. Published compact results, hashes
and finite-horizon limitations; the fixed fourteen-campaign archive is unchanged.

## 2026-09-14 — Autonomous cycle 96

Confirmed CI 34788020711 for source 8cbbadf completed successfully across all
six Windows/Linux and Python 3.12–3.14 jobs. Updated the Chinese acceptance guide
with fifteen-campaign counts, conditional follow-up findings and the explicit
boundary between current main and the fixed fourteen-campaign archive.

Added a V0 graduation evidence matrix mapping all six roadmap criteria to engine,
tests, declared-seed experiments, saved records and browser/portable checks. The
matrix distinguishes historical artifact scope from later code and identifies
V1–V4 evidence as missing. V0's minimal milestone does not establish sensing,
intelligence or open-ended evolution. Checked relative links in the changed
acceptance/roadmap documents. No new simulation or runtime change this cycle.

## 2026-09-14 — Autonomous cycle 97

Added all-four-world campaign-015 trajectory figures with early-detail and full
30,000-tick panels. Raw CSV hashes match the independent audit; observation and
first-loss annotations are checked. All saved points are supplied with path
simplification disabled. The repeated early panels are explicitly identified.

Visual inspection caught clipped right-edge tick labels; widened the margin and
rechecked the corrected PNG before committing PNG/SVG/provenance. Caption states
that boundary fractions mean one label, not demographic stasis, and preserves the
conditional-cohort limitation. No new experimental executions or engine changes.

## 2026-09-14 — Autonomous cycle 98

Extended the review builder to campaign 015 while preserving existing generated
pages and the default eight-campaign route. New section includes all four cases,
first group losses, original/final counts and the complete trajectory figure.
A guard compares the selected historical cohort and all saved result fields
against the independent audit; reordered input is accepted, duplicate records,
changed outcomes and an unselected reference are rejected in three new tests.

Built data/review-v0-15.html. Checked 714 executions, 6,340,000 ticks, 24 follow-ups,
212,000 prefix replays and all ten local targets. In-app browser inspection
confirmed the four table rows and the loaded figure. Recorded the page hash and
verification scope; updated local entry guidance without implying the old
fourteen-campaign download has changed. All 92 tests pass. No runtime change.

## 2026-09-14 — Autonomous cycle 99

Extended packaging to fifteen campaigns with an explicit campaign-014 reference
for the conditional follow-up verifier. Committed source 0344839 and produced a
new local archive: 1,071 payload files, 100,031,797 bytes. Full-run and selected
metric audits pass; expected-hash standalone verification confirms thirteen HTML
pages and twelve local targets. Manifest counts match the committed inventory.

A documentation read initially used the Windows default encoding and failed;
no document was partially written. Corrected the read to UTF-8 after the clean
source archive completed, then updated main's command guide. The fixed snapshot
is explicitly identified and not silently rebuilt. New archive installation and
upload verification remain subsequent steps; previous uploaded drafts unchanged.

## 2026-09-14 — Autonomous cycle 100

Hash-verified and extracted the fifteen-campaign archive, created a fresh venv,
and installed its noneditable wheel. All 92 archived tests pass; package imports
resolve inside the new environment. A new 1,000-tick demo passes audit and matches
archived events/metrics byte for byte and lineage/summary structurally. Recomputed
campaign 015 with archived scripts/raw records; the complete report is identical,
including hashes. Engineering demo ticks are excluded from formal totals.

Uploaded a separate draft v0.0.1-preview.7, release 388062162. API confirms both
asset states, archive bytes and SHA-256, and the checksum asset's bytes/digest.
Source 0344839 CI is successful. Updated acceptance entry to the fifteen-campaign
download, retaining explicit source and prior-archive limits. Build dependency
resolution is not an offline-install guarantee; this is not every-campaign replay.

## 2026-09-14 — Autonomous cycle 101

Quantified demographic turnover after neutral label loss using only the four
already audited campaign-015 trajectories. Common ticks 5,001–30,000 contain
33,623–46,148 births per world, with substantial population ranges despite fixed
labels and genomes. Cost-1 seed 1206 starts/ends with 110 individuals but ranges
66–173 and has 46,148 births plus 46,148 deaths. Equal endpoints are not stasis.

Saved common-window and per-world post-loss counts, with exact event/state window
conventions and overlapping-observation limits. Verified raw input hashes and
accounting; three tests cover window boundaries and corrupted/truncated input.
This is demographic turnover, not new genetic or functional innovation. No formal
execution counts changed; the supplement postdates the fixed uploaded archive.

## 2026-09-14 — Autonomous cycle 102

Reviewing launch provenance exposed a real attribution defect: directly importing
archived source nested under this checkout reported outer main revision 052da87,
although the extracted archive source is 0344839. Added a reproducing regression
test that failed, then restricted Git lookup to a source root with its own .git
directory or worktree file. Source hashes remain available without Git metadata.

All 97 tests pass. A separate exported copy of corrected source under the outer
checkout now reports null Git revision/dirty state; the real checkout still
reports its own revision. A regression test preserves support for .git worktree
files. No engine rules or RNG changes. Documented the fixed archive's direct-src
limitation; its tested noneditable installation route remains unaffected. Old
records and uploaded snapshots remain unchanged.

## 2026-09-14 — Autonomous cycle 103

Malformed-artifact review reproduced an uncaught AttributeError for metadata
containing a JSON list or null. Added explicit expected top-level object/array
checks for metadata, summary, lineage and frames, with filenames in error text.
The new multi-case regression failed before the change and passes afterward.

All 98 tests pass. A real CLI invocation on malformed metadata exits 2, names
metadata.json and its expected JSON object, emits no traceback, and leaves the
file hash and directory contents unchanged. No simulator rules, successful output
schema or historical files changed. Documented the old fixed archive's error-path
limitation without implying its valid-run verification is invalidated.

## 2026-09-14 — Autonomous cycle 104

Demonstrated that the auditor accepted metadata substitutions such as 50.0 for
requested/completed steps, true for seed and 8.0 for width. Added strict integer
checks and the complete fixed V0 config key set; missing seed and unknown keys
are rejected too. Numeric equality is no longer sufficient for integer metadata.

The five substitution cases failed their rejection test before the fix and pass
afterward. All 99 tests then passed; added and ran the further key-set regression
as part of the ten-test audit suite (100 tests now in total). Eleven historical
full-record audits, campaign 001's ten worlds and the acceptance demo, pass without
changes. No engine semantics, random draws or old records were modified. The
checks validate metadata form, not independent seed replay or authenticity.

## 2026-09-14 — Autonomous cycle 105

A corruption probe changed one intermediate replay organism's genome or founder
label while retaining valid bounds, population and embedded metrics. Both damaged
frames incorrectly passed the prior auditor. Added per-frame joint trait/founder
multiset reconciliation against the living lifecycle records, maintaining one
rolling counter rather than copies of every historical population.

The reproducing two-case regression now passes. All 101 tests pass, and eleven
historical full-run audits reconcile all 1,111 stored frames unchanged. Documented
that this does not independently reconstruct individual position histories or
unsaved movement steps. The engine and replay format are unchanged; the stronger
audit postdates the fixed archive.

## 2026-09-14 — Autonomous cycle 106

Reviewed the current auditor against its advertised scope and added an explicit
coverage matrix for metadata, metrics, lineage, events, intermediate frames and
final artifacts. Distinguished recorded consistency, archive integrity, execution
inventory, reference replay and controlled scientific evidence. Linked it from
the README and archive verification guide.

The matrix states concrete limits: no per-individual movement reconstruction,
no independent exact birth-energy split verification, no certification of every
advertised intermediate sample, no seed authentication and no causal inference
from offspring totals. Confirmed source 3dbadf4 CI 34789147628 succeeded across the
configured matrix. Documentation links resolve; no new simulation or code change.

## 2026-09-14 — Autonomous cycle 107

Deleting a saved intermediate replay frame reproduced another audit gap: endpoints
and remaining frame consistency alone did not detect missing advertised samples.
Added exact frame schedule comparison using the effective recorded interval,
including final nonaligned ticks and the single initial frame for zero-step runs.

The missing-frame regression failed before the fix and passes afterward. All 103
tests pass, including zero/nonaligned horizons; eleven historical full runs remain
valid without edits. Updated the audit scope matrix to describe the stronger
sampling guarantee and retain the limit on unobserved events between samples.
No simulator, recording format or archived files changed.

## 2026-09-14 — Autonomous cycle 108

Preregistered campaign 016 and committed runner/protocol at d56af66 before launch.
Thirty 10,000-tick executions cross ten new seeds (1300–1309) with uniform,
dispersed and torus-translated block food maps. All begin with 5,120 food energy
plus 1,920 organism energy; fixed trait 250, mutation disabled and regrowth 15.
Dispersed/block maps share the exact value multiset; uniform changes both local
amounts and arrangement and is not an arrangement-only contrast.

Validated all thirty initial maps for total energy, bounds, repeated construction
and shared concentrated multiset; all block maps are connected on the torus.
Layout RNG is separate from world RNG. Initial food/founders and RNG-state digest
are saved for independent pairing checks. Launched from clean source; results
remain provisional until the whole grid and initial-state/metric records are
independently verified. Formal inventory remains fifteen completed campaigns.

## 2026-09-14 — Autonomous cycle 109

Campaign 016 completed all thirty runs. Built an independent standard-library
verifier for the declared initial layouts, exact founders/world RNG pairing,
initial exposure and all 300,030 metric rows. All thirty initial states and ten
matched seed triplets pass, as do terminal and observation summaries. Three new
helper tests pass; full suite 106 tests. This verifier does not step the engine.

At tick 500, uniform/dispersed/block have 8/7/0 surviving worlds; at 5,000 they
have 3/0/0; at 10,000 all are extinct. Block extinction times are 110–169,
dispersed 152–3,362, uniform 148–8,845. Block dies earlier than dispersed in all
ten matched pairs. Reported controls, absence of dynamic RNG matching after
initialization, and uniform's additional local-amount confound. No universal
geometry or evolved-sensing claim.

Committed compact data and verification hashes; inventory now sixteen campaigns,
744 executions and 6,640,000 computed ticks (212,000 declared prefix replays
unchanged). The fixed fifteen-campaign archive remains unchanged and excludes
this new campaign. Raw full death/movement histories were not retained.

## 2026-09-14 — Autonomous cycle 110

Added campaign-016 figure combining the first declared seed's three initial food
maps with all thirty extinction times. Shared map color scale and identical
founder rings show the intervention; outcome points retain all ten seed triplets
on an explicitly logarithmic time axis. Inputs match the independent audit and
illustrative map hashes.

Visual inspection found nearly equal outcome markers obscuring one another for
two seeds. Applied small treatment offsets and rechecked the corrected figure;
all points remain visible. Caption distinguishes illustrative maps, matched
initial seeds and divergent later draws. Published PNG/SVG/provenance and linked
from the report. No new simulation, summary change or stronger causal claim.

## 2026-09-14 — Autonomous cycle 111

Extended the local review builder to sixteen campaigns. It validates the full
arm/seed grid and equality with the independent campaign-016 report before
rendering all three observation horizons, extinction ranges and the map/outcome
figure. The section preserves the uniform-arm confound and limits on paired RNG.

Built data/review-v0-16.html. Checked workload counts and all eleven local targets;
in-app browser inspection confirms the new section, table and image presence.
Recorded page hash and inspection scope. Updated local entry guidance while
retaining the fifteen-campaign download scope; source 114ad02 CI 34789702658 is
successful with 106 tests. Existing generated pages and archives are unchanged.

## 2026-09-14 — Autonomous cycle 112

Extended packaging to campaign 016 and committed clean source 8acb86c before
building. New archive includes all sixteen raw campaigns, initial geometry maps,
current strengthened audits, 106 tests and the sixteen-campaign review page.
The full-run and selected metric audits pass, including initialization pairing.

Produced 1,154 payload files / 101,914,494 bytes. Standalone standard-library
expected-hash verification passes with thirteen HTML pages and thirteen local
targets; manifest source, workload and campaign-016 audit counts match. Recorded
checksum and scope. Extracted installation and upload remain independent follow-up
checks. Prior archives and their source scopes are unchanged.

## 2026-09-14 — Autonomous cycle 113

Extracted the hash-verified sixteen-campaign archive into a fresh directory and
installed it noneditably in a new environment. All 106 archived tests passed.
A fresh thousand-tick run passed audit and reproduced acceptance metrics/events
byte for byte and lineage/summary structurally. Installed provenance has no Git
commit. Recomputed campaign 016 with the archived isolated standard-library
verifier: all 30 initial states, ten paired triplets and 300,030 metric rows pass;
the complete report equals the archived report, including hashes.

Uploaded separate draft preview.8 (release 388070091) and verified API state,
size and SHA-256 for both assets against local files. Source 8acb86c CI is
successful. Updated the Chinese acceptance entry and research index to this
sixteen-campaign snapshot. Prior archives remain unchanged; formal execution
counts do not include this installation demonstration.

## 2026-09-14 — Autonomous cycle 114

Checked a known remaining audit limitation: V0 configuration values had strict
integer types but incomplete domain validation. Adversarial metadata with
probabilities 1,001 or an insufficient birth threshold was accepted. Added
independent v0-darwin-1 range checks, preserving valid negative seeds and zero
parameters where the rules permit them. The new test first failed on the old
code; a legal empty 2-by-2 boundary run verifies acceptance of allowed extremes.

All 108 local tests pass. Eleven existing full records, totaling 1,111 replay
frames, still pass the strengthened auditor. Engine code and raw records are
unchanged. Updated the audit scope to separate valid parameter domains from
proving the values were actually used. The fixed sixteen-campaign archive
predates this correction and retains its original auditor and hashes.

## 2026-09-14 — Autonomous cycle 115

Retrospectively analyzed initial food access in campaign 016 without additional
world runs. A standalone standard-library script hash-checks all thirty maps
against the existing verification report, reconciles immediate exposure, and
computes nearest-food distances on the torus while ignoring occupancy.

Block has more founders initially on food in seven matched pairs, equal in one
and fewer in two, yet goes extinct earlier in all ten. Dispersed maps put every
founder within four cells of initial food; each block world has maximum founder
distance thirteen. Recorded all thirty rows and distance histograms, and added
an explicit distinction between geometric access and actual feeding trajectories.
No unique causal mechanism, travel-time estimate or starvation claim is made.

Three distance tests include independent toroidal Manhattan comparisons with
single/multiple sources and narrow worlds, all-food maps and invalid/missing food.
All 111 local tests pass. Updated campaign report; fixed sixteen-campaign archive
remains unchanged and formal inventory totals do not increase.

## 2026-09-14 — Autonomous cycle 116

Extended the campaign-016 interpretation with first-100-tick energy accounting.
Hash-checked thirty full metric files and metadata against the existing verifier,
then reconstructed food uptake over all 3,000 early transitions and reused the
established basal/birth/movement accounting helper. No new formal runs.

Block worlds consumed 5,688–6,012 food units, above all uniform (3,893–5,134) and
dispersed (3,048–4,008) worlds, while producing 108–119 births and peaking at
123–167 individuals before falling to 1–8 at tick 100. Substantial food remains.
This constrains the previous spatial-distance observation: greater initial
distance is not evidence of lower total early consumption. Added explicit limits
on causal explanations and on confusing global food stock with individual access.

A direct food-removal observer test agrees with reconstructed uptake while
preserving snapshots and RNG relative to an uninstrumented reference; invalid
accounting cases fail. All 113 local tests pass. Saved every run and provenance,
updated the report, and preserved fixed archive scope and formal inventory totals.

## 2026-09-14 — Autonomous cycle 117: campaign 017 protocol

Prepared a new 2-by-2 experiment motivated by campaign-016 retrospective results:
dispersed/block food crossed with reproduction threshold 40/160, all seeds
1400–1409, fixed 10,000-tick horizon. Primary survival/extinction observations
and secondary first-100-tick feeding/birth/peak measures are declared before
execution. No rescue, replacement or optional extension. Forty planned runs are
not yet included in completed inventory totals.

The runner reuses the frozen food-map helper, keeps V0 dynamics unchanged, and
saves full initial states and metric tables. Initialization tests check all ten
seed quadruplets: identical founders and world RNG; same map within each layout;
exact food multiset and total energy. Raising the threshold does not isolate a
single mediator such as crowding or birth cost. Protocol and runner are committed
before launch so the execution source is identifiable.

Campaign 017 launched from clean source `05508f0fd1d933fbc318a80440e3990f698586b6` using
Python 3.12.10. The live process has produced its first complete runs;
no interpretation or completed-inventory change is made while it is running.
All 115 local tests passed before launch. Next step is independent reconstruction
of initial pairing, complete metrics and predeclared early/end observations.

## 2026-09-14 — Autonomous cycle 118

Campaign 017 completed all forty runs. Independently verified forty initial
states, ten founder/RNG quadruplets, twenty threshold-map pairs, 400,040 metric
rows and 4,000 early food-uptake transitions. Every stored observation matches
reconstruction. All 117 local tests pass; launch source CI 34790910564 passed.

All twenty threshold-160 runs survive to 10,000; threshold-40 survivors are two
of ten dispersed and zero of ten block. High threshold greatly suppresses early
births and population peaks. This is threshold-dependent finite-horizon evidence,
not identification of a unique mediator or long-term stability. New block seeds
also show extinction later than campaign 016's range, reinforcing its seed scope.

Saved report/results and added campaign 017 to the completed inventory only after
verification. Totals: 784 executions / 7,040,000 computed ticks; 24 historical
follow-ups and 212,000 replayed ticks unchanged. Updated research entries while
keeping the sixteen-campaign page/download scope explicit.

## 2026-09-14 — Autonomous cycle 119

Added the campaign-017 figure for all forty worlds. Top panels explicitly
separate observed extinction from right-censored survivors at 10,000; bottom
panels show predeclared early births with paired thresholds. Shared axes,
small treatment offsets and censoring symbols retain the two low-threshold
survivors without treating their observation limit as an extinction event.

The plotting script validates the full outcome grid and endpoint/censoring
consistency, records source/report hashes and every plotted outcome, and writes
PNG/SVG. Visually inspected the layout, then clarified the subtitle to distinguish
matching founders/RNG from food maps that match only within each layout.
Added the figure and interpretation to the report. No new simulation runs or
runtime changes; the sixteen-campaign archive remains unchanged.

## 2026-09-14 — Autonomous cycle 120

Extended the Chinese review builder through campaign 017. It validates all forty
arm/threshold/seed identities and exact equality with the independent report
before displaying the four treatment rows and all-seed figure. Censoring, paired
seed scope and the threshold intervention's multiple consequences are explicit.

Generated data/review-v0-17.html. Static HTML inspection verifies all four table
rows, workload counts and twelve local targets. Saved page hash and the limited
verification scope; this turn adds no browser interaction certification. Updated
local review entries while preserving the sixteen-campaign download scope and
all old generated pages. No new simulation runs or runtime changes.

## 2026-09-14 — Autonomous cycle 121

Extended packaging through campaign 017 and committed clean source 8e4cf89 before
building. Named full-run/metric audits pass, including forty initial states and
400,040 rows for the new campaign. The archive holds 1,260 payload files and
106,192,281 bytes. Independent expected-hash verification passes; recorded the
fixed source, checksum and workload scope. Added explicit UTF-8 reading of helper
reports during packaging. Extracted installation and upload remain follow-up
checks; previous archives and their source scopes are unchanged.

## 2026-09-14 — Autonomous cycle 122

Freshly extracted and installed the seventeen-campaign archive. All 117 archived
tests pass; a new thousand-tick demo reproduces reference metrics/events exactly
and lineage/summary structurally. Installed provenance correctly has no Git commit.
Archived campaign-017 verification reproduces the complete saved report from
extracted raw data with its archived helper. Source CI 34808083099 is successful.

Uploaded separate draft preview.9 and verified both remote assets against local
sizes and SHA-256 values. Updated acceptance download links and scope. Earlier
archives remain unchanged. Installation demonstration ticks are not formal
experimental executions; no offline-install guarantee is made.

## 2026-09-14 — Autonomous cycle 123

Consolidated the post-V0 decision note after the verified seventeen-campaign
handoff. It maps the latest evidence into future sensory controls and defines
what a bounded mechanism observer would need to measure and prove before use.
No new survival-only sweep is scheduled merely to increase execution totals.

Updated the V1 design contract with geometry/uptake and threshold-layout lessons:
match initial maps and reproductive parameters, and measure information use
separately from total intake or survival. The note distinguishes an observational
replay from an independent replicate or causal intervention and records a staged
future implementation/pilot/preregistration sequence. All additions are design
only; V0 remains the only runtime stage and fixed archives remain unchanged.

## 2026-09-14 — Autonomous cycle 124

Implemented a research-only feeding observer around the unchanged, source-pinned
V0 engine. It records actor identity, location, food before/after, intake and
pre-feeding energy, including zero-intake attempts; deaths before feeding produce
no feeding row. A drained buffer remains separate from lifecycle events.

Six configurations compared against ordinary worlds for 100 ticks each preserve
snapshots, food, full lineage, events and RNG state. Intake totals reconcile with
aggregate resource accounting; tests cover death-before-feed, zero intake,
source mismatch and replaced lists. All 120 tests pass. This is not the complete
movement/congestion/reproduction observer and no formal mechanism study has run.
Documented the missing gates, source coupling, retention and checkpoint limits.

## 2026-09-14 — Autonomous cycle 125: feeding replay preparation

Prepared a source-recorded retrospective replay of all forty campaign-017
first-hundred-tick prefixes. No cases are chosen based on outcome. The runner
hash-checks original maps/metrics, reconstructs initial founders/RNG, compares
every prefix snapshot and reconciles direct intake with the verified early total.
It drains per-individual feeding rows each tick into separate JSONL artifacts.

This is instrument validation and added observation of existing trajectories,
not an eighteenth campaign or independent replication. It covers only feeding,
not the complete movement/congestion/reproduction observer gate. Source is
committed before launch; failure/interruption metadata and new-only output paths
preserve reviewability.

Feeding replay completed from clean source 0479c34: all forty prefixes match all
4,040 original metric rows and yield 166,886 individual feeding attempts.
Separate JSONL readback reconciles per-run counts/intake/zero attempts, checks
unique tick/ID pairs, energy and food bounds, and matches file hashes. Recorded
all-run results and source provenance. Historical per-individual reference paths
are unavailable; the matching claim concerns original aggregate metrics. These
4,000 replay steps are not added to formal campaign totals.

## 2026-09-14 — Autonomous cycle 126

Analyzed all forty replay feeding files with a standalone standard-library tool.
Verified hashes, unique tick/ID keys, intake bounds and all prior counts/totals;
retained per-world histograms and ratios rather than pooling attempts as replicates.
At threshold 40, block worlds have both more attempts and higher mean intake per
attempt than dispersed worlds. Higher early total intake is not solely an
attempt-count difference, but this observation does not establish a survival
mechanism or an individual causal benefit.

Added full tables, provenance and explicit survivor/positive-intake conditioning
limits to campaign 017. Zero-intake fractions are not starvation rates; repeated
attempts are not independent samples. No simulation or formal inventory change.
Fixed seventeen-campaign archive remains unchanged and excludes these later
observer records and analysis.

## 2026-09-14 — Autonomous cycle 127

Extended the source-pinned feeding observer with explicit schema 2: energy-based
birth eligibility, empty neighboring cells immediately before the birth check,
and actual child ID supplied by the engine's birth method. This distinguishes
eligible-but-space-blocked cases from realized reproduction without copying or
changing V0 stepping code.

Full-occupancy and lone-parent edge tests pass; all six reference configurations
still match complete state/events/RNG, and observed child IDs reconcile with
lineage and per-tick births. All 122 local tests pass. Prior feeding JSONL files
remain their original schema and are not retroactively populated. Complete
movement/death action observation remains outside the tool's current scope.

## 2026-09-14 — Autonomous cycle 128

Replayed all forty historical first-100-tick prefixes with schema 2 from clean
source 0255c88, storing a separate dataset. All 4,040 original metric rows match.
A standalone readback compares all 166,886 prior feeding records field-for-field,
checks both datasets' hashes, reconstructs eligibility and verifies actual child
counts against original births.

Only block/40 seed 1409 has space-blocked eligible attempts: two of 120, with 118
births. The other thirty-nine worlds have none. Added all-world results and the
limited conclusion: frequent lack of adjacent birth space is not supported as
the direct early-birth explanation. Movement obstruction, food competition and
later behavior are not excluded. No formal campaign or independent sample added;
old replay files and fixed archives remain unchanged.

## 2026-09-14 — Autonomous cycle 129

Extended observations to schema 3 with pre-action position, movement attempt and
realized position change for individuals reaching feeding. Payment-phase tracking
distinguishes basal, pre-feeding movement and post-feeding reproduction without
modifying the pinned V0 engine. Lethal movement remains outside feeding rows and
is explicitly excluded from whole-population rate claims.

Forced full-occupancy, single-occupancy, nonmoving-reproducing and lethal-movement
cases validate the fields and preserve reference snapshots/events/RNG. All 124
local tests pass. Earlier replay datasets and fixed archives remain unchanged;
no new formal experiment or schema-3 outcome analysis is claimed yet.

## 2026-09-14 — Autonomous cycle 130

Replayed all forty early prefixes with schema 3 from clean source a70a9ab.
All 4,040 historical metric rows match. Independent readback verifies both replay
hashes and all 166,886 shared schema-2 fields, excluding only the schema version;
movement flags and toroidal cardinal displacement pass checks.

Occupied-target movement fractions among feeding survivors are 18.28–26.63%
for block/40 versus 4.12–6.97% for block/160; dispersed ranges are 5.91–12.53%
and 3.34–5.72%. Added all-world records and interpretation separating movement
obstruction from the rare adjacent-birth-space blocks. Lethal movement is absent
from the denominator, and no causal extinction mechanism is inferred. Formal
inventory and all prior datasets/archives remain unchanged.

## 2026-09-14 — Autonomous cycle 131

Added a separate pre-feeding death observer buffer with basal/movement phase,
initial action energy/position and attempted-movement flag. Feeding schema 3 is
unchanged. Tests prove each pre-tick living ID belongs exactly once to feeding or
terminal records, and preserve full reference state/events/RNG across six cases.
Explicit basal/movement death and zero-cost movement cases pass; all 126 tests
pass. Death on movement payment precedes destination choice and is not a block.

Documented dual-buffer draining and the remaining writer/readback step. Existing
historical feeding datasets do not acquire terminal rows retroactively; no new
whole-population fraction or mechanistic conclusion is claimed yet.

## 2026-09-14 — Autonomous cycle 132: complete-action replay preparation

Updated the historical prefix writer to drain and save terminal records alongside
feeding schema 3, declare both schemas in metadata, and check that their IDs
partition every pre-tick living population without duplicates. Outputs remain
new-only and include hashes for both streams. This extends the same all-forty,
first-hundred-tick replay, not the formal experiment count. Source is committed
before execution; old feeding-only datasets remain unchanged.

Complete-action replay finished from clean source 41144b6. All 4,040 original
metric rows match, and feeding JSONL bytes equal prior schema-3 files. Independent
readback reconstructs all active IDs from founders/children/deaths through 4,000
ticks, with exact stream partition and original birth/death/population accounting.
It validates 3,413 basal and 908 movement-payment terminal records under the
fixed unit costs. Saved all-world verification, hashes and scope. Counts denote
execution phases, not independent observations or a causal death attribution.

## 2026-09-14 — Autonomous cycle 133

Reconciled verified movement and terminal summaries using matching full grids and
feeding-stream hashes. All-attempt denominators now include lethal movement
payments and partition into success, occupied target and payment death. The prior
feeding-conditioned fraction is retained alongside the new fraction per world.

Block/40 occupied-target fractions are 17.79–25.73% versus 4.06–6.84% for block/160
under the complete movement denominator. Added exact per-world counts, group
ranges and limits separating execution-phase death from a counterfactual effect
of costs. No new runs, independent observations or causal conclusions added.

## 2026-09-14 — Autonomous cycle 134

Added a four-panel figure showing all forty per-world movement compositions.
Each bar partitions all attempted moves into success, occupied target and lethal
payment, using common 0–100% axes. Counts differ across worlds and are explicitly
linked rather than implied equal by normalized bars. Complete grids and integer
component sums are checked before rendering, with input/script hashes retained.

Visually inspected the PNG for legible seeds, axes, legend and caveats; saved PNG,
SVG and plot data beside the campaign report. No new trajectories or statistical
claims. The figure makes the distinction between occupied targets and pre-choice
payment deaths visible and keeps prior archive scope unchanged.

## 2026-09-14 — Autonomous cycle 135

Consolidated the growing campaign-017 mechanism report into a concise Chinese
briefing linked from the review guide and research index. It separates total
feeding, adjacent birth space, occupied movement targets and terminal payment
phases, with explicit supported/unsupported interpretations and denominator scope.

The briefing explains observer validation without claiming unavailable original
individual-path comparisons. It identifies the need to specify side effects of
any future causal intervention, and preserves the distinction between formal
campaigns and retrospective observations. Fixed seventeen-campaign downloads do
not silently acquire later observer data. No new runtime or experiment added.

## 2026-09-14 — Autonomous cycle 136

Built a separate observation supplement from clean source e2a06ce. It includes
tracked source, original campaign-017 records and four successive observer replay
datasets, not campaigns 001–016 raw data or generated review pages. Five analyses
reproduce their complete saved reports before packaging. The verified ZIP contains
596 payload files / 13,880,997 bytes, with checksum recorded.

Hash-checked and extracted into a new directory, then ran all five archived
standard-library analyses with isolated Python and that extracted working tree.
Every complete report equals the archived reference, including hashes. This
establishes portable reanalysis for the supplement without package installation
or new world execution. Upload remains a separate next step; the fixed full
seventeen-campaign archive is unchanged.

## 2026-09-14 — Autonomous cycle 137

Uploaded the observation supplement as separate draft v0.0.1-observations.1,
release 388168066. Verified both remote asset sizes and SHA256 digests against
local files through the GitHub API; no independent download claimed. Linked the
download and fresh-extraction evidence from the review guide and mechanism brief.
Updated next-decisions to distinguish completed bounded retrospective observations
from the broader original observer specification and unperformed causal studies.
The full seventeen-campaign archive and V0 engine remain unchanged.

## 2026-09-14 — Autonomous cycle 138

Reviewed the future V1 assay and added a design-only evaluation contract. It separates
behavioral response, reproductive information value and increased information
dependence relative to the actual ancestor. Defined candidate terminal-abundance
contrast with explicit both-extinct status, birth denominators, nested training-world
aggregation, unavailable samples and engineering failures. Specified same-state
controller probes and exact permutation averaging to avoid comparing behavior only
on divergent trajectories. Seed blocks, budgets and positive-claim thresholds remain
future preregistration fields. No V1 runtime or new experiment was introduced.

## 2026-09-14 — Autonomous cycle 139

Audited portable-review manifest handling. Negative fixtures exposed silently
accepted duplicate JSON keys, floating-point byte lengths and empty/null source
metadata. Added explicit manifest schema checks and duplicate-key rejection while
preserving optional inventory metadata. Added malformed-record/top-level cases,
duplicate ZIP members, traversal/absolute paths and symlink regression coverage.

All 129 local tests pass. Rechecked both fixed seventeen-campaign and observation
ZIPs against their externally recorded hashes with the stricter helper: 1,260/596
payload files pass unchanged. Existing archives and V0 world rules are unchanged;
this verifies stored integrity and format, not provenance authenticity or science.

## 2026-09-14 — Autonomous cycle 140

Analyzed individual intake on the forty verified early action replays. Included
all founders and newborns, including terminal-only actors and horizon births;
reconciled per-ID exposure with lifespan, action partitions and aggregate intake.
CSV cohort counts and sums match all eighty world/cohort report entries.

At threshold 40, block founders eat less and include more zero-intake individuals
than dispersed founders despite higher whole-world intake; most block intake is
by post-initialization births. Founder intake concentration is also high in surviving
threshold-160 block worlds, so it alone does not establish the extinction mechanism.
Added a standard-library analysis, complete report, Chinese interpretation and
boundary tests. Fixed archives retain their original scope; no new simulation.

All 132 local tests pass; 4,764 individual rows are retained in the generated CSV.

## 2026-09-14 — Autonomous cycle 141

Added PNG/SVG figures showing all forty worlds' founder/descendant intake and
zero-intake founder counts with shared axes and fixed founder denominators.
Verified every plotted record against the individual report and every stacked
total against the earlier feeding-only analysis. Visually inspected the PNG for
legible labels, complete seed rows and unclipped values. Figure metadata retains
all rows and source/script hashes. Linked it from the report and research index.
No new simulation or runtime change; the existing observation ZIP predates this
analysis and figure. The previous archive-verifier commit passed remote CI.

## 2026-09-14 — Autonomous cycle 142

Implemented a research-only energy ledger layered on the existing pinned feeding
observer, preserving both old record schemas and V0 engine source. Captures actual
payments, intake, child transfer and final parent energy for every acting ID,
including pre-feeding deaths. Reconciles each action locally without RNG draws.

Six configurations over 100 ticks match prior-observer state, full lineage,
events, RNG and both observation streams. Ledger totals match world energy flows.
Focused examples cover zero costs, odd child splits and capped lethal payments.
No historical energy replay was run and fixed supplement contents are unchanged.

All 135 local tests pass.

## 2026-09-14 — Autonomous cycle 143

Committed the bounded energy replay writer and launched it from clean source
be4ad5a. All forty campaign-017 prefixes completed, matching 4,040 original metric
rows and the prior feeding/terminal byte hashes. Recorded 171,207 per-action energy
ledgers, including 4,321 terminal actions; 4,000 replayed ticks are historical
observation work, not new formal worlds or independent seeds.

A standalone isolated standard-library verifier then reconstructed individual
energies from original initial states and the verified feeding/terminal records:
actual capped payments, food intake, child splits, ending stocks, population and
global dissipation all reconcile for every tick. Saved complete report and input
hashes. Existing fixed observation ZIP does not include the new ledger dataset.

## 2026-09-14 — Autonomous cycle 144

Separated founder and descendant energy budgets from verified historical ledgers.
Founder-to-descendant transfers cross cohort boundaries; descendant-to-descendant
birth splits cancel internally, rather than becoming new energy supply. Reconciled
both cohort balances, whole-world flow totals and prior cohort intake for all forty
worlds. All low-threshold block founders are dead by tick 100; surviving energy is
held by descendants. This describes cohort replacement, not a causal mediator.
Added analysis, complete report, Chinese interpretation and boundary tests for
internal transfers, endpoint births and rejection of unbalanced records.

All 137 local tests pass.

## 2026-09-14 — Autonomous cycle 145

Built observation supplement revision 2 from clean source 02df9c1, adding the
energy replay dataset and three analyses to the five existing checks. The archive
contains 738 payload files / 17,503,463 bytes. Eight analyses match complete saved
reports before packaging and again from a fresh extracted directory with isolated
standard-library Python. No package installation or new simulation was required.

Uploaded separate draft v0.0.1-observations.2 and verified both asset sizes and
SHA256 values through the GitHub API against local files. Linked extraction/upload
evidence and updated review entry points. Revision 1 and the full seventeen-campaign
archive retain their original scopes; no independent remote download claimed.

## 2026-09-14 — Autonomous cycle 146

Verified revision-2 source CI 34811470630 and all six Windows/Linux × Python
3.12/3.13/3.14 job conclusions. Saved compact evidence with explicit CI scope.
Reorganized the supplement guide around revision 2, eight contiguous commands,
exact output/reference mapping and the archive hash. Moved revision 1 to a
preserved-history section. This removes the previous split instructions and
keeps software CI separate from local historical reanalysis evidence.

## 2026-09-14 — Autonomous cycle 147

Reviewed prior protocols and registered campaign 018 as a necessary-condition
probe of charged movement: the complete layout × threshold × movement cost 0/1
grid on new seeds 1500–1509, eighty planned 10,000-tick worlds. Fixed all outcomes,
early observer window, pairing, failure accounting and verification gates before
execution. This is not a pure crowding intervention and must not identify a unique
mediator merely from an effect. No outcome runner or world has yet been executed.

Expanded observer/reference comparisons to include 100-step zero-charge sparse
and fully occupied engineering worlds, outside the outcome seed block. All state,
RNG, events, old observations and energy identities remain covered. Workload
inventory stays at seventeen verified campaigns until new results are complete.

## 2026-09-14 — Autonomous cycle 148

Implemented campaign-018 runner with clean-source enforcement, full metric output,
three early observation streams and explicit zero-charge assertions. Observer
buffers and engine events drain every tick; all worlds retain the fixed horizon.
Eight-treatment initialization and ten-step observer/reference trajectories passed
on engineering seed 23, including full lineage/RNG equality and matched food maps.
All 138 local tests pass. Protocol and implementation are committed before outcome
execution; completion and independent verification remain separate milestones.

## 2026-09-14 — Autonomous cycle 149

Confirmed the campaign-018 execution handle remains live. Implemented the
independent initialization/metric verifier with exact eight-treatment grid,
registered-protocol/source checks, paired initial maps/founders/RNG, original
metric invariants, strict zero-charge dissipation and joint threshold survival
statuses. Separate early individual-observation verification remains pending.

Two focused verifier tests pass, including a counterexample that conserves global
energy but violates zero-charge dissipation. Verified the eighteen completed worlds
available at inspection (180,018 metric rows) against their stored summaries;
this partial check is not full campaign acceptance. The runner is unchanged and
continues from its original clean launch source ff8ee77; do not restart it.

## 2026-09-14 — Autonomous cycle 150

Confirmed campaign-018 process is still live. Implemented separate early-observation
verification: exact actor partitions, inherited founder labels, feeding and birth
eligibility, legal cardinal displacement, death phases, reconstructed individual
energy and global stock/flow accounting. Reconciles founder/descendant budgets
without double-counting internal birth transfers. Zero-cost movement must have
no movement dissipation or payment deaths.

Focused tests detect wrong energy, duplicate actors, wrong founder labels and
teleportation, and accept both declared movement charges. Partial inspection of
45 completed worlds verified 227,582 early actor energy records. Full campaign
acceptance awaits the entire grid. Unrecorded blocked destinations, actual birth
positions and complete local food histories are explicitly outside this verifier's
scope. The original experiment process and source remain unchanged.

## 2026-09-14 — Autonomous cycle 151

Verified the new early-observation checker against all forty preserved campaign-017
worlds: 171,207 actor records accepted and every whole-world energy flow agrees
with the prior independent energy report. Saved the compatibility evidence and
verifier/reference hashes. No historical simulation was rerun.

The original campaign-018 handle remains live, with 65/80 worlds observed complete.
Prepared the final inventory/report integration points without changing completed
workload totals. Await remaining outcomes before full metric and early-observation
verification; no restart, seed replacement or changed horizon is authorized by
this intermediate progress check.

## 2026-09-14 — Autonomous cycle 152

Campaign-018 original process exited successfully after all 80 worlds. Independent
metric verification checked 800,080 rows and all initial pairings; early verification
checked 397,140 energy records over 8,000 world-ticks. Results CSV equals reconstructed
records. Standard-library sibling imports require -S, not -I; initial isolated import
failure created no result and did not rerun any world.

Zero-charge block/threshold-40 seeds 1501, 1502, 1504 still extinct at 169, 118, 190.
Thus a positive movement charge is not necessary for every failure in this design.
All high-threshold worlds survive the horizon; zero-charge low-threshold survival
is 10/10 dispersed and 7/10 block, versus 0/10 each with charge 1. Preserve the finite
sample, coupled dynamics and causal-mediator limits. Added full reports, all-world
censoring plot (visually checked), compact CSV and workload entry. Fixed downloads
retain their previous scopes. No V0 rule changes or V1 implementation.

## 2026-09-14 — Autonomous cycle 153

Summarized campaign-018 preregistered early processes from the two verified reports,
checking report provenance, all eighty identities, movement partitions, cohort
intake/ending stocks and birth expenditure. Added complete per-world JSON/CSV and
an all-treatment table to the main report, without selecting by survival.

Free-movement low-threshold block worlds still show 23.07–28.89% blocked attempts,
124–134 births and greater early basal expenditure than charged counterparts,
yet higher finite-horizon survival. These coupled trajectory differences do not
identify a mediator; the necessary-condition conclusion still rests on actual
zero-charge extinction counterexamples. No new simulation or rule change.

## 2026-09-14 — Autonomous cycle 154

Extended the local review builder to eighteen campaigns, requiring the complete
80-world treatment grid and exact outcome equality with independent verification.
The new section displays all eight survival groups, the all-world censoring figure,
zero-charge counterexamples and interpretation/download boundaries. Existing
seventeen-campaign pages are unchanged; default builder scope remains eight.

Generated review-v0-18.html and checked all eight new table rows against verified
groups, current workload totals and fourteen local targets. Recorded page hash and
static scope. Requested the page in the Codex browser panel; no fresh browser
interaction verification claimed. Updated local review entry points separately
from the still-fixed seventeen-campaign download.

## 2026-09-14 — Autonomous cycle 155

The original eighteen-campaign packaging handle completed successfully. Archive
source b304f2d contains 1,736 payload files / 124,483,734 bytes. The externally
recorded SHA256 matches; 13 HTML pages and 16 local targets pass archive checks.
Fresh extraction reproduced all three complete campaign-018 reports, including
hashes, without executing the simulator.

Created a new virtual environment and noneditable installation from the extracted
source. Confirmed site-packages import, passed 143 archived tests and audited a
new 1,000-tick demo. Metrics/events are byte-identical to the archived acceptance
demo; lineage/summary JSON agree; installed source correctly reports no Git commit.
Pip resolved build dependencies, so this is not an offline-install guarantee.
Upload remains separate; older archives are unchanged.

## 2026-09-14 — Autonomous cycle 156

Uploaded the verified eighteen-campaign archive and checksum as separate draft
v0.0.1-preview.10. GitHub API asset sizes/digests match local files; source b304f2d
CI passed. Saved remote evidence; no independent remote download claimed.
Rewrote the current review guide around the latest full package and separate
observation supplement, and moved stale acceptance opening statements beneath an
explicit historical-notes boundary. Updated download entry points without changing
old archives or their recorded evidence. No new experiment or runtime changes.

## 2026-09-14 — Autonomous cycle 157

Updated the post-V0 decision note to the eighteen-campaign checkpoint and corrected
its obsolete statement that no download contains the historical energy dataset.
Integrated campaign-018's necessary-condition counterexamples and the limits of
blocked-attempt/expenditure comparisons into subsequent research decisions.

The V1 design now explicitly treats free movement as an environment/viability
choice, requiring equal movement charges within all sensory contrasts. Any cost
robustness experiment must retain the full crossed grid. No new experiment or
runtime stage is launched; repeating the completed grid solely for a stronger
survival percentage is not prioritized. Links and document changes checked.

## 2026-09-14 — Autonomous cycle 158

Compared prior protocols: campaign 012 removes birth deductions but retains movement
charges, whereas campaign 018 does the reverse in different initial backgrounds.
Registered campaign 019 to test their joint absence, using forty new-seed block-food
worlds with movement cost zero and threshold × birth-cost 0/4 contrasts. Fixed
horizon, early observations, falsification rule and all-world reporting before any
outcome execution. This tests a conjunction, not a unique remaining mediator.

Added a 100-tick observer/reference case with both charges zero on engineering seed
5. Preserved source/RNG/lineage/event and energy checks. No campaign-019 outcome
world has been run; inventory remains eighteen verified campaigns. Old metric
helpers' birth-cost-4 assumptions require explicit new verification support.

## 2026-09-14 — Autonomous cycle 159

Implemented the preregistered campaign-019 runner: block layout, zero movement
charge, threshold × birth-cost treatments, forty new-seed worlds. Saves full metrics
and early feeding/terminal/energy records, with explicit zero-movement and zero-birth
payment checks. Clean-source enforcement and new output paths preserve provenance.

Engineering seed 23 confirms all four initial founder/RNG/map pairings and exact
instrumented/reference state, lineage, events and RNG over short trajectories.
All 144 local tests pass. Commit before outcome launch; full verification and
completed workload accounting remain separate steps. Earlier runners are unchanged.

## 2026-09-14 — Autonomous cycle 160

Confirmed original campaign-019 handle is live. Added a dedicated metric verifier
with exact zero-movement dissipation using the configured birth deduction 0/4,
complete preregistered grid and source/protocol checks, plus founder/RNG/map
pairing and paired threshold outcomes. Earlier campaign verifiers are unchanged.

Focused tests accept each correct birth-cost accounting and reject swapped-cost
records even when global energy balances. Verified the fourteen completed worlds
available at inspection (140,014 metric rows) against their stored summaries.
All 146 local tests pass. Full campaign acceptance and early-observation validation
remain pending; do not restart the running experiment or alter its seed grid.

## 2026-09-14 — Autonomous cycle 161

Previous cycle made progress by implementing and testing metric reconstruction.
The original campaign-019 execution handle exited successfully: all forty worlds
completed without restart. Full verification checked 400,040 metric rows, forty
initial states and all ten founder/RNG/map quadruplets. Every saved CSV summary
field also agrees with the JSON results.

Added a dedicated early-observation wrapper that reuses the configuration-driven
actor verifier without modifying historical code. All forty worlds / 4,000 early
world-ticks / 239,309 individual energy records pass reconstruction. Four targeted
tests cover both birth charges, actor/identity/displacement corruption and locally
balanced but incorrect birth-charge or child-transfer ledgers. Zero direct charges
do not eliminate extinction: low-threshold birth-cost-zero worlds survive 6/10
at 10,000 ticks, versus 7/10 with birth cost four; both high-threshold groups are
10/10 at the horizon. This does not establish a unique mechanism or permanent
survival. Reports and compact data are retained; the narrative report, formal
inventory addition, process summary and updated review/archive remain next steps.

All 150 local tests pass after these additions.

## 2026-09-14 — Autonomous cycle 162

Previous cycle completed full campaign-019 metric and early-observation verification.
Added a process summary that validates the complete forty-world grid, cross-report
hashes, cohort/metric identities, cost-dependent birth deductions and universally
zero movement payments. All predeclared early process ranges cover every world.
Published a Chinese report with the complete ten-seed outcome table, threshold and
birth-cost paired statuses, finite-horizon limitations and reproduction commands.

The low-threshold cost contrast contains five both-alive, one free-only, two
charged-only and two both-extinct pairs. Neither a universally beneficial free
birth intervention nor a unique remaining extinction mechanism is established.
Added campaign 019 to the formal inventory: 904 executions / 8,240,000 computed
ticks, including 24 follow-ups and 212,000 declared replay ticks. Updated current
indexes while explicitly retaining the eighteen-campaign page/archive boundary.
No runtime rules, registered protocol or historical experiment outputs changed.

All forty narrative outcomes and local report links verified; all 150 local tests pass.

## 2026-09-14 — Autonomous cycle 163

Previous cycle published campaign-019 findings and updated verified workload totals.
Added a complete forty-outcome censoring figure, with input/script hashes and every
verified row retained. Visual inspection caught title/legend/footer overlap in the
first layout; preserved that draft locally and corrected spacing before acceptance.
The final PNG is legible and distinguishes extinction from finite-horizon survival.

Extended the review builder to nineteen campaigns with exact full-grid/raw-result
agreement against campaign-019 verification. Generated a new local page; old pages
are unchanged. Parsed all four new treatment rows against verified groups and
checked every local link target. Figure data also matches all forty verified rows.
This is static artifact verification, not renewed browser interaction testing.
Updated the research index; a nineteen-campaign portable archive remains pending.

All 150 local tests pass; sixteen local page targets exist.

## 2026-09-14 — Autonomous cycle 164

Previous cycle added and verified the nineteen-campaign review and complete outcome
figure. Extended portable packaging to nineteen campaigns. Before archiving, the
new branch recomputes campaign-019 metric, early-observation and process reports
and requires complete JSON equality (including input/helper hashes) with committed
references. Historical packaging gates and immutable output behavior remain.
Commit this source before producing the archive; archive verification and fresh
extraction results will be recorded separately after they actually finish.


Archive completed successfully from clean source eec26ab887e23ec4b3b1e9253e89958e4f7a8f66:
1,961 payload files / 134,751,855 bytes, SHA-256
80a4c7526709a5d21a8693bdc09b8a689987d7c0c72c007e6c9cfd033d567b60.
Expected-hash verification passes for all files, thirteen HTML pages and eighteen
local HTML targets. Newly extracted archived scripts reproduce all three full
campaign-019 reports exactly, including hashes. Source CI run 34815145967 completed
successfully. All 150 local tests passed before packaging. Fresh noneditable
installation, installed demonstration and remote upload remain pending; the new
archive is immutable and older downloads retain their original scope.

## 2026-09-14 — Autonomous cycle 165

Previous cycle produced the immutable nineteen-campaign archive and exact extracted
reanalyses. A new virtual environment installed the extracted project noneditably;
import resolved to its own site-packages. All 150 archived tests passed. The
1,000-tick installed demonstration passed audit: population 83, births 1,561,
deaths 1,558, 1,641 lineage individuals and 101 frames. Metrics/events match the
archived reference byte-for-byte; lineage/summary JSON match exactly. Installed
provenance reports no git commit. Pip resolved build dependencies; no offline claim.

Uploaded archive and checksum as draft v0.0.1-preview.11, release 388195439.
GitHub API sizes and SHA-256 digests match both local files; no independent remote
download was performed. Updated current review/acceptance guides to nineteen while
preserving older archives and historical notes. Archive content is fixed at eec26ab;
these post-upload documentation changes are later main commits.

## 2026-09-14 — Autonomous cycle 166

Previous cycle completed fresh installation and delivered the verified nineteen-
campaign archive. Reconciled decision/briefing documents with campaign 019 and
added a post hoc terminal-resource audit of all forty existing trajectories.
All seven extinctions have positive food before and at extinction. Each final
survivor has energy one, and the terminal tick has zero uptake/births and one unit
of dissipation. The basal-death interpretation follows the unchanged rules; it is
not a retained late actor observation. All thirty-three censored worlds retain
missing terminal measurements rather than zeroes.

Published full hashed output and a bounded interpretation. Global food exhaustion
is excluded for these events; local accessibility and the prior causes of energy
loss remain unknown. The next measurement priority is local resources/positions
with observer noninterference gates, before choosing any spatial intervention.
No new simulation, formal campaign, runtime rule or fixed archive changed.

## 2026-09-14 — Autonomous cycle 167

Previous cycle audited terminal global food and identified missing spatial evidence.
Implemented a research-only local-resource stream before each actor's basal payment,
after regrowth/earlier actions. Recorded values include the current site and unique
neighbors, food and occupant IDs; no information is passed to organism behavior.
Parity tests compare plain World, earlier EnergyWorld and new observer over births,
zero/positive costs, full occupancy and lethal phases; old streams remain identical.
A width-one fixture was rejected by existing config validation and corrected to
valid 2-by-2 geometry; rules are unchanged. All 153 tests pass.

Registered a bounded retrospective all-forty-world campaign-019 replay: final twenty
action ticks and twenty-one full boundary states, aligned to recorded extinction or
10,000 for survivors. Explicitly conditional/descriptive, not new independent seed
evidence. The observer exists; recording-window controls and replay runner still
need implementation and verification before this replay starts. No outcomes from
this new spatial observation have been examined or claimed.

## 2026-09-14 — Autonomous cycle 168

Previous cycle added the observer and registered the complete retrospective cohort.
Added a boolean local-capture switch with transition/noninterference tests, plus a
runner that verifies original hashes and initialization, compares every replayed
metric, and saves exactly twenty action ticks and twenty-one complete boundary
states. Window actor partitions and energy totals are checked during capture;
source/input/output hashes and failed/interrupted statuses are retained. Existing
observer streams are drained every tick even when local capture is disabled.

The full 154-test suite passed after switch implementation; the subsequent new
runner test also passed for engineering seed 23 under both birth charges, comparing
RNG/metrics and exact window boundaries. Commit clean source before launching the
registered forty-world replay. Stronger independent local-record reconstruction
and scientific interpretation remain pending; no new formal campaign is counted.

## 2026-09-14 — Autonomous cycle 169

Previous cycle implemented and launched the registered local-resource replay.
Confirmed original execution handle remains live; at inspection twenty-six of
forty worlds were complete. Added an independent standard-library boundary checker
covering exact terminal windows, source/output hashes, original metrics, food
capacity/totals, unique living IDs/positions, occupancy, founder/descendant label
constraints, energy/population accounting and valid RNG-state structure.

All 546 boundaries from the first twenty-six completed worlds pass the structural
helper. Corruption tests reject changed food, occupancy, energy and duplicate IDs;
all 156 local tests pass. This is boundary-accounting evidence, not reconstruction
of individual resource writes or proof that recorded RNG states equal independent
historical states. The full forty-world CLI report remains gated on completed
replay. Next implement per-action spatial consistency; keep the original replay
running without restart. Formal campaign counts and frozen archives are unchanged.

## 2026-09-14 — Autonomous cycle 170

Previous cycle implemented boundary checks while the original replay continued.
The original handle exited normally with all forty worlds complete. Full boundary
verification passes for 840 states against original metric rows and recorded hashes.
Added sequential spatial reconciliation: infer legal per-site regrowth from ending
food plus recorded intake; apply recorded actor order, deaths, movement, food writes
and newborn occupancy; compare each local snapshot and final living/food/occupied
state. Per-action energy ledgers and birth space also reconcile.

All forty windows pass (800 action ticks). Corruption tests reject modified local
food/occupants, actor order, feeding writes and child-energy ledgers; all 159 tests
pass. This check uses recorded order/moves and newborn boundary positions, so it is
not independent random-choice replay or proof of historical actor paths. Full
hashed reports are retained; descriptive scientific summary remains next. Original
formal workload and frozen nineteen-campaign archive are unchanged.

## 2026-09-14 — Autonomous cycle 171

Previous cycle completed all-window structural and sequential checks. Added the
registered descriptive summary for all forty windows, grouped by threshold, birth
charge and observed endpoint status, retaining zero-sample groups and null extinct
locations for censored worlds. Recomputed current-site/free-neighbor counts from
hash-verified local records and matched prior action-verifier counts.

All seven terminal actors have energy one, zero current-site food and at least one
empty food-containing neighbor; all four neighbors are empty at those final actions.
Published every final neighborhood plus full per-world action-fraction ranges.
Immediate neighboring occupancy does not explain these final deaths, but earlier
crowding and energy depletion are not excluded. No sensory benefit or causal rescue
is established. Updated mechanism/decision indexes; the fixed nineteen-campaign
archive does not yet contain this retrospective dataset. Formal counts unchanged.

## 2026-09-14 — Autonomous cycle 172

Previous cycle published the complete local-resource description. Added a separate
campaign-019 spatial supplement packager and extraction guide. Exact report gates
cover original metrics, boundary maps, sequential actions, local summaries and
terminal global resources. The action check uses the newly recomputed boundary
report. Payload includes tracked source, original campaign 019 and all forty
terminal-window records; historical raw campaigns and review pages are excluded.
Source must be clean and output must be new. Commit before packaging; fresh
extracted results and any upload are separate evidence, not assumed here.


Supplement packaging completed from source 779a28dfa3edc467b294050c06a470622d13dbbe:
798 payload files / 19,103,056 bytes, SHA-256
8527875a92462c238f8cc5b7442f14894a6e61be35eb5c2afc077ea07dfd879e.
Expected-hash verification passes. A new-directory extraction reproduced all five
complete reports exactly, including hashes, using archived standard-library scripts.
No fresh runtime installation or full simulation rerun was needed for these
reanalyses. Upload remains pending; original full review/supplement archives stay
immutable. Evidence is recorded in local-supplement-019.json.

## 2026-09-14 — Autonomous cycle 173

Previous cycle created the fixed local-resource supplement and verified all five
fresh extracted reanalyses. Uploaded its archive/checksum as draft
v0.0.1-local-observations.1 (release 388205438). GitHub API sizes and SHA-256 values
match both local files. Source CI 34817034476 completed successfully. No independent
remote redownload is claimed. Updated download and acceptance guides with distinct
scopes for full nineteen-campaign review, campaign-017 revision-2 observations and
campaign-019 local-resource supplement. Older assets remain unchanged.

## 2026-09-14 — Autonomous cycle 174

Previous cycle delivered the verified spatial supplement. Added an explicitly post
hoc trace analysis selecting the final individual in each of seven extinctions,
with all thirty-three censored worlds listed as excluded. Hash-verified original
streams yield 140 chronological action rows with continuous individual energy and
balanced payments/transfers. Six individuals never block, one blocks once, and
none reproduces in its final twenty actions. Every initial-energy-plus-intake
budget equals twenty basal payments. This limits terminal-individual explanations,
not earlier population mechanisms or hypothetical sensory rescue.

Published all seven cases and a reproducible script; no new simulation, independent
sample, rule change or archive rewrite. The fixed supplement contains the input
records but predates this new analysis script/report. Updated research/decision
indexes to distinguish terminal individual trajectories from population history.

## 2026-09-14 — Autonomous cycle 175

Previous cycle documented all seven final-survivor traces. Added a common-scale
figure with energy after each action, actual intake and pre-action empty food-
containing neighbors. All seven traces and thirty-three excluded world identities
match the source report exactly; source/script hashes are saved alongside PNG/SVG.
The energy trace starts with the pre-window boundary value at relative tick -20;
neighborhood squares are categorical markers, not negative energy values.

Visual inspection caught the reading-note panel using data coordinates; corrected
to axes coordinates and inspected the final readable image. The initial layout
was retained locally. Integrated the figure with Chinese reading guidance and
explicit post hoc/age-alignment limits. No new simulation or archive rewrite.

## 2026-09-14 — Autonomous cycle 176

Previous cycle made final-individual traces visually inspectable. Reviewed all six
V0 graduation criteria against current engine/tests and version-specific retained
evidence. The old matrix still pointed to the fourteen-campaign installation;
updated it to the nineteen-campaign installation while distinguishing its 150 tests
from the current 159-test suite. Current suite passes; normalized V0 engine hash
is unchanged. Preserved historical browser-test scope and explicitly separated
static later page checks from interactive browser evidence.

Added the four bounded mechanism findings and formal versus retrospective workload
counts to the matrix, with hashed reference records. All matrix links resolve.
V0 milestone evidence does not constitute V1 graduation, user acceptance or ending
the active research goal. No runtime or experiment artifact changed.

## 2026-09-14 — Autonomous cycle 177

Previous cycle refreshed V0 milestone evidence. Added a separate boundary-conditioned
RNG verifier, preserving prior checkers and report hashes. Independently consumes
regrowth draws, shuffle, movement decisions/targets, birth locations and mandatory
zero-mutation decision draws, and compares ending RNG state. Calls the earlier
sequential map/energy checker first. All forty windows / 800 ticks / 38,471 actions
pass. Two tests cover valid zero/positive movement charges and reject modified
initial/final RNG states; all 161 local tests pass.

This strengthens internal replay consistency without supplying an independent
historical actor-path record or causal intervention. Published the hashed report
and reproduction command; the immutable supplement already contains inputs but
predates this checker. No new simulation or modification of V0 dynamics.

## 2026-09-14 — Autonomous cycle 178

Previous cycle strengthened random-state replay checks. Added a bounded analytical
one-action opportunity calculation for campaign-019 physiology/trait. With empty
current site and sufficient basal energy, each free food neighbor contributes
1/16 positive-intake probability; four contribute 1/4. At energy one it is zero.
Blocked moves correctly retain current-site intake. Three arithmetic tests pass.
Applied exact Fraction arithmetic to all 38,471 verified local rows and retained
per-world expectations and realized intake separately. No random draws/simulations.

The report explicitly conditions on observed local states under the policy's
uniform-draw distribution, not deterministic saved-PRNG state. Endpoint selection
precludes naive residual significance or sensory-rescue claims. Published the
formula and full result, preserving fixed archive contents and formal counts.

## 2026-09-14 — Autonomous cycle 179

Previous cycle added analytical intake opportunity results. Reviewed its domain
assumptions and found the helper accepted arbitrary feeding rates while the report
claimed a fixed campaign-019 formula. Added explicit rate/integer/site validation,
full forty-world grid validation, and hash-verified original configuration checks
for geometry, basal/movement/feeding/capacity/mutation and founder trait conditions.
Four focused tests pass, including rejection of inapplicable rates and boolean or
fractional numeric inputs. Recomputed all 38,471 actions: every per-world result
matches the earlier report exactly; updated provenance includes original-state
hashes. This changes validation, not V0 rules or empirical conclusions.

## 2026-09-14 — Autonomous cycle 180

Previous cycle tightened opportunity-analysis input constraints without changing
results. Added revision-2 local supplement packaging with eight exact-report gates,
including the new random-choice verifier, final-survivor traces and opportunity
analysis. Revision 1 remains selectable with its five original check categories;
existing archives are immutable. Added the three extra extraction commands and
explicit source-snapshot semantics. Commit clean source before producing the new
archive; packaging and fresh extraction outcomes remain separate evidence.


Revision-2 packaging completed from clean source
3b7ba66841aec35ba0c3cbee89e18bc1c018d35f: 815 payload files / 19,404,752 bytes,
SHA-256 9842b1da470872807a2c166f7d20c26b9e433b15a59d7e4f504a70339e05adcd.
Expected-hash verification passes. A new-directory extraction reproduces all eight
full reports exactly, including input/helper hashes. No full simulation or fresh
package installation is claimed. Remote upload remains pending; revision 1 and
other fixed archives retain their original contents.

## 2026-09-14 — Autonomous cycle 181

Previous cycle produced supplement revision 2 and reproduced all eight archived
reports from a new extraction. Uploaded archive/checksum as draft
v0.0.1-local-observations.2, release 388213658. API sizes/digests match both files;
source CI 34818289336 passed. Updated default download guidance to revision 2,
retaining revision-1 evidence and clarifying historical late-analysis scope notes.
No independent remote redownload, new simulation or runtime-install claim. Existing
archives remain immutable and formal experiment counts are unchanged.

## 2026-09-14 — Autonomous cycle 182

Previous cycle delivered supplement revision 2. Reviewed earlier resource protocols:
004/006 varied probability with fixed packet size, changing nominal supply. Registered
campaign 020 to compare probability/amount pairs (60,1), (15,4), (5,12), all exact
nominal mean 0.06, crossed with thresholds 40/160 on ten new seed blocks 1700–1709.
Both direct charges remain zero; all sixty worlds have fixed 10,000-tick horizons.

The protocol explicitly rejects a pure-variance/equal-realized-supply interpretation
because cap truncation, feeding limits and trajectory feedback can change actual
supply and uptake. Full outcomes, paired statuses, realized-resource totals and
early observation checks are specified before execution. No new run launched in
this cycle; implement and validate the runner next. Formal completed counts and
historical artifacts remain unchanged.

## 2026-09-14 — Autonomous cycle 183

Previous cycle preregistered campaign 020. Implemented its separate runner using
unchanged EnergyWorld and the existing block map. Six-way seed-23 engineering
checks confirm identical founders/maps/initial RNG and 100-tick observer/plain
state, events, lineage and RNG equality for each renewal configuration. Packet
fixtures verify saturation adds only remaining capacity. Both direct payments are
zero and each full-tick dissipated increment equals the prior population.

Runner saves all metric rows, early observation streams, registered resource/uptake
checkpoints and status/provenance. Original campaign runners are unchanged.
Commit clean source before launching the sixty-world outcome cohort; independent
full-grid and observation verification remains a separate gate after execution.


## 2026-09-14 — Autonomous cycle 184

Previous turn answered the user's planning question without changing project state.
Revalidated the live campaign-020 process and implemented a separate independent
metric verifier. It checks actual renewal configuration before construction-only
normalization, all six initial states per seed, packet-specific supply bounds,
zero-charge basal accounting and uptake limits over every transition. It reconstructs
all registered endpoints, checks JSON/CSV agreement, and reports both renewal-versus-
reference and within-renewal threshold pairs. Three adversarial tests reject excess
supply, hidden energy charges and impossible uptake; all 170 tests pass.

The original process completed normally: sixty worlds / 600,000 simulation ticks.
The standard-library verifier passes all 600,060 metric rows, sixty initial states,
forty renewal pairs and thirty threshold pairs. Saved its hash-bound report as
results/campaign-020-verification.json. Early observer streams remain a separate
uncompleted verification gate; no full campaign acceptance, updated formal inventory,
new archive or causal mediation claim is made in this cycle. Existing protocols,
runners and V0 engine semantics remain unchanged.


## 2026-09-14 — Autonomous cycle 185

Previous cycle completed campaign-020 metric verification. Added its separate early
observation wrapper, binding metadata and input hashes to the metric report and
revalidating actual renewal configurations before checking actor lifecycles. All
sixty worlds pass: 6,000 early world-ticks and 370,320 individual energy records.
Reused the existing lifecycle/energy helper; its known limits on unrecorded spatial
history and stochastic replay remain explicit. Added six-group early process
summaries, checking cohort intake/ending energy against metrics and zero direct
charges. Reports include source/helper hashes.

Completed the Chinese outcome report with every low-threshold seed, all paired
statuses, all four registered resource/uptake checkpoints, and early process ranges.
Low-threshold survival is 3/10, 1/10, 3/10; high-threshold survival is 10/10 in all
three renewal treatments. Rare-large versus reference includes both treatment-only
and reference-only survival. Realized supply differs despite equal nominal means;
no universal ordering, pure-variance mechanism or information-use claim follows.

Updated the compact inventory to twenty campaigns / 964 executions / 8,840,000
computed ticks, retaining 24 follow-ups / 212,000 declared replay ticks. Inventory
verification passes; these totals are not independent replicate counts. Existing
nineteen-campaign archives/pages are unchanged and exclude campaign 020. The next
bounded delivery is the twenty-campaign review/archive and evidence synthesis,
not another unregistered parameter sweep. V1 remains design-only.

All 170 tests pass after these changes; report links and saved observation counts
were checked. No engine or historical runner changes.


## 2026-09-14 — Autonomous cycle 186

Previous cycle completed campaign-020 observation verification and result synthesis.
Added a three-panel survival figure retaining all sixty worlds, paired seed rows,
explicit censoring and nominal-versus-realized-supply caveats. PNG inspected:
labels, legend and marks are legible. Figure data exactly match the verified cohort.
Added campaign-20 review support with raw-versus-verified row equality and full-grid
checks, preserving historical pages and the default eight-campaign option.

Generated data/review-v0-20.html; eighteen local targets exist, sixty figure rows
match, static page SHA-256 is
8459cd02d0534ec90f65868988896baa51790cc667211ea741681c695f963f16.
No new browser-interaction claim. Added twenty-campaign packaging support with exact
metric, early-observation and process-report gates. All 170 tests pass. Commit
clean source before packaging; fresh extraction and remote upload remain separate
subsequent gates. Historical fixed archives remain immutable.


## 2026-09-14 — Autonomous cycle 187

Previous cycle added the twenty-campaign review and launched packaging from clean
source 58d4c0236fa04ba9b3fa32ef28abcb52cfb6d9d4. Revalidated the original process;
it completed normally after all archived metric/observation/process gates passed.
The immutable archive bitgenesis-v0-twenty-campaigns.zip contains 2,323 payload
files / 149,102,002 bytes, SHA-256
ec499ac80c301052e8fd3b47e163e2a811defd5d3f80887014758016852a3785.

Expected-hash archive verification passes, including thirteen HTML pages and twenty
local targets. Extracted into new data/portable-review-20 and reran all three
campaign-020 reports with archived standard-library scripts and sibling helpers.
Metrics, early observations and processes match archived JSON exactly, including
provenance hashes. Saved results/portable-review-020.json and the local checksum
sidecar. Source CI 34819975721 passed. This establishes file integrity and fresh
analysis reproduction; fresh runtime installation and remote delivery remain
separate pending gates. No independent remote redownload or all-campaign rerun
claim. Existing archives and engine semantics remain unchanged.


## 2026-09-14 — Autonomous cycle 188

Previous cycle verified the twenty-campaign archive and reproduced its three
campaign-020 reports from a new extraction. Created a new runtime virtual environment
and installed the extracted project noneditably via pip. Import resolves to its
site-packages, not working-tree src. All 170 archived tests pass. A new installed-CLI
1000-tick demo passes the audit: population 83, births 1561, deaths 1558, 1641 lineage
records and 101 replay frames. Metrics/events match the archived reference byte for
byte; lineage/summary match as parsed JSON. Installed provenance correctly records
git_commit null. Saved results/portable-wheel-020.json.

Build dependencies were resolved by pip; this is not an offline-install guarantee
or a rerun of twenty full campaigns. Immutable archive source remains 58d4c02;
this later validation record is separate. Remote upload is the next delivery gate.


## 2026-09-14 — Autonomous cycle 189

Previous cycle verified a fresh installation and launched the original draft upload.
Revalidated that upload handle; it completed normally as draft v0.0.1-preview.12,
release 388226471. Both GitHub API asset sizes and digests match local archive and
checksum. Saved results/release-020.json; no independent remote download claimed.
Updated the default Chinese review guide and current acceptance header to the
immutable twenty-campaign source/archive, preserving historical checkpoint notes.
The separate retrospective supplement datasets retain their own delivery scope.

Updated V0 evidence synthesis to source 58d4c02 and the freshly installed 170-test
archive, with campaign-020 mechanism limits and twenty-campaign counts. Rechecked
normalized engine hash: 8f3ed33ad0ebe802c099e3e6f8ae61f9bcc526b98512f31f48ec40478fbfa7ff.
No V1 implementation, new campaign, or user-acceptance claim. The original goal
remains active; the review package is a checkpoint, not completion of research.


## 2026-09-14 — Autonomous cycle 190

Previous cycle delivered the verified twenty-campaign draft. Added a post hoc
all-sixty-world supply-window decomposition using hash-bound original metrics.
Active-start ticks include the extinction tick because renewal precedes basal
payment; subsequent empty-world ticks have zero uptake, zero organism energy and
unchanged dissipation. Both supply windows reconcile to registered cumulative
supply, and active-window uptake equals the registered final uptake. No simulation
or new replicate is added.

Twenty-three worlds became extinct. Their post-extinction fractions of cumulative
added resources range from 51.50% to 79.67%. Reported per-treatment conditional
ranges explicitly retain differing window lengths; these are not causal effects
or rate comparisons. Added three boundary tests for extinction-tick attribution,
illegal empty-world uptake and terminal extinction versus censoring. All 173 tests
pass. Saved script, full report and Chinese explanation; the fixed twenty-campaign
archive contains the necessary raw data but predates this additional analysis.


## 2026-09-14 — Autonomous cycle 191

Previous cycle separated supply before/after extinction. Added an exact conditional
renewal-capacity calibration: 25 stocks times three campaign-020 treatments. Mean
added resource is p*min(packet,remaining capacity); variance and nominal cap loss
are retained as exact fractions. Equal nominal means imply frequent-small >=
reference >= rare-large conditional mean at identical stock, not pathwise input,
stochastic dominance, survival ranking or measured causal contribution.

Independent integer-draw enumeration checks mean, variance and positive-input
probability over all 75,000 stock/treatment/draw cases, with full/one-unit capacity
and invalid-input boundaries. All 175 tests pass. Bound the calibration to unchanged
normalized engine hash and saved report/CSV plus Chinese derivation. No simulation,
new formal replicate, or historical archive change. Further interpretation must
account for differing endogenous stock trajectories rather than assuming matched
realized supply from matched nominal input.


## 2026-09-14 — Autonomous cycle 192

Previous cycle derived exact conditional renewal moments. Inspected the current
engine: the row-major renewal loop consumes the first 1,024 randrange(1000) draws
before any actor shuffle. Registered a bounded retrospective all-sixty-world,
100-tick stock observation connecting conditional expectations to retained maps.
Specify cloned-RNG sampled arrivals/discard separately from expected cap loss,
all/active/empty-start partitions, independent full-record checks and source-pinned
plain-engine parity. Original outcomes are already known; this registration is
prospective only with respect to new stock capture, not the original experiment.

No new observation or outcome run launched. The next action is runner engineering
on seed 23 and independent verification. Budget is exactly 6,000 supplementary
replay ticks, reported separately from the unchanged formal experiment totals.
Historical archives and V0 rules remain unchanged; V1 stays design-only.


## 2026-09-14 — Autonomous cycle 193

Previous cycle registered the bounded retrospective stock observation. Implemented
read-only capture of full pre-renewal food/RNG, stock histograms, all three exact
conditional means, expected cap loss and shadow sampled arrivals/admitted/discarded
energy. Reconciliation requires the shadow admitted amount to equal actual supply.
The observer never replaces or advances the world RNG and pins reviewed engine
semantics. Seed-23 tests cover all six treatments for 100 ticks, comparing complete
state/events/lineage/RNG against plain World, plus empty/full/near-full fixtures.

Implemented a separate replay runner with complete original input hash checks,
initial reconstruction, all 101 historical metric matches per world, atomic
status/results and fresh-only output paths. Protocol and historical runner are
unchanged. All 177 tests pass; CLI imports successfully. No outcome replay launched
in this cycle. Next implement independent record verification before interpreting
any replay output; planned supplementary workload remains 6,000 ticks.


## 2026-09-14 — Autonomous cycle 194

Previous cycle implemented observer parity and replay engineering. Added an
independent stdlib verifier reconstructing histograms from maps, conditional means
from the capped formula, and sampled arrival totals from copied RNG states. It
checks complete cohort/window, original/output hashes, initial map/RNG, all metric
boundaries and active/empty partitions. Explicitly does not reconstruct intervening
actor actions or independently certify later historical RNG states.

Before any cohort execution, extended replay output with actual before/after metric
snapshots so independent original-prefix checking is concrete. Added valid-regime
and adversarial corruption tests for histogram, rational expectation, discarded
energy and historical metrics. All 179 tests pass. Commit clean source before
launching the registered 6,000-tick supplementary replay. Interpretation waits for
complete output and independent verification; formal campaign totals stay unchanged.


Executed the registered retrospective cohort from clean source 41b3736 after the
engineering commit. All sixty worlds completed normally: 6,000 replay ticks and
6,060 historical metric matches. Independent stdlib verification passes all 6,000
records and 6,144,000 renewal draws, including full histograms, exact expectations,
sampled discard and boundary metrics. Saved the complete hash-bound verification
report. These replay ticks are supplementary and do not change formal campaign
counts. Descriptive treatment/partition synthesis remains the next step.


## 2026-09-14 — Autonomous cycle 195

Previous cycle completed all-sixty-world stock replay and independent verification.
Added descriptive synthesis of all/active-start/empty-start partitions with exact
rational reconciliation and explicit unavailable ratios for zero-length windows.
Retained 180 world-partition records and eighteen ten-world group summaries.
Actual discard fractions use sampled uncapped arrivals; expected cap-loss fractions
use nominal expected arrivals. Added boundary tests for missing ratios and damaged
partition/nominal identities. All 181 tests pass.

Chinese report shows all six full-window cells and empty-window coverage. Within
each renewal treatment, high-threshold early discard-fraction ranges exceed the
low-threshold ranges despite all high-threshold worlds surviving to 10,000. This
precludes treating discard fraction as a direct survival ranking; it does not show
beneficial discard or identify a causal direction. Complete raw observation and
original-outcome scope remain explicit. No new simulation or formal-count change;
fixed twenty-campaign archive excludes these later retrospective records.


## 2026-09-14 — Autonomous cycle 196

Previous cycle summarized verified stock observations. Added the complete sixty-world
loss comparison figure with shared percentage axes, paired seed rows and threshold
colors. Filled circles show sampled discard divided by sampled uncapped arrivals;
open diamonds show conditional expected cap loss divided by nominal expectation.
Connecting segments are explicitly not confidence intervals. No outcome selection,
new estimator or simulation is introduced.

PNG visually inspected: titles, legend, axes and all seed rows are legible. Figure
JSON matches exactly the sixty full-window rows from the verified summary; input
hash checked. Linked figure with Chinese interpretation in the observation report.
The existing 181-test result remains the latest runtime test evidence; no runtime
code changed in this visualization-only cycle. Raw observation delivery as a
separate reproducible supplement remains pending; fixed archives are unchanged.


## 2026-09-14 — Autonomous cycle 197

Previous cycle visualized all sixty loss comparisons. Added a separate renewal-stock
supplement packager retaining tracked source plus original campaign 020 and its
registered stock replay. Seven exact-report gates cover original metrics, early
observations/processes, supply-window decomposition, capacity calibration, stock
verification and stock summary. Fresh dependent summaries use freshly generated
verification reports. Archive manifest/checksum and stored-file verification reuse
the existing safe review format; old archives are unchanged.

Added the extraction/reanalysis guide with seven explicit stdlib commands and
limits on source snapshots, raw-data scope and runtime/replay claims. CLI loads
and diff checks pass. Commit clean source before packaging. Actual archive,
fresh extracted verification and remote delivery remain separate subsequent gates.


## 2026-09-14 — Autonomous cycle 198

Previous cycle launched supplement packaging from clean source
99c4f62af72079b6179ba6843a2d8770b092dc04. Original process completed normally with
all seven report gates passing. The archive contains 824 payload files / 40,157,090
bytes; SHA-256 4d1482c8f49192c4f039d2599cbb4a142db3bc5c2c30400615aa9743038bd17d.
Verified against its checksum and extracted into a new portable-renewal-stocks-020
directory. All seven archived stdlib reports reproduce exactly, including the
newly generated verification supplied to dependent observation/summary commands.

Saved results/renewal-supplement-020.json. Source CI 34822173518 passed. These checks
establish integrity and fresh analysis reproduction, not a new engine installation,
full simulation replay, remote redownload or biological claim. Remote draft delivery
is next; existing archives remain immutable and formal experiment counts unchanged.


## 2026-09-14 — Autonomous cycle 199

Previous cycle reproduced all seven supplement reports and launched draft upload.
The original upload completed as v0.0.1-renewal-stocks.1, release 388239326.
Rechecked both remote asset sizes/digests against local files: exact matches.
Saved results/release-renewal-020.json and linked the verified download from the
supplement guide, Chinese acceptance entry and observation report. Distinguish
its original campaign-020/stock-replay scope from the full twenty-campaign archive
and the separate earlier retrospective supplements.

No independent remote redownload or new runtime/replay claim. Immutable supplement
source remains 99c4f62 and its archived guide predates upload evidence. Formal
counts and engine semantics unchanged. This completes this bounded supplementary
data delivery, not the ongoing research objective or user acceptance.


## 2026-09-14 — Autonomous cycle 200

Previous cycle delivered the renewal-stock supplement. Reworked the mechanism
brief into a current twenty-campaign synthesis rather than retaining conflicting
"current" seventeen/eighteen/nineteen-campaign totals in one document. Retained
specific earlier evidence and linked every claim to its actual cohort or analysis.
Integrated supply-window, exact-capacity and measured-discard findings, distinguishing
rule-level conditional expectations, observed paths and still-untested causal
interventions. All local source links resolve.

Updated decision notes to mark the twenty-campaign archive and stock supplement as
delivered, with matching scope limits. The synthesis explains why capacity increases,
spillover redistribution or adaptive loss replacement are not automatically isolated
loss interventions. No new campaign registered or simulation launched; runtime,
fixed archives and formal counts unchanged. This is evidence consolidation for
review and future experimental choice, not V1 graduation or user acceptance.


## 2026-09-14 — Autonomous cycle 201

Previous cycle consolidated mechanism evidence. Checked existing protocols for
capacity interventions; campaign 020 fixed capacity 24. Registered campaign 021:
capacity 24/96 with identical initial stock, both reproduction thresholds and all
three renewal treatments on seeds 1800–1809. Specify a directional paired survival
prediction and per-seed counterexamples before execution, retain all 120 worlds and
fixed 10,000-step horizons. Capacity is explicitly a buffer intervention changing
multiple downstream processes, not isolated loss removal or unlimited storage.

Protocol fixes secondary resource-window accounting, early records, twelve-way
initial pairing, observer parity and capacity-aware independent verification.
No outcome run launched. Current formal workload and fixed artifacts unchanged.
Next implement and validate the runner on engineering seed 23 before executing
this new prospective cohort. V0 rules unchanged; V1 remains design-only.


## 2026-09-14 — Autonomous cycle 202

Previous cycle registered the prospective buffer-capacity experiment. Implemented
its separate runner using unchanged EnergyWorld with capacities 24/96. Initial
map remains the original 5,120 food units at both capacities; total initial energy
is 7,040. Registered twelve-way grid, full horizon, early streams, checkpoint
resources and extinction/active-window partitions are retained with provenance.
Old runners and frozen protocol are unchanged.

Seed-23 engineering checks all twelve configurations for 100 ticks against plain
World: initial maps/founders/RNG, full metrics/food/events/lineage/RNG match. Existing
independent early lifecycle/energy reconstruction passes all twelve cases using
the actual capacity. Full/near-capacity fixtures cover both capacities and all
three packets. All 183 tests pass. Commit clean source before launching the cohort;
full independent campaign metrics, pair statuses and record verification remain
separate gates before outcome interpretation. Formal completed counts unchanged.


## 2026-09-14 — Autonomous cycle 203

Previous cycle launched campaign 021 from source 087e053. Revalidated the original
live process; it continues without restart. Implemented independent capacity-aware
initialization/metrics verification, preserving the old verifier. The new verifier
checks twelve-way initial pairing, packet and capacity bounds, all uptake/payment
transitions, fixed checkpoints, active/empty-window partition endpoints, CSV/JSON
agreement and sixty capacity pairs with six signed-discordance summaries. Full
execution is gated on complete 120-world metadata.

Added adversarial capacity-bound and extinction-window boundary tests; all 185 tests
pass. Partial independent checks of the first twenty completed worlds reconstruct
all saved endpoints exactly from 200,020 metric rows. This is not complete cohort
verification or an outcome interpretation. Running runner/protocol and historical
artifacts remain unchanged. Continue full-cohort execution and prepare early-record
verification while awaiting completion.


## 2026-09-14 — Autonomous cycle 204

Previous cycle implemented campaign-021 independent metrics and confirmed the
original process remained live. Added a separate full-120-world observation wrapper
binding metadata and original input hashes to the metric verification, rechecking
actual capacity-aware initialization and reconstructing early actor energy and
lifecycles. Added twelve-cell process synthesis with separate capacity identities;
old campaign wrappers and helpers remain unchanged.

Both CLIs load. Partial completed-prefix observation checks pass for 34 worlds /
3,400 early world-ticks / 283,268 energy records. Six focused engineering/adversarial
checks pass, including twelve-configuration plain-engine parity and corrupted
individual ledgers. The last full suite remains 185 passing tests. Full wrappers
remain gated on complete cohort evidence; process synthesis will run only after
both full verified reports exist. Original outcome process re-polled live without
restart. No full-cohort result or new formal completion claim.


## 2026-09-14 — Autonomous cycle 205

Previous cycle prepared early-record verification while campaign 021 ran. Re-polled
the original live process. Prepared the complete-cohort survival plot: two threshold
rows, three renewal columns, paired seed rows and distinct capacity colors, with
explicit extinction/right-censoring symbols. Axis bounds retain any valid early
extinction. The plot requires all 120 unique identities and valid censoring data.

CLI loads; an explicit partial input with the first 57 completed worlds is rejected
as incomplete without producing an image. No formal plot or visual-QA claim yet;
generate and inspect only after full verified results exist. Running source and
protocol unchanged, full cohort pending. Last full suite remains 185 passing tests;
no runtime changes or extra simulation introduced by this plotting preparation.


## 2026-09-14 — Autonomous cycle 206

The preceding user-facing planning turn inspected completed observation evidence;
no experiment was restarted. Completed campaign-021 publication work: all 120
worlds / 1,200,000 ticks, 1,200,120 metric rows and 12,000 early world-ticks passed
independent verification. Copied the verified reports, ran the full process
synthesis with report-hash and cohort/metric reconciliation, and generated the
complete survival figure. All 120 figure records equal the verified run records;
PNG visually inspected with all six panels, paired seeds and censoring symbols.

The Chinese report retains all twelve groups, all low-threshold seed pairs,
checkpoint resource ranges and active/empty supply partitions. Signed capacity
advantages +1/-2/-4 do not support the registered all-positive prediction; all
three treatments have small-capacity-only survivors. High-threshold worlds all
survive. No significance, pure mediation or V1 claim is made.

Inventory now independently verifies 21 campaigns / 1,084 executions / 10,040,000
computed ticks, with unchanged 24 follow-ups and 212,000 replayed prefix ticks.
Current full test evidence remains 185 passing from cycle 203; this cycle changes
reports and documentation only. Fixed twenty-campaign downloads retain their
scope. Next prepare the twenty-one-campaign review and fresh-extraction package.
The autonomous research goal remains active, not user-accepted or complete.


## 2026-09-14 — Autonomous cycle 207

Previous cycle published complete campaign-021 results as 26132b3. Extended the
review builder and archive packager to explicit scope 21 while preserving older
choices and the default scope 8. The page requires the complete 120-world grid
and exact agreement with the independent metric report. It displays all twelve
groups and the complete survival figure, with registered prediction failures and
capacity/realized-supply interpretation limits.

Generated data/review-v0-21.html; all 20 local targets exist and all twelve table
rows equal independently verified group results. Page SHA256 is
1d56f03edeed75e7a58ef7a81aabb9c0f918626ee34c821c352a9e63743f6228.
Five existing review-grid tests pass; packaging CLI loads. These are static checks,
not a renewed interactive browser acceptance claim. Packaging now reruns all three
campaign-021 reports and requires exact agreement, preserving previous gates.
Commit this source before running the new archive; extraction, installation and
remote publication remain separate subsequent checks. Old archives are unchanged.


## 2026-09-14 — Autonomous cycle 208

Previous cycle added and committed scope-21 packaging as 9fb1bb3 and launched one
packager. Re-polled that same process to exit 0 without restart. It generated
bitgenesis-v0-twenty-one-campaigns.zip with 2,975 payload files / 179,498,867 bytes,
SHA256 a72916f80bd9b5f4a59842732144dcc09a30bde15ce29dd9d8d3411e27a4e161,
source 9fb1bb37503c35831309b5d03c796afa647e9a23. Source CI run 34825175457 passed.
Internal archive checks cover all payload hashes, 13 HTML pages and 22 static
local targets. Existing archives retain their original bytes and scope.

Extracted to new data/portable-review-21 and independently reran all three
campaign-021 reports using extracted standard-library scripts/data, including
sibling helpers. All three JSON reports exactly match the archived reports.
A fresh virtual environment installed the extracted package noneditably; import
resolves to its site-packages. All 185 archived tests passed. Installed 1,000-tick
demo has 83 survivors, 1,561 births, 1,558 deaths, 1,641 lineage records and 101
frames; audit passes. Metrics/events match reference bytes, lineage/summary match
JSON, and installed source metadata has git_commit null. Pip resolved build
dependencies, so no offline installation guarantee is claimed.

Saved portable-review-021.json and portable-wheel-021.json; archive SHA sidecar is
local. Remote upload and updated download instructions remain next. This is a
verified local portable checkpoint, not user acceptance or goal completion.


## 2026-09-14 — Autonomous cycle 209

Previous cycle verified the fixed scope-21 archive and fresh installation. Created
new draft release v0.0.1-preview.13 at source 9fb1bb3, retaining all earlier assets.
The upload process completed normally. Release 388261318 contains the ZIP and SHA
sidecar; GitHub API sizes and digests match both local files. ZIP is 179,498,867
bytes with SHA256 a72916f80bd9b5f4a59842732144dcc09a30bde15ce29dd9d8d3411e27a4e161;
sidecar is 106 bytes with SHA256
da85c35819c96c169ae7b54003b0067470270f3fecef0203cc145cc1d6f7cfb9.
Saved release-021.json. No independent remote download is claimed.

Updated Chinese review/download instructions, acceptance and research index to
scope 21, with 185 archived tests and exact fresh reports. The mechanism summary
now includes the completed capacity intervention and its negative registered
prediction result instead of treating capacity intervention as still untested.
Kept retrospective supplements separate and old archives immutable. Checked local
Markdown targets in the six changed navigation/synthesis documents. Runtime and
experimental results unchanged; no additional simulation or runtime tests needed.
The user-facing portable checkpoint is delivered, while the autonomous research
goal remains active and V1 remains design only.


## 2026-09-14 — Autonomous cycle 210

Previous cycle delivered the fixed scope-21 release and updated synthesis. Added
an explicitly post hoc horizon-sensitivity analysis of all 120 verified campaign-021
worlds, with no new simulation. The analyzer checks complete identities, censoring,
registered population checkpoints and unchanged primary four-state pair counts.
It partitions every integer post-step horizon at extinction events, retaining the
state at extinction as already absent and keeping tick zero outside horizon totals.

At threshold 40, frequent-small has 2,254 positive / 841 negative / 6,905 zero
horizons; reference has 18 / 9,845 / 137; rare-large has 0 / 9,896 / 104. Every
high-threshold comparison remains zero. These are correlated horizon counts, not
replicates, confidence levels or replacement outcomes. Registered final signed
counts remain +1/-2/-4 and the primary prediction remains unsupported.

Two added tests cover 256 small two-pair cases exhaustively with first-step,
terminal-step extinction and censoring, plus invalid times. Independently checked
all 60,000 full-cohort group/horizon states using direct seed-set operations against
the interval report. All 187 tests pass. Published all low-threshold intervals,
input/code hashes, reproducibility command and inferential limits. Fixed scope-21
archive predates this analysis and retains its exact bytes; no repackaging or
new campaign was introduced. Autonomous goal remains active.


## 2026-09-14 — Autonomous cycle 211

Previous cycle verified the post hoc all-horizon capacity analysis. Added a six-panel
step figure with all matched groups, shared axes and explicit registered-horizon
markers. Plotting rederives the interval analysis from the complete metric report
and requires exact equality plus the input hash; figure JSON preserves all six
interval series and source hashes. All plotted series match the analysis report.

Inspected the rendered PNG and expanded the lower axis to keep the transient -5
value visible above the frame. Marked the time axis as logarithmic, positive/negative
meaning, post hoc scope and correlated-horizon/non-CI limits. Added the figure to
the existing report. No simulation or runtime changes; prior 187-test evidence
remains applicable. Immutable scope-21 archive is unchanged and predates this
later analysis. Autonomous research goal remains active.


## 2026-09-14 — Autonomous cycle 212

Previous cycle delivered the all-horizon figure. Exported committed source 2a8f24c
with git archive to a new directory and reran the horizon analysis using only its
compact committed input. All computed fields and the metric report hash match.
The sole differing field is raw script_sha256: local LF versus exported CRLF.
Confirmed each reported raw hash matches its respective bytes and the complete
scripts are byte-equal after newline normalization. This is provenance variation,
not changed outcomes or a reason to rewrite the prior report.

Saved capacity-horizons-source-review-021.json with both hashes, normalized hash,
line-ending counts and exported archive identity; documented the exact comparison
scope in the analysis report. No new simulation or implementation changes. Existing
187-test runtime evidence and fixed scope-21 download remain unchanged. The result
closes a source-only reproduction check without falsely claiming complete JSON
byte equality across checkouts. Autonomous research goal remains active.


## 2026-09-14 — Autonomous cycle 213

Previous cycle checked clean-source reproduction of the horizon analysis. Reviewed
campaigns 001 and 013 against the original V0 evolutionary question: both used
standing founder variation, while the recent resource-mechanism cohorts fixed
all genomes at 250 with mutation disabled. Registered a distinct finite-budget
mutation-treatment assay from monomorphic founders in the resource-stressed block
layout. Protocol 022 fixes twenty new seed pairs, two existing mutation settings,
all 10,000-step endpoints and complete birth/death/lineage reconstruction before
engineering or outcome execution. It adds no new engine biology or parameters.

The primary prediction is positive signed survival discordance; nonpositive and
no-mutation-only counterexamples must be retained. Explicitly separates mutation
attempts, changed births, vocabulary coverage and adaptive improvement. Initial
founder-reset event consistency is an engineering gate. Future common-environment
performance evaluation is distinguished from this protocol and remains unregistered.
No simulation launched; verified counts and fixed archives unchanged. Next implement
and validate the registered runner before launching from clean committed source.
Autonomous research goal remains active; V1 stays design only.


## 2026-09-14 — Autonomous cycle 214

Previous cycle preregistered campaign 022 as 87a2e4d. Implemented its dedicated
runner using unchanged plain World. Both arms start at genome 250 with corrected
initial birth events, identical food/founders/RNG and total energy 7,040. Records
include all per-tick metrics, compact birth/death events, final full lineage and
all registered living/ever-born histograms; changed births are explicitly distinct
from mutation attempts. Metadata records clean source and protocol hashes, writes
incremental completed results and marks failure/interruption without replacement.

Seed-23 engineering comparison covers both treatments and every tick 0..100:
food, occupancy, complete lineage, events, snapshots and RNG equal independently
initialized plain World. Recorded founder events retain 250 and energy 24; final
birth and living histograms reconcile, no-mutation closure holds and the mutation
case exercises changed births. Existing output and undeclared settings rejected.
All 189 tests pass. Added explicit birth_tick alias to exported birth records to
match the preregistered schema and reran both focused tests successfully; this
record-only alias does not change engine state. Frozen protocol and historical
runners are unchanged. Commit clean source before launching all forty worlds.
Full independent event/lineage/metric verification remains a separate gate before
any formal completion or scientific result claim. Goal active, V1 design only.


Campaign-022 launch note: direct script-path invocation failed at import before
creating data/campaign-022 (confirmed absent). Correct module invocation
`python -m scripts.run_v0_monomorphic_mutation --output data/campaign-022` launched
successfully from clean c63a72e; source and registered outcomes were unchanged.
The first two worlds completed; the same process continues. This is execution
progress only, not independently verified cohort completion.


## 2026-09-14 — Autonomous cycle 215

Previous cycle launched campaign 022 from clean c63a72e. Re-polled the same live
process without restarting. Added independent initialization and aggregate-metric
verification, using the historical independent geometry constructor rather than
the runner. It verifies the actual mutation/configuration, founder/map/RNG identity,
initial energy, complete paired states, per-step population/energy/uptake accounts,
trait bounds and no-mutation closure, registered checkpoint aggregates, terminal
summary, and per-world/cohort CSV/JSON equality. Full gate requires all forty
completed worlds and preserved protocol/clean provenance.

New corruption test exercises real engineering records under both arms and rejects
wrong founder genome, capacity/energy corruption, invalid changed-birth count,
nonfinite mean, tick-order damage and truncated horizon. All 190 tests pass.
Independently checked the completed prefix of 37 worlds / 370,037 metric rows;
this is not full-cohort certification. The event/lineage/histogram gate remains
explicitly separate and required before scientific completion. Source/runtime and
registered experiment unchanged; formal completed totals remain at 21 campaigns.
Autonomous goal stays active. Next finish cohort and reconstruct individual histories.


## 2026-09-14 — Autonomous cycle 216

Previous cycle completed all forty campaign-022 worlds and the full aggregate
metric gate. Added independent event/history reconstruction using only compact
birth/death records and final lineage. Every tick reconstructs living identities,
mean/variant counts, founder lineages, maximum generation, cumulative changed
births and ever-born vocabulary; all checkpoint histograms and final lineage
parentage/dates/offspring/energy and terminal positions reconcile. Parent survival
at birth, earlier parental birth, inheritance bounds, founder records and death
validity are checked. Input hashes bind the metric and individual-history gates.

Corruption tests use both real engineering treatments and reject wrong founder,
unavailable parent, omitted death, damaged histogram and false offspring totals.
All 191 tests pass. Full run verifies 148,821 individuals / 400,040 metric rows.
Primary counts: both alive 4, mutation-only 6, no-mutation-only 4, both extinct 6;
signed discordance +2. This is finite-cohort positive directional evidence, with
four monotone-rescue counterexamples, not significance or adaptive improvement.
Saved both full gate reports. Full Chinese synthesis and inventory publication
remain next; formal published totals unchanged at this checkpoint. No runtime
change, protocol revision, additional simulation or V1 implementation. Goal active.
