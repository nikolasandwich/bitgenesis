# BitGenesis

**Simple Rules + Energy + Information + Time -> ?**

A long-term artificial-life research project guided by **design the world more
than the life**. Build a small, inspectable world, then measure what inheritance,
variation, resource limits, and time can produce. Complex life or intelligence
is a research question, not a promised outcome.

> 在比特世界创造一个细胞，给它环境，让它复制，突变，感知，存储，反应和死亡，在突变与选择中进化。

## Current status

V0 is the only runtime stage. This initial release is a **scaffold**: it creates
an empty world and prints a text summary. Feeding, movement, reproduction,
mutation, death, and time stepping are future V0 work. It does not yet demonstrate
Darwinian evolution. No neural controllers or complex biology are implemented.

## Quick start (Python 3.12+)

```sh
python -m venv .venv
# Activate: Windows PowerShell: .venv\Scripts\Activate.ps1
# Activate: macOS/Linux: source .venv/bin/activate
python -m pip install -e .
bitgenesis v0 --seed 42 --width 16 --height 12
python -m bitgenesis v0 --seed 42
python -m unittest discover -s tests -v
```

The CLI reports `scaffold`, tick zero, and an empty population. The seed is stored
for future stochastic rules; the empty initialization itself uses no randomness.

## Research stages

| Stage | Scope | Status |
| --- | --- | --- |
| V0 | Minimal Darwinian World | Runtime scaffold |
| V1 | Evolving Controllers | Planned |
| V2 | Development: genome -> development -> organism | Planned |
| V3 | Ecology | Planned |
| V4 | Self-Organization | Planned |
| Later | Open-Ended Evolution | Open research direction |

See the [roadmap and graduation criteria](docs/roadmap/README.md),
[emergence design note](docs/design/emergence.md), and
[experiment compatibility policy](docs/design/experiments.md).

## Repository layout

```text
src/bitgenesis/   CLI and current V0 engine modules
experiments/v0/   Versioned experiment definitions and instructions
docs/roadmap/    Stage goals and graduation criteria
docs/design/     Assumptions, evidence, and compatibility decisions
tests/           Small executable contract checks
data/            Local outputs (ignored except .gitkeep)
scripts/         Developer and experiment helper instructions
```

There is no explicit fitness score: planned selection operates through survival
and offspring in a resource-limited world. We explicitly design V0 organisms,
genomes, and reproduction; later stages will challenge those assumptions.

Contributions: [CONTRIBUTING.md](CONTRIBUTING.md). License: [MIT](LICENSE).
