# V1 evaluation contract — outcomes before execution

Design only. This supplements the [controller design](v1-experiment-design.md).
No V1 runtime, pilot or outcome experiment exists. These are proposed analysis
rules to freeze in a future protocol, not measured results or an external fitness
function. The simulator must never read evaluation scores to allocate reproduction.

## Three claims that need different evidence

| Claim | Required comparison | Insufficient evidence |
| --- | --- | --- |
| A controller responds to supplied food information | The same genome and physical state under intact and intervened inputs | Different actions in different evolved worlds |
| That information has reproductive value in the assay | Intact versus intervened copies with matched physiology, including competition | A response to food or long survival alone |
| Evolution increased information dependence | Descendant information contrast versus its actual founding controller's contrast | Descendant ablation alone; the founder might already depend on information |

The last contrast is a difference of matched effects, not proof that one particular
mutation caused improvement. Initial-pool comparisons address sorting separately.
Randomized controllers retain the existing initialization distribution and are
sampled before evaluation, never screened for poor performance. All comparisons
use held-out environments, with the same evaluation mutation setting (disabled).

## Population outcomes and extinction

Each direct competition starts with equal group sizes (candidate: 40 and 40).
Pair runs by controller, environment and initial-position allocation, then swap
which treatment occupies each initial position. Treatment labels do not alter
world rules. Include identical-controller, intact-versus-intact allocation swaps.
Record persistent group ancestry so newborn membership is unambiguous.

At the fixed horizon H, preserve integer counts N_intact and N_control. Report
four mutually exclusive statuses: both present, intact only, control only, and
both extinct. A living singleton group has fraction 1 or 0; if both groups are
extinct, terminal fraction is null, never 0.5. A temporary lead is not fixation.

Candidate primary endpoint is signed terminal abundance per initial group:
D = (N_intact - N_control) / n0. Both-extinct worlds contribute D = 0 **and** retain
their separate extinction status. Thus a zero does not imply viable neutrality.
D is not bounded by [-1, 1] because reproduction can increase abundance beyond n0.
Present the raw counts and four statuses beside D; do not publish the score alone.

Secondary endpoints are cumulative births per initial group, death counts,
finite-horizon survival and late turnover. Births include all group descendants;
they are not the original founder's direct offspring. Count births over the same
H in every run; an extinct group's count remains unchanged after extinction.
Fix the late window before running. Do not switch the primary endpoint from D to
births or survival after seeing which one favors intact sensing.

## Replicates and unavailable samples

The independent evolutionary replicate is a training world. Freeze an endpoint
sample count k, sample living individuals uniformly without replacement using an
analysis-only RNG, and take all survivors if fewer than k remain. Record actual
sample size. No replacement world or genome is introduced after extinction.

For each controller and control type, average the paired allocation swaps within
each evaluation environment, then environments, then sampled controllers within
one training world. Report one summary per training world with all lower-level
rows available. Descendant and actual-founder contrasts use identical environment
and allocation sets before taking their difference. Extra descendants or evaluation
seeds improve conditional measurement; they are not extra training replicates.

An extinct training world has no endpoint controller: its conditional controller
estimate is null, not zero. Report training failure counts using **all** declared
training worlds as the denominator, beside the conditional estimates. An engineering
failure is a different status from ecological extinction. Preserve its files and
reason; any rerun must use the same declared inputs with an explicit replacement
link. Never silently drop failed evaluations from an average.

Report every per-training-world effect and its direction. Any uncertainty interval
must resample training worlds as clusters and retain their nested comparisons;
name the method, seed and repetitions in the protocol. Do not treat individual
actions, descendants or shared-environment assays as independent samples. With few
training worlds, intervals may be unstable; inspect the complete replicate table.

## Behavioral probes without trajectory confounding

Predeclare a separate physical-state probe collection with directional food,
current-site food and energy specified independently of evaluation outcomes.
Include equal-food and zero-food cases, asymmetric neighbors, occupied targets,
and the declared energy range. These are synthetic probes, labeled separately
from states actually encountered by organisms. They do not create a training task.

For each archived genome and probe state, compute the action distribution from
scores: maxima have equal probability, other actions zero. For shuffled input,
average over all 24 permutations of the four directional slots, including repeated
values with their permutation multiplicity. Blind inputs zero all five food slots;
energy and bias remain unchanged. This arithmetic check consumes no world RNG and
does not feed actions or rewards back into an experimental world.

Compare the intact and intervened action distributions on the same states. Also
report movement execution, blocked moves and payment deaths from world records:
a chosen food-directed action can fail to move or provide no reproductive benefit.
Off-trajectory probe responsiveness and on-trajectory reproductive value are
separate outcomes. Zeroed inputs can be outside the experienced distribution;
shuffling preserves neighboring readings but not their directional correspondence.
Neither intervention alone isolates every possible sensory mechanism.

## Protocol fields still to freeze

Before outcome execution, assign exact train/pilot/held-out seeds, k, H, environment
grid (including a changed resource distribution), input scaling and action timing,
random stream derivations, probe states, controls and randomized-controller counts,
recording limits, uncertainty method and minimum practically meaningful effect.
Name one primary sensory comparison; label other contrasts secondary or specify
multiplicity handling. Fix the interpretation rule before inspecting results.

A positive stage claim requires a reproducible reproductive information contrast,
a corresponding behavioral response, and the relevant ancestor/random controls.
A null or reversed result remains a valid completed experiment, but does not meet
that positive claim. Memory or a larger network must not be added to rescue it.
V0 rules and archived experiments remain unchanged.

The [control identifiability review](v1-control-identifiability.md) specifies
candidate input timing, blocked-move costs and the limits of permutation and
random-stream matching. These remain design choices for future preregistration,
not runtime evidence.
