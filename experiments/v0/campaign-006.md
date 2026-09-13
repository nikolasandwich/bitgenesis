# Campaign 006: finite-horizon extinction under scarce resources

Preregistered after campaigns 001–005 and before running new seeds. Campaign 004
found extinction for regrowth 10/1000 and persistence for 40/1000 in five seeds.
Question: what happens at intermediate resource probabilities, and how variable
is time to extinction across independent runs?

Keep baseline 32×32, 80 founders, evolving movement traits and all other rules.
Test regrowth probabilities 10, 15, 20, 30, 40 per 1000 sites per tick, each with
seeds 500–509. Run every world through tick 5000, including after extinction:
50 runs / 250,000 ticks. No rescue, replacement, discarded runs or tuning after
seeing results. Same seed numbers across treatments do not give identical future
resource draws because organism actions also consume the random stream.

Primary outcomes: fraction extinct by tick 5000 and first extinction tick for each
run. Surviving runs are right-censored at 5000, not assigned an extinction time of
5000. Plot empirical fraction not yet extinct against tick. Describe extinct-only
time ranges explicitly; do not label these as group-wide mean survival time.
Secondary outcomes: final population and mean population over ticks 4001–5000,
including zeros from extinct runs. Preserve per-tick metrics, all seed outcomes
and provenance. No significance claim or universal critical resource threshold:
this is a finite world, finite time, ten-seed descriptive assay.

Prediction: increasing supply will reduce extinction over this horizon, but
intermediate conditions may produce mixtures of early extinction and persistence.
This expectation does not establish a monotone result for every seed.

```sh
python scripts/run_v0_extinction.py --output data/campaign-006
```

The helper saves metric-only artifacts. Full lineage/event files and replay are
not exported. Unchanged engine invariants are checked every tick.
