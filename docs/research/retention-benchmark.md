# Retention measurement and streamed checkpoint output

Operational benchmark on baseline seed 42, Python 3.12.10 / Windows. Two modes
keep all lineage records; one drains pending events every tick, the other retains
them as the state-only checkpoint command does. This does not change dynamics.
See the [measurement protocol](../../experiments/v0/retention-benchmark.md).

At tick 10000 both modes had 68 living organisms but 14,993 lineage records.
The retained mode also held 29,918 pending events. Historical state, rather than
current population alone, therefore determines much of the retained memory.

## Before and after streaming JSON

The old atomic helper first constructed a complete pretty-printed JSON string.
It now writes encoder chunks into the temporary file, flushes and syncs it, then
atomically replaces the target. The final newline and JSON formatting are unchanged.

All MB figures below use 1 MB = 1,000,000 bytes. These are Python allocations
reported by `tracemalloc`, **not process RSS**. Live allocation is measured after
garbage collection; save peak includes live state and serialization temporaries.

| Events | Tick | Live allocation, approximately MB | Old save peak MB | Streamed save peak MB | Checkpoint MB |
| --- | ---: | ---: | ---: | ---: | ---: |
| Drained | 1000 | 0.458 | 3.918 | 1.447 | 0.450 |
| Drained | 5000 | 2.052 | 17.562 | 6.494 | 2.020 |
| Drained | 10000 | 4.063 | 34.774 | 12.836 | 3.995 |
| Retained | 1000 | 1.254 | 8.281 | 2.753 | 0.943 |
| Retained | 5000 | 5.795 | 38.083 | 12.685 | 4.361 |
| Retained | 10000 | 11.486 | 74.166 | 25.157 | 8.659 |

At 10000 ticks the observed save peaks decreased by 63.09% and 66.08% respectively.
This is a measurement of these states and environment, not a universal percentage.
Tracing adds overhead and the two processes ran concurrently; recorded elapsed
times must not be presented as uninstrumented throughput benchmarks.

The remaining save peak includes lineage conversion and canonical checksum
serialization. Complete lineage and retained events still grow. This change does
not provide a bounded-memory engine or justify million-generation capacity claims.
A later design would need deliberate archival/streaming semantics for history,
with corresponding replay and audit support.

## Evidence

- Baseline source `1afd161`; streamed source `f0befe4`.
- All six corresponding checkpoint files (two modes × three ticks) are byte-identical
  before and after the change.
- Final checkpoint payloads from the two modes agree after removing pending events;
  RNG state, lineage, resources and all other fields match.
- Tests preserve JSON formatting, rejection of nonfinite values, cleanup of temporary
  files and the preceding checkpoint when replacement fails. Full local suite: 38 tests.
- [Measurement records](results/retention-benchmark.json) include source commits,
  interpreter/platform, exact sizes/timings and final checkpoint hashes.

These four benchmark executions are operational checks, excluded from formal
research totals. Raw files remain under `data/retention-*`; earlier snapshots
and review archives remain untouched.
