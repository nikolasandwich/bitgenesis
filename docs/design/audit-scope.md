# What a successful V0 audit means

`bitgenesis audit DIRECTORY` checks consistency among saved records without
stepping the world. It does not regenerate the experiment from its seed. The
scope below describes source `3dbadf40d1554520701942cf89e2cb89ff51fc61`;
fixed archives retain the auditor shipped with their own source revision.

## Recorded-run checks

| Evidence | What is checked | What remains outside this check |
| --- | --- | --- |
| Metadata | Complete status; supported rules/output schema; fixed configuration keys and integer types; nonnegative integer requested/completed ticks that agree | A recorded seed is not replayed, and provenance is not authenticated. This is not a complete independent validation of every parameter range. |
| Per-tick metrics | Contiguous ticks and expected row count; population equals founders plus births minus deaths; total energy accounting; nonnegative energy and population; monotone cumulative supplied/dissipated energy | Global energy balance alone cannot prove the correct action order or each individual's energy transfers. |
| Lineage | Unique IDs, founder/parent relationships, birth/death ordering, generations, bounded genomes and mutation steps, no-mutation inheritance, direct offspring counts | Differential offspring counts do not isolate a causal benefit of the inherited trait. Founder labels are not species. |
| Lifecycle reconstruction | Birth/death totals, living trait mean and distinct values, founder counts and maximum living generation match each metric row | Aggregate values do not reconstruct movement or access to food. |
| Birth/death event stream | Events match lineage, occur in tick order, have valid positions, and contain the required births/deaths without duplicates; birth energy positive; death energy zero and last position consistent | Positive birth energy alone does not independently verify the exact parental split. Movements and feeding transfers are not in this event stream. |
| Every saved replay frame | Endpoints and tick ordering; resource dimensions/bounds/total; occupancy bounds/no collisions; population count; joint `(genome, founder_id)` multiset reconstructed from lifecycle; embedded metrics when present | No individual ID appears in a replay triple. Intermediate position-to-identity assignment and unsaved movements cannot be reconstructed. The audit does not certify that every advertised intermediate sampling point was retained. |
| Final frame and summary | Final organism triples and total living energy agree with lineage; summary agrees with final metrics | Agreement among files does not establish an external truth about how they were produced. |

For example, a changed intermediate founder label now fails even when the frame's
population and food total remain correct. Conversely, permuting the positions of
two living individuals within an intermediate frame can preserve every checked
aggregate. Passing is evidence for the stated checks, not proof of the entire
trajectory. Claims about exact replay require a separate engine replay comparison.

## Different verification tools answer different questions

| Tool or procedure | Question answered |
| --- | --- |
| `bitgenesis audit` | Do these full recorded-run artifacts satisfy the cross-file checks above? |
| `scripts/verify_v0_review.py` | Does this ZIP match its file manifest and, when supplied, an expected archive hash; do static local HTML targets exist? It does not execute its contents. |
| `scripts/check_v0_campaign_inventory.py` | Do committed result tables match the declared execution identities, seed counts, horizons and replay accounting? These are not independent-replicate counts. |
| Campaign-specific verifier | Do the particular retained observations meet that campaign's recorded consistency checks? Full event/lineage records may be absent; consult each report. |
| Frozen replay or clean installation comparison | Does a stated runtime/environment reproduce a specified reference trajectory or artifact? This is evidence for that checked case, not every possible configuration. |
| Controlled research experiment | Does an observation survive the specified comparisons within its seed, rule and observation-window scope? Neither test counts nor archive hashes replace those controls. |

The [acceptance guide](../research/REVIEW.zh-CN.md) separates fixed archive evidence
from later main changes. Source `3dbadf4` passed the six Windows/Linux × Python
3.12/3.13/3.14 jobs in [CI 34789147628](https://github.com/nikolasandwich/bitgenesis/actions/runs/34789147628).
The strengthened auditor also passed eleven historical full runs and 1,111 saved
frames. Those successful checks do not broaden the scope stated in this document.
