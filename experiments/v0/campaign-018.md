# Campaign 018: charged movement as a necessary-condition probe

Status: preregistered, not executed. V0 rules stay `v0-darwin-1`; all treatments
use existing configuration fields. No V1 runtime or controller is introduced.

## Question and falsifiable interpretation

Does a positive movement energy charge remain necessary for low-threshold failure
under the campaign-017 food layouts? Does the finite-horizon threshold contrast
persist when attempted movement costs zero? The motivation comes from recorded
movement obstruction, pre-feeding deaths and cohort energy turnover in campaign
017. Those observations alone did not identify a causal mediator.

A low-threshold world that goes extinct with movement cost zero is a counterexample
to the claim that a positive movement charge is necessary for *every* failure in
this declared design. It does not prove that movement costs never contribute.
If low-threshold extinction and higher-threshold survival occur in the same
zero-charge seed/layout pair, the threshold contrast can occur without that charge.
If removing the charge eliminates the sampled failures, this is consistent with
its contribution but does not prove necessity outside the finite sample.

Zero cost also changes remaining energy, mortality, reproduction, population,
consumption and subsequent RNG draw paths. Occupancy still blocks movement and
newborns still occupy neighboring cells. This intervention is neither removal of
spatial competition nor a pure intervention on blocked-move cost. No cost is
subtracted retrospectively from an unchanged trajectory.

## Fixed design

Use the complete 2 × 2 × 2 × 10 grid:

- Initial food layout: dispersed / block.
- Reproduction threshold: 40 / 160.
- Movement energy charge: 0 / 1.
- New world seeds: 1500–1509, used in all eight treatments per seed.

Eighty worlds, 10,000 ticks each: 800,000 planned computed ticks. Continue to the
fixed horizon even after extinction. No replacement seeds, adaptive grid expansion,
rescue or longer horizon after observing outcomes. Ten matched seed octuplets are
the design units; eighty runs are not eighty independent initial environments.

Keep the 32 × 32 baseline, 80 founders with energy 24, fixed movement trait 250,
mutation probability zero, basal cost 1, birth cost 4, feeding rate 8, food capacity
24, regrowth probability 15/1000 and regrowth amount 4. Use the campaign-016 map
function: zero food at construction, then 213 sites at 24 and one at 8, totaling
5,120 food energy and 7,040 total initial energy. Layout RNG uses 1,000,000 + seed.
Within each seed, all founder lists and initial world RNG states must match; within
each seed/layout, all four maps must match. Save full initial states. Later RNG
paths and realized food replenishment are allowed to diverge.

## Outcomes fixed before execution

Primary: survival at tick 10,000 and the four joint survival statuses for each
threshold pair within seed/layout/movement charge. Preserve extinction in both
arms explicitly. Also report each world's first extinction tick, right-censored
at 10,000. No significance threshold or universal-effect claim is planned.

Secondary: survival at 500 and 5,000; population and cumulative births at 100;
earliest peak population in ticks 0–100; food uptake over ticks 1–100; food and
organism energy at 100. Present each seed and paired treatment differences.

Mechanism observations, fixed to ticks 1–100 for every world: all feeding,
pre-feeding terminal and per-action energy rows. Report total attempted movement,
successful moves, occupied-target blocks and payment deaths; terminal movement
payments occur before destination selection, so they are not blocked moves.
Report actual basal/movement/birth expenditure and parent-to-child transfers,
plus fixed-founder versus descendant intake and energy budgets. Internal transfers
within descendants cancel in cohort energy accounting. Zero-charge arms must have
zero actual movement dissipation and no death during movement payment; remaining
basal deaths are retained. Observations are dependent records, not extra replicates.

## Implementation and verification gates

Commit protocol and runner before any outcome run. First compare zero-charge
instrumented and uninstrumented worlds on short engineering cases, including
full occupancy, births, deaths, zero payments and odd energy splits. Verify full
state, RNG, events, old observation streams and per-actor/global energy identities.
These engineering seeds are not the declared outcome seed block.

The runner must retain all standard per-tick metrics through 10,000 and save full
observation JSONL only through tick 100. Drain observation buffers and engine
events every step; retained lineage still grows. Record clean source/config and
complete/failed/interrupted status, completed worlds, plus each initial state and
all raw early observations. Never overwrite output directories. An engineering
failure is not ecological extinction; preserve partial artifacts and document any
same-input rerun as a replacement, not another independent observation.

Before interpretation, independently verify the exact grid and treatment configs,
map/founder/RNG pairing, all metric rows, all early actor partitions, and energy
reconstruction against stored initial states. Check movement outcomes and cost
zero semantics directly from observations. Summaries must match stored raw records.
Only then add completed workload to the formal inventory. Existing campaign-017
records, fixed archives and earlier experiment routes remain unchanged.

Run the committed implementation from the repository root:

```sh
python -m scripts.run_v0_movement_charge --output data/campaign-018
```
