# Campaign 024: early sampled trait versus ancestor in direct competition

Status at registration: no campaign024 runtime, engineering fixtures or outcome
worlds exist. The question is chosen after campaign023's zero mean monoculture
survival contrast; this is a new prospective competition assay on known source
material, not an independent evolutionary cohort or a replication of that endpoint.
Commit this protocol before engineering or outcomes. Keep v0-darwin-1 unchanged.

## Question and interpretation

When early sampled and actual founding-ancestor traits share one resource world,
do sampled-trait lineages leave more living descendants at10,000 steps? Separate
homogeneous populations can have the same survival probability while differing in
competition. Conversely, competitive displacement need not increase persistence.
This comparison tests performance conditional on this opponent, starting frequency
and environment, not intrinsic fitness, selection mediation or new sensing.

Directional prediction: mean source-level signed terminal abundance contrast >0.
Zero or negative does not support the prediction. No significance claim is planned.
Retain all directions, extinctions and unchanged samples; no trait subset replaces
the primary comparison. Do not compare its numeric scale directly with campaign023's
survival-probability difference. A positive outcome is not a rescue of that null
result, whose question and conclusions remain unchanged.

## Fixed sources and evaluation grid

Use the exact committed campaign023 sample manifest and its independent sample
verification: all20 source seeds1900–1919, including all16 unchanged traits and
sampled founders. Bind both files by SHA256 in metadata and archive copies. Do not
resample or choose by campaign023 outcome. Use selected.genome and the recorded
actual founder_genome; do not transfer source age, position or energy. Missing or
corrupt files are engineering errors, not an opportunity to replace samples.
A manifest-declared unavailable source is retained as unavailable with no assay.
The current frozen manifest has20 available sources.

For each available source, replicates r=0..4 use seed
2100 + 5*(source_seed-1900) + r, giving2100–2199. These are new outcome seeds;
engineering uses24/25. Each replicate has two allocation runs, swap=0 and swap=1,
with the same seed and initial physical state before genotype assignment.
Maximum200 runs, each10,000 full ticks including empty worlds:2,000,000 computed
ticks. No added seeds, longer horizons, replacements or outcome-dependent stopping.

Initialize80 founders using the existing V0 initializer. Founder IDs0–39 are
sampled and40–79 ancestor for swap0; reverse membership for swap1. Assign their
traits accordingly in both living objects and initial birth events. Group identity
is derived exclusively from founder ancestry in observation/analysis, not added
to sensing, feeding, scheduling, genotype mutation or reproduction logic. Record
the complete founder-ID-to-group map. Descendants retain the group of their
founder, even when both groups have the same genotype.

Swap runs match founder positions, IDs, energy, food and RNG immediately before
trait assignment; only genotype allocation and the observer's group map differ.
Different-genotype trajectories can diverge. Same-genotype swaps must reproduce
identical physical records and complementary group observations exactly. Their
swap-averaged contrast must be exactly zero at every registered checkpoint; neither
identical run is deduplicated. This provides a neutral label/allocation check.

## Environment and recording

Use the same environment as campaign023:32x32 torus,80 founders at energy24;
initial_food0 followed by the existing deterministic block map (213 sites24 and
one site8), total food5120 and total initial supplied energy7040. Food capacity24,
regrowth15/1000 and amount4, feeding limit8, basal cost1, movement cost0, birth
threshold40, birth cost0, mutation probability0 and mutation step100. Preserve
V0 scheduling, energy division and all existing random draw rules. Group labels
must consume no RNG and confer no physiological difference.

Save config, initial food, founders, snapshot, RNG state and group map; full metrics
at ticks0..10000; complete birth/death events and final full lineage; final-state
digest, incremental/global results and clean source/protocol/sample provenance.
At every metric tick also save sampled/ancestor population and cumulative births/
deaths, deriving membership from founder ancestry. Birth counts exclude the40
original founders per group. Group sum must equal each corresponding world total.

Registered checkpoints:0,100,500,1000,5000,10000. Retain total and group population,
births/deaths, organism energy, founder-lineage count, maximum living generation
and living genotype histograms. Empty group mean genotype and max generation are
null; count/energy are zero. World food is shared, not artificially attributed to
one group. No complete spatial action-history claim. Record first whole-world
extinction and first group extinction (absorbing with mutation0 and no immigration).

## Primary analysis and secondary outcomes

For a run, D=(N_sampled-N_ancestor)/40 at tick10000. Use exact rational arithmetic.
This is terminal abundance per initial group size, not the founder's direct
number of offspring. It is not bounded to[-1,1]. Whole-world extinction contributes
D=0 and separately retains its both-extinct status; do not call it coexistence.

For each source, first average the two swaps within each replicate, then the five
replicates. Primary endpoint is the equally weighted mean of these source means.
Keep all200 run rows,100 swap-pair rows,20 source rows, and positive/zero/negative
source counts. Replicates and swaps share a source; they are not independently
evolved samples. Report unavailable sources out of the original20 and undefined
mean if no source is available. Engineering failure prevents complete-cohort
interpretation; retain files and diagnosis rather than silently dropping a run.

Secondary: four terminal group statuses (both present, sampled only, ancestor only,
both extinct); group fractions (null when both extinct); cumulative births per40
founders, first extinction times, and the same signed abundance at checkpoints.
Do not switch the primary from abundance to survival, births or a favorable window.
Do not pool swapped counts as independent evidence. No uncertainty interval or
p-value is planned for this exploratory but preregistered finite cohort.

## Engineering and independent gates

On engineering seeds24/25, verify same and different trait fixtures against plain
World for100 steps, including complete food/state/events/lineage/RNG equality and
no observer side effects. Include both allocations, traits at boundaries0/1000
and a nonboundary changed trait. Confirm assignment and initial events agree.

Before formal counting/publication independently check the exact source/replicate/
swap grid, initial group count40/40, config and pair mapping, and all10001 metric
rows. Reconstruct group ancestry through parent edges, enforce mutation0 inheritance,
life histories, per-tick group population/birth/death sums and checkpoint histograms.
Verify nonnegative resource/energy accounts and existing total-world invariants.
Recompute all run, swap, source and primary contrasts and terminal categories from
records. For all unchanged-trait sources verify identical physical event/metric/
lineage records (excluding observer group columns) and complementary group counts.
Publish complete outcomes and scope before increasing verified campaign counts.

No new controller, fitness reward, V1 runtime or changed V0 semantics is introduced.

Frozen manifest SHA256: `58fe9c9c7484da17db5d095fbeb93289903ffe5b801b7d3709a297f52a19c741`.
Independent sampling verification SHA256: `9aee4ba43d99b541da878fa26231cc78e484f2dcb51e103d45ea7705a63c0a68`.
