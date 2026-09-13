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
