# V0 experiments

From the repository root after installation:

```sh
bitgenesis v0 --config experiments/v0/empty-world.toml
```

Expected: an empty 16 x 12 world at tick 0 with seed 42, zero organisms, and zero
resource energy. This is a smoke experiment, not an evolution result. CLI options
`--seed`, `--width`, and `--height` override the corresponding configuration values.

Add independent, named experiment definitions as V0 develops. Keep the schema and
rules versions explicit and follow the compatibility policy in
`docs/design/experiments.md`. No result files are written by this scaffold.

## Darwinian world

```sh
bitgenesis v0 --config experiments/v0/darwin-baseline.toml --steps 1000 --output data/first-run
```

Open `data/first-run/index.html` for world replay, population/trait histories and
founder colors. Inspect `metadata.json`, `metrics.csv`, `events.jsonl`, and
`lineage.json` for the exact run definition and observations. The initial
population contains varied movement probabilities; even without mutation,
selection can change their proportions. A no-mutation control is not a
no-selection control.

See `docs/design/v0-rules.md` for rule ordering and energy accounting.
