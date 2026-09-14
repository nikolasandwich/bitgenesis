# Local-resource observer, schema 1

Research-only `LocalResourceWorld` layers on the pinned `EnergyWorld`; V0 organisms
receive no new inputs. It captures exactly one row per preexisting acting individual,
including individuals that die before feeding. It consumes no random draws.

The snapshot is after tick regrowth and earlier individuals' actions, immediately
before this actor's basal payment. It is not a simultaneous population snapshot.
Fields: observation_schema, tick, id, founder_id, position, energy_before_action,
and sites. Each site contains position, food and occupant_id (null means empty).
Sites contain the current position first, then unique neighbors in pinned E/W/S/N
order. A 2-by-2 world has three sites, not five. Food and occupancy are copied values.

This records available stocks, not chosen movement targets, paths, future resource
regrowth or successful feeding. An occupied neighbor is not a feasible immediate
move under the current rules, but the actor may stay, fail to attempt a move or die
before moving. Positive food at the current site does not rescue a basal-stage death.
Do not label this measurement a new sensor or an estimate of policy intelligence.

Drain local resources plus the three inherited streams after successful steps.
Failed-step partial buffers are not complete observations. Checkpoint resume is
not supported. The inherited engine-source hash guard remains active.

Engineering acceptance compares full state, food, occupied sites, lineage, events
and RNG against both the earlier observer and plain World; all three old streams
remain identical. Tests cover zero and positive costs, births, blocked full worlds,
lethal movement, immediate basal death despite food, deterministic regrowth,
sequential depletion and neighbor deduplication. A first test mistakenly used width
one, which V0 rejects; corrected to the valid 2-by-2 case without changing rules.
A boolean `local_capture_enabled` switch may be set between steps; false suppresses only the new local stream, while inherited streams continue and must still be drained. Invalid switch types fail before advancing. Toggle tests preserve state, RNG and old streams. The replay runner validates original initialization and every metric prefix, retains exactly twenty action ticks and twenty-one full boundary states, and records source/input/output hashes and failures. Full independent spatial-record reconstruction remains a separate gate.
