# Stages and reproducibility

The modules directly under `src/bitgenesis/` are the current V0 scaffold. There is
no plugin system or placeholder implementation of V1–V4. CLI routing explicitly
accepts only `v0`. Module responsibilities are small enough to split later.

Before introducing V1, move stage-dependent V0 rules into `bitgenesis.v0`, retain
compatibility imports and the `bitgenesis v0` command, and add `bitgenesis.v1` for
new rules. Share only utilities whose semantics are truly stable. Later stage
commands must be explicit; never silently redirect an old experiment to new rules.

Experiment definitions live under `experiments/<stage>/`. The initial TOML file
has schema version 1 and rules version `v0-scaffold-1`; the CLI validates both.
It initializes an empty world only. Future changes to dynamics require a new
rules version and definition, leaving the old definition intact. Preserve a
compatible runner or tag/pin the last supporting commit and document that route.
Git history is the authority for exact historical replay, not package version alone.

When time stepping and result writing are added, every run must save the full
configuration, seed, rules/schema versions, Git commit (and dirty state), Python
version, invocation, and output schema version alongside raw events and metrics.
Use a simulation-local RNG; record update order and all sources of randomness.
Do not claim cross-version/platform bitwise reproducibility without testing it.

Store generated runs in ignored `data/` directories. Keep small definitions and
necessary regression fixtures in Git; archive large research datasets separately
with checksums and retrieval instructions. Do not overwrite past experiment runs.
