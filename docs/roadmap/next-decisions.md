# Decisions after the nineteen-campaign V0 checkpoint

V0 now has a fixed, independently installable review of nineteen campaigns.
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
the separate nineteen-campaign full archive includes the formal campaign-018 and campaign-019
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

## What the joint-zero-charge result changes

[Campaign 019](../research/campaign-019.md) retains four low-threshold extinctions
with both movement and direct birth charges zero; paired high-threshold worlds
survive to the horizon. The low-threshold cost contrast also contains both free-only
and charged-only survival pairs. Do not assume eliminating a charge benefits every
trajectory, or repeat cost sweeps merely to accumulate survival percentages.

A [post hoc terminal-stock audit](../research/terminal-resources-019.md) checks all
forty outcomes: all seven extinctions occur with positive global food, including
positive stock one tick earlier. Each last survivor has energy one and dies before
feeding under the unit-basal rules. This excludes global resource exhaustion for
these events; it does not identify spatial accessibility or the earlier cause of
energy depletion. Survivors have no extinction-time stock observation.

The next bounded measurement should record actor positions and local resource
availability without consuming RNG or changing the world. Specify the complete
cohort and observation window before replaying; compare all original metrics and
RNG/state in engineering tests. This is retrospective observation, not new seed
evidence or a causal intervention. Do not launch a food-redistribution or occupancy
variant until its changed processes and falsifiable predictions are explicit.
This note does not register or launch another campaign. V1 remains design only.

## Completed terminal-local observation

The registered all-forty-world [local study](../research/local-resources-019.md)
has now completed. All seven last survivors have energy one, no food at their
current site, and at least one empty food-containing neighbor; all four adjacent
sites are empty at those final actions. Basal death precedes any movement/feeding.
Thus immediate neighbor occupancy does not explain those final transitions.
This does not exclude earlier crowding or explain the prior energy loss.

Do not treat nearby food as proof that a sensory controller would succeed.
A timing intervention (feeding before basal cost) and an earlier directional
policy intervention change different rules/processes. Preserve V0's ordering;
future information-value comparisons must keep physiology and timing identical.
The retrospective study checks descriptive consistency, not causal rescue.

## Final-individual traces: stop conflating scales

The post hoc [last-survivor traces](../research/last-survivors-019.md) show no
terminal-window births for the seven selected individuals, six without any blocked
movement and one with a single block. Initial energy plus intake equals twenty
basal payments in each case. These are outcome-selected individual windows, not
random samples or explanations of earlier population decline. Keep physiological
timing and costs matched in future information comparisons; no V1 outcome or
hard-coded food-seeking behavior follows from this observation.

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
nineteen-campaign archive and explains installation checks. The full
[research index](../research/README.md) contains all protocols and results.
The latest engine is still V0; documentation or packaging work does not advance
the runtime stage or prove emergence of life, sensing or intelligence.

The [evaluation contract](../design/v1-evaluation-contract.md) now makes extinction
denominators and ancestor information contrasts explicit. It remains design only.


## Registered next V0 question: renewal granularity

[Campaign 020](../../experiments/v0/campaign-020.md) now registers a new sixty-world
cohort at equal uncapped nominal supply, varying renewal probability and packet
size together. This differs from the earlier supply-rate sweeps. It explicitly
retains capacity/feeding truncation as intervention consequences and measures
realized supply, rather than calling the comparison a pure variance manipulation.
The protocol preceded runner engineering and outcome execution. All sixty worlds
have now completed; independent metric verification passes. Early observer-stream
verification and full result synthesis remain pending. This supersedes earlier statements in this note that no
new V0 campaign had yet been registered. V1 remains design only.
