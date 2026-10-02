# BitGenesis

**Simple Rules + Energy + Information + Time -> ?**

A long-term artificial-life research project guided by **design the world more
than the life**. Build a small, inspectable world, then measure what inheritance,
variation, resource limits, and time can produce. Complex life or intelligence
is a research question, not a promised outcome.

> 在比特世界创造一个细胞，给它环境，让它复制，突变，感知，存储，反应和死亡，在突变与选择中进化。

## Current status

V0 is the preserved baseline: an explicit-organism Darwinian world with resource
growth, movement, feeding, energy costs, reproduction, mutation, death and lineage
logging. Experimental V1–V4 runtimes are also implemented. Their existence does
not mean that their scientific graduation criteria have been met.

The latest completed V4 study is
[study011: demographic events during structural continuity](docs/research/v4-study-011.zh-CN.md).
All twenty retained sources and 6,299 eligible component windows passed independent
event accounting. High-input cohorts had no births or deaths; a few local
low-input cohorts did, so uninterrupted sampled cohesion is not always demographic
stasis. No window established complete original-member replacement, active
organizational maintenance, or structural replication. The next step is to map
local events to boundary changes before designing a discriminating intervention.

Start with the [current stage evidence and unmet criteria](docs/roadmap/stage-status.zh-CN.md)
and [research log](docs/research/LOG.md). A fresh clone contains compact evidence,
not the ignored raw `data/` trajectories. Study009 requires the original
`data/v4-study-005` directory and validates its archived provenance; do not
substitute an unchecked new run for missing historical records. The
[recovery procedure](docs/design/v4-recovery.md) authenticates deterministic replay
against archived trajectory hashes and labels regenerated metadata explicitly.

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
| V1 | Evolving Controllers | Implemented; first evolutionary information-value comparison negative |
| V2 | Development: genome -> development -> organism | Implemented; evolutionary advantage not established |
| V3 | Ecology | Mechanism studies verified; stable coexistence and evolved division of labor not established |
| V4 | Self-Organization | Local heredity and competition studied; structural replication not established |
| Later | Open-Ended Evolution | Open research direction |

See the [roadmap and graduation criteria](docs/roadmap/README.md),
[emergence design note](docs/design/emergence.md), and
[experiment compatibility policy](docs/design/experiments.md).

V0 has 24 campaign records. The [research index](docs/research/README.md) links
protocols, reports and compact datasets across stages, distinguishing observations
from untested explanations. Start hands-on review with the
[Chinese guide](docs/research/REVIEW.zh-CN.md) or
[V0 acceptance checkpoint](docs/research/ACCEPTANCE.md). Preserved visual reviews
and archives retain their stated campaign and source-revision scopes; they are
not complete archives of the latest V1–V4 work.

## Repository layout

```text
src/bitgenesis/   CLI, preserved scaffold, and versioned v0/ through v4/ runtimes
experiments/     Versioned v0/ through v4/ experiment definitions and instructions
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
