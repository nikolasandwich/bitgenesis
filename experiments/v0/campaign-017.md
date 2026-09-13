# Campaign 017: food geometry × reproduction threshold

Question: does increasing the reproduction threshold change establishment and
finite-horizon survival differently for dispersed versus block initial food?
Campaign 016 motivates this comparison: block worlds had higher early aggregate
feeding and reproduction yet died sooner. This is a new intervention experiment,
not a retrospective test on the same seeds or an identification of a unique cause.

Use all seeds 1400–1409 in the full 2 × 2 design: food layout dispersed/block and
birth threshold 40/160. Forty executions, 10,000 ticks each, 400,000 computed ticks.
No optional stopping, replacement seeds, rescue, or horizon extension. Continue
all worlds through tick 10,000 even after extinction. Report every seed.

Use the 32 × 32 Darwin baseline, 80 founders at energy 24, trait fixed to 250,
mutation disabled, regrowth 15/1000, birth cost 4. Only threshold differs from
these common dynamics. Use campaign-016 food construction: initialize with zero
food, then insert 213 cells at 24 and one at 8, and add 5,120 supplied energy
before tick zero. Total energy is 7,040. Layout RNG is Random(1,000,000 + seed),
independent of the world RNG. Dispersed shuffles all positions; block translates
row-major positions 0–213 with x then y offsets on the torus.

For each seed, all four initial founder lists and world RNG digests must match.
Within each layout, both thresholds must use exactly the same food map. All maps
share the food-value multiset. Save full initial states and check these pairings.
Subsequent draws and realized replenishment can diverge; no common subsequent
random-number schedule is asserted.

Primary observations: alive at 500, 5,000 and 10,000, plus first extinction tick
with right censoring at 10,000. Compare thresholds within each layout and layouts
within each threshold; report paired outcomes per seed rather than treating four
arms as forty independent seeds. Ten seed quadruplets remain a limited scope.
No formal significance or universal-effect claim is planned.

Secondary observations: births at 100, population at 100, peak population during
ticks 0–100 with earliest peak tick, food consumed over ticks 1–100, and food and
organism energy at 100. Retain every-tick standard metrics for independent
reconstruction, plus endpoint metrics and initial on-food founder count/energy.
These early measures are fixed before running this campaign, though motivated
by retrospective campaign-016 analysis. Do not choose a different early window
based on outcomes.

Raising the threshold changes the timing and eligibility of reproduction and the
energy distribution among individuals. It does not selectively disable crowding,
feeding competition, or birth cost. A survival change would not isolate which of
these mediates the effect. No sensing, learning, or evolved controller is present.

Save clean source/config provenance, all forty initial states and metric tables,
compact JSON/CSV outcomes, and complete/failed/interrupted status. Drain events;
full individual and movement histories are not exported. Commit protocol and
runner before execution. Do not add workload totals to the completed inventory
until the complete grid and observations are independently verified.

```sh
python scripts/run_v0_geometry_threshold.py --output data/campaign-017
```
