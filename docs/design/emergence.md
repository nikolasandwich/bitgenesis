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
