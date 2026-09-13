# Campaign 004 — Extinction, turnover, and demographic arrest

Protocol: `experiments/v0/campaign-004.md`. Clean starting commit
`0f30f17482cf2a70916414281e4a8679da4a41ae`, Python 3.12.10. Twenty runs,
10,000 ticks each. All energy/occupancy invariants passed. Raw local outputs:
`data/campaign-004/`; compact CSV evidence is committed beside the other reports.

Each regime uses five seeds, 300–304. Regrowth probability is per thousand
site-ticks; each successful event supplies up to four energy units, limited by
the food cap. All other settings and dynamics remain the baseline.

| Regrowth probability | Final population range | Births in last 1,000 ticks | Surviving founders | Whole-world extinctions |
| ---: | ---: | ---: | ---: | ---: |
| 10/1000 | 0 | 0 | 0 | 5/5 |
| 40/1000 | 67–98 | 1,443–1,519 | 1 | 0/5 |
| 200/1000 | 480–509 | 5,189–5,310 | 3–4 | 0/5 |
| 1000/1000 | 1,024 | 0 | 80 | 0/5 |

Scarce supply caused extinction between ticks 83 and 136. Baseline supply
maintained turnover for twice campaign 001's horizon, but again only one founding
lineage survived. Higher stochastic supply retained 3–4 founding lineages at the
observed horizon; that is not evidence of permanent coexistence or new species.

Guaranteed supply exposed a designed boundary condition: all five worlds reached
full occupancy by ticks 22–24, and none recorded any deaths. All 80 founders
remained represented. There were no births or deaths in the final 1,000 ticks.
Total stored organism energy reached 24,947,035–25,623,560 by tick 10,000.

The mechanism follows directly from the implemented rules. Every site receives
four energy units each tick, while an organism pays at most two for basal plus
movement costs. At full occupancy all moves are blocked and no adjacent birth
site exists. There is no aging and no upper bound on energy storage. Thus
individuals can persist and accumulate energy without opening reproduction space.
This is demographic arrest, not a fixed state of every variable: energy keeps
changing while births, deaths and inherited traits stop changing.

This counterexample matters: a large population with many founder colors can be
less evolutionarily active than a smaller population with continuing turnover.
Do not add an ad hoc death rule during the experiment just to produce a more
interesting animation. Any later mortality/storage model needs a separate rules
version and a comparison with this preserved baseline.

V0 supports a narrow set of inherited strategies. These findings identify limits
of that model, not a general resource law for living systems. The sampling of four
regimes does not estimate a full extinction boundary or an evolutionary phase diagram.
