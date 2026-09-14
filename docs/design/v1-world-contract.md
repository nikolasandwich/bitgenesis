# Experimental V1 world: v1-world-1

Status: a tested world with a [bounded persisted runner](../../experiments/v1/README.md),
not a completed pilot. Config defaults are engineering defaults, not a preregistered experiment.
The V0 engine is untouched. The controller uses `v1-linear-1`.

## Space and initialization

A finite torus has one organism per site and integer food bounded by capacity.
Dimensions are at least three, giving four distinct adjacent sites. Initial
food is uniform; founders occupy uniformly sampled sites without replacement.
Founders have independently initialized controller weights and explicit energy.
The initialization stream chooses positions first, then genomes in founder-ID
order. IDs are consecutive birth IDs; ancestry and original founder IDs persist.

## Randomness

Seven independent Python `random.Random` instances use integer seeds obtained
from SHA-256 of ASCII `v1-world-1:{decimal_seed}:{stream_name}`, digest interpreted
as an unsigned big-endian integer. Stream names are `initial`, `resources`,
`order`, `ties`, `sensors`, `birth`, `mutation`. Record Python version in future
run metadata: replay of Python helper algorithms across versions is not promised.

Resources draw `randrange(1000)` once per row-major site every tick, including
full sites and extinct worlds. Actor order uses `shuffle` on current living IDs
in insertion order. Every decision-eligible actor draws a sensor index in 0..23
then a tie ticket in 0..59 from separate streams, irrespective of intervention
or tie count. Successful birth chooses uniformly among free adjacent sites in
east/west/south/north order, then invokes the controller's mutation stream.
Equal resource proposals do not imply equal realized food. Sequential streams
do not guarantee corresponding descendant draws after demography diverges.

## One tick

1. Resource proposals add food up to capacity. Fix and shuffle preexisting actors.
2. Each actor pays basal cost, then decision cost, dying immediately at zero.
   Actual payment is capped by available energy. Dead actors cannot eat or act.
3. Read food and post-charge energy; intervene and select the controller action.
4. Directional attempts pay movement cost even when blocked. If alive and the
   target is free, move; rest pays no movement cost. There is no occupancy input
   or action masking. Feed up to the declared limit at the resulting site.
5. If energy reaches the birth threshold and a neighboring site is free, pay
   birth cost and transfer floor(remaining energy / 2) to the offspring, retaining
   the remainder. Configuration requires threshold >= birth cost + 2. Failed
   attempts without space pay no birth cost and draw no birth/mutation numbers.
   Offspring inherit the parent's intervention mode and act starting next tick.

## Accounting and current boundaries

Each step returns actual resource addition, expenses, total energy before/after,
and actor records including inputs, intervened inputs, tickets, action, blocked
status, intake and energy transferred to the child. The world asserts
`after = before + actual resource addition - actual costs` each tick. Individual
energy reconciliation and occupancy/resource bounds are checked in tests.

Birth events snapshot genomes and parentage; death events identify the charging
phase. The in-memory lineage retains endpoints and offspring counts. These are
components for a bounded recorder, not an indefinite storage design. A CLI,
on-disk metadata and streaming records now exist. A reusable independent audit,
pilot protocol and outcome assays remain outstanding. No adaptation claim follows
from engineered fixture controllers or deterministic replay.
