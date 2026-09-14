# Explicit-program matched assay

`v4-program-assay-1` starts one HeritableUnit carrying an explicitly supplied
four-entry program. Defaults:16x16 periodic space, central site(width//2,height//2),
material0,energy64,raw1 at every site, copy cost1 and the usual growing rules.
Geometry, site, material and energy are explicit configurable metadata. There is
no random physical/program initialization. Mutation is fixed to0 and is not a
caller option. Drive/direction/mutation RNG namespaces and per-site draws match
hereditary runs, including unused mutation tickets.

`program_assay.run(output, seed, program, ...)` persists complete states, events,
costs and random states. `program_assay_audit.audit(output)` independently rebuilds
the declared founder and continued hereditary dynamics. This verifies what was
run, not whether the supplied program belongs to a claimed ancestor: source-pair
provenance is an additional cohort gate. Keep the frozen selection record and its
lineage binding when assigning descendant/founder programs.

Matched pairs use identical initial expressed material even when their source
units had different materials. This isolates program effects conditional on the
chosen assay phenotype/environment; it is not a replay of the source ecology.
No competition against other genotypes or prescribed target pattern is included.
Occupancy over time measures monoculture expansion/persistence under these rules,
not general intelligence, group reproduction or universal fitness.

Engineering seeds97000/97001 test exact neutral replay, matched physical initial
states/RNG streams, independently reconstructed random/constant programs and
zero horizon. Scientific assay seeds must be separate. Existing hereditary
random initialization and all prior study semantics remain unchanged.
