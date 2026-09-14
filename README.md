# BitGenesis

**Simple Rules + Energy + Information + Time -> ?**

A long-term artificial-life research project guided by **design the world more
than the life**. Build a small, inspectable world, then measure what inheritance,
variation, resource limits, and time can produce. Complex life or intelligence
is a research question, not a promised outcome.

> 在比特世界创造一个细胞，给它环境，让它复制，突变，感知，存储，反应和死亡，在突变与选择中进化。

## Current status

V0 is the only runtime stage. It now supports an explicit-organism Darwinian
world: resource growth, random movement, feeding, energy costs, reproduction,
mutation, death, and lineage logging. Genomes encode movement probability, not
a food-seeking strategy. No neural controllers or complex biology are implemented.
The original empty-world scaffold remains available with its original rules.

## Quick start (Python 3.12+)

```sh
python -m venv .venv
# Activate: Windows PowerShell: .venv\Scripts\Activate.ps1
# Activate: macOS/Linux: source .venv/bin/activate
python -m pip install -e .
bitgenesis v0 --seed 42 --width 16 --height 12
python -m bitgenesis v0 --seed 42
bitgenesis v0 --config experiments/v0/darwin-baseline.toml --steps 1000 --output data/first-run
bitgenesis audit data/first-run
python -m unittest discover -s tests -v
```

Without a Darwin configuration, the CLI still reports the original empty scaffold.
The Darwin command writes `index.html` (open locally for replay), per-tick metrics,
birth/death events, lineage records, sampled frames, and provenance metadata.
Output directories must be new; previous runs are never overwritten.
Replay retains up to 1,001 frames by default (`--max-frames`); long-run charts
are sampled, while CSV metrics retain every tick. Sampling intervals are recorded.
The read-only audit reconciles saved metrics, lifecycle events, lineage and replay
without stepping the simulator. Its [coverage and limits](docs/design/audit-scope.md)
distinguish record consistency from exact replay and biological interpretation.

For recoverable state-only runs, use `bitgenesis checkpoint`; see the
[checkpoint and recovery guide](docs/design/checkpoints.md). This separate command
preserves complete world and random-generator state, but does not produce replay
or per-tick CSV artifacts.

## Research stages

| Stage | Scope | Status |
| --- | --- | --- |
| V0 | Minimal Darwinian World | Minimal milestone validated; research continues |
| V1 | Evolving Controllers | Planned |
| V2 | Development: genome -> development -> organism | Planned |
| V3 | Ecology | Planned |
| V4 | Self-Organization | Planned |
| Later | Open-Ended Evolution | Open research direction |

See the [roadmap and graduation criteria](docs/roadmap/README.md),
[emergence design note](docs/design/emergence.md), and
[experiment compatibility policy](docs/design/experiments.md).

Seventeen campaigns total **784 executions / 7,040,000 computed ticks**. This includes
24 longer follow-ups of existing worlds and 212,000 replayed prefix ticks;
follow-ups are not new independent seed replicates. The
[research index](docs/research/README.md) links every protocol, report and compact
dataset, and distinguishes supported observations from untested explanations.
Start hands-on review with the [Chinese guide](docs/research/REVIEW.zh-CN.md) or
[V0 acceptance checkpoint](docs/research/ACCEPTANCE.md). Preserved visual reviews
and archives identify the campaigns and source revisions they include.

## Repository layout

```text
src/bitgenesis/   CLI, preserved scaffold, and versioned v0/ runtime
experiments/v0/   Versioned experiment definitions and instructions
docs/roadmap/    Stage goals and graduation criteria
docs/design/     Assumptions, evidence, and compatibility decisions
tests/           Small executable contract checks
data/            Local outputs (ignored except .gitkeep)
scripts/         Developer and experiment helper instructions
```

There is no explicit fitness score: selection operates through survival
and offspring in a resource-limited world. We explicitly design V0 organisms,
genomes, and reproduction; later stages will challenge those assumptions.

Contributions: [CONTRIBUTING.md](CONTRIBUTING.md). License: [MIT](LICENSE).
