# Verify a portable review

For recorded runs, see the separate [audit coverage matrix](audit-scope.md).
ZIP integrity and experiment-record consistency are different checks.

The standalone helper requires Python 3.12+ and the standard library only. Run it
from the current repository checkout; older archives can predate this helper.
It reads the ZIP without extracting files or executing embedded scripts.

```sh
python scripts/verify_v0_review.py data/bitgenesis-v0-review-8.zip --expected-sha256 c0905b233a635a383d0321cccca31a63cdcbdac079f19d94f7f7112d5928c38b
```

This specific hash identifies the eight-campaign source-`1202f61` archive. For a
later archive use its separately recorded hash. Without `--expected-sha256`, the
helper still checks internal consistency and prints the archive hash; it does
not establish that the archive matches a previously reviewed copy.

Checks include:

- Unique normalized file paths, with no traversal, absolute paths or symlinks.
- Exactly the manifest's payload files plus the manifest and start instructions.
- Every payload's recorded byte length and SHA-256.
- Every static local `href`/`src` found in the archived HTML resolves to another
  manifest payload. External URLs are not fetched, anchors are not validated,
  and JavaScript-created links are not executed or checked.

The manifest and start instructions are envelope files, outside the per-payload
hash list. An externally recorded whole-archive hash also covers those bytes.
Someone replacing both payload and manifest can create an internally consistent
different archive, so internal hashes alone are not proof of origin or authenticity.

Verification of source-`1202f61` found 563 payload files, 13 HTML pages and six
static local targets. The expected whole-archive hash matched. Deliberate corrupt
payload, missing target and unlisted file fixtures are rejected by tests.

The packager uses the same helper after writing future archives. Its full-run
and metric audits remain separate checks. Neither file integrity nor simulated
energy accounting proves the scientific interpretation of a research result.

## Build a new review archive

`python scripts/package_v0_review.py --campaigns 17` includes the local raw
outputs for campaigns 001–017 and `data/review-v0-17.html`, along with tracked
source, compact results and the acceptance demonstration. Generate the page first
with `python scripts/build_v0_review.py --campaigns 17`. Both commands require
the complete local inputs; the packager also requires a clean committed checkout.
An existing output is rejected; use `--output` for a distinct snapshot.

The default remains eight campaigns. The manifest records the selected raw-data
workload separately from all tracked source documents, which may discuss later
campaigns. For seventeen campaigns it identifies twenty-four longitudinal follow-ups
and 212000 replayed prefix ticks. Packaging reruns the existing full-run audits,
campaign-005 audit, and selected 009–017 metric verifiers. The 011 verifier also
compares all recorded prefixes with campaign 010. These are artifact consistency
checks with the scope of each named verifier, not independent simulation reruns.

The 013 verifier reconstructs cumulative genome coverage from the complete birth
catalog and checks every recorded metric row. Its missing full death records
limit independent reconstruction of living trait sets; see the campaign report.

The 014 verifier checks the full cost/frequency/treatment/seed grid, per-tick
group/trait/energy consistency, irreversible group loss and terminal outcomes.
It does not reconstruct unsaved individual histories or establish stable coexistence.

The 015 verifier checks the complete selected neutral cohort, all 120,004 metric
rows and all 12,004 prefix rows against the hashed campaign-014 reference. This
is a conditional extension, not a new independent sample or stable-coexistence
claim. The corresponding raw reference directory is explicitly supplied.

## Malformed recorded-run JSON

The current `bitgenesis audit DIRECTORY` first checks that `metadata.json` and
`summary.json` contain JSON objects and that `lineage.json` and `frames.json`
contain JSON arrays. Wrong top-level types are rejected with the file name and
expected type; the CLI exits with code 2 and leaves inputs unchanged. This is a
format check before the lifecycle and energy consistency checks, not a guarantee
that every syntactically valid object represents a valid experiment.

This error-reporting improvement postdates the fixed fifteen-campaign archive.
That snapshot can show an AttributeError traceback for list/null metadata; its
valid recorded runs and prior verification results are unaffected.

The current auditor also requires the complete fixed V0 configuration key set,
integer configuration values, and nonnegative integer requested/completed ticks.
JSON booleans and numerically equal floating-point values do not satisfy integer
fields. This aligns artifact types with the engine's configuration contract;
it does not independently replay the seed or authenticate who generated a file.
The older fixed fifteen-campaign auditor did not reject all such type substitutions.
Eleven saved full runs (campaign 001 plus the acceptance demo) pass the stricter
checks unchanged.

## Intermediate replay labels

For each saved frame, the current recorded-run auditor reconstructs the living
multiset of `(genome, founder_id)` pairs from birth/death records and compares it
with the rendered organism triples. This rejects wrong intermediate trait or
founder labels even when population, food and embedded summary metrics agree.
The pair check preserves their association, not only separate marginal totals.

Intermediate positions are checked for bounds and collisions, but their historical
identity assignment cannot be recovered from these triples: replay frames omit
individual IDs and movement events are not recorded. This is not an independent
reconstruction of every movement or the spatial history between sampled frames.
The stricter check passed all 1,111 saved frames across eleven historical full
runs. It postdates the fixed fifteen-campaign archive; raw records are unchanged.

## Replay sampling completeness

The current auditor compares stored frame ticks with the exact schedule implied
by the recorded effective `frame_interval`: tick zero, interval-aligned ticks,
and the final tick if not already included. The interval must be a positive
integer. A missing intermediate frame is rejected even when endpoints and all
remaining frames are individually consistent. A zero-step run has one frame.
This catches lost samples, not hidden events between the advertised samples.
The fixed fifteen-campaign archive predates this additional check.

The 016 verifier checks all thirty initial food maps, founder/RNG-state pairing
for ten seed triplets, and 300,030 metric rows before packaging. This verifies
retained initialization and observations without stepping the simulator.

The 017 verifier checks forty initial states, ten founder/RNG quadruplets,
twenty matching threshold-map pairs, 400,040 metric rows and 4,000 early feeding
transitions. Its sibling geometry helper is included in the archive. Passing
these checks does not reconstruct individual movement or identify a causal
mediator of the reproduction-threshold effect.
