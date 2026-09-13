# Stages and reproducibility

The modules directly under `src/bitgenesis/` preserve the original V0 scaffold.
The Darwinian runtime lives under `bitgenesis.v0` with rules `v0-darwin-1`.
There is no plugin system or placeholder implementation of V1–V4. CLI routing
accepts only `v0` as a runtime stage; `audit` and `checkpoint` are V0 utilities.

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

CI run [34776314237](https://github.com/nikolasandwich/bitgenesis/actions/runs/34776314237)
passed the 34-test suite on Windows/Linux × Python 3.12/3.13/3.14. The frozen fixture
is a seed-314159, 8×8, 12-founder, 120-tick world; equality there is a useful
compatibility check, not a rerun of every research campaign on every interpreter.
Use the recorded interpreter for exact historical work. Checkpoint loading still
requires matching Python major/minor versions despite this passing fixture.

Every Darwinian run saves the full
configuration, seed, rules/schema versions, Git commit (and dirty state), Python
version, invocation, source file hashes, and output schema version alongside raw events and metrics.
Use a simulation-local RNG; record update order and all sources of randomness.
Do not claim cross-version/platform bitwise reproducibility without testing it.

Installed wheels also hash their package source. They report Git provenance as
unavailable rather than accidentally attributing code to an unrelated enclosing
checkout. Source installs additionally hash committed research helper scripts.

## Recorder output schema 2

Dynamics remain `v0-darwin-1`; recording changes have a separate
`output_schema_version`. Schema 2 embeds exact metrics in each replay frame.
The recorder retains at most `--max-frames` frames (default 1,001), including
initial/final states, increasing the effective interval when necessary. Charts
retain at most 10,001 evenly sampled tick observations; their horizontal positions
use actual tick numbers. Metadata records requested/effective replay intervals
and chart interval. Sampling can omit brief changes; raw `metrics.csv` still
contains every tick and `events.jsonl` every lifecycle event.

This bounds replay/plot retention, not total engine memory: complete lineage
records still grow with births. Prior output files and generated viewers are not
rewritten. Caught interruptions mark status `interrupted`; other caught runtime
errors mark `failed`, including failures during world initialization. Metadata
`completed_steps` records the last tick whose loop and record handling finished,
not the mutable world tick if the next step fails halfway through. An initialization
failure reports zero completed steps and does not claim a valid tick-zero world.

Partial outputs are retained for diagnosis, not accepted as complete audit inputs.
A recording failure can leave an incomplete trailing record or an unflushed buffer;
the completion count is not a crash-safe storage guarantee. The recorded-run command
does not resume that prefix. Use the separate checkpoint route for recoverable
world state, and a new directory for a new recorded run.

JSON checkpoints use a temporary file in the same directory, flush it, then
replace the previous checkpoint. A failed replacement leaves the preceding JSON
intact. This reduces partial-write exposure; it is not a blanket power-loss
guarantee. CSV/event streams still represent a growing prefix during a run.
Metadata saying `running` describes its last saved state, not proof that the
process is currently alive. Check a live process/job handle before resuming work.

Store generated runs in ignored `data/` directories. Keep small definitions and
necessary regression fixtures in Git; archive large research datasets separately
with checksums and retrieval instructions. Do not overwrite past experiment runs.
