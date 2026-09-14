# Material-retaining damage

`v4-damage-1` uses the validated site selection of extraction, removes each selected
unit and exports its energy, then returns one raw token to its original site.
Empty selected sites do nothing. The record retains original unit labels/energies,
recycled material count, zero exported material and exact before/after ledgers.
Raw tokens carry no inherited material label: reconstruction must use a surviving
neighbor template. This removes local material deficiency without installing an
instruction to restore the original pattern.

Each site's raw tokens plus occupation remains invariant at this boundary. Total
energy decreases by the removed units' energies. This is a specified experimental
intervention, not endogenous damage detection, repair or adaptation.

`v4.damage_branches.run` persists `v4-damage-branch-1` with the same origin audit,
absolute ticks, drive/direction continuation and explicit threshold override as
extraction branches. `v4.damage_audit.audit(branch, origin)` independently rebuilds
the recycling boundary from serialized states, then verifies continued dynamics.
Extraction schemas and behavior remain unchanged. Tests cover matched sham versus
continuous results, RNG pairing, disabled formation, zero horizons, local material
conservation and rehashed recycling corruption. Seeds90900/90901 are engineering.

Study004 compares extraction and retained-material damage on the same fresh
prefixes, with matched shams and formation-disabled controls. It can separate a
material availability effect from pattern matching under available material;
it cannot establish ancestry, functional repair or structural reproduction.
