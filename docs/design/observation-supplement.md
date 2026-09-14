# Campaign-017 observation supplement

Use [revision 2](https://github.com/nikolasandwich/bitgenesis/releases/tag/untagged-c9fe26b8ca6cb88bead1)
for the current eight-analysis observation review. This is a GitHub draft requiring
repository permissions. It complements the full seventeen-campaign review rather
than replacing it.

## Verified revision-2 download

Download `bitgenesis-v0-observations-017-r2.zip` and its `.sha256` sidecar. The ZIP
is 17,503,463 bytes, contains 738 payload files, and fixes source `02df9c1`.
Its SHA-256 is:

```text
48d613d4189acc84fe878b5199bca682fb164a9abd5baaaa80081a47df053377
```

Extract into a **new directory**, preserving the layout. From the extracted
`bitgenesis` directory, read the [Chinese mechanism briefing](../research/mechanism-summary.zh-CN.md),
[individual intake report](../research/individual-intake-017.md) and
[cohort energy report](../research/cohort-energy-017.md).

The archive contains tracked source, campaign-017 original initial states and
metrics, and five observer datasets: feeding-only, schema 2, schema 3, action
replay with terminal records, and energy replay. Energy replay includes 171,207
actor records plus unchanged copies of its feeding/terminal streams.
It excludes campaigns 001–016 raw data and generated HTML review pages. Historical
tracked documents can reference those excluded artifacts; use the full archive
for them. Figures included here can be read directly from the Markdown reports.

## Reproduce all eight analyses

Use Python 3.12+ from the extracted `bitgenesis` directory. These commands require
only the standard library, no package installation. Output directories must be
new. They read stored records; they do not simulate new worlds.

```sh
python -I -S scripts/analyze_v0_feeding_attempts.py --output data/check-feeding
python -I -S scripts/analyze_v0_birth_opportunities.py --output data/check-births
python -I -S scripts/analyze_v0_movement_observations.py --output data/check-movement
python -I -S scripts/verify_v0_action_replay.py --output data/check-actions
python -I -S scripts/analyze_v0_complete_movement.py --output data/check-complete
python -I -S scripts/analyze_v0_individual_intake.py --output data/check-individuals
python -I -S scripts/verify_v0_energy_replay.py --output data/check-energy
python -I -S scripts/analyze_v0_cohort_energy.py --output data/check-cohorts
```

Compare each generated `summary.json` with the corresponding file in the extracted
`docs/research/results/` directory. Compare complete parsed JSON, including hashes;
console ranges alone are not a complete verification.

| Output directory under data/ | Archived reference under docs/research/results/ |
| --- | --- |
| check-feeding | feeding-attempts-017.json |
| check-births | birth-opportunities-017.json |
| check-movement | movement-observations-017.json |
| check-actions | action-replay-017.json |
| check-complete | complete-movement-017.json |
| check-individuals | individual-intake-017.json |
| check-energy | energy-replay-017.json |
| check-cohorts | cohort-energy-017.json |

All eight complete reports matched before packaging and again after fresh
extraction with isolated Python. See the [extraction record](../research/results/observation-supplement-017-r2.json).
Remote asset sizes and SHA-256 values match local files via the GitHub API;
see the [upload record](../research/results/release-observations-017-r2.json).
No independent remote download was performed.

The packaged source also passed [CI 34811470630](https://github.com/nikolasandwich/bitgenesis/actions/runs/34811470630)
on Windows/Linux × Python 3.12/3.13/3.14. The [CI record](../research/results/observation-source-ci-r2.json)
distinguishes its software checks from the historical reanalyses above. None of
these checks proves a causal interpretation, life, sensing or intelligence.

## Build another snapshot

From a clean committed checkout with all required local datasets, run:

```sh
python scripts/package_v0_observations.py --output data/new-supplement.zip
```

The current packager requires all eight reports to match, records source and
input files in `MANIFEST.json` with `observation_revision: 2`, and verifies stored
file integrity without executing the ZIP. A new build needs its own extraction
and upload evidence; it does not inherit those claims from this document.

## Preserved revision 1

[Revision-1 draft](https://github.com/nikolasandwich/bitgenesis/releases/tag/untagged-b86474d93a9aef685e01)
remains unchanged: 13,880,997 bytes, 596 payload files, source `e2a06ce`.
It supports only the first five analyses and does not contain the later energy
dataset or individual/cohort analysis tools. Its [extraction record](../research/results/observation-supplement-017.json)
and [upload record](../research/results/release-observations-017.json) retain that scope.
Neither edition overwrites the full seventeen-campaign review.
