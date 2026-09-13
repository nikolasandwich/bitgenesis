# Campaign 004: persistence versus turnover across resource regimes

Preregistered after campaigns 001–003. Question: do different resource supplies
produce extinction, continuing turnover, or crowded persistence without births?
Do not treat persistence alone as sustained evolutionary activity.

Unchanged `v0-darwin-1` dynamics. Change only regrowth probability to 10, 40, 200,
or 1000 per thousand site-ticks. All other values are baseline defaults, including
mutation. Seeds 300–304, duration 10,000 ticks: 20 runs / 200,000 ticks. The 40
treatment extends the baseline horizon on held-out seeds. The 1000 treatment
supplies each site every tick and intentionally probes a boundary condition.

Primary endpoints: population, births/deaths in the final 1,000 ticks, extinction
time, and most recent birth/death. Secondary: founder lineages, trait variation,
mean trait, generation and energy stores. Include all failures and zeros.

Predictions to test, not assumed results: scarce supply may cause extinction;
abundant supply may saturate occupancy, making reproduction space-limited and
allowing survival without generational turnover. V0 has no age-related death or
energy storage cap, so these choices may create a stationary demographic state
with accumulating energy. Report this if it occurs rather than adding mortality
mid-experiment to force evolution.

```sh
python scripts/run_v0_resource_regimes.py --output data/campaign-004
```

Outputs: streamed per-tick metric CSVs, aggregate JSON/CSV, and protocol/provenance.
Lifecycle events are consumed to count birth/death activity; full event and
replay files are not exported in this assay. Five seeds per regime yield bounded
descriptive evidence. No formal hypothesis test or universal phase boundary claim.
