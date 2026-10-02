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
[study015: exchange history dependence](docs/research/v4-study-015.zh-CN.md).
All ten additional baselines and eighty branches passed fresh independent audits.
Using the same five sources, 100-step occupancy contrasts changed from -4.50/-4.55
under exchange-on history to +0.35/-1.35 under exchange-off history. The direction
therefore depends on history in the mutation-free condition, while the mutation
condition remains negative. Greater material cohesion still does not establish
self-renewal; continuously cohesive full replacement remains absent.

The earlier new-source replication is
[study014: five new sources](docs/research/v4-study-014.zh-CN.md).
All ten baselines and eighty branches passed verification. Exchange reduced
100-step world occupancy by 4.50/4.55 units while increasing continuous material
cohesion by 4.154/4.322 percentage points and reducing lineage survival by
6.079/6.837 points. Source-level exceptions are retained; no continuously closed
cohort fully replaced its original members. These are five new random sources,
with the two mutation conditions paired within each source.

The earlier [study013](docs/research/v4-study-013.zh-CN.md) examined immediate effects.
All 4,000 historical-state reset pairs passed independent reconstruction.
Exchange reduced births by 0.3675/0.3185 per step in the two mutation conditions,
but prevented more dissolutions, increasing immediate occupancy by 0.9095/0.804.
These conditional one-step effects do not replace the long-branch findings:
[study012](docs/research/v4-study-012.zh-CN.md) found higher average cohesion but
lower lineage survival; its [cohort supplement](docs/research/v4-study-012-tradeoff.zh-CN.md)
found demographic stasis in 68 of 77 cohorts cohesive only with exchange.
No study establishes active maintenance, self-renewal or structural replication.
The [target audit](docs/research/v4-study-013-targets.zh-CN.md) verifies all 1,176
occupancy-blocked cases involved an original target rescued from dissolution.
Another 96 energy-blocked cases also had rescued targets, so outcome labels
are not mutually exclusive causal contributions. The [full population paths](docs/research/v4-study-012-population-paths.zh-CN.md)
show the same world-level count changing from an early advantage to a 100-step
deficit of 6.05/4.95 units. All ten source means are negative at the endpoint,
with positive or zero individual pairs retained. The [retention weighting audit](docs/research/v4-study-012-retention-weighting.zh-CN.md)
reconciles the apparent discrepancy: initial singletons lose original members,
and the mutation-free local retention contrast changes from +1.854 points with
equal component weights to -0.360 points with equal original-member weights.
These are distinct estimands, not population-wide evidence of benefit.

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
