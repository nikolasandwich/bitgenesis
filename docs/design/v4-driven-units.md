# Open energy boundary for fixed V4 units

v4-driven-1 wraps the unchanged v4-local-1 interaction kernel. It is an open
energy model, not open-ended evolution. Unit positions and material labels
remain fixed; there is no birth, death, material synthesis or replication.
Implemented: deterministic driven steps and bounded v4-driven-run-1 persistence
with a separate input RNG. Independent input/transition reconstruction is available
through v4.driven_audit, reusing the independent local verifier.

Each site receives a nonnegative integer energy proposal specified externally.
At empty sites none is accepted. At occupied sites acceptance is limited by
capacity minus current energy. Rejected input never enters the system and is
reported separately. Existing states above capacity are invalid, not silently
clipped. A per-unit leakage charge then removes min(leak,current energy), after
which ordinary local bond formation, charging and synchronous transport occur.

    E_after = E_before + accepted_input - leakage - bond_costs

Transport preserves the capacity: a unit with post-charge energy e receives at
most four transfers, each no larger than(capacity-e)/8. Even ignoring its outgoing
transfers, the final energy cannot exceed capacity. No additional clipping sink
is necessary. This bound depends on the existing four-neighbor geometry/divisor.

With zero proposals and zero leakage, a capacity that admits the initial state
gives exactly the closed kernel's next state. With input, formerly inactive units
can reconnect. Such reactivation is driven by supplied energy and engineered
material affinity; it is not evidence of spontaneous replication.

The kernel consumes no random draws. Future runners must specify and preserve
external proposal generation separately from initialization so drive/no-drive
and exchange/no-exchange controls share the intended starting states. Record
accepted and rejected input, leakage, interaction costs, units and transition
components. Avoid calling proposal totals actual energy supply when capacity or
empty sites reject it. Engineering seed90300 covers randomized accounting/bounds.

Next implement bounded persisted drive schedules and independent reconstruction,
then preregister persistence/perturbation measurements. Static components and
continuing energy flow alone cannot meet the V4 replication/graduation criteria.
