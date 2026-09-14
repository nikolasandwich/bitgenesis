# Fixed-phenotype construction control

The `paired_control` interface first develops a specified genotype at the declared
founder allocation. It requires a living result and mutation disabled. It then
runs developmental copies and direct copies of precisely those expressed weights
with identical site/resource/physiology settings. This is a neutral engineering
control conditional on a viable genotype, not a new evolutionary comparison.
Failed genotypes must remain in separate unconditional sample accounting.

Direct expression padding is35*(development rounds-1), so a completed direct
build costs the same as the reference development. If a child cannot afford a
build, the two paths may spend different amounts on attempted work versus lose
different unspent remainders; both dissipate exactly the same transferred
allocation. The comparison preserves these separate records and checks their
sum when comparing physical trajectories. Both outputs receive full V2 audits.

Founder assignments are applied before construction, after the ordinary random
initialization draws. They are stored in metadata and checked against initial
attempts. Initial genotype RNG states differ between encodings and are excluded
from cross-encoding state equality; the remaining streams are compared. The
initial/final physical state and each actor ledger (with construction+failure
loss combined) must agree. Genotype representations and developmental histories
are deliberately not claimed equal.

This check supports the premise that downstream differences require changed
phenotypes/costs/trajectories rather than a hidden encoding label in decisions.
It does not show that the two genotype spaces have equal evolvability. Future
mutation studies must declare their perturbation distributions and distinguish
conditional phenotype controls from population-wide construction failures.
