# Research roadmap

Only V0 has runtime code, including a minimal Darwinian world. These stages are
research milestones, not release dates. Graduate only with reproducible evidence,
documented assumptions, and preserved earlier experiments. Failure to meet a
criterion is a useful result; do not add complexity just to move up a stage.

## V0 — Minimal Darwinian World

Assume explicit organisms, genomes, energy, and reproduction. Implement a finite
2D world with resources, action costs, feeding, death, inheritance, and mutation.
Use simple baseline actions without a hand-coded food-seeking strategy. Selection
comes from differential reproduction, never from an externally assigned score.

Graduation criteria:

- Demonstrate a complete birth -> action -> feeding -> reproduction/death loop.
- Test world boundaries, resource bounds, energy transfers/costs, and inheritance.
- Replaying the same seed, rules version, and configuration reproduces events.
- Record genomes, parent IDs, birth/death ticks, and offspring counts; retain
  population and energy time series with run metadata.
- Across at least five declared seeds, show heritable variation and differential
  reproductive success; include a no-mutation control and report extinctions.
- Provide a basic world view and lineage inspection. Explain every designed rule.

## V1 — Evolving Controllers

Genomes encode a small sensor-to-action controller. Start from random parameters;
do not encode `if food nearby: move toward food` or add a reward optimizer.

Graduation criteria:

- Sensor inputs and action outputs are explicit; mutations change controller
  parameters or topology through a documented genome mapping.
- Compare evolved descendants with ancestors and randomized controllers across
  at least five held-out seeds using survival/offspring observations.
- Disable or shuffle sensory inputs to test whether any apparent food response
  depends on sensing. Report null results and inherited versus engineered parts.
- Preserve the V0 baseline and its reproducible execution route.

## V2 — Development

Replace direct controller encoding with genome -> development -> organism.

Graduation criteria:

- Document local developmental rules, stopping conditions, and resource costs.
- Reproduce development under fixed seeds and validate the resulting structure.
- Show inherited genomic variation changing developed structure and measured
  behavior, with a direct-encoding control under matched resource budgets.
- Measure invalid developments and costs as well as successful outcomes.
- Keep V0/V1 experiments runnable with their original semantics.

## V3 — Ecology

Investigate multiple niches and interactions such as competition, predation,
cooperation, or parasitism without assigning desired ecological roles.

Graduation criteria:

- Track resource flows and lineage interactions under explicit accounting rules.
- Measure coexistence or turnover across at least five seeds over a predeclared
  observation window; do not infer stable species from color or appearance.
- Use removal or perturbation controls to test the proposed ecological mechanism.
- Separate imposed niches/roles from evolved differentiation in the results.
- Reproduce earlier single-population experiments.

## V4 — Self-Organization

Weaken explicit organism boundaries using interacting local units. Challenge
assumptions one at a time rather than deleting all scaffolding simultaneously.

Graduation criteria:

- State which organism, genome, sensor, and reproduction assumptions remain.
- Specify observable criteria for identifying a reproducing unit independently
  of any hand-assigned organism ID.
- Show persistent organization, inheritance, and variation under local rules,
  across multiple seeds and perturbations, with a suitable non-organizing control.
- Measure boundary-detection uncertainty and failed replication events.
- Preserve explicit-organism baselines and their experiment definitions.

## Later — Open-Ended Evolution

An open research direction, not a feature switch or a guaranteed destination.

Evidence required before making a bounded claim:

- Predeclare novelty/diversity/complexity measures, compute and resource budgets,
  observation horizons, and baseline/control systems.
- Observe continued meaningful innovation across multiple seeds and increasing
  time horizons; rule out mere random drift or exploitation of the metric.
- Publish plateaus, extinctions, counterexamples, and reproducibility materials.
- State the finite scope of evidence: a finite run cannot establish unbounded
  evolution. No final graduation criterion can certify it forever.
