# V0 rules: v0-darwin-1

This is a designed-organism baseline, not spontaneous abiogenesis. A genome is
one integer in [0, 1000]: the per-thousand probability of attempting a random
cardinal move. Organisms have no food sensor or memory. Spatial position and
energy are state; only the genome is inherited. Initial genomes are uniform
integers, initial occupied sites are sampled without replacement, and each cell
starts with the configured food quantity.

Space is a 2D torus with one organism per cell. Cardinal neighbors have fixed
east, west, south, north order with duplicates removed for width/height two.
Food is an integer energy store with a per-cell cap. The environment receives
external energy through probabilistic regrowth: it is an open system.

Each tick:

1. Visit cells in row-major order. Draw a regrowth decision at each site, adding
   up to the configured quantity without exceeding capacity.
2. Shuffle IDs of organisms alive at tick start using the local seeded RNG.
3. Charge basal cost, limited to available energy. At zero energy die immediately.
4. Draw a movement decision from the inherited probability. If attempted, charge
   movement cost even if blocked. Death at zero occurs before movement/feeding.
   Otherwise choose a random neighbor, moving only if it is unoccupied.
5. Transfer up to the feeding rate from the current cell to the organism.
6. If energy reaches the birth threshold and an adjacent cell is free, choose a
   free neighbor, pay birth cost, split remaining energy (child receives floor
   half), copy the genome and optionally perturb it by a uniformly sampled
   integer in [-mutation_step, mutation_step], clamped to [0, 1000].

Each parent can reproduce at most once per tick. Newborns occupy space immediately
but act next tick. Failed reproduction due to crowding incurs no birth cost.
Mutations can be neutral (zero perturbation or clamping); the configured mutation
probability is the probability of a mutation attempt, not guaranteed change.
Death returns no energy to food because death follows exhaustion. There is no
age limit, predation, inherited energy bonus, fitness ranking or population cull.

Every tick must satisfy the exact integer identity:

`organism energy + food energy + cumulative dissipated energy = cumulative supplied energy`

Supplied energy includes initial organism/food stores and actual regrowth, not
regrowth lost to capacity. Dissipation includes actual basal, movement, and birth
payments. Reproduction and feeding are transfers. These checks run during every
recorded experiment, alongside bounds and occupancy checks.

Known modeling choices: death before feeding creates a starvation boundary;
asynchronous updates create local priority effects; mutation clamping can bias
edge traits; shared RNG streams diverge between experimental treatments. Paired
seeds match initialization but do not guarantee identical subsequent environmental
realizations. Long-run causal claims need multiple seeds and targeted controls.

Lineage records preserve genome, parent/founder IDs, generation, birth/death ticks,
offspring count, and final or last-observed energy/position. Events log births and
deaths; frames sample spatial states; aggregate metrics cover every tick. Detailed
movement/feeding event logging is not implemented. In-memory lineage and replay
storage currently bound practical run length; this is not a million-generation
engine yet.
