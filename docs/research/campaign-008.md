# Campaign 008 — An initial resource pulse enables establishment, not permanence

Twenty preregistered runs / 200,000 ticks completed from clean source
`ff63d739c2298c94cc018a36f68f0e34f825e809`. The only treatment difference was
initial food, 0 or 8 energy units per cell. All worlds used 32×32, 80 founders
with energy 24 and genome 250, no mutation, regrowth 15/1000, seeds 700–709 and
10,000 ticks. See [protocol](../../experiments/v0/campaign-008.md) and
[all seed outcomes](results/campaign-008.csv).

| Initial food per cell | Alive at 500 | Alive at 5000 | Alive at 10000 | Extinct-only tick range | Group mean population, ticks 9001–10000 |
| --- | --- | --- | --- | --- | --- |
| 0 | 0/10 | 0/10 | 0/10 | 30–65 | 0 |
| 8 | 10/10 | 8/10 | 3/10 | 3053–8685 | 11.5527 |

Means include all seeds and extinction zeros. Surviving runs are right-censored
at 10000. Their terminal populations were 1, 16 and 95; being alive at the endpoint
does not establish subsequent persistence. No run is dropped for failing to establish.

## Interpretation

In this seed block and resource regime, the initial food reservoir separates rapid
extinction from successful early establishment. It adds 8192 units of initially
available food energy, with ongoing regrowth unchanged. The worlds without initial
food still contain founder organisms with stored energy and later resource input;
this is not a life-origin experiment.

The established populations also show later losses: eight were alive at 5000,
only three at 10000. This directly demonstrates observation-window sensitivity
within the same runs, rather than comparing different seed blocks. Initial food
can support establishment without guaranteeing long-term maintenance.

All organisms retain one fixed movement trait throughout. Therefore these outcomes
do not depend on newly evolved behavior. Spatial and demographic randomness remain.
The treatment affects both the initial food field and total initial energy; those
are two descriptions of the same intervention, not separately isolated factors.

This ten-seed comparison is descriptive. It does not prove that every empty-food
world must fail, nor give an exact survival probability. Founder positions and
initial RNG state match within a seed, but later resource draws can diverge once
the trajectories consume different random numbers. Other initial energies,
movement traits, food amounts and regrowth rates were not tested here.

## Verification and reproduction

### Exploratory uncertainty supplement

The following **post-experiment**, pointwise 95% Wilson intervals summarize the
precision of each ten-world survival fraction. They were not preregistered tests.
The calculation follows the [NIST binomial interval description](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm).

| Initial food | Horizon | Alive | Pointwise interval |
| --- | --- | --- | --- |
| 0 | 500, 5000 or 10000 | 0/10 at each horizon | 0.0%–27.8% |
| 8 | 500 | 10/10 | 72.2%–100.0% |
| 8 | 5000 | 8/10 | 49.0%–94.3% |
| 8 | 10000 | 3/10 | 10.8%–60.3% |

These are model-based intervals under independent, identically distributed
Bernoulli outcomes across worlds within a treatment and fixed horizon. The
preregistered consecutive seeds are deterministic replicates, not a random sample
of all possible seeds; the independence model is an analysis assumption. The
intervals quantify sampling uncertainty under that model, not its validity or
uncertainty over untested world rules. Wilson coverage is approximate.

The same ten worlds recur across horizons, so there are not thirty independent
replicates. These are neither simultaneous confidence bands nor intervals for
the paired treatment difference. Interval overlap is not a significance test.
At these horizons every world has been observed, so administrative censoring at
10000 does not leave endpoint survival unknown; survival beyond 10000 is unknown.
Neither 0/10 nor 10/10 establishes an exact probability of zero or one. The broad
3/10 interval reinforces the report's descriptive scope.

Reproduce from the already verified compact outcomes, without rerunning worlds:

```sh
python scripts/analyze_v0_survival_uncertainty.py --output data/new-survival-uncertainty.json
```

The [result sidecar](results/survival-uncertainty-008.json) includes all six rows and
input/script hashes. The helper checks the complete seed grid and consistency
between survival counts and extinction times; it does not independently re-audit
the raw metric tables. Tests verify interval endpoints against the binomial score
equation, including all-success and all-failure cases.

### Original run verification

Engine invariants ran every tick. A separate helper read all 200,020 metric rows
and checked the run grid, tick completeness, initial food/organism energy,
population and energy accounting, fixed-trait constancy, extinction persistence,
and all terminal, intermediate and late-window outcomes against saved JSON.
It does not reconstruct dynamics or audit unavailable lifecycle records.

```sh
python scripts/summarize_v0_initial_food.py --input data/campaign-008 --output data/new-initial-food-summary
```

The [verification sidecar](results/campaign-008-verification.json) records hashes
of all raw CSVs and the analysis helper. Raw outputs are in `data/campaign-008/`.
CI for preregistered source passed in run 34775932916; core rules were unchanged.
Formal totals now: 370 runs / 1,740,000 ticks. Earlier visual archives retain their
declared campaign scope.
