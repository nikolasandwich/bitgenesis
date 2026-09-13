# Campaign 002: fixed-trait intervention assay

Declared after campaign 001, before this assay. Campaign 001 showed trait means
concentrating near high movement probability even without mutation. This assay
asks whether demographic outcomes depend on inherited movement propensity and
on the designed cost of movement. It does not test food sensing.

Engine rules remain `v0-darwin-1`. Experimental intervention: initialize normally,
then set all founder genomes to one fixed treatment value and disable mutation.
The intervention and its timing are recorded explicitly; baseline experiments
and engine semantics are unchanged. Initialization consumes the same RNG draws.

Factorial treatments: trait = 0, 250, 500, 750, 1000; movement cost = 1, 4;
held-out seeds = 100–109; duration = 2,000 ticks. Other values come from
`darwin-baseline.toml`. Ten seeds per combination, 100 runs total.

Primary endpoint: mean population over the final 500 ticks, including zeros
after extinction. Also report extinction counts/ticks, births and generations.
Do not exclude unsuccessful treatments. This is a population-level fixed-trait
assay, not a competition invasion test or a proof of evolved adaptation.

Prediction: movement can improve access to undepleted food in the low-cost
environment; the advantage may weaken or reverse when movement becomes costly.
Subsequent environmental RNG streams need not match across traits; replicate
across seeds and report distributions without a preplanned significance test.

```sh
python scripts/run_v0_trait_assay.py --output data/campaign-002
```

Artifacts: per-run per-tick CSVs, aggregate JSON/CSV and protocol/provenance.
This assay does not export lifecycle/replay artifacts; campaign 001 does.
