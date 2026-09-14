# Passive unit ancestry

`v4.lineage.trace(directory)` first independently audits an ordinary hereditary
run, then assigns unique observation identities. Initial occupied sites become
founders in ascending site order, starting at0. Every successful formation gets
a fresh identity in recorded proposal order. Dissolutions are processed before
births, so a site reused in the same tick receives a different identity.

Each record retains site, birth/death tick, actual parent, initial founder,
generation, expressed material, program at birth, birth energy, whether that
birth mutated, and direct offspring count. End-of-run site identities map living
units back to complete ancestry. Program/material equality is checked against
every recorded living state; offspring totals are checked against audited events.
The fixed-site engine does not move units, so a living identity's site is stable.

These are unit identities, not organism or connected-component identities. They
are never supplied to the engine and do not affect resource access or selection.
Identical programs can belong to unrelated founders; a mutation can recur or
revert, and identity persists independently of genotype equality. The observer
does not infer parentage from a matching program. Initial zero-energy units are
founders because they are present in the initial state; later dynamics determine
whether they are rescued or dissolve.

The event consumer `Observer` is separately testable but does not by itself audit
the dynamics. Use `trace` for scientific records. It binds the full independent
audit and observer source hash. For export use:

    python -m bitgenesis.v4.lineage RUN_DIRECTORY --output NEW_JSON_FILE

Engineering001 reconstructs182 founders,79 births,5 deaths,256 living units,
maximum generation3 and1 mutation birth. This is an engineering demonstration,
not an evolutionary advantage result. Seed95006 covers runtime ancestry tests.

Next derive ancestry for the registered variation cohort before selecting assay
pairs. Prespecify descendant sampling without using held-out assay performance;
compare the sampled program with its recorded founder program under identical
initial expressed material, energy, raw stocks, location and environmental tickets.
Disable additional mutation during the assay to attribute differences to the
tested inherited programs. Equal-program pairs are useful neutral controls and
must not be silently excluded. An assay runner must record explicit initial
program provenance and independently reconstruct its declared initialization.
