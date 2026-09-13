# V0 acceptance checkpoint

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

Twenty local checks passed at this checkpoint. Campaigns 001–004 cover 690,000
simulation ticks. Campaign 001 finds lineage collapse; campaign 002 shows that
the trait maximizing population abundance need not match the trait favored in
mixed populations; campaign 003 directly tests competition with neutral-label
controls and confirms dependence on movement cost. Campaign 004 separates
extinction, turnover and crowded persistence without reproduction. Read the reports before
interpreting animations. An installed wheel and its provenance were also tested.
GitHub CI verified Windows/Linux and Python 3.12/3.13, including the frozen replay:
[run 34773024529](https://github.com/nikolasandwich/bitgenesis/actions/runs/34773024529).
That earlier CI run covered 16 checks; the added artifact-audit suite brings the
current local total to 20 and is included in subsequent CI runs.

The read-only `bitgenesis audit` command independently reconciled all ten full
campaign-001 runs and the acceptance demonstration, plus a sampled extinction
run. It catches corrupted energy accounting, missing lifecycle events and broken
parent references. This checks artifact consistency, not biological validity.

A portable local bundle, `data/bitgenesis-v0-review.zip`, contains tracked source,
four campaigns, the demonstration and the Chinese review page. Its manifest
lists 348 source/artifact files and checksums; all archived files were read back
and matched their hashes. Bundle source checkpoint: `925b031`. Existing archives
are never overwritten; use a new `--output` for a later checkpoint.

V0's minimal milestone is reached. Continue V0 mechanism/robustness experiments
before deciding whether a V1 controller adds a useful research question. Meeting
this checklist does not certify realism or open-ended evolution.

## Limits and next work

- Organisms, inheritance, reproduction, resource rules and trait meaning are
  designed assumptions. No abiogenesis claim.
- Stochastic treatments share initialization, not guaranteed identical future
  environmental events. Cross-platform bitwise replay is not established.
- Complete lineage remains in memory; replay and chart retention are now bounded.
- Trait mutation clamps at boundaries; this may affect endpoint distributions.
- Whole-population fixed-trait results do not replace direct competition tests.

Direct competition, a frozen replay regression, and installed-package provenance
are now checked, as are longer-horizon/resource regimes. Next: independent
artifact auditing and a portable review bundle. A V1 proposal is documented,
but V0 remains the only runtime. Preserve existing rules and preregister experiments.
