# Mutation calibration — the boundary rule is biased inward, not toward movement

Protocol and exact formula: `experiments/v0/mutation-calibration.md`. Calculation
started from clean commit `314ea77`, using the baseline 10% mutation-attempt
probability and integer perturbations from -100 through +100. All 1,001 parent
genomes were enumerated with rational arithmetic. This is not another population
experiment and contributes no simulated world ticks to the campaign totals.

| Parent trait | Expected child-minus-parent per birth | Probability of actual change |
| ---: | ---: | ---: |
| 0 | +505/201 ≈ +2.51244 | 4.9751% |
| 50 | +85/134 ≈ +0.63433 | 9.9502% |
| 100 | 0 | 9.9502% |
| 500 | 0 | 9.9502% |
| 900 | 0 | 9.9502% |
| 950 | -85/134 ≈ -0.63433 | 9.9502% |
| 1000 | -505/201 ≈ -2.51244 | 4.9751% |

The interior interval 100–900 has zero one-birth mean change. Near each endpoint,
clamping produces a mean change toward the interior. The drift at g is exactly
the negative of the drift at 1000-g, so averaging uniformly over all possible
parent traits gives zero directional drift. The attempt rate is not the actual
change rate: at a boundary, many attempts clamp back to the parent's value.

This rules out a simple claim that the documented one-step mutation operation
always pushes traits toward high movement. It does not determine the long-run
distribution under differential reproduction, spatial competition and mutation.
The earlier no-mutation and direct-competition experiments are stronger evidence
that high-movement success in the low-cost world does not require this clamping
operation at all.

Clamping still matters: it changes the distribution and change rate near either
edge. Keep it documented. Reflection, resampling or unbounded latent values would
be different mutation models, requiring new rules and a controlled comparison.

The complete exact/decimal table is in `results/mutation-kernel.csv`; the local
calculation provenance is in `data/mutation-calibration-001/calibration.json`.
