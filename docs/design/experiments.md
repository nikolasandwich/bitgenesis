# Stages and reproducibility

The modules directly under `src/bitgenesis/` preserve the original V0 scaffold.
The Darwinian runtime lives under `bitgenesis.v0` with rules `v0-darwin-1`.
There is no plugin system or placeholder implementation of V1–V4. CLI routing
explicitly accepts only `v0`.

When introducing V1, retain V0 rules and the `bitgenesis v0` command, and add `bitgenesis.v1` for
new rules. Share only utilities whose semantics are truly stable. Later stage
commands must be explicit; never silently redirect an old experiment to new rules.

Experiment definitions live under `experiments/<stage>/`. The initial TOML file
has schema version 1 and rules version `v0-scaffold-1`; the CLI validates both.
It initializes an empty world only. Future changes to dynamics require a new
rules version and definition, leaving the old definition intact. Preserve a
compatible runner or tag/pin the last supporting commit and document that route.
Git history is the authority for exact historical replay, not package version alone.

The frozen `v0-darwin-1` replay test fingerprints events, lineage, resources and
terminal metrics for a declared seed/configuration. Do not update its checksum to
hide changed dynamics: introduce a new rules version or document an interpreter
compatibility boundary. Its reference was captured on Python 3.12.10 at `d789db1`.

Every Darwinian run saves the full
configuration, seed, rules/schema versions, Git commit (and dirty state), Python
version, invocation, source file hashes, and output schema version alongside raw events and metrics.
Use a simulation-local RNG; record update order and all sources of randomness.
Do not claim cross-version/platform bitwise reproducibility without testing it.

Installed wheels also hash their package source. They report Git provenance as
unavailable rather than accidentally attributing code to an unrelated enclosing
checkout. Source installs additionally hash committed research helper scripts.

Store generated runs in ignored `data/` directories. Keep small definitions and
necessary regression fixtures in Git; archive large research datasets separately
with checksums and retrieval instructions. Do not overwrite past experiment runs.
