# Selection for a future matched ancestral assay

Freeze this rule before reconstructing and sampling study005 lineage. Include
all20 registered sources (five seeds × drive250/500 × mutation0/100). Eligible
units are alive at tick500 and have a recorded parent; initial founders themselves
are not descendants. No filtering on program novelty, mutation, energy, fertility
or any future assay outcome. Keep empty eligibility sets explicitly unavailable.

For each source rank eligible unit IDs by the hexadecimal SHA256 of the ASCII
string `v4-ancestor-selection-1:{seed}:{drive}:{mutation}:{id}` ascending, with ID
as a tie-breaker. Select the first three, or all if fewer than three. Preserve
every source, its eligible count and selection hashes. This is deterministic
sampling, not performance ranking. Selection uses passive birth identities.

Pair each selected unit with its recorded initial founder, not a matching genotype
or a randomly selected ancestor. Retain the full parent chain and source output
hashes, selected birth record, founder birth record, and whether programs match.
Do not deduplicate repeated programs, founders or shared ancestry. Later analysis
must treat source runs, not individual pairs, as independent sampling units.

The subsequent assay configuration and outcomes have not yet been specified or
run. Use equal initial material, energy, location, raw stocks, cost settings and
environmental random tickets for descendant/founder programs; disable mutation.
Equal-program pairs remain mandatory neutral controls. Selection availability is
not evidence of adaptive value. This document fixes sampling only, not assay
graduation criteria or a result.
