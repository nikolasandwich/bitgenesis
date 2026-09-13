# Helper scripts

Keep helpers thin: simulation rules belong in `src/bitgenesis/`, and experiment
definitions in `experiments/`. No helper is needed for the current scaffold.

From the repository root, use:

```sh
python -m unittest discover -s tests -v
bitgenesis v0 --config experiments/v0/empty-world.toml
```
