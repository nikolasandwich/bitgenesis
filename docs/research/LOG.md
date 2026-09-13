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
