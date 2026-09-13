# Campaign 005: finite-world size and founder persistence

Preregistered after campaign 004. Question: how much does the observed loss of
founding lineages depend on finite world size, and does it also occur when all
founders have identical behavior?

Worlds: 16×16, 32×32, 64×64; initial populations 20, 80, 320 respectively (density
5/64). All per-site resource rules and per-organism costs remain baseline values.
Treatments: ordinary evolving genomes with mutation, and neutral founders fixed
to trait 250 with mutation disabled. The latter changes genomes after ordinary
initialization and does not make founder labels affect the engine.

Use seeds 400–404 for each combination, 10,000 ticks per run: 30 runs / 300,000
ticks. Size changes both available space and total energy supply/population at
fixed density; it is not an isolated manipulation of population count. Shared seed
numbers do not imply matching spatial arrangements or later environmental draws.

Primary measures: terminal surviving founder count and fraction of initial
founders, first tick with exactly one founder, and whole-world extinction tick.
Record one-founder states even if extinction occurs later. Secondary measures:
late mean population, trait diversity, generation, births/deaths and energy.

Prediction: larger worlds may retain founding lineages longer at this finite
horizon, but selection and neutral demographic loss need separate treatment.
Founder labels do not identify species, and more founders at tick 10,000 do not
establish sustained ecological novelty. Report all seeds and extinct runs.

```sh
python scripts/run_v0_world_sizes.py --output data/campaign-005
```

Outputs: per-tick metrics, aggregate JSON/CSV and provenance. Full lifecycle and
replay data are not exported by this assay. No extrapolation to infinite worlds
or formal significance testing is planned from these five-seed groups.
