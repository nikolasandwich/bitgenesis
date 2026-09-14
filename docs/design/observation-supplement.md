# Campaign-017 observation supplement

This separate ZIP contains tracked source, campaign-017 raw initial states and
metrics, and four observer datasets: feeding-only, schema 2, schema 3, and the
complete-action replay with terminal records. Extract into a new directory,
keeping the original seventeen-campaign archive unchanged. It does not contain
raw data for campaigns 001–016 or the generated visual review pages. Some tracked
historical documents therefore describe artifacts outside this supplement.

Read the [Chinese mechanism briefing](../research/mechanism-summary.zh-CN.md).
For verification, run these commands from the extracted `bitgenesis` directory,
using Python 3.12+ and new output directories. They use only the standard library:

```sh
python -I -S scripts/analyze_v0_feeding_attempts.py --output data/check-feeding
python -I -S scripts/analyze_v0_birth_opportunities.py --output data/check-births
python -I -S scripts/analyze_v0_movement_observations.py --output data/check-movement
python -I -S scripts/verify_v0_action_replay.py --output data/check-actions
python -I -S scripts/analyze_v0_complete_movement.py --output data/check-complete
```

The corresponding complete reports are under `docs/research/results/` with names
`feeding-attempts-017.json`, `birth-opportunities-017.json`,
`movement-observations-017.json`, `action-replay-017.json`, and
`complete-movement-017.json`. Compare each generated `summary.json` structurally,
including its source/input hashes. These are reanalyses of recorded observations,
not new simulations or independent biological evidence.

The packager runs all five analyses and requires exact report equality before
archiving. `MANIFEST.json` identifies source, datasets and file hashes. The existing
`verify_v0_review.py` checks this shared container format without executing payload.
Fresh extraction/reanalysis and upload are separate checks; the presence of this
document alone is not evidence that they have passed. The standalone supplement
is built with `python scripts/package_v0_observations.py --output data/new-supplement.zip`
from a clean committed checkout with all local inputs available.

## Verified download

[Observation supplement draft](https://github.com/nikolasandwich/bitgenesis/releases/tag/untagged-b86474d93a9aef685e01) (repository permissions required).
The 13,880,997-byte ZIP contains 596 payload files from source `e2a06ce`.
All five reports matched after fresh extraction. GitHub asset sizes and SHA256
digests match local files; see the [upload record](../research/results/release-observations-017.json)
and [extraction record](../research/results/observation-supplement-017.json).
