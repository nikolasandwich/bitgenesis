# V4 study006: matched descendant/founder program expansion

Use exactly the60 pairs frozen in study005-ancestor-selection (three per source,
20 source cases), including55 equal-program pairs. No replacement or novelty/
performance filtering. Bind the selection JSON and selection protocol hashes;
verify each selected descendant/founder against its retained lineage before runs.

Each pair crosses role descendant/founder, fresh environment seed98000/98001 and
assay drive250/500 per thousand:480 runs. Use v4-program-assay-1,200 steps,8x8
periodic sites,initial_site36,initial_material0,initial_energy64,initial_raw1,
drive_amount8,capacity64,leak1,bond_cost1,exchangeTrue,threshold16,
construction_cost4,copy_cost1,mutation0. Program is the selected role's recorded
program; other initial states and random streams must match within each pair.

Primary endpoint: mean occupied-site fraction over all ticks1..200 inclusive.
Keep zeros after extinction. Report descendant-minus-founder for every pair,
environment seed and assay drive (240 contrasts). Average first over the two
environment seeds and three selected pairs within each source case, separately
by assay drive. Then report source-seed means for each training drive, training
mutation and assay drive combination (five training seeds each, eight groups).
Do not treat siblings or shared training-seed conditions as independent replicates.
No significance threshold or graduation rule is specified for this descriptive assay.

Secondary outcomes: final population, formations, dissolutions, accepted/rejected
input and total/copy/construction/leak/bond costs. Save every run's summary and
primary numerator/denominator. No horizon extension or survivor filtering.
Equal-program pairs must have byte-identical initial/step/final/summary outputs
for the same assay environment. Any mismatch is a verification failure, not a
biological difference. Different-program pairs must share physical initial state
and all random states while differing only in declared program.

Require independent assay dynamics audit, exact480-case coverage, configuration,
selection/source/protocol binding, matched streams and independent primary counting.
Launch from a clean frozen commit. Site-record budget12864 per run (64*201).
Check2GiB cohort soft bound between runs; bounded overshoot possible. On errors or
limit stop incomplete, retain records, never silently deduplicate neutral pairs.
These assay seeds have not run. Results concern isolated-program expansion with
fixed starting material, not competitive ecological fitness or open-ended evolution.
