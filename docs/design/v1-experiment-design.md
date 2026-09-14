# V1 design contract informed by V0

**Experiment design; no V1 world is implemented.** The
[controller component contract](v1-controller-contract.md) now fixes and implements
the controller-level choices. This document resolves candidate
implementation choices and identifies the future experiment to preregister. It
does not report evidence that a sensory controller works or authorize a stage claim.

## The question worth adding complexity for

Does inherited use of local food information improve reproductive outcomes beyond
what an equally costly sensor-blind controller can achieve?

V0 already produces reproduction, trait sorting, persistence and extinction without
sensing. Those observations alone will not count as V1 success. A sensory response
must be measured separately from its consequences for reproduction.

| V0 evidence | Consequence for V1 design |
| --- | --- |
| [Population size and competitive success differ](../research/campaign-003.md) | Include direct competition; a large monoculture is insufficient. |
| [Neutral founder labels disappear](../research/campaign-005.md) | Keep equal-controller label controls; lineage fixation is not proof of a superior policy. |
| [Finite-trait worlds persist without mutation](../research/campaign-007.md) | Require an information intervention, not survival alone. |
| [Initial food changes establishment](../research/campaign-008.md) | Fix and report initial energy/food; retain failed training worlds in the accounting. |
| [Equal initial energy has different allocation effects](../research/campaign-009.md) | Match food and founder energy separately, not just their sum. |
| [Reproduction threshold changes survival and birth tempo](../research/campaign-010.md) | Match reproduction parameters across sensory controls; survival alone does not identify information value. |
| [Energy allocation explains substantial population differences](../research/energy-budget.md) | Charge matched controller costs in every relevant comparison. |
| [Spatial access and early aggregate uptake differ](../research/campaign-016.md#retrospective-early-energy-accounting) | Measure information-dependent behavior separately from global food intake; match initial layouts between sensory arms. |
| [Threshold × layout experiment](../research/campaign-017.md) | Fix reproduction threshold across ablations; reduced early births and improved survival do not by themselves imply sensory value. |
| [Zero-charge extinction counterexamples](../research/campaign-018.md) | Match movement charge within information contrasts; treat free movement as a declared environment choice |
| [Complete history keeps growing](../research/retention-benchmark.md) | Bound planned trials and recording budgets; do not promise indefinite runs. |

## Smallest candidate controller

Use seven integer inputs: food at the current site and east/west/south/north sites,
current energy, and a constant bias. Scale food to 0–1000 using capacity (zero if
capacity is zero), energy to 0–1000 using a separately declared fixed energy scale
(candidate: 160 units, clipping at 1000), and bias to 1000. Keep this scale identical
across treatment arms; changing a reproduction threshold must not silently change
the meaning of a controller input. The candidate scale is a design choice, not a
value optimized or validated by a V1 trial.
Absolute cardinal directions keep the first version free of orientation state.

Five outputs are rest/east/west/south/north. Each output is the dot product of its
seven inputs and seven inherited weights: **35 integer weights**, no hidden layer,
recurrent state or learning within an individual's life. Choose a maximum-score
action; break ties uniformly among maxima. This supplies a sensor/action interface
but never specifies which food reading should produce which movement.

Candidate initialization: weights independently uniform on integers [-100, 100].
Candidate mutation: on 10% of births, choose one of the 35 coordinates uniformly,
add a uniform integer perturbation in [-10, 10], and clip to [-100, 100]. This is
a designed search space, not an assertion that it is unbiased or biologically real.
Calibrate its boundary behavior before interpreting controller-weight distributions.

Candidate decision charge: one energy unit per evaluated controller, after basal
cost and before acting. If the organism reaches zero it dies before taking an
action. All intact, shuffled and blind controllers pay the same charge and retain
the same parameter count. Movement and reproduction have their separately logged
costs. This flat computational cost is an experimental convention, not a conversion
from CPU operations into biological energy.

For V1, use explicitly separated random streams for resource proposals, action
ties, mutation and sensor interventions. Their derivation and draw order become
versioned rules. A matched resource-proposal stream does not imply matched realized
food fields: different consumption and capacity clipping still change those fields.
Leave V0's existing random-stream rules untouched.

## Controls that distinguish the explanations

During evaluation, freeze genomes and disable reproduction mutations. Evaluate:

1. The sampled descendant controller with intact inputs.
2. The same controller with food inputs zeroed, retaining energy/bias inputs.
3. The same controller with the four directional food readings permuted at each
   decision; retain current-site food and energy. This tests directional information,
   not all sensing. Use its declared intervention RNG stream.
4. A parameter-randomized controller with the same dimension and weight range.
5. Recorded initial controllers and, separately, the actual founding controller
   of each sampled descendant, to distinguish sorting of initial variation from
   changes within a selected lineage.

Blind inputs change the input distribution, while permutation preserves the set
of neighboring food readings and randomizes their directional correspondence.
Some slots or the whole vector may remain unchanged on a draw. Neither
control answers every question alone. Apply interventions only in evaluation when
testing the information dependence of an already evolved controller.

Monoculture assays measure persistence, offspring and resource use. Competition
assays place intact and ablated copies into one resource-limited world with balanced
initial allocation. Swap group labels/spatial allocation and include intact-versus-
intact controls. All groups pay the same decision cost. Group identity must never
enter sensing, action scoring, feeding or reproduction logic.

## Sampling and evaluation units

Predeclare at least ten independent training worlds, held-out environment seeds,
training/evaluation horizons and resource conditions before outcome runs. No exact
seed block is assigned in this design document; the eventual preregistration must
name it and confirm it has not been used for tuning.

At the fixed training endpoint, sample descendants uniformly from living organisms
using an analysis-only RNG; do not pick the most prolific or best-looking lineage.
Archive the initial genome pool before training. Multiple sampled individuals from
one world are nested observations, not independent evolutionary replicates.

Report the fraction of training worlds that failed before producing an endpoint
sample. Do not silently drop them or invent a replacement genome. Present both the
all-training-world failure accounting and conditional controller evaluations.
Any additional seed or horizon after inspecting results belongs to a new study.

Primary evaluation observations: offspring, extinction and terminal group fractions
in direct competition, with initial denominators and all-world extinction reported.
Behavioral observations: action probabilities conditional on directional food,
alongside actions under sensor interventions. Observe them; never feed these measures
back as an external reproductive reward or ranking function.

## Gates before interpretation

### Separate information value from reproductive physiology

Campaign 010 changed only existing allocation/threshold parameters and produced
large survival differences with a fixed movement trait and no mutation. Therefore
the first V1 information contrast must lock the following within each comparison:
founder number and positions, initial food and founder energy separately, resource
parameters, basal/movement/decision costs, birth threshold/cost, energy division,
action schedule and input normalization. Save them in trial metadata.

The same sampled controller is evaluated under intact and intervened food inputs
with those parameters unchanged. Do not let the blind control use threshold 40
while the intact controller uses 160, or select different viability settings after
seeing either outcome. A later robustness experiment may cross sensory treatment
with thresholds, but its complete factorial grid and comparisons must be declared
before running, and each information contrast remains within one physiology.

The viability pilot can select a usable shared environment before the held-out
evaluation protocol is fixed. It does not justify changing V0 defaults or choosing
only favorable controller samples. Pilot outcomes and subsequent choices should
be recorded explicitly, including failed pilot conditions.

Report birth tempo and late birth/death turnover beside offspring and survival.
Campaign 010 shows that fewer cumulative births can accompany more endpoint
survival, and that late survival can include turnover without new functional
variation. These are distinct observations. Retain the direct competition and
information-intervention requirements above instead of turning survival into a
proxy for controller quality.

### Do not confuse cheaper movement with information use

Campaign 018 improved low-threshold survival by removing movement payment without
adding sensing, yet retained three block-layout failures. Thus free movement is
neither proof of useful information nor a guarantee of viability. Its early records
retain blocked attempts and changed birth/expenditure totals. Those quantities
must be interpreted in their changed trajectories, not as fixed-exposure effects.

If the separate viability pilot chooses movement cost zero, all information arms
in the main comparison still use zero, with the same decision charge and other
physiology. Do not compare an intact free-moving controller against a charged
blind controller. A later cost-robustness experiment must cross cost with all
information conditions, fix every cell and seed before execution, and retain null
or reversed contrasts. This does not change the proposed controller architecture
or establish a new stage's scientific success. Implementation is now authorized
by the expanded autonomous research mandate.

### Implementation and evidence gates

- First verify energy accounting, input/output bounds, mutation inheritance,
  tie behavior, observational isolation, same-seed replay and preserved V0 tests.
- Run an explicitly separate viability pilot. If every controller dies because
  costs or initialization make the assay unusable, record that failure and revise
  the design before preregistering outcome trials; do not tune on held-out seeds.
- Predeclare the comparisons and reporting method. Preserve null/reversed outcomes;
  a favorable example video is not sufficient evidence.
- Only make a bounded claim about inherited use of supplied information when it
  improves the relevant reproductive outcomes and depends on that information
  under controls. This is not emergence of sensors, memory, intelligence or life.

V1 remains separate `bitgenesis.v1` code with an explicit future command and new
rules/output versions. V0 research and its historical execution routes stay intact.

The [evaluation contract](v1-evaluation-contract.md) specifies candidate competition
endpoints, extinction handling, nested replicate aggregation, matched ancestor
information contrasts and fixed-state behavioral probes. Exact protocol fields
remain to be preregistered before any outcome run.

The [control identifiability review](v1-control-identifiability.md) specifies
candidate input timing, blocked-move costs and the limits of permutation and
random-stream matching. These remain design choices for future preregistration,
not runtime evidence.
