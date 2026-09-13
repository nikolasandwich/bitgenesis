# Campaign 012: allocation × threshold × direct birth cost

Preregistered before executing the fresh seed block 1000–1009. Campaign 010
changed reproduction threshold throughout life and jointly changed birth timing,
energy division, population demand and competition. This experiment asks whether
removing the explicit per-birth energy deduction removes early failure under the
low threshold. It does not remove all consequences or indirect costs of birth.

Use unchanged v0-darwin-1 rules and the full eight-arm factorial:
allocation food (initial_food=5, initial_energy=24) or stored (0, 88),
birth_threshold 40 or 160, and birth_cost 0 or 4. Each arm starts with 80 founders,
32×32 space and total energy 7040. Regrowth probability is 15/1000; assign all
founder genomes 250 after ordinary initialization, with mutation probability zero.
All remaining parameters come from the existing darwin-baseline.toml. No default
or engine changes. Zero direct cost still divides parental energy between parent
and child, occupies space and adds future basal and movement expenditure.

Each arm uses all ten seeds for 10000 ticks, including after extinction:
80 executions / 800000 ticks. No seed replacement, outcome-dependent stopping,
or horizon extension. Initial randomization matches within seed; subsequent RNG
consumption may diverge, so future resource draws are not guaranteed matched.

Primary descriptive outcomes: survival at 500, 5000 and 10000 and first extinction
time. For each allocation, compare costs within each threshold and thresholds
within each cost. Report the difference between the two threshold survival
contrasts (high minus low, cost 0 minus cost 4) descriptively, retaining all ten
worlds per cell. Do not pool backgrounds or treat repeated horizon observations
as independent samples. No hypothesis-test significance threshold is declared.

Secondary outcomes: population and cumulative births at 10/100/500/5000;
maximum population over ticks 0–100 and its first tick; late mean population and
birth/death counts over 9001–10000; terminal births/deaths and energy accounting.
Include zero populations and all extinct worlds in arm means. Survivors are
right-censored at 10000. All per-tick metrics are saved; full events and lineage
exports are not, and their consistency cannot be claimed from these files.

Prediction: removing direct cost may improve low-threshold stored-energy survival,
but early splitting and population demand may still cause failure. Any early
failure with cost zero disproves the necessity of positive direct birth deduction
for that observed failure, not the existence of other costs. Improvement under
cost zero is a total parameter effect, not an isolated estimate of one dynamic
pathway or evidence for evolved reproductive regulation. Reversal/null outcomes
must be retained. This is V0 physiology, not sensory adaptation or V1.

Commit protocol and runner before execution:

```sh
python scripts/run_v0_birth_cost.py --output data/campaign-012
```

Save clean source provenance and all metrics; check engine invariants every tick.
Before accepting counts/results, independently verify the complete 8×10 grid,
fixed parameters, 7040 initial energy components, every tick's accounting and
fixed trait, extinction and all declared early/late summaries. Report exact
interventions and limitations. Existing eleven-campaign archives remain fixed.
