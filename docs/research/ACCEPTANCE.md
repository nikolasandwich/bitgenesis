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

Thirteen checks passed at this checkpoint. Campaigns 001 and 002 cover 250,000
simulation ticks. Campaign 001 finds lineage collapse; campaign 002 shows that
the trait maximizing population abundance need not match the trait favored in
mixed populations. Read both reports before interpreting animations.

V0's minimal milestone is reached. Continue V0 mechanism/robustness experiments
before deciding whether a V1 controller adds a useful research question. Meeting
this checklist does not certify realism or open-ended evolution.

## Limits and next work

- Organisms, inheritance, reproduction, resource rules and trait meaning are
  designed assumptions. No abiogenesis claim.
- Stochastic treatments share initialization, not guaranteed identical future
  environmental events. Cross-platform bitwise replay is not established.
- Lineage and frame data are retained in memory; long runs need a bounded recorder.
- Trait mutation clamps at boundaries; this may affect endpoint distributions.
- Whole-population fixed-trait results do not replace direct competition tests.

Next: direct competition, a frozen V0 replay regression, and recorder/provenance
hardening. Preserve existing rules and predeclare new experiment protocols.
