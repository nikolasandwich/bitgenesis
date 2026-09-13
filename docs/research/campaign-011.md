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

### Exploratory recorded-lineage comparison

At tick 10000, sixteen of the seventeen surviving worlds already had one recorded
founder lineage. Food-160 seed 905 retained two; its count first reached one at
tick 18651. At tick 100000 all seventeen survivors had one. This is a loss of
ancestral labels while populations persist, not a reduction from multiple movement
strategies: all organisms started with the same genome and mutation stayed off.

| Surviving worlds | Recorded founder count at 10000 | At 100000 | Maximum living-generation depth at 100000 |
| --- | --- | --- | --- |
| food-160 (10) | 1–2 | 1 in each | 224–287 |
| stored-160 (7) | 1 in each | 1 in each | 221–268 |

Generation depth here is the maximum among **currently living** individuals,
not a count of synchronized generations or a functional novelty measure. Founder
labels are genealogical markers, not species. Both stored seeds 901 and 906 passed
through a single-founder state before extinction; reaching one lineage is not
evidence of successful maintenance. Stored seed 908 went extinct without a sampled
end-of-tick single-founder state.

The [per-run comparison](results/campaign-011-lineages.csv) retains all twenty
worlds and records first single-founder times, horizon populations and depth.
A streaming check enforces complete ticks, nonincreasing bounded founder counts,
extinct/living consistency and one fixed genome variant while alive. It validates
recorded counts, not the unexported full genealogy. [Hash metadata](results/campaign-011-lineages-verification.json)
documents scope. Reproduce with `python scripts/analyze_v0_long_lineages.py
--output data/new-long-lineages`. This is a retrospective analysis, not a new run.

### Original execution verification

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
