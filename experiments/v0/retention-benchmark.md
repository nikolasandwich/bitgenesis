# Operational retention benchmark

Use baseline seed 42, 32×32 and 10000 ticks. Two separate processes differ only
in whether pending events are cleared after each tick (like a recorder consuming
them) or retained (like the state-only checkpoint command). Both preserve all
living/dead lineage records and check invariants each tick. Save checkpoints at
1000, 5000 and 10000. No rule or parameter change and no new biological hypothesis.

Measure Python allocations tracked by `tracemalloc` after garbage collection,
checkpoint byte length, and the traced peak during serialization. This is not
process RSS, an operating-system memory cap or a benchmark of uninstrumented
throughput. Trace-enabled stepping excludes explicit checkpoint measurement work;
reported serialization times include tracing overhead. Concurrent benchmark runs
can contend for CPU, so timings are descriptive only.

Compare final checkpoint payloads excluding pending events: every other field
should agree. Results quantify current retention at three sizes; do not extrapolate
to millions of generations or promise a memory bound. These are operational checks,
excluded from formal research campaign totals.

```sh
python scripts/benchmark_v0_retention.py --events drained --output data/retention-drained
python scripts/benchmark_v0_retention.py --events retained --output data/retention-retained
```
