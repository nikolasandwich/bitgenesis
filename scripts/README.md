# Helper scripts

Keep helpers thin: simulation rules belong in `src/bitgenesis/`, and experiment
definitions in `experiments/`. No helper is needed for the current scaffold.

V0 research helpers now include preregistered campaign runners, local review
generation, a hashed review archive, and an optional scientific figure exporter.
They keep explicit output paths and do not overwrite completed runs/figures.

From the repository root, use:

```sh
python -m unittest discover -s tests -v
bitgenesis v0 --config experiments/v0/empty-world.toml
```

For the campaign-005 figure after completing its runs:

```sh
python -m pip install -e ".[analysis]"
python scripts/plot_v0_world_sizes.py
```

The analysis extra is optional; the engine and CLI retain no runtime dependencies.
The figure exports PNG/SVG and a JSON provenance sidecar with input/output hashes.
