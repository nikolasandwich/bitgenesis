# Campaign 008: initial food and establishment

Preregistered before seeds 700–709. Campaign 007 showed finite-horizon persistence
without movement-trait variation. Test dependence on the initial food reservoir.

Two treatments: initial food 0 or baseline 8 per cell. Both retain 32×32, 80 founders
with energy 24, all founder genomes set to 250 after normal initialization, no
mutation, regrowth 15/1000 and all other baseline rules. Same-seed founder positions
and initial RNG state match; later trajectories and environmental draws can diverge.
Changing initial food changes the initial supplied-energy total by 8192 units.
The intervention is an initial resource pulse, not a change to ongoing regrowth.

Seeds 700–709, 10,000 ticks each, including after extinction: 20 runs / 200,000
ticks. Primary: survival at 500, 5000 and 10000; first extinction tick. Secondary:
terminal population, mean population over ticks 9001–10000 including extinct zeros,
and cumulative births/deaths. Do not condition primary outcomes on early survival.
No replacement seeds, altered horizon or discarded runs after seeing outcomes.

Prediction: initial food may improve early establishment without guaranteeing
late persistence. Report null or opposite differences. Survivors are right-censored
at 10000. Ten seeds support descriptive frequencies, not precise probabilities or
an infinite-time survival claim. Even an empty-food world starts with organisms
and stored energy; this is not spontaneous life or replication from no resources.

```sh
python scripts/run_v0_initial_food.py --output data/campaign-008
```

Save every tick's metrics, protocol/provenance and all-run summaries. No full
lifecycle or replay files are exported. Check existing engine invariants every tick.
