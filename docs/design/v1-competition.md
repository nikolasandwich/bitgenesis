# Matched V1 sensory competition

Implemented assay interface; no formal evaluation has launched. `compete` places
equal numbers of intact and control copies of the same genome in one resource
world. Controls are intact (neutral check), blind or shuffled. Reproduction
mutation must be disabled and the founder count must be positive and even.

Initialization first consumes the normal initial position/genome draws. It then
assigns archived genome weights and modes to every founder and regenerates the
initial birth snapshots before recording. No additional random draws occur.
Founder assignments are explicit run metadata and checked against birth records.
The world's tick rules are unchanged; this is a different declared initialization.

Swap0 assigns first-half founder IDs to intact and second-half to control; swap1
reverses that allocation. Positions, initial energy, food and random states match
between swaps. Equal modes and genomes reproduce byte-identical physical records
with complementary group counts. Different modes can diverge through their actions;
swaps do not guarantee identical realized food or descendant draw correspondence.

Group membership is reconstructed from original founder ancestry outside the
world. Groups do not enter sensor inputs, scores, costs or reproduction. Modes
are inherited intervention settings, separate from the genetic parameters.
All individuals incur the same configured energy costs.

Each output has full runner records and independent audit, plus group terminal
population, cumulative births/deaths and living energy. Report contrast
(N_intact - N_control)/initial_group_count as an exact rational. Both-extinct
contrast is0 but fraction is null and status remains both_extinct. All four
statuses are retained. These descriptive quantities are not simulation rewards.

Next: preregister training/sampling/environment sets and nested comparisons,
then implement complete cohort execution and analysis. Actual-founder and random
controller comparisons use additional matched assays; they cannot be inferred
from this interface's tests. Engineering seeds through70402 are reserved.
