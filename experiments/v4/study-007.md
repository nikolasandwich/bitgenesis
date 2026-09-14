# V4 study007: paired competition with role-location swaps

Use all60 frozen study005 descendant/founder pairs, including55 equal-program
pairs; retain selection and lineage hash binding. No selection based on study006
performance. Each pair crosses fresh environment seeds100000/100001, drive250/500
and placements normal/swapped:480 two-founder runs. These seeds have not run.

Use v4-competition-1,200 steps,8x8 periodic sites,programs ordered descendant then
founder. Normal role sites are(34,38), swapped(38,34). Both founders start with
material0,energy64;initial_raw1 everywhere,capacity64,drive_amount8,leak1,bond_cost1,
exchangeTrue,threshold16,construction_cost4,copy_cost1,mutation0. All per-site
environmental ticket streams remain matched across placements.

Primary per-run score: sum over ticks1..200 of(descendant-role living count minus
founder-role living count), divided by12800(64*200). Include founders themselves
while alive and zeros after extinction. An independent passive lineage observer
must derive roles from actual birth parents, not program equality. Save role
counts at every tick and terminal counts, as well as complete energy/material
summaries. Do not introduce a separate fitness reward into the engine.

First average scores over the two placements per pair/environment/drive (240
placement-paired scores). Then average over3 selected pairs and2 environments
within each training source case, separately by assay drive (40 source means).
Finally average over5 training seeds within each training drive/mutation/assay
drive condition (eight group means). No sibling pseudo-replication, significance
threshold or graduation rule. Positive favors descendant, negative favors founder.

For the55 equal-program pairs, both placements must have byte-identical physical
initial/step/final/summary files and reversed role-count sequences. Every averaged
neutral score must be exactly0 (220 environment/drive comparisons). Different-
program placements need matched physical founder energy/material, swapped declared
program locations and identical initial/final random streams. Preserve all signs.

Require exact480-case coverage, source-selection/configuration/protocol binding,
clean launch commit, independent dynamics and lineage counts. Freeze source hashes.
Use12864 site records per run;2GiB cohort soft limit between bounded runs, with
possible single-run overshoot. Stop incomplete on error/limit, retain records.
This tests specified two-founder competition, not equivalence to training ecology,
structural reproduction, intelligence or open-ended evolution.
