# Campaign 021: larger resource buffers with identical initial food

Status at registration: not executed. Preserve `v0-darwin-1` and all historical
experiments. Change only the existing food_capacity configuration between each
capacity pair. This is a prospective new cohort motivated by retrospective
campaign-020 stock observations, not a replay of selected extinct worlds.

## Question, predictions and interpretation

Does increasing per-site storage capacity from 24 to 96 change finite-horizon
persistence under the three registered renewal patterns? Test a larger environmental
buffer, not isolated removal of cap loss. Capacity also changes retained stock,
future intake, population demand and subsequent stochastic trajectories. Capacity
96 remains finite and can still truncate arrivals; do not label it unlimited or
loss-free. Feeding rate stays 8, so larger stored stocks do not increase the
per-action feeding limit or guarantee timely access.

Directional prediction for the vulnerable threshold-40 condition: within each
renewal treatment, more paired seeds survive only under capacity 96 than survive
only under capacity 24. Report the three signed discordance counts separately;
zero or negative values do not support that prediction in the corresponding cell.
No significance threshold is specified and ten seeds do not establish a universal
benefit. The stronger claim that no seed is harmed is contradicted by any
capacity-24-only survivor. Equal survival with different populations or uptake is
not confirmation of the primary persistence prediction.

Threshold 160 supplies a matched robustness condition, not an assumed successful
control. Retain all outcomes even if both capacities survive. Do not pool the two
thresholds to conceal a null or reversed threshold-40 comparison. Differences
between renewal treatments are secondary descriptive context, not a new primary
ranking chosen after observing results.

## Frozen grid and budget

120 worlds: seeds 1800–1809 crossed with thresholds 40/160, capacities 24/96, and
renewal pairs (probability per thousand, packet) frequent-small=(60,1),
reference=(15,4), rare-large=(5,12). Nominal input is 0.06 per site-tick in all cells.
Every world executes exactly 10,000 steps including after extinction: 1,200,000
computed ticks. Ten initial seed blocks, not 120 independent initial environments.
No stopping at favorable outcomes, replacements or survivor-only extensions.

Keep 32x32, 80 founders at energy 24, fixed genome 250, mutation probability zero,
basal cost 1, movement cost zero, birth cost zero, feeding rate 8. Initial food is
zero during construction. Apply the original block-map algorithm using independent
Random(1,000,000+seed), with 213 sites at 24 and one at 8: initial food 5,120,
initial total energy 7,040. In capacity-96 worlds the same map is used; do not
fill the larger capacity initially. All twelve founder lists, maps and initial RNG
states per seed must be identical. Only configuration fields differ as registered.

## Outcomes fixed before execution

Primary: alive at tick 10,000 and first extinction tick with right censoring.
For every threshold/renewal/seed capacity pair, report both alive, capacity-96-only,
capacity-24-only or both extinct, retaining raw terminal populations. Publish all
60 pair records, plus the signed count of capacity-96-only minus capacity-24-only
for each of the six threshold/renewal cells. No survivor-only extinction average.

Secondary: populations at 100, 500 and 5,000; births at 100; maximum population
in ticks 0–100 and its earliest tick; cumulative uptake and actual added resources
at 100, 500, 5,000 and 10,000; food and organism energy at 100. Endpoint-added
resources include continued renewal after extinction, which must be labeled.

At first extinction or tick 10,000 if alive, additionally save global food,
cumulative added resources and uptake. Partition added resources into ticks
starting with a living population (including the extinction tick) and subsequent
empty-start ticks. Give each window's length; zero observed post-extinction ticks
for a survivor do not imply permanent survival. These partition summaries are
secondary and must not replace fixed-horizon outcomes.

Retain all 10,001 standard metric rows, full initial states/configurations,
provenance, complete/failed/interrupted status, and all early feeding/terminal/
individual-energy records for action ticks 1–100. Keep all 120 worlds. No new
full-map/RNG stock replay or terminal-local observation is registered here.
If further spatial observation becomes necessary, register it separately.

## Engineering and independent verification gates

Commit this protocol and validated runner before launching the cohort. Engineering
uses seed 23 outside 1800–1809. Test all twelve configurations against plain World
for 100 ticks with full state/events/lineage/RNG equality. Existing observers must
accept and validate capacity 96 rather than assuming 24. Test near/full-capacity
truncation at both capacities and verify identical initial energy/maps. Preserve
old runner behavior and frozen-engine regression.

Before interpretation, independently reconstruct initial maps, founders/configs
and RNG; check complete twelve-way pairing. Check every metric row, nonnegative
supply/uptake, population/lineage accounting, food bounds 1,024*capacity, supplied
increment at most 1,024*packet and dissipated increment exactly prior population.
Verify uptake at most 8*prior population and zero uptake after extinction. Rebuild
all endpoints, partitions and paired statuses from full rows, and reconcile JSON
and CSV summaries. Verify early individual records against metrics and actual
capacity/threshold configuration. Record hashes for inputs and verification code.

A failed replay or invariant check is an engineering failure, not biological
extinction. Preserve partial records with error/status and never overwrite failed
runs silently. Formal totals change only after complete results and verification;
this registration alone adds no executions or time steps.

## Decision after the result

If capacity-24-only survivors exist, reject per-seed monotone rescue for this
cohort. If signed discordance is nonpositive, do not claim support by switching to
population, uptake or a selected renewal subset. If positive, describe the finite
buffer intervention's effect in this cohort without asserting pure cap-loss
mediation. Do not automatically add another parameter sweep or more complex
biology to obtain a preferred result. V1 remains design-only under current scope.
