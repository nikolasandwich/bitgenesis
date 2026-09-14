# V4 study004: material availability in recovery

Preregister before seeds94000..94004. Generate five ordinary growing prefixes
with exactly the study003 configuration:300 steps,16x16 periodic sites,
occupancy250,max_energy64,initial_raw1,drive500/1000,drive_amount8,capacity64,
leak1,bond_cost1,exchangeTrue,threshold16,construction_cost4. Do not select prefixes.

From every prefix run six200-step branches: sham/extraction/damage crossed with
threshold16/65. Use extraction-branch schema for sham (empty selection) and
extraction. Use damage-branch schema for material-retaining damage. Both actual
interventions select x=6..9,y=6..9 inclusive, export unit energy and remove units;
only damage returns one raw token per removed unit. All branches retain the same
continued drive/direction RNG states and all parameters except threshold. Total:
5 prefixes and30 branches, no source replacement or extension.

Reference is the prefix endpoint. Primary is final patch material-match fraction
on reference-occupied sites. Per source compare damage-minus-extraction at each
threshold, damage-minus-sham at each threshold, and threshold16-minus65 under
damage (five sets of five contrasts). Report exact rational source means with
defined counts; preserve nulls if no reference site was occupied. No significance
or graduation claims.

Also report patch occupation, reference-site refill and material matching at
post-boundary tick300 and ticks310,350,400,500; reference matching outside the
patch; contemporary threshold-matched sham label matching on reference-occupied
patch sites for both interventions. A label match requires both sites occupied.
Report boundary exports/recycling and per-site initial/final patch raw stocks to
expose material constraints. Finite labels are not lineage identifiers.

Independently audit all prefixes and branches. Cohort verification must check exact
35-case coverage, all configurations, intervention schemas/sites, source/protocol
binding, clean launch, matched before states and final RNGs. Compute observations
without runtime recovery.observe. Site-record budgets77056 per prefix,51456 per
branch;2GiB cohort soft limit checked between runs, with bounded overshoot allowed.
Retain incomplete/error records and null/zero outcomes. Do not silently drop cases.
No scientific case from this protocol has run yet.
