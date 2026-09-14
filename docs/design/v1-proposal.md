# V1 proposal — Does sensory information acquire reproductive value?

Status: the [controller component](v1-controller-contract.md) is implemented.
V0 remains the only complete world runtime; V1 has no outcome experiments yet.

The [V0-informed design contract](v1-experiment-design.md) now specifies candidate
integer inputs/weights, decision costs, ablations, sampling and interpretation
gates. It is a design, not a completed preregistration or implemented stage.

## Question and minimum change

V0 permits inherited variation in random movement but cannot express a response
to food. A future V1 could replace that scalar with a small inherited controller
while keeping energy, space and explicit organisms visible as assumptions.

Candidate interface: normalized food at the current and four adjacent sites,
plus normalized energy and a constant bias input; actions are rest or movement
in one of four cardinal directions. A small linear controller is enough for the
first experiment. Initialize its parameters randomly. Do not write a rule that
selects the direction with most food, add gradient-based training, or assign a
food-seeking reward. Controller outputs govern actions, not reproductive scores.

This deliberately supplies sensors and an action vocabulary. It tests evolution
within that interface, not emergence of sensing itself. Memory is a separate
later extension with its own necessity test, not a default extra capability.

## Required comparisons before any claim

1. Random ancestors versus descendants from independent training worlds.
2. Descendants versus randomized controllers with matched parameter scale.
3. Intact sensing versus shuffled sensory inputs and a sensor-blind control.
4. Held-out seeds and changed resource distributions; report extinction too.
5. Measure offspring/survival and behavioral response separately. A controller
   can react to food without gaining a reproductive advantage, or reproduce well
   for reasons other than sensing.

Predeclare sample counts, train/held-out seeds, horizons, resource and controller
budgets, and primary measures before running. A positive result needs an effect
that survives the relevant controls, not merely a nicer trajectory plot.

## Compatibility and stop conditions

Add `bitgenesis.v1` and an explicit `v1` command; never change `v0-darwin-1`.
Keep V0's frozen replay, historical definitions, and output interpretation.
Version new input/output encodings and log every controller genome in lineage.

Before implementing, settle the experimental question and controller cost model.
If an invariant failure, loss of replayability, or undocumented assumption appears,
repair that before increasing controller complexity. Null results remain useful.
Do not claim intelligence, abiogenesis, or open-endedness from a sensory response.
