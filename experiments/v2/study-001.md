# V2 study001: local genotype-to-development sensitivity

Preregistered before generating this study's genotypes. This is a structural and
behavioral mapping assay, not evolution, reproduction or an encoding-benefit test.

Twenty source streams use Python Random seeds83000..83019. Each independently
initializes five DevelopmentGenome values with the existing uniform coordinate
bounds. Preserve all100 parents, including invalid/empty structures. Each parent
has20 ordered perturbations: coordinate0..9 crossed with delta{-1,+1}, clipped
to its existing bounds. Retain duplicate/silent clipped variants. This symmetric
unit-step sensitivity neighborhood is not the runtime mutation distribution,
which allows larger steps on some coordinates.

Construct each parent and all variants with budget640 and exact existing local
rules:100 parent builds +2000 variants. Save every gene vector, full construction
result/history and independently reconstructed result. Valid means construction
valid with positive remaining energy. Report four parent/variant validity states,
invalid reasons, silent genotypes, expressed-weight changes, active-site changes,
cost changes, and which coordinate was perturbed. For two valid structures,
compare intact action distributions using all32 physical states from the fixed
V1 probe collection, equally weighted; report exact mean total variation and
whether it is nonzero. Invalid comparisons have null behavioral estimates, never
zero. Fixed probes are synthetic and consume no simulation RNG.

For every valid parent/variant, construct a direct copy of its expressed weights
with padding35*(rounds-1) and the same640 budget; independently reconstruct it
and require identical weights, valid status and total cost. This is conditional
same-phenotype accounting, not an independently mutated direct-genome control.
No ecological world runs or outcome-based genotype selection are included.

Each of20 source streams is a reporting cluster; its five parents and their20
variants are nested observations. Report all100 parent rows and2000 variant rows,
plus per-source tables and complete unconditional failure denominators. Primary
output is the four-state validity table; all structural/behavioral measures are
descriptive with no significance, superiority or stage-graduation claim. The
purpose is to identify which local perturbations affect developed structure and
whether those changes affect the supplied controller interface.

Freeze clean source/protocol hashes before execution. Store full outputs within
1GiB; check between parents and stop incomplete if reached, never analyze a
partial grid as complete. Preserve failure reasons and execution errors. No
replacement seeds, changed neighborhoods or resampling after inspection. Results
may motivate a separately registered population experiment or model revision,
without changing this study retrospectively.
