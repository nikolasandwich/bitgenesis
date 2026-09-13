# Campaign 003: direct competition versus neutral lineage loss

Preregistered after campaigns 001/002. Question: does high movement displace low
movement within a shared world, beyond neutral founder-label turnover, and does
that result depend on movement cost?

Initialize ordinary `v0-darwin-1` worlds, then assign founder traits. Mutation is
disabled. First B founder IDs (either 8 or 40 out of 80) form lineage group B;
remaining IDs form A. Initial positions are already uniformly sampled without
replacement, and initial RNG consumption is unchanged by this intervention.
All descendants retain group identity through founder ID. Group identity itself
never affects actions, survival or reproduction.

Competition treatment: A=250 and B=1000 movement propensity. Neutral-label
control: A=B=250, with identical group assignment. Movement costs = 1 or 4.
Initial B fractions = 10% or 50%. Held-out seeds = 200–209; duration = 3,000 ticks.
Total: 80 runs / 240,000 ticks. All other values use the baseline config.

Primary endpoints: B-only survival, A-only survival, whole-world extinction,
coexistence at the terminal tick, and first loss times. Report all outcomes.
Distinguish lineage fixation conditional on survival from whole-world extinction.
Secondary: terminal population and B fraction. A missing fraction after total
extinction is undefined, not zero. No formal significance test is planned.

The ten-seed groups yield preliminary frequencies, not precise fixation
probabilities. Costs and initial proportions are separate conditions; do not
pool them into a universal ranking. This is direct competition between two
specified traits, not a test of open-ended innovation or a complete invasion map.

```sh
python scripts/run_v0_competition.py --output data/campaign-003
```

Outputs: per-tick group CSVs, aggregate JSON/CSV, protocol and provenance. Founder
label tracking in neutral controls allows drift to be observed without phenotype
differences. As elsewhere, matched seeds do not synchronize all future RNG draws.
