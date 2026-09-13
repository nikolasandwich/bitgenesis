# Mutation kernel calibration (not a world experiment)

Question: does the documented clamping rule itself impose a directional drift
toward high movement? Enumerate all 1,001 parent genomes and all uniformly likely
mutation perturbations under the baseline mutation attempt probability and step.
Use exact rational arithmetic for expectations before formatting decimal output.

For parent genome g, mutation attempt probability p and integer step s:

`E[child - parent | g] = p * (sum(clamp(g+d, 0, 1000), d=-s..s)/(2s+1) - g)`

Also calculate the probability that the child actually differs from the parent;
an attempted mutation can make no change. Check reflection symmetry between g
and 1000-g exactly. This is a finite enumeration of the specified kernel, not
a simulation of selection, an estimate of stationary population composition, or
another campaign to add to the experiment/tick totals.

```sh
python scripts/calibrate_v0_mutation.py --output data/mutation-calibration-001
```

Preserve the generated kernel table and provenance. Do not alter the baseline
mutation rule based on the calibration; any proposed alternative needs a separate
rules version and controlled comparison.
