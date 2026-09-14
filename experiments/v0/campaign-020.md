# Campaign 020: resource arrival granularity at equal nominal mean

Status at registration: not executed. Keep unchanged `v0-darwin-1` runtime.
Use existing regrowth probability/amount configuration only; no sensors, mortality
changes, action reordering or adaptive resource placement.

## Distinct question and competing explanations

Campaigns 004/006 changed renewal probability while holding packet size fixed,
therefore changing nominal mean supply. Campaign 019 and its local observations
showed that global or neighboring food does not guarantee timely intake under the
fixed random policy. Test whether renewal frequency/packet size changes survival
when the *uncapped nominal mean per site-tick* is held fixed.

Treatments (probability per thousand, packet size):

| Label | Probability | Amount | Nominal mean | Uncapped one-tick variance |
| --- | ---: | ---: | ---: | ---: |
| frequent-small | 60 | 1 | 0.06 | 0.0564 |
| reference | 15 | 4 | 0.06 | 0.2364 |
| rare-large | 5 | 12 | 0.06 | 0.7164 |

These variances describe an unconstrained Bernoulli arrival, not realized site
stocks. Capacity is 24 and feeding rate 8: larger packets can be truncated or left
uneaten. Occupancy, resource depletion, population demand and later RNG calls can
also change. This intervention changes both temporal and spatial event granularity;
it is not a pure variance intervention at matched realized energy supply.

Competing predictions, not conclusions: frequent-small arrivals may reduce long
local dry periods and improve persistence; alternatively larger packets may provide
more useful intake on occasional random visits, and cap losses/population feedback
may reverse or erase that ranking. The design allows either result. No claim of
monotonic benefit for every seed, significance threshold or universal phase law.

## Frozen grid and budget

Sixty worlds: all seeds 1700–1709 crossed with the three renewal treatments and
birth thresholds 40/160. Both direct movement and birth charges are zero.
Every world runs through tick 10,000, including after extinction: 600,000 computed
ticks. No selective seed replacement, rescues, adaptive horizon or survivor-only
extensions. Ten seed blocks are matched initial environments, not sixty independent
initial conditions. This is a new cohort, not the seven selected extinctions.

Keep 32-by-32, 80 founders at energy 24, fixed genome 250, mutation probability 0,
basal cost 1, food capacity 24, feeding rate 8. Construct with initial food zero,
then initialize the original block-food map with independent Random(1,000,000+seed):
213 sites at 24 and one at 8, total food 5,120. Total initial energy 7,040.
All six founder lists, food maps and initial world RNG states must match per seed.
Subsequent states and RNG consumption can diverge. Do not describe shared initial
RNG as matched realized resources throughout a trajectory.

## Outcomes fixed before execution

Primary: alive at 10,000 and first extinction tick (right-censored if alive),
reported for every world and each treatment cell. Compare each nonreference renewal
treatment with reference within threshold: report both alive / treatment only /
reference only / both extinct for every seed. Also report threshold-paired statuses
within renewal treatment. Do not reduce results to survivor-only extinction means.

Secondary: alive at 500 and 5,000; population and births at 100; peak population
in ticks 0–100 and earliest peak tick; cumulative uptake through 100; food and
organism energy at 100. Report cumulative realized added resources and uptake at
100, 500, 5,000 and 10,000 separately. Resource totals after extinction include
continued renewal; label this rather than treating such totals as available to a
living population. These secondary variables do not by themselves mediate survival.

Save initial states, all 10,001 standard metric rows per world, provenance and
complete/failed/interrupted status, plus early feeding/terminal/energy streams for
ticks 1–100 in every world. New local-resource terminal-window replays are not part
of this protocol. Early observation records are process descriptions, not sensors.

## Verification and interpretation gates

Commit protocol and runner before outcome launch. Engineering seeds must be outside
1700–1709. Test initial six-way pairing and instrumented/plain-state, event, lineage
and RNG equality under all three renewal configurations. Verify actual cap handling
and zero movement/birth payments. Keep current historical runners unchanged.

Independently verify complete grid, config/initial hashes, all metric accounting,
predeclared endpoints and paired statuses. Per-tick dissipated increment equals
prior population because basal cost is one and both direct charges are zero.
Cumulative uptake is added supply plus prior food minus ending food; retained early
actor energy/intake must reconcile with metrics. Constructor initialization must
not accidentally create food twice. Report any engineering failure separately from
extinction and preserve its partial records; no silent overwrite/replacement.

The nominal equality is exact: 60*1 = 15*4 = 5*12 = 60 per thousand.
Do not claim equal realized supply unless measured values actually match, and do
not use post hoc realized-supply matching to replace the registered full grid.
Any result remains evidence about this joint renewal intervention under fixed V0,
not information use, evolved sensing or a unique explanation of campaign 019.


## Execution command

```sh
python -m scripts.run_v0_renewal_granularity --output data/campaign-020
```

Runner engineering uses seed 23 across all six initial treatments, with 100-tick
instrumented/plain comparisons and capacity-truncation fixtures before launch.
