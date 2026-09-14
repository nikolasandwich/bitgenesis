# Decisions after the eighteen-campaign V0 checkpoint

V0 now has a fixed, independently installable review of eighteen campaigns.
Keep it as the experimental baseline. The next useful milestone is evidence
about inherited use of information, not a larger V0 execution count. Only V0
runtime is currently in scope; the V1 documents specify future work, not results.

## Evidence that changes the next design

| Observation | Decision | Remaining uncertainty |
| --- | --- | --- |
| Campaign 016 block worlds consume more early food and have more early births, yet die sooner | Do not interpret initial food distance or total consumption as individual information value | We did not retain individual feeding paths or local congestion |
| Campaign 017 high thresholds improve finite-horizon survival in both layouts | Keep reproduction threshold and initial energy identical across future sensory controls | The intervention changes multiple processes; the mediator is unidentified |
| Campaign 017 new block seeds exceed the earlier extinction-time range | Use new held-out seeds and retain every failure; do not promote a sampled range into a world law | Generality across settings remains untested |
| Campaign 018 retains three low-threshold block extinctions with zero movement charge; all paired high-threshold worlds survive | Reject positive movement charge as necessary for every failure in this design; lock movement cost across sensory comparisons | The finite sample does not identify a unique mediator or show costs never contribute |
| V0 can persist, sort traits and lose founder labels without sensors | Require a direct information intervention for V1 | No V1 controller or sensory-advantage evidence exists |

## A bounded V0 mechanism study, if needed

Do not launch another survival-only threshold sweep. First validate an observer
that measures, for each action, food taken, energy immediately before and after
feeding, attempted versus successful movement, occupied neighboring cells, and
birth eligibility versus successful birth. Keep observer data separate from
world state; it must consume no random draws or alter action order.

Observer acceptance requires byte-identical reference metrics/events and exact
world RNG equality in instrumented and uninstrumented runs, plus reconciliation
of summed food uptake and energy costs with existing aggregate accounting. Tests
must include blocked moves, deaths before feeding, births and full occupancy.
Only after this gate should a protocol choose a bounded early window and all
cases to inspect. A replay of old seeds adds observations of those trajectories,
not independent seed evidence. Label any outcome-selected comparison explicitly.

These measurements could distinguish low local intake from high population-wide
intake and detect congestion. They would still be observational: a separate
intervention would be needed to attribute the threshold effect to a mediator.
The [observer](../design/feeding-observer.md) now records feeding, birth eligibility
and available birth space, surviving movement outcomes, and deaths before feeding.
Instrumented/reference state, events and RNG comparisons passed in targeted tests.
All forty original campaign-017 worlds were replayed over ticks 1–100, matching
4,040 original metric rows; feeding and terminal records partition the acting
population at every step. Original individual paths were not retained, so these
are not independently verified historical action paths.

The bounded retrospective study is complete for these measurements; it is not a
causal intervention or new independent seed evidence. Read the
[mechanism briefing](../research/mechanism-summary.zh-CN.md) and
[reproducible observation supplement](../design/observation-supplement.md).
Before another mechanism experiment, specify a falsifiable intervention and its
side effects. A separate per-action energy ledger is now implemented and tested, including
actual phase payments and transfer to newborns. Historical replay now covers all forty early prefixes, with 171,207 energy
records independently reconciled against the retained observations and original
energy totals. The revision-2 observation supplement contains this campaign-017 energy dataset;
the separate eighteen-campaign full archive includes the formal campaign-018
early observations. See the guide for exact download scopes.

## What the completed movement-charge probe changes

[Campaign 018](../research/campaign-018.md) completed the preregistered layout ×
threshold × movement-charge grid, including all early observer records. Zero charge
improved low-threshold finite-horizon survival, but three block worlds still died.
This answers the registered necessary-condition question; repeating the same grid
only to obtain a stronger-looking survival percentage is not the next priority.

The early process table also shows that free movement retains blocked destinations
and can accompany more births and greater basal expenditure. A new mechanism
proposal must therefore name the intervention, all processes it changes, the
competing predictions and what observation would reject its claim. Neither higher
blocked fraction nor greater total expenditure alone qualifies as a causal target.
Do not select only the three counterexamples and present them as an unbiased
sample of all worlds. Any case study must include its outcome-selection rule.

For a future sensory experiment, keep movement payment equal across intact,
blind, permuted and ancestor controls, as well as reproduction and decision costs.
A zero-charge viability pilot is an allowed design option, not evidence that a
controller found food. If a later robustness grid includes both movement charges,
compare information treatments within each charge and report the complete grid.
No new formal V0 campaign or V1 outcome run is preregistered by this decision note.

## V1 implementation sequence when runtime scope expands

1. Freeze a versioned sensor/weight/action specification, costs and independent
   RNG stream derivations. Keep v0-darwin-1 unchanged. Candidate details are in
   the [design contract](../design/v1-experiment-design.md).
2. Implement the tiny controller with random initial weights and inherited
   mutations; validate arithmetic, ties, bounds, costs and deterministic replay.
   No hand-coded food-seeking policy or reward optimizer.
3. Run a separately labeled viability pilot. Its purpose is to choose a viable
   experimental environment; it supplies no held-out evidence of sensory value.
   Record all pilot settings and failures before freezing the main protocol.
4. Freeze training/evaluation seeds, sampling, budgets and primary comparisons.
   Evaluate intact/blind/permuted inputs, random controls and actual ancestors.
   Match reproduction and initial food geometry across each comparison.
5. Measure behavioral information use separately from survival and offspring.
   If sensory ablation has no reproducible effect, report that result rather than
   adding memory or enlarging the controller to make a stage-success claim.

Memory remains a later question requiring a task where history can matter.
Development, ecology and self-organization keep their existing graduation gates.

## Reviewable checkpoint

The [Chinese review guide](../research/REVIEW.zh-CN.md) points to the fixed
eighteen-campaign archive and explains installation checks. The full
[research index](../research/README.md) contains all protocols and results.
The latest engine is still V0; documentation or packaging work does not advance
the runtime stage or prove emergence of life, sensing or intelligence.

The [evaluation contract](../design/v1-evaluation-contract.md) now makes extinction
denominators and ancestor information contrasts explicit. It remains design only.
