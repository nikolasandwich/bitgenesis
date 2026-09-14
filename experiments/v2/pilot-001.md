# V2 pilot001: construction and ecological viability

Status: preregistered before execution. Calibration only, not a claim that
indirect encoding outperforms direct encoding or that V2 has graduated.

Run all40 combinations: seeds82000..82004 × initial energy{640,1280} ×
renewal probability{15,30}/1000 × encoding{developmental,direct}. Each1000 ticks,
including after extinction. Config16x16,32 attempted founders,capacity24,
initial_food12,renewal_amount4,basal1,decision1,movement0,feeding_limit8,
birth_threshold=2*initial_energy,birth_cost0,mutation100/1000,direct_padding_cost0.
All intact. The energy/threshold pair is a bundled physiology intervention.
Genotypes use existing uniform per-coordinate initialization and mutation.
World rules v2-world-1; freeze clean source and protocol hash at launch.

Every attempted founder receives identical energy within paired encoding cells;
food and attempted sites use identical configuration/seeds. Different encodings
have different construction costs, genotype spaces and initialization draws;
this is not matched cost, matched phenotype or a causal encoding-benefit test.
Retain all failed founders/children, costs, failure loss, histories, successful
births, deaths, extinction ticks, generations and final populations. Independently
audit each run before inclusion. Do not select only successful developments.

A developmental cell is provisionally usable if at least4/5 worlds survive to1000
and each surviving world has at least one successful non-founder birth. Select
in this fixed order: (energy640,renewal15), (1280,15), (640,30), (1280,30).
Direct controls describe calibration differences and do not select a favorable
control after outcomes. If no cell qualifies, report no usable cell and register
a new calibration based on identified failure mechanisms; do not extend seeds.
Report failed-attempt reason counts separately for founders and offspring.

Per-run actor budget256000; maximum10,240,000 actor records. Retain full bounded
records. Dataset budget4GiB checked between runs; stop incomplete on reaching it
and do not treat a subset as the registered cohort. Future held-out seeds exclude
80000..82999. This pilot does not test developmental benefits, general adaptation
or ecology. A positive viability result alone is not V2 graduation.
