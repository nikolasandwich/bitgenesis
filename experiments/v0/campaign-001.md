# Campaign 001: does the minimal world sustain heritable variation?

Declared before running the campaign. Rules: `v0-darwin-1`.

Question: Does the explicit-organism baseline sustain birth/death turnover, and
how do trait composition and surviving founder counts differ with mutation?

Treatments: `darwin-baseline.toml` defaults (mutation attempts 100/1000 births)
versus an otherwise identical configuration with mutation probability zero.
Run each for seeds 0, 1, 2, 3, 4 and 5,000 ticks. Do not tune defaults after
viewing results within this campaign. Record all outcomes, including extinction.

Primary descriptive measures: terminal population, mean population over the
last 1,000 ticks, total births/deaths, extinction tick, terminal movement trait
mean/variant count, surviving founder count, and maximum generation. Inspect
founder offspring ranges to verify differential reproductive outcomes. Compare
initial and final trait means without declaring improvement from that alone.

Controls do not remove selection or initial genetic variation. Matching seeds
matches initial conditions, but later RNG streams can diverge between treatments.
Five seeds support a preliminary descriptive comparison, not a robust estimate
of mutation benefit or causal adaptation. No significance test is planned.

Run from the repository root after installation:

```sh
python scripts/run_v0_campaign.py --output data/campaign-001
```

Each run logs every tick and samples replay every 50 ticks. The campaign writes
incremental `results.json` and a final `results.csv`. Existing output paths are
rejected. Report engine commit and source hashes from each run's metadata.
