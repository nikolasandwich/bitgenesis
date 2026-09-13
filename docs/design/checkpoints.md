# V0 checkpoints and recovery

`checkpoint` advances the existing `v0-darwin-1` engine and periodically saves its
complete state. It does not change biological rules. This is a state continuation
tool: the normal `v0` command remains the way to produce metrics CSV, replay and
auditable research artifacts. Checkpoint directories are not inputs to `audit`.

```sh
bitgenesis checkpoint --config experiments/v0/darwin-baseline.toml --steps 1000 --interval 100 --output data/state-first
bitgenesis checkpoint --resume data/state-first/state.json --steps 500 --interval 100 --output data/state-next
```

The second command advances 500 additional ticks and ends at tick 1500. Every
output directory must be new, including after interruption. A resumed state keeps
its original configuration; passing both `--resume` and `--config` is rejected.

## Exact continuation contract

JSON format `bitgenesis-state-1` stores configuration, tick, resources, all living
and dead individuals, pending events, energy accounting, next ID, and the full
random-generator state. Living-individual and lineage insertion order are retained
because they affect random scheduling. No founders are regenerated on loading.

Loading requires the same rules version, normalized engine source hash and Python
major/minor version. This conservative compatibility check can reject an otherwise
harmless source edit. Keep the original commit and Python environment when resuming
an old experiment. The format uses JSON, without executable object serialization.
A SHA-256 digest detects accidental corruption; it is not an authenticity guarantee.

Loading also validates historical lineage, independently of the checksum: scalar
types/bounds, founders, earlier parent IDs, generation and founder inheritance,
birth/death chronology, one birth per parent per tick, and offspring totals.
Each child genome must be within the configured mutation step of its parent;
with mutation disabled or step zero it must be identical. Boundary clipping does
not permit a larger change. This checks both living and dead descendants.
Dead individuals must have zero energy under these rules. A syntactically valid
file with a recomputed checksum is still rejected if those structural conditions
fail. This is not exhaustive replay of every historical transition. The checks
remain active with Python optimization enabled.

Retained pending events are checked for supported fields, integer types, bounds,
chronological order and duplicate birth/death identities. Birth ticks, parent IDs
and genomes must match lineage; founder energy must match configuration. Death
ticks, zero energy and final positions must match the dead individual. Buffers
may be empty after draining: these checks do not certify a complete event history.
Historical child birth energy and birth location are bounded but cannot be fully
reconstructed from final lineage alone. No authenticity claim follows from loading.

Tests compare continued state with uninterrupted state, including random state,
events, lineage and spatial state. A CLI test compares complete checkpoint payloads
across three separate processes. Existing frozen-rule regression tests remain in
place, and the cross-platform CI runs these tests on Python 3.12, 3.13 and 3.14.

Boundary tests also cover an initially empty world, extinction, full occupancy
with no turnover, and ongoing turnover. Each is resumed with both retained and
explicitly drained pending-event buffers; the final saved files must be byte
identical to uninterrupted continuation. Drained events are not regenerated.
This verifies state continuation, not recovery of an external event log: a caller
that drains events remains responsible for saving them before discarding them.

## Interrupted work

The initial world is saved, then each configured interval and the final tick.
Each state file is flushed and atomically replaced. If execution stops inside a
tick, recovery starts at the last successfully saved complete tick; no partially
changed world is saved by the exception handler. Unsaved progress must be rerun.
Atomic replacement does not promise durability through every hardware failure.

`metadata.json` records the start, target, saved tick and completion status. A hard
process termination can leave status `running`, or metadata one save behind the
state. The validated `state.json` is authoritative for the saved tick; a status flag
does not prove that a process is still alive.

This command retains full lineage and pending events in memory and each checkpoint.
It is not a bounded-memory solution for millions of generations. It does not append
to, repair, or reconstruct a previous run's CSV, replay or event files. Recoverable
recorded runs would need a separate segment format and corresponding audit support.

The atomic writer streams JSON chunks to avoid building the entire pretty-printed
text in memory. A [retention benchmark](../research/retention-benchmark.md) measured
smaller serialization peaks while preserving checkpoint bytes. Full historical
state and checksum preparation still allocate memory; consult the measured scope
before choosing long-run budgets.

## Historical-file compatibility check

After strengthening lineage and pending-event validation, source `043fad3`
loaded all three preserved engineering checkpoints from the earlier recovery
exercise (ticks 1000, 2500, 2500) under Python 3.12.10. Resuming the historical
1000-tick state for another 1500 ticks produced a complete 2219615-byte file
identical to both preserved 2500-tick states, including RNG and pending events.
The old files were not rewritten. [Recorded hashes and scope](../research/results/checkpoint-compatibility-001.json).

This is evidence for those compatible files, not a promise that incompatible
engine revisions or Python minor versions will load. These 1500 replay ticks
are an engineering check outside the formal campaign totals.

```sh
bitgenesis checkpoint --resume data/checkpoint-validation/first/state.json --steps 1500 --interval 500 --output data/my-historical-resume
```

The preserved local checkpoint inputs are not included in the thirteen-campaign
review archive. The automated test suite provides separately generated recovery
fixtures when those local historical files are unavailable.
