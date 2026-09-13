# Emergence versus hard-coded behavior

**Design the world more than the life.** Every digital world has designed rules.
The question is which observed patterns were directly specified and which arise
from interactions, inheritance, variation, and selection under those rules.

V0 deliberately defines an organism, its energy, its genome, and eventually its
reproduction mechanism. These are scaffolding assumptions, not emergent life.
The preserved empty-world initialization supports no claim of evolution. The
Darwinian V0 adds inherited movement probability and mutation under explicit
reproduction rules; empirical claims require its controlled run results.

An energy cost for movement defines a constraint. `if food_nearby: move_to_food()`
defines a strategy. Observing food seeking after writing that strategy is not
evidence that food seeking evolved. Similarly, a random walk can encounter food
without sensing or adaptation. A visualization alone cannot distinguish these.

In V1, a random genome may encode a small controller. If descendants respond to
food, compare them with ancestors and randomized controls, then ablate sensing.
Measure reproductive consequences on held-out worlds. This supports a bounded
claim about an evolved behavior, not intelligence or consciousness.

No explicit fitness function means no ranking score used to award reproduction.
World rules still create selection pressures: resource placement, update order,
action costs, and birth thresholds all affect outcomes and must be documented.
Offspring counts are observations, not an optimization objective fed back into
the engine. Observers and visualizers must never alter world state.

For each experiment, record:

1. What was designed: entities, rules, sensors, actions, and resource flows.
2. What was inherited and what could mutate.
3. What was observed, with seeds, controls, and uncertainty.
4. Alternative explanations and which interventions could rule them out.

Remove assumptions gradually. Development and local self-organization should
earn their complexity through testable questions, while earlier baselines remain
available for comparison.

## V0's encoded behavior ceiling

In `v0-darwin-1`, the inherited genome is one integer in [0, 1000]. Conditional on
being alive after basal payment, it controls only the probability of attempting a
random move. The destination is chosen uniformly among the deduplicated neighboring
sites; occupancy can prevent the move. Neighboring food does not enter that choice.
Eating at the current site and energy-triggered reproduction remain fixed rules.

There are therefore 1001 possible **encoded movement settings**. Mutation cannot
add a sensor, controller node, memory register, developmental rule or new action.
More generations can explore and reweight this family; they cannot enlarge the
genome-to-controller mapping implemented by these rules.

This is not a claim that the entire world has only 1001 possible states. Spatial
arrangements, energy, resource distributions and genealogies make the world much
richer, and collective patterns can still arise. The limit concerns the inherited
controller vocabulary. Food-associated spatial patterns alone can result from
feeding, reproduction, mortality and occupancy without a food-directed policy.

A retrospective count from campaign 001 illustrates distinct meanings of growth:

| Quantity across five seeds, each 5000 ticks | Mutation enabled | Mutation disabled |
| --- | --- | --- |
| Distinct initial genome values | 76–79 | 76–79 |
| Distinct values ever recorded | 241–303 | 76–79 |
| Distinct values alive at the endpoint | 7–19 | 1 |
| Maximum generation among endpoint survivors | 110–143 | 101–115 |

For example, no-mutation seed 0 recorded 7510 individuals and a terminal maximum
generation of 104, but zero genome values beyond the 77 present initially. Longer
genealogy is not new genetic variation. In mutation-enabled runs, a newly visited
scalar value is new variation within the same policy family, not a new function.

The [all-seed counts](../research/results/trait-coverage-001.csv) and
[input hashes](../research/results/trait-coverage-001.json) come from complete
lineage records, with genome bounds, unique IDs, terminal counts and no-mutation
closure checked. This is retrospective analysis, not an additional world campaign.

```sh
python scripts/analyze_v0_trait_coverage.py --input data/campaign-001 --output data/new-trait-coverage
```

Consequently, V0 acceptance concerns inspectable inheritance, variation and selection.
Testing whether local information acquires reproductive value requires the separate
[V1 controller design](v1-experiment-design.md). Even that would test evolution
within a supplied interface, not emergence of sensing or a general intelligence.
