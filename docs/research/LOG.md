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
