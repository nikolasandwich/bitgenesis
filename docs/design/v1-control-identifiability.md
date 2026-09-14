# V1 control identifiability review

Design only, reviewed after campaign023. No V1 simulator, pilot, controller
training or outcome assay is introduced. These candidate semantics supplement
[controller design](v1-experiment-design.md) and [evaluation contract](v1-evaluation-contract.md).
A future protocol still must freeze the exact configuration and rule version.

## What permutation removes and retains

Uniformly sample all24 permutations of the four directional food slots, retaining
current-site food, energy and bias. Randomization removes reliable directional
correspondence across draws; it does not guarantee that every reading moves on
every decision. The identity occurs with probability1/24, each slot remains fixed
with probability1/4, and only9/24 permutations move all four slots. Repeated food
values increase the chance that the observed input vector is unchanged. All-equal
neighbors are unchanged by every permutation.

The [exact design enumeration](../research/results/v1-permutation-design-check.json)
checks these counts; it is not a world experiment. Behavioral probes must average
all24 index permutations with multiplicity, as already specified. Do not substitute
only derangements or unique value vectors after seeing outcomes: those would be
different interventions. Current-site food and the multiset of neighboring food
remain available, so this comparison addresses directional alignment rather than
absence of food information. The zero-food-input control is a separate contrast.

## Candidate timing and movement semantics

Use the same schedule in every information arm:

1. Apply resource proposals, then establish the preexisting-actor order.
2. Charge basal energy and stop if dead; charge one decision unit and stop if dead.
3. Read the current world immediately after charges and before this actor moves.
   Earlier actors may already have changed the state. Energy input is this
   post-charge energy, including in fixed-state probes labeled as such.
4. Normalize nonnegative food by floor(1000*food/capacity), using zero at capacity0;
   normalize energy by min(1000,floor(1000*energy/160)); bias is1000. Integer
   rounding and timing are designed choices, not inferred biological properties.
5. Score all five actions, including occupied directions; uniformly resolve maxima.
   Do not mask blocked directions or resample until finding food or free space.
6. For any selected directional attempt, pay the declared movement charge even
   if occupied; death ends the turn. If alive, move only when the target is free.
   Rest pays no movement charge. Feed at the resulting site, then apply the
   declared reproduction rule. Newborns act starting next tick.

This preserves visible distinctions between intended action, paid attempt,
blocked movement, actual displacement and intake. Occupancy is not a controller
input in this candidate. Filtering actions by occupancy would supply extra
information through the action interface. Report synthetic probe actions and
actual executed actions separately. All arms share these semantics; none has an
engineered food-direction preference.

## Random streams require an explicit coupling contract

Separate streams prevent sensor-intervention draws from consuming resource draws,
but sequential action or mutation streams can still drift when the number of
actors, ties or births diverges. Never describe separate streams as identical
random choices for corresponding descendants in diverged worlds.

Candidate resource coupling: make one proposal draw per site per tick in fixed
row-major order, including full sites and extinct worlds, for the whole declared
horizon. This keeps proposal schedules aligned between paired worlds. Consumption
and clipping still change realized food; equal proposals are not equal supply.

Candidate action/intervention coupling: consume one tie draw and one uniform
index-permutation draw per actor that reaches a decision, even for a unique
maximum or an intact/blind arm. Record actor ID and decision eligibility. Uniform
selection must avoid modulo bias. This matches consumption when actor schedules
match, not after different births/deaths or scheduling histories. Exact RNG
algorithm, stream seed encoding and shuffle algorithm remain protocol fields;
these paragraphs are not sufficient for a replay claim.

For fixed-state behavioral probes, use analytic maximum probabilities and exact
permutation averaging, consuming no world RNG. These probes provide the direct
within-state response comparison, rather than assuming trajectory coupling can
provide it. Identical-controller/identical-intervention runs must reproduce all
records with the same allocation; swapped allocations are reported separately.

## Permitted interpretation and remaining gates

| Comparison | Can address | Cannot establish alone |
| --- | --- | --- |
| Same genome/state: intact vs permuted | Action dependence on directional alignment | Reproductive value, complete sensory deprivation |
| Same genome/state: intact vs food-zeroed | Dependence on supplied food channels | Absence of distribution-shift effects |
| Same physiology: intact vs intervention competition | Conditional reproductive contrast in that shared ecology | Intrinsic fitness independent of opponent or environment |
| Descendant contrast minus actual-founder contrast | Change in measured information dependence along a sampled lineage | Selection rather than drift, emergence of sensors |

The unchanged-trait sources in campaign023 illustrate why unchanged controllers
must remain in future samples; ancestor identity is traced, never replaced by a
convenient weak reference. Training extinction yields no endpoint sample and a
null conditional estimate, not an invented zero-effect controller.

Before any V1 runtime outcome study, freeze train/pilot/evaluation seed blocks,
controller sampling and probe states, RNG details, environment grid, horizon,
primary contrast and missing-evaluation policy. Verify the candidate timing and
charges against records, and include engineered probe fixtures only as arithmetic
checks, never as evolved findings. No V0 rule or historical archive changes.
