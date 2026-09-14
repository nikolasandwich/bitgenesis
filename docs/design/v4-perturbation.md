# Removal and recovery observations

`v4-removal-1` is an experimental boundary outside the growing dynamics. It removes
the units at a specified set of sites, exports their material and energy, and
leaves raw material at all sites unchanged. Empty selected sites do nothing.
Unlike endogenous dissolution, removal does not return a raw token to the site.
Zero-energy units still export one material token. Site indices are validated,
duplicates rejected and records sorted. Inputs are copied; no RNG is consumed.

    material_after = material_before - number of removed units
    energy_after = energy_before - sum of removed unit energies

This intervention models physical extraction, not damage repaired for free by
returning the removed material. Resource limitation after removal is part of its
effect. A future recycling-damage intervention must be separately specified.
An empty-site-list boundary supplies the matched sham condition.

`recovery.observe` is a passive comparison of a fixed reference state and a later
state on specified sites. It reports occupied fraction across all selected sites,
refill fraction on reference-occupied sites, and matching-material fraction on
those same reference-occupied sites. Fractions are exact rational strings; an
empty denominator is null, not zero or perfect recovery. Newly occupied sites
that were empty in the reference do not inflate reference refill or matching.

For example, if two removed sites originally held labels 0 and 1 and later hold
2 and 1, refill is 1 while material matching is 1/2. Even a match of 1 proves
neither survival of original units nor ancestry: labels are not unique identities.
These measures do not encode connections, shape equivalence under translation,
fragmentation, functional repair or structural reproduction.

The next persisted branch design should reconstruct a verified prefix, preserve
absolute drive/direction RNG states, save the pre/post-boundary states and export
ledger, and run sham/removal branches under the same remaining random tickets.
Include formation-disabled branches to distinguish templated regrowth from
passive survival. Compare each branch to both the pre-removal pattern and its
contemporaneous sham, so ordinary pattern drift is not attributed to damage.
Independently verify the boundary and branch histories before registering a
scientific cohort. No such recovery cohort has run yet.
