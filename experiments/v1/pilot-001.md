# V1 pilot-001: bounded viability calibration

Status: registered design, not launched. This is a calibration pilot, not a
confirmatory test of evolution or information value. Registering it before
execution separates environment selection from later held-out evaluations.

## Fixed grid

- Rules: v1-world-1, controller v1-linear-1. Freeze the clean source commit and
  source hashes at launch after spatial/resource reconstruction passes fixtures.
- Seeds: 71000, 71001, 71002, 71003, 71004, unused as engineering or outcome seeds.
- Cross birth threshold {40, 80} with renewal probability {15, 30}/1000.
- Every cell runs all five seeds: 20 independent world executions, 1000 ticks
  each, including resource proposals after extinction. Same seeds across cells
  are paired environmental initialization, not additional independent seeds.
- Config: width16, height16, capacity24, initial_food12, founders32,
  initial_energy24, renewal_amount4, basal_cost1, decision_cost1,
  movement_cost0, feeding_limit8, birth_cost0, mutation_per_thousand100.
- All controllers initially random and intact; no ancestor filtering, sensory
  ablation or competition in this viability-only pilot. Mode/physiology comparisons
  for information value belong to the later preregistered study.
- Retain full runner records, metadata, audits and all failures. Per-run actor
  budget256000; at most5,120,000 actor records across the grid. Hard local
  dataset budget4GiB: pause between runs if the total reaches that amount,
  report incomplete coverage, and do not analyze an incomplete grid as complete.

## Measures and decision rule

Report every cell's five terminal populations, extinction ticks (null if still
alive), births, deaths, maximum generation and total actor/byte counts. Survival
means population>0 at tick1000; this does not prove useful sensing.

A cell is provisionally viable if at least4/5 worlds survive and each surviving
world has at least one non-founder birth. Select among viable cells in the
predeclared order (threshold40, renewal15), (80,15), (40,30), (80,30). This chooses
the lower resource renewal before the lower threshold, not the largest observed
population. If no cell qualifies, retain all results and register a new pilot
with an explicit rationale; do not silently extend or replace seeds.

Pilot findings may choose shared physiology for a subsequent experiment. They
cannot count as held-out support. Later training/evaluation seeds must be outside
70000..71999; their exact blocks, sampling, controls, horizons and analysis must
be fixed before those runs. No stage graduation follows from this pilot alone.

## Execution gate

Before launch: independent ledger/ancestry/decision audit, spatial resource and
movement reconstruction, all current tests, clean source revision, and an output
directory that does not already exist. Mixed-mode competition and controller
sampling are not prerequisites for this calibration but are required before the
later information-value assay. Do not modify this protocol after launch.
