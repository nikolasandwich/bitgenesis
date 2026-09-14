# V1 engineering runs and future experiments

V1 has a separate execution route; existing V0 commands are unchanged:

```console
python -m bitgenesis.v1 --seed 70101 --steps 100 --output data/my-v1-check
```

Use a new directory. Optional `--config config.json` accepts an object of the
fields in `bitgenesis.v1.world.Config`; unspecified fields use engineering
defaults. `--mode intact|blind|shuffled` selects the inherited intervention mode
for all founders. This runner currently supports one mode per world; mixed-mode
competition needs a separately specified initialization interface.

The output includes configuration, Python and source versions/hashes, initial
food/genomes/RNG state, per-tick actor ledgers, birth/death events, final lineage
and RNG state, summary and output hashes. Metadata distinguishes running, failed
and complete runs. Completed output is never overwritten. The step horizon is
0..100000, and width * height * steps must fit `--max-actor-records` (default
1000000). This conservative limit bounds potential recording volume; it is not
a byte limit. Initial population/world allocation must also be chosen responsibly.
Events are streamed and drained; lineage remains in memory for this bounded run.

Engineering seeds 70001..70210 are reserved for fixtures and smoke checks and
must not be reused as unseen evaluation seeds. The initial seed70101/default
100-step smoke check produced population20, births285 and deaths345; these are
engineering observations, not pilot selection or evidence of adaptation.

Audit serialized records without importing the simulation engine:

```console
python -m bitgenesis.v1.audit data/my-v1-check --output data/my-v1-audit.json
```

This checks output hashes, actor membership and timing, individual/world energy
payments and transfers, event ancestry and mutation support, final population,
occupancy bounds and summary. It does not yet reconstruct spatial food history,
verify sensor/action arithmetic from the recorded state, or replay random draws.
Rehashed semantic-corruption tests exercise the checks beyond file integrity.

Next: spatial/action verification and a declared viability pilot with a fresh
seed block and bounded configuration grid, then a frozen training/evaluation
protocol. No V1 scientific campaign is complete. See the
[world contract](../../docs/design/v1-world-contract.md) and
[evaluation contract](../../docs/design/v1-evaluation-contract.md).
