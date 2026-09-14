# V3 engineering runs

```console
python -m bitgenesis.v3 --seed 85102 --steps 50 --output data/my-v3-check
```

Use a new directory. Optional --config accepts a JSON object with V3 Config
fields. recycling is0 or1; initial_b defaults0. The world supplies only A from
outside. These defaults are engineering choices, not an ecological study.
Seeds85000..85102 are reserved for engineering and excluded from held-out work.

The v3-run-1 records retain initial/final A (food) and B (substrate_b) grids,
lineage, all failed/successful construction attempts, random states, streamed
events and actor records. Per-actor feeding records separate raw substrate intake,
energy gain, B release and dissipation. Summary resource_flows totals these and
external A supply; it is accounting, not a fitness measure.

Metadata binds v3-world-1, v3-resources-1, v1-linear-1, V3 source files, reused V1
controller and V2 development sources, configuration, Python and Git state, and
output hashes. The worst-case actor budget is checked before a world is allocated.
Events are streamed, but retained lineage and development histories remain in
memory. This count bound is not a byte bound; future studies need storage limits.

Replay tests and substrate balance tests pass. Independent V3 spatial, ancestry
and resource reconstruction is still pending. Do not describe the runner's own
ledger assertions or output hashes as an independent audit or ecological evidence.
Preserved V0/V1/V2 commands are unchanged.
