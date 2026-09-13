# Verify a portable review

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
