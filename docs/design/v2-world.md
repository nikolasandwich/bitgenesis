# V2 world integration: v2-world-1

Status: engineering implementation with a [persisted runner](../../experiments/v2/README.md),
not a scientific pilot. It forks
the V1 schedule into a separate module and uses a new RNG seed namespace. No V0
or V1 world rules change. The sensor/controller arithmetic remains V1's supplied
interface; each organism now retains both inherited genome and built controller.

## Construction as part of life history

Founders begin as attempted constructions with the configured initial energy.
Developmental encoding builds from ten genes; direct encoding reads35 weights,
charges expression and the declared fixed padding. Successful construction must
leave strictly positive energy. Only then does the organism enter the world.

A reproducing parent pays the existing birth cost and splits its remaining energy
in half (floor to the embryo). The embryo inherits a possibly mutated genotype
and pays construction from this transferred allocation. The parent retains its
share regardless of construction success. A successful child enters next tick;
failed attempts do not occupy a site or increment successful offspring counts.
The selected birth site and mutation draws occur even if construction fails.

For each attempt: allocation = construction cost + living energy + failure loss.
If construction is invalid or leaves no positive living energy, all unspent
allocation is dissipated as failure loss. This intentionally supplies no recycling;
it is a designed assumption requiring a separate future intervention, not an
inferred biological fact. No energy is silently refunded or given to newborns.

Attempt IDs are unique across successful and failed births. Consequently living
and lineage IDs can have gaps. Every attempt records parent, genotype, position,
construction history/reason, costs, failure loss and outcome. Successful birth
events and lineage are separate from invalid developmental attempts. Founder
failures remain in the original energy and attempted-founder denominator.

Initial energy accounting includes all attempted founders. Tick accounting
subtracts basal/decision/movement/birth charges, construction and failure losses.
Actor records distinguish transferred living child energy from development costs.

## Controls and limits

Engineering defaults allocate640 units per founder and use birth threshold1280;
they are not viability-tuned conditions or a preregistered study. Both encodings
receive identical configured initial energy and food. They have different genome
spaces and potentially different construction costs. Fixed direct padding is
explicit configuration; it does not automatically match each evolved developmental
program's cost. Matched per-phenotype controls must be separately specified.

Remaining work: independent development/life-history audit,
founder assignment controls, preregistered viability grid and scientific evaluation.
Do not reuse the V1 auditor for V2 events or its successful-founder assumptions.
Current tests establish arithmetic and replay under synthetic fixtures only.
