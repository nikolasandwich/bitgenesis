# Retrospective campaign-020 renewal-stock observation

Status at registration: not executed. This supplementary replay uses completed
campaign-020 outcomes; it is not a new prospective experiment or independent seed
cohort. No changes to V0 physiology, actions, resource rules or organism inputs.

## Question and complete observation window

The exact capacity calibration gives p*min(packet,24-stock) per site, conditional
on stock. Measure the actual distribution of pre-renewal stocks during ticks 1–100
in all sixty original campaign-020 worlds: seeds 1700–1709, block map, thresholds
40/160, and frequent-small/reference/rare-large renewal. Include all worlds even
if already extinct; mark whether population was positive at each tick's start.
The fixed window is chosen before this new stock observation, although original
outcomes and the earlier aggregate/process analyses are already known.

Replay exactly 100 ticks per world (6,000 replay ticks total), matching all 101
original metric rows. No extension, selected survivor subset or replacement seeds.
Retain a 25-bin histogram of stock before each renewal; bins must sum to 1,024 and
the weighted sum must equal the preceding metric food total. Resource renewal is
first in a tick, so the previous boundary is the pre-renewal stock state.

## Recorded quantities

For every world/tick, save identity, prior population, histogram, actual supplied
increment, and the three conditional expected added amounts computed on that same
histogram. Store rational numerator/denominator (or exact fraction strings), not
only rounded floats. Summed expected cap loss is nominal expectation 61.44 minus
the actual treatment's conditional expectation. It is an expected loss, not a
measurement of realized discarded resource.

To measure realized truncation separately, clone the pre-step RNG state into a
separate random.Random instance. Enumerate only its first 1,024 randrange(1000)
draws, which correspond to the original row-major renewal loop. Record successful
arrival count, uncapped successful-arrival energy, admitted energy and discarded
energy. Sampled admitted energy must equal the actual world's supplied increment;
uncapped = admitted + discarded. The clone must never replace, reseed or advance
the world's RNG. Preserve each pre-renewal full food vector and RNG state so a
standard-library verifier can independently reconstruct histograms and sampled
arrivals. This is a shadow read of the existing trajectory, not an intervention.

Retain per-tick start-population flags and report sums for all 100 ticks as well
as active-start and empty-start partitions. An extinction tick is active-start if
the population was positive before stepping; do not silently omit post-extinction
observations. Report all ten world-level values in every treatment cell; range or
mean summaries are descriptive, not confidence intervals. Do not rank individual
actions as independent evolutionary replicates.

## Integrity gates

Before replay, verify original metadata, initial states, and metric file hashes
against the campaign-020 metric report. Reconstruct initialization with unchanged
rules and compare founders, map, full config, initial metrics and RNG digest.
Record clean source commit, engine hash, protocol hash, original input hashes,
completed/failed status and output hashes. Keep partial failed outputs; a mismatch
is an engineering failure, not extinction. New output paths only.

Engineering uses seed 23 across all six configurations, outside outcome seeds.
Compare the recording route against a plain engine for every boundary: metrics,
full food, living/lineage state, events and world RNG. Exercise full-capacity,
near-capacity and empty-world cases; verify that shadow RNG draws do not mutate
world state. Commit the runner before executing the retrospective cohort.

Independent verification must reconstruct all 6,000 histograms from saved food,
all three exact conditional means, the 1,024 shadow draws per tick, sampled loss
identities, all original metric matches and complete cohort/window coverage.
Retained pre-step RNG states are not independently archived historical RNG states;
metric-prefix agreement alone does not certify unique stochastic paths. Engineering
plain-engine equality and source pinning provide the separate observer parity gate.

## Interpretation limits and delivery

The three means on a single histogram are one-step conditional calculations. They
are not counterfactual worlds: different renewal treatments would change future
stocks, feeding, births and RNG consumption. Neither conditional cap loss nor
realized discard uniquely mediates survival. The first 100 ticks do not represent
the full 10,000-tick resource history. This observation cannot establish sensing,
learning, adaptation or the benefit of a directional controller.

Publish the all-world report and compact summaries with explicit post hoc labeling.
Raw replay data remain a separately versioned supplement; the fixed twenty-campaign
archive is immutable. Formal campaign counts remain twenty / 964 executions /
8,840,000 computed ticks; account for these 6,000 retrospective replay ticks
separately. V1 remains design-only. No campaign 021 is registered here.
