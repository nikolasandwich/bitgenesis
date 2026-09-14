# V3 boundary interventions and limits of resource compensation

Implemented: explicit between-step lineage removal and ordered B injection,
version v3-boundary-1. A persisted branched-assay runner and independent boundary
audit remain pending. This document is an engineering design, not a registered
ecological result or authority to reinterpret earlier pilots.

At the boundary after tick T and before T+1, removal exports all energy in living
members of a specified successfully constructed founder lineage. It frees their
occupied sites, records death at T and retains their ancestry/offspring counts.
Already-deposited A/B stays in place. Dead lineage members remain dead. Empty
living lineages produce a recorded zero removal; invalid founder IDs fail before
any operation. Export is an experimental sink, not feeding or ordinary death.

B additions follow removal and are ordered (site, proposed amount) pairs.
Each records pre-stock, accepted amount, capacity rejection and post-stock.
Rejected import never enters the world; it is not a second internal loss.
All input validation precedes changes. No simulation random stream is consumed.

    after energy = before energy - exported living energy + accepted B import

The operation appends an experimental_boundary event. It must be stored in a
separate assay schema and cannot pass as an ordinary v3-run-1 life history.
The original World.step rules and older experiment sources are unchanged.

## Intended branched mechanism assay

Start from one fully recorded common prefix, then copy the complete state,
including random streams and existing deposits. Compare an intact continuation,
lineage removal, and removal plus externally replayed donor B deposits.
Select the target using only the prefix under a separately registered rule;
keep unavailable targets and extinct cases instead of silently replacing them.

An intact reference can supply a fixed donor-release schedule. Replay retained
release from reference tick t at the boundary before t+1 at the recorded site.
This intentional one-step lag avoids pretending an absent donor has an actor
slot in a different shuffled population. The schedule is external experimental
input, not a behavior learned by recipients. Record its source hashes and all
accepted/rejected amounts. Do not adapt the schedule to treatment outcomes.

Removal also changes A competition, occupancy and subsequent actor ordering.
Resource replay restores neither these interactions nor necessarily the exact
amount of retained B: treatment capacity may clip additions differently.
Therefore call it a deposit-replay control, not a perfectly energy-matched world.
Report imported energy and rejected amounts before interpreting recovery.
Even full outcome recovery would support only this particular intervention
mechanism; it would not establish evolved mutual benefit or stable coexistence.

The first engineering checks cover descendant removal, untouched legacy stocks,
preserved RNG, capacity clipping, validation before mutation and continued base
step accounting. Seed85500 is reserved for these fixtures. Next implement full
branch persistence and independent intervention accounting, then freeze a bounded
source/target selection protocol before any scientific execution.
