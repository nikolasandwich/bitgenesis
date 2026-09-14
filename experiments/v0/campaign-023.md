# Campaign 023: early sampled trait versus its actual founder in a common environment

Status at registration: no samples extracted for this assay and no evaluation
worlds run. This is a prospective evaluation of existing campaign-022 material,
not a prospectively unseen training cohort. Commit before extraction/engineering.
Preserve v0-darwin-1, all earlier protocols, archives and V0-only runtime scope.

## Question and scope

Does a trait sampled from a mutation-enabled source population at tick 100 improve
finite-horizon population persistence when placed in a fresh common environment,
relative to its actual founding ancestor's trait? Campaign 022's mutation-enabled
survival difference does not answer this: enabling mutation changes subsequent
variation and RNG draws throughout the run. Here freeze the sampled genotype in
evaluation by disabling mutation in both arms.

The result concerns one sampled early trait per source, tested in homogeneous
founder populations. It is not the performance of the full evolved population,
late surviving descendants, individual competitive fitness, or isolation of
natural selection from mutation/drift. An advantage cannot establish a new sensory
function: the only inherited variable remains random movement probability.

## Frozen source and sampling rule

Use all twenty mutation_probability=100 worlds from campaign 022, source seeds
1900–1919. Bind extraction to the committed campaign-022 metric/history/checkpoint
reports and their original per-world input hashes. Do not choose source worlds by
terminal survival, terminal trait, population size, offspring count or a desired
result. The source outcomes are already known; this is not held-out training data.

Sample at post-step tick 100, before most of the registered 10,000-step horizon.
This fixed early window tests early variation, not late adaptation. Reconstruct
eligible living IDs from complete birth/death records: birth_tick <=100 and
(death_tick is null or death_tick >100). Include surviving founders as well as
descendants. Do not reject individuals whose genome remains 250.

For each eligible ID compute SHA256 of the UTF-8 ASCII string
`bitgenesis-c023-sample-v1:{source_seed}:{individual_id}` with decimal integers and
no trailing newline. Choose the smallest hexadecimal digest, breaking a collision
by the smaller ID. This deterministic pseudorandom priority is fixed before
extraction and independent of trait, offspring count and terminal survival.
Save every candidate ID/digest, selected ID, source seed, selected genome, birth
tick, founder ID and founder genome. Independently reconstruct the candidate set
and priority selection. Follow parent IDs to the actual founding ancestor rather
than substituting an unrelated random control; all source founders should verify
as genome 250. A sampled surviving founder is its own ancestor and is retained.

If a source has no living individuals at tick 100, record unavailable and run
neither arm for it. Do not replace it, carry forward dead individuals or impute
an evaluation extinction. Report available/20 sources prominently and identify
all missing sources. The primary comparison is conditional on available source
material. A missing input file or corrupt history is an engineering failure,
not biological unavailability. No source sample may be changed after evaluation.
Commit the extracted sampling manifest before outcome execution.

## Evaluation grid and maximum budget

For each available source, five replicates r=0..4. Evaluation seed is
2000 + 5*(source_seed-1900) + r, yielding distinct 2000–2099 if all sources exist.
Run sampled-trait and actual-founder-trait arms for each replicate, 10,000 steps
each including empty worlds. Maximum 20*5*2=200 worlds and 2,000,000 computed ticks;
actual budget is available_sources*100,000. No extra seeds, replacements, rate
sweeps, horizon extensions or outcome-dependent stopping.

Both arms use the existing campaign-022 common environment: 32x32, 80 founders at
energy 24, initial_food=0 during construction, identical block food from
Random(1,000,000+evaluation_seed), 213 sites at24 and one at8, total initial energy
7,040, capacity24, feeding8, basal1, movement_cost0, birth_cost0, threshold40,
regrowth_probability15, amount4, mutation_probability0 and mutation_step100.
All eighty evaluation founder genomes are set to the arm's selected trait or
actual founder trait; correct their initial birth events too. No source energy,
position, age, population size or history is transferred. This standardization is
an explicit intervention, not resuming the source world.

Within each replicate, initial positions, food, energy and RNG must match exactly.
Only founder genomes and corresponding birth events differ. Genome250 sampled
cases are still executed in both arms; their full recorded dynamics must be
identical, giving a natural identity-control gate. The frozen engine's future RNG
streams may diverge when different traits lead to different action paths.

## Primary outcomes and interpretation

For every evaluation: first extinction tick, terminal population and right
censoring at10,000. For each source, retain all five pairs and four categories:
both alive, sampled-only, ancestor-only, both extinct. Define source contrast
D_s=(sampled-only - ancestor-only)/5, equal to the difference in survival fraction.
Primary summary: arithmetic mean D_s across available sources, with every source
contrast and the numbers positive/zero/negative. If no source is available, the
primary summary is undefined and no efficacy conclusion is possible.

Directional prediction is mean D_s >0; zero or negative does not support it.
No significance test is specified. Replicates within a sampled source share a
trait and source history, so do not treat 100 evaluations as 100 independently
evolved traits. Any ancestor-only case contradicts per-case monotone advantage.
Do not restrict reporting to non250 traits or eventual source survivors. Such
subsets may only be labeled post hoc and cannot replace the primary comparison.

Predeclared secondary checkpoints:0,100,500,1000,5000,10000 with population,
births/deaths, living trait/variant count, founder lineages, maximum living
generation, food/organism/supplied/dissipated energy. Keep empty means/generations
null and extinct worlds in denominators. Save sampled-trait difference from the
founder as description, not an optimization score. Evaluation does not feed back
into source evolution or choose another source sample.

## Recording and verification gates

Save source manifest, per-evaluation initial config/food/founders/RNG and snapshot,
all10,001 metric rows, complete birth/death events, final full lineage, checkpoint
summaries, incremental results and clean code/protocol/manifest provenance. No
full spatial history claim. Retain errors/partial data; reject existing outputs.

Engineering seeds are23/24, outside evaluation seeds. Compare both same-trait and
different-trait fixtures against plain World for100 steps, with complete metrics,
food, events, lineage and RNG equality. Exercise traits0,250,1000 to check trait
bounds and record construction; these fixtures are not outcome evaluations.

Independent verification must reconstruct sampling from original hashed source
histories, ancestor chains and candidate priorities; check full declared available
evaluation grid and initial pairing. Verify all row counts, population/energy
accounts, nonnegative supply <=4096, food <=24576, basal dissipation equal prior
population, uptake0..8*prior population, absorbing extinction, no-mutation
inheritance and all birth/death/lineage relationships. Reconstruct checkpoint
traits and pair/source/primary contrasts. For identical sampled/ancestor traits,
require exact event, metric and lineage equality and matching initial RNG states.
Publish source availability and all outcomes before adding verified campaign
counts. No adaptive-improvement, selection-mediation or V1 claim follows from
engineering tests alone.
