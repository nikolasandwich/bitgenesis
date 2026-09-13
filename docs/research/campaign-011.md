# Campaign 011 — High-threshold cohorts through 100,000 ticks

Twenty preregistered follow-up executions completed from clean source
`a843547117e042bc8baf9192a1e490516f62aad4`. They extend the two complete threshold-160
cohorts of campaign 010 (seeds 900–909), including its three early failures.
They do **not** add independent seed replicates. All parameters and the V0 engine
remain unchanged. See [protocol](../../experiments/v0/campaign-011.md) and
[all outcomes](results/campaign-011.csv).

| Allocation | Alive at 10,000 | Alive at 50,000 | Alive at 100,000 | Mean population, ticks 99,001–100,000 |
| --- | --- | --- | --- | ---: |
| food-160 | 10/10 | 10/10 | 10/10 | 41.5739 |
| stored-160 | 7/10 | 7/10 | 7/10 | 28.3673 |

All group means retain extinct zeros. The same stored seeds 901, 906 and 908 died
at ticks 167, 214 and 195; no additional extinction was observed between 10,000
and 100,000. Endpoint survivors remain right-censored at the new horizon.

## Interpretation

The seventeen earlier endpoint survivors persist through a tenfold longer
observation window in these two cohorts. This strengthens the finite-horizon
maintenance observation and rules out failure during this specific additional
interval for those worlds. It does not establish permanent viability, an exact
extinction hazard, or robustness to other seeds, parameters or resource changes.
The unobserved time beyond 100,000 remains unobserved.

The extension is longitudinal evidence about the same worlds, not an independent
replication of campaign 010's threshold contrast. Baseline threshold-40 arms were
not extended here. No new movement trait can arise because mutation remains off;
longer persistence alone does not demonstrate adaptation, sensing or open-ended
innovation. The finding does not change the default reproduction threshold.

## Computation and verification

No original full-state checkpoints existed, so each world was regenerated from
its seed. Every saved snapshot from ticks 0–10,000 matched the corresponding
campaign-010 record, both during execution and in the independent verifier.
This checks observable prefixes, not an unavailable historical RNG-state file.

The twenty executions used **2,000,000 computational ticks**: **200,000 repeated
prefix ticks** and **1,800,000 additional observation ticks**. Including this
follow-up, the project has eleven campaigns / 460 executions / 4,440,000 computed
ticks, with these 20 executions reusing earlier cohorts. Do not describe that
total as 460 independent evolutionary replicates.

Engine invariants ran every tick. Independent streaming verification checked all
2,000,020 metric rows and matched 200,020 reference rows (including tick zero).
It validates the fixed protocol, full grid, reference hashes, time sequence,
energy/population identities, cumulative monotonicity, fixed trait, extinction
persistence, intermediate values, final summaries and late means. It does not
reconstruct unexported lifecycle events or validate biological realism.

```sh
python scripts/summarize_v0_long_horizon.py --input data/campaign-011 --reference data/campaign-010 --output data/new-long-horizon-summary
```

The [verification sidecar](results/campaign-011-verification.json) records input,
reference and helper hashes plus the counting distinction. Verifier source
`31a8cc8` passed the 53-test suite across six environments in CI run 34780384606.
Existing ten-campaign pages and nine-campaign downloadable archives keep their
earlier scope; this report and compact results are on main.
