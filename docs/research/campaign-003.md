# Campaign 003 — The favored trait changes with movement cost

Protocol: `experiments/v0/campaign-003.md`. Started from clean commit
`d789db1`, Python 3.12.10. Eighty runs, 3,000 ticks each; every tick passed
invariants. Raw local output: `data/campaign-003/`. Mutation was disabled.

Group A has trait 250. Group B has trait 1000 in competition or 250 in neutral
controls. Group labels are inherited founder membership and have no engine
effect. Initial B is either 8/80 (10%) or 40/80 (50%). Each row uses seeds 200–209.

| Move cost | Initial B | Treatment | B only | A only | Both persist | Total extinction |
| ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 1 | 10% | Competition | 10 | 0 | 0 | 0 |
| 1 | 10% | Neutral | 0 | 8 | 2 | 0 |
| 1 | 50% | Competition | 10 | 0 | 0 | 0 |
| 1 | 50% | Neutral | 3 | 1 | 6 | 0 |
| 4 | 10% | Competition | 0 | 10 | 0 | 0 |
| 4 | 10% | Neutral | 1 | 9 | 0 | 0 |
| 4 | 50% | Competition | 1 | 7 | 0 | 2 |
| 4 | 50% | Neutral | 5 | 5 | 0 | 0 |

At low movement cost, high movement displaced low movement in all 20 competition
runs, including when initially rare. Neutral labels did not show the same pattern.
At high movement cost, low movement survived alone in 17/20 competition runs;
high movement survived alone once, and two whole populations became extinct.

This is evidence of environment-dependent differential reproductive outcomes in
the specified model, beyond simply observing one random founder survive. Ten
seeds per condition are preliminary frequencies; they are not exact invasion
probabilities or a universal ordering of all possible genomes.

Together with campaign 002, the low-cost result illustrates a distinction:
trait 1000 can spread in competition even though a separate fixed-250 population
supports more individuals. Selection is not programmed to maximize total
population size. These finite assays do not establish a general evolutionary
tragedy, optimality, intelligence or open-ended evolution.

Neutral labels sometimes both persisted for the full observation window and
sometimes one disappeared. Both persistence at tick 3,000 and total lineage loss
are observations at a finite horizon, not proof of stable coexistence or an
inevitable long-run outcome.

Next priorities: make the acceptance material easy to inspect, freeze replay
semantics, and test longer/contrasting resource regimes before increasing the
behavioral search space. Preserve null and extinction cases alongside successes.
