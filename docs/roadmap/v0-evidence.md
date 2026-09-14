# V0 graduation evidence

The six V0 criteria in the [roadmap](README.md) have concrete evidence below.
This supports the minimal Darwinian-world milestone. It does not graduate V1,
certify emergent life, or end the ongoing research project. The implementation
reviewed here is `bf3221a28f471d2d2eb259fc4a2bf04fcc6a93d6`; older experiments
retain their own source revisions and artifacts. Normalized V0 engine SHA-256 remains
`8f3ed33ad0ebe802c099e3e6f8ae61f9bcc526b98512f31f48ec40478fbfa7ff`.
The current 159-test suite passed at this review. This is a V0 milestone assessment,
not user acceptance or completion of the ongoing autonomous research goal.

| V0 criterion | Evidence to inspect | What it supports and what it does not |
| --- | --- | --- |
| Complete birth, action, feeding, reproduction and death loop | [World engine](../../src/bitgenesis/v0/engine.py), [ordered rules](../design/v0-rules.md), [campaign 001](../research/campaign-001.md) | Ten 5,000-tick worlds have thousands of births and deaths. Organisms, feeding and reproduction are explicitly designed. |
| Test boundaries, resources, energy and inheritance | [Darwin tests](../../tests/test_darwin.py): torus/unique neighbors, energy/occupancy across five seeds, inheritance with mutation disabled, mutation enabled, charge-before-feed and newborn scheduling | Checks concrete invariants and edge cases; does not exhaust all configurations. The full recorded-run audit also reconciles energy and life histories. |
| Reproduce events for fixed rules, seed and configuration | Same test module: frozen 120-tick digest and two-world event/state equality; [portable installation report](../research/results/portable-wheel-019.json) | A fresh installed archive reproduces the saved 1,000-tick demo events and metrics byte for byte. Evidence is for these checked trajectories/environments, not arbitrary future Python versions. |
| Retain genomes, parents, life dates, offspring, population, energy and metadata | [Recorded-run writer](../../src/bitgenesis/v0/runner.py), [independent artifact audit](../../src/bitgenesis/v0/audit.py), portable report above | The standard recording route retains the required records. Specialized research runners may deliberately omit events or spatial history and must state this limitation; summary-only runs cannot replace full-history evidence. |
| At least five declared seeds with inherited variation and differential reproduction, plus no-mutation control and extinction reporting | [Campaign 001 protocol](../../experiments/v0/campaign-001.md), its [report](../research/campaign-001.md), [all-seed trait counts](../research/results/trait-coverage-001.csv), [trait decomposition](../research/trait-change.md) | Five seeds in each arm; no extinctions in that campaign; founder direct offspring range includes zero and unequal positive counts. No-mutation controls retain initial genetic variation. Differential reproduction and demographic sorting alone do not isolate a causal trait advantage. |
| Basic world view, lineage inspection and explicit designed rules | Campaign-001 browser check, [lineage browser record](../research/results/lineage-browser-014.json), [rules](../design/v0-rules.md), [emergence note](../design/emergence.md) | Playback, coloring, individual/parent lookup and invalid-query recovery were exercised. This is not comprehensive browser or assistive-technology certification. |

The portable installation evidence concerns fixed archive source `eec26ab` and its
150 tests. The current 159-test suite includes later local-observer and spatial
consistency checks. These later tests are not part of the older full archive.
The [local-resource supplement](../design/local-resource-supplement.md), source
`779a28d`, supplies the retrospective data and five exactly reproduced extracted
reports. It has not been presented as another fresh runtime installation test.
Browser interaction evidence remains the explicitly dated lineage record above;
later review-page checks were static table/link and figure checks, not renewed
interactive browser acceptance. Current download and source-CI evidence is linked
from the [acceptance guide](../research/REVIEW.zh-CN.md).

## Mechanism evidence now available

| Question | Observed evidence | Boundary of the claim |
| --- | --- | --- |
| Are positive direct movement/birth charges necessary for every failure? | [Campaign 019](../research/campaign-019.md): four extinctions with both charges zero, paired high-threshold worlds alive at the horizon | Not necessary in these cases; no unique mediator or permanent-survival claim |
| Is global food exhausted at extinction? | [Terminal stocks](../research/terminal-resources-019.md): all seven extinctions retain positive food before and at death | Does not by itself establish local access |
| Are all adjacent food sites occupied at the final death? | [Local windows](../research/local-resources-019.md): all seven final actors have empty food-containing neighbors | Final basal death precedes movement; earlier crowding is not excluded |
| Does the last individual keep losing energy to births or blocked moves? | [Final traces](../research/last-survivors-019.md): no births, six without blocks and one with a single block in the last twenty actions | Outcome-selected individuals, not a population-history or sensory-benefit experiment |

Formal totals are nineteen campaigns / 904 executions / 8,240,000 computed ticks,
including 24 follow-ups and 212,000 declared prefix replay ticks. The spatial study
adds 337,368 separately recorded retrospective replay ticks, not independent worlds.
These counts are workload context, not a graduation criterion or evidence of novelty.

## Decision for further work

Keep V0 as a versioned experimental baseline. The current genome has 1,001
movement-probability settings and cannot mutate a new sensor or memory into
existence. More V0 runtime is useful only when it resolves a stated question;
longer survival or larger execution totals do not satisfy V1 criteria.

[Campaign 015](../research/campaign-015.md) illustrates a useful extension:
following all four selected neutral two-group endpoints resolved whether those
particular labels persisted longer. All lost one group before tick 4,766. This
does not establish stable coexistence or a general fixation theorem.

The [V1 proposal](../design/v1-proposal.md) and [evaluation design](../design/v1-experiment-design.md)
remain plans. V1 evidence is **missing** until a versioned controller runtime,
held-out comparisons and sensory interventions are implemented and evaluated.
V2–V4 and open-ended evolution also remain unimplemented. Passing the V0 gate
does not silently authorize changing the meaning of the preserved V0 rules.
