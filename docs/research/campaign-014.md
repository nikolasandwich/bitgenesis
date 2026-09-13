# Campaign 014: movement cost and initial trait frequency

All 160 preregistered worlds completed 3000 ticks. At costs 1 and 2, the high
movement group survives alone in all competition worlds from both initial
fractions. At cost 3, outcomes vary; at cost 4, starting mostly high-movement
individuals includes five whole-world extinctions. A single universal trait
ranking does not describe this grid.

Protocol: [campaign 014](../../experiments/v0/campaign-014.md). Simulation source
`7fabacef5a4dd5e5d19289fe5383ad8ea974e760`, clean checkout, unchanged `v0-darwin-1`.
New seeds 1200–1209; A=250, B=1000 in competition, A=B=250 in neutral controls.
Mutation disabled. B starts with 8 or 72 of 80 founders; other parameters are
baseline. These are fresh mixed populations, not introductions into equilibrated
residents. No seed omitted, run restarted or horizon extended.

## Complete endpoint grid

Each row has ten worlds. A-only/B-only mean that group is still alive at tick
3000 and the other is absent. Extinction is separate, even if a group had earlier
become the sole survivor. Both-present is a finite endpoint observation.

| Cost | Initial B | Treatment | A-only | B-only | Both present | Extinct |
|---|---|---|---:|---:|---:|---:|
| 1 | 8/80 | competition | 0 | 10 | 0 | 0 |
| 1 | 8/80 | neutral | 9 | 1 | 0 | 0 |
| 1 | 72/80 | competition | 0 | 10 | 0 | 0 |
| 1 | 72/80 | neutral | 1 | 8 | 1 | 0 |
| 2 | 8/80 | competition | 0 | 10 | 0 | 0 |
| 2 | 8/80 | neutral | 7 | 2 | 1 | 0 |
| 2 | 72/80 | competition | 0 | 10 | 0 | 0 |
| 2 | 72/80 | neutral | 0 | 9 | 1 | 0 |
| 3 | 8/80 | competition | 4 | 6 | 0 | 0 |
| 3 | 8/80 | neutral | 8 | 2 | 0 | 0 |
| 3 | 72/80 | competition | 0 | 9 | 0 | 1 |
| 3 | 72/80 | neutral | 2 | 8 | 0 | 0 |
| 4 | 8/80 | competition | 10 | 0 | 0 | 0 |
| 4 | 8/80 | neutral | 9 | 1 | 0 | 0 |
| 4 | 72/80 | competition | 4 | 1 | 0 | 5 |
| 4 | 72/80 | neutral | 1 | 8 | 1 | 0 |

The cost-1/2 competition rows each have 10/10 B-only endpoints, while the neutral
controls retain strong differences between the initial label fractions. At cost
3, B starts rare and survives alone in 6/10 worlds versus 9/10 when initially
common, with one extinction in the latter group. These small-sample frequencies
are descriptive, not a formal test of frequency-dependent selection.

At cost 4, initially rare B disappears in all ten competition worlds. Initially
common B survives alone in one world, A survives alone in four, and five go
extinct. Reporting only the five surviving worlds would hide half the outcomes.
No neutral world in this grid goes extinct, but that control also changes the
mixed population's movement composition; it is not a single-mechanism isolation.

## Every extinction

All six occur in competition with initial B=72. Their early timing does not
establish a unique cause. Two cost-4 worlds first lose B; the other four extinct
worlds first lose A. Earlier sole survival is not lasting success.

| Cost | Seed | A first absent | B first absent | World extinct |
|---|---:|---:|---:|---:|
| 3 | 1205 | 43 | 69 | 69 |
| 4 | 1200 | 38 | 97 | 97 |
| 4 | 1201 | 53 | 57 | 57 |
| 4 | 1203 | 50 | 43 | 50 |
| 4 | 1208 | 117 | 69 | 117 |
| 4 | 1209 | 36 | 68 | 68 |

## Verification and limits

The independent verifier checked 480160 rows (including tick zero) across the
full grid. It checks fixed metadata, initial conditions, group/population/energy
accounting, per-tick transition bounds, absence of group return, trait means and
diversity implied by the two fixed genotypes, and first loss times. Recomputed
terminal summaries match all saved results. [Verification hashes and every run](results/campaign-014-verification.json).
[Compact CSV](results/campaign-014.csv) retains all 160 endpoints.

Individual birth/death catalogs and spatial states were not saved. These checks
cannot independently reconstruct every founder membership or explain the spatial
mechanism of extinction. The verifier's first pass incorrectly expected a zero
maximum generation after extinction; it was corrected to the engine's established
undefined value, with a regression test. No experiment or engine change followed.
Verifier source `d6c06f5` passed 78 tests and
[CI 34786356370](https://github.com/nikolasandwich/bitgenesis/actions/runs/34786356370).

Matched seeds share initialization, not synchronized future random draws. The
sixteen arms are not independent replicates per seed, and the ticks are not
replicates. No significance test, critical cost estimate, stable-coexistence or
rare-invasion conclusion is made. Campaign 003's cost-1/4 results remain a separate
seed block with partly different initial fractions; they are not pooled here.

```sh
python scripts/run_v0_frequency_cost.py --output data/my-campaign-014
python scripts/summarize_v0_frequency_cost.py --input data/my-campaign-014 --output data/my-campaign-014-audit
```

Output paths must be new. This adds 160 executions and 480000 computed ticks,
with no repeated historical prefix. Current fixed thirteen-campaign HTML and
uploaded archive predate this campaign and remain unchanged.
