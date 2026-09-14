# Campaign 019 local-resource supplement

This separate archive contains tracked source, the complete original campaign-019
dataset, and all forty registered terminal-window replays. It does not replace the
nineteen-campaign review or add independent worlds. Earlier raw campaigns and their
review pages are excluded. Read [the result](../research/local-resources-019.md).

Extract into a new directory. The original nineteen-campaign archive remains fixed
and does not include this later spatial dataset. This supplement retains 337,368
replayed prefix ticks, 840 boundary states and 38,471 local action observations.
These replay ticks are not added to the formal campaign execution inventory.

## Verified download

Download the [campaign-019 local-resource draft](https://github.com/nikolasandwich/bitgenesis/releases/tag/untagged-5e0e3047d668feaa3597)
with an authorized GitHub account. The archive is 19,103,056 bytes (about 19.1 MB),
798 payload files, source `779a28d`. Whole-archive SHA-256:

```text
8527875a92462c238f8cc5b7442f14894a6e61be35eb5c2afc077ea07dfd879e
```

All five complete reports reproduced exactly from a fresh extraction. GitHub asset
sizes and digests match local files. Source [CI 34817034476](https://github.com/nikolasandwich/bitgenesis/actions/runs/34817034476)
passed. Evidence: [extracted checks](../research/results/local-supplement-019.json)
and [remote assets](../research/results/release-local-019.json). No independent
remote redownload or new package-install test is claimed for this supplement.

## Reproduce after extraction

From the extracted `bitgenesis` directory, with Python 3.12+:

```sh
python -S scripts/summarize_v0_joint_zero_charge.py --output data/check-metrics
python -I -S scripts/verify_v0_local_boundaries.py --output data/check-boundaries
python -I -S scripts/verify_v0_local_actions.py --boundaries-verification data/check-boundaries/summary.json --output data/check-actions
python -I -S scripts/summarize_v0_local_resources.py --output data/check-local
python -I -S scripts/analyze_v0_terminal_resources.py --output data/check-terminal
```

These commands require only standard-library modules. The first command uses a
sibling helper, so omit `-I`. Each output must be a new directory. Full report JSON,
including input/script hashes, should match respectively:

- `docs/research/results/campaign-019-verification.json`
- `docs/research/results/local-boundaries-019.json`
- `docs/research/results/local-actions-019.json`
- `docs/research/results/local-resources-019.json`
- `docs/research/results/terminal-resources-019.json`

The action verifier checks sequential consistency using recorded order and moves,
not an independent repetition of all stochastic choices. Outcome-aligned windows
are descriptive and do not establish sensory benefit or a unique causal mechanism.

## Build and integrity

```sh
python scripts/package_v0_local_resources.py --output data/bitgenesis-v0-local-resources-019.zip
python -I -S scripts/verify_v0_review.py data/bitgenesis-v0-local-resources-019.zip
```

Packaging requires a clean committed source and all local inputs. It recomputes
all five reports before archiving, saves per-file sizes/hashes and creates a whole
archive checksum sidecar. File integrity is separate from scientific validation.
The verification records above document completed extraction and upload checks.
Later main-branch changes do not alter this fixed archive.
