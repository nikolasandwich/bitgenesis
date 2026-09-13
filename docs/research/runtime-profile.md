# Exploratory V0 runtime profile

A local engineering observation on Windows/Python 3.12.10, source
`dfd5305` (full source and environment hashes in the [record](results/runtime-profile-001.json)).
This is not a scientific campaign or a throughput guarantee. No engine changes
were made as a result.

Construct `World(Config(seed=42))`. For 2000 ticks call `step()`,
`check_invariants()`, `snapshot()` and `events.clear()` in that order. Measure
one run with `time.perf_counter`; repeat the same loop wrapped in `cProfile`.
Include construction and final digest preparation in both measurements.
The inline harness hashes a JSON object containing final metrics, RNG state,
food array and ordered living tuples (id, position, energy, genome, offspring).
These hashes match between the two runs. This is a selected final-state check,
not comparison of every event or historical lineage entry.

Observed unprofiled wall time: 1.3141 seconds. Profiled total function time:
4.5793 seconds. Profiling overhead is substantial; the two measurements must
not be used as an optimization before/after comparison. Only one sample each
was collected, and the machine may have other background work.

| Function | Calls | Profile self time, seconds | Cumulative time, seconds |
| --- | ---: | ---: | ---: |
| Random._randbelow_with_getrandbits | 2531769 | 0.9199 | 1.4584 |
| World.step | 2000 | 0.8087 | 3.8076 |
| Random.randrange | 2215635 | 0.8040 | 2.2101 |
| World.neighbors | 152431 | 0.1584 | 0.2067 |
| World.snapshot | 4002 | 0.0373 | 0.2314 |

Cumulative values include callees and overlap; do not sum them as disjoint
categories. The caller explicitly takes one snapshot and invariant checking
takes another. Neighbor queries are a modest share here. Random-number work
is prominent, consistent with drawing for every resource cell each tick.

Decision: retain the V0 implementation. Replacing random sampling, skipping
apparently unnecessary draws or batching resource updates can change the stream
and historical trajectory. Neighbor caching would need exact ordering and
narrow-world duplicate behavior preserved, while adding retained state and
checkpoint compatibility considerations. This small profile does not justify
that change by itself. Any optimization should be measured over repeated
representative configurations and checked against frozen trajectories before
adoption. Do not remove invariant checks to present an artificial speedup.

For a standard-library reproduction of the call profile, run this from a source
checkout with the package installed (the timing/selected-state comparison above
used the stated inline harness):

```python
import cProfile
from bitgenesis.v0.engine import Config, World

def exercise():
    world = World(Config(seed=42))
    for _ in range(2000):
        world.step()
        world.check_invariants()
        world.snapshot()
        world.events.clear()

cProfile.run("exercise()", sort="tottime")
```

The profile result is operational evidence about this loop. It does not include
CSV writing, frame rendering, full lineage serialization or checkpoint saving.
Those workloads require separate measurements; see the
[retention and serialization benchmark](retention-benchmark.md).
