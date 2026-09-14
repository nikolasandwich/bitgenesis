# Campaign 019: failure with both direct movement and birth charges removed

Status at registration: not executed. Use unchanged `v0-darwin-1` rules and existing
configuration fields only. This protocol does not introduce a V1 runtime.

## Why this is a distinct question

Campaign 012 removed direct birth deductions while retaining movement charges in
uniform-food/stored-energy backgrounds. Campaign 018 removed movement charges
while retaining birth cost 4 in dispersed/block-food backgrounds. Separate
counterexamples to each charge's necessity do not establish failure when **both**
charges are absent. Test that conjunction in the block-food background using new
seeds, not only the three outcome-selected campaign-018 counterexamples.

An extinction with movement_cost=0 and birth_cost=0 falsifies the claim that at
least one of those positive direct charges is necessary for every failure in this
finite design. Failure to observe such an extinction is not proof of universal
necessity or permanent viability. A paired low-threshold extinction with
high-threshold survival would show a threshold contrast without either charge.

Zero direct birth deduction still splits parental energy, occupies a neighboring
site and adds future basal demand. Zero movement charge still permits movement
and occupancy blocking. Removing charges changes future trajectories and RNG
consumption; it is not an isolated intervention on crowding, splitting or starvation.

## Fixed design and budget

Forty worlds: all seeds 1600–1609 crossed with birth thresholds 40/160 and direct
birth deductions 0/4. Movement cost is always zero; layout is always block.
Run every world for 10,000 ticks, including after extinction: 400,000 planned ticks.
No adaptive stopping, seed replacement, selected-seed replay, rescue or horizon
extension. Report each of the ten matched seed quadruplets and every failure.

Keep the 32 × 32 baseline, 80 founders at energy 24, fixed movement trait 250,
mutation probability zero, basal cost 1, food capacity 24, feeding rate 8,
regrowth probability 15/1000 and amount 4. Construct with initial food zero, then
use the original block map construction with independent Random(1,000,000+seed):
213 sites at 24, one at 8. Food energy 5,120; initial organism energy 1,920;
initial supplied energy 7,040. All four founder lists, food maps and initial world
RNG states must match within seed. Subsequent realized fields need not match.

## Outcomes fixed before execution

Primary: survival at 10,000 and all four joint survival states for each threshold
pair within birth cost, plus first extinction tick with right censoring at 10,000.
Report cost contrasts within threshold too, without pooling the four treatment
cells as independent initial environments. No significance threshold is planned.

Secondary: survival at 500/5,000, population and cumulative births at 100,
earliest peak population in ticks 0–100, uptake during 1–100, and food/organism
energy at 100. Keep all per-tick standard metrics and final counts.

Mechanism observations: save feeding, terminal and energy JSONL for ticks 1–100
in all forty worlds. Summarize attempted/successful/blocked movements, basal and
movement-payment deaths, actual phase expenditures, and founder/descendant energy
budgets. Child energy is a transfer, not supply; internal descendant transfers
cancel. Both movement dissipation and movement-payment deaths must be zero in
all worlds; birth dissipation must also be zero in birth_cost=0 worlds. At every
tick, dissipation must equal prior population plus configured birth_cost times
new births, since basal cost is one and movement is free.

## Gates and failure accounting

Commit protocol and runner before outcome execution. Test instrumented versus
reference dynamics with both charges zero, including repeated births and odd
energy splits. Verify existing observer streams, RNG, lineage, events and complete
energy accounting. Engineering tests use seeds outside 1600–1609.

Preserve all initial states, clean source/config provenance, full metric tables,
raw early observations, and complete/failed/interrupted status. Drain observer
buffers and engine events each tick; lineage still grows. Outputs must use a new
directory. Engineering failures are separate from extinction; preserve partial
records and explicitly identify any same-input replacement run.

Independent verification must check the exact forty-world grid, all configurations
and initial pairings, all 400,040 metric rows, early actor partitions, genealogy
labels, energy reconstruction and zero-cost semantics. Reconstruct all published
summaries from raw records before updating formal workload totals. Older helpers
that assume birth_cost=4 must not be used unchanged to validate this experiment.
Earlier experiments, their verifiers and fixed archives retain their semantics.

Run the committed implementation from the repository root:

```sh
python -m scripts.run_v0_joint_zero_charge --output data/campaign-019
```
