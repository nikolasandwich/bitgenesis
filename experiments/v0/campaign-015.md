# Campaign 015: conditional follow-up of neutral two-group endpoints

Preregistered after campaign 014. Include **all four** neutral worlds retaining
both groups at tick 3000, and no other worlds. These are outcome-selected follow-ups,
not new independent seeds or an unbiased sample of all neutral worlds.

| Movement cost | Initial B of 80 | Original seed |
|---|---:|---:|
| 1 | 72 | 1206 |
| 2 | 8 | 1200 |
| 2 | 72 | 1208 |
| 4 | 72 | 1208 |

Question: which of these four finite-window two-group endpoints still retains
both groups at 30000 ticks? All use original baseline parameters with the listed
cost/seed, fixed founder genome 250, mutation disabled and the original nested
founder label assignment. No introduction, reseeding or rules change.

Replay ticks 0–3000 from the original seed and compare every recorded metric/group
row exactly to the hashed campaign-014 reference. Stop and report a mismatch rather
than substituting another seed. Continue every case to tick 30000, even after group
loss or whole-world extinction. No optional stopping or duration extension.

Four executions compute 120000 ticks: 12000 repeat prior prefixes and 108000 extend
the observation window. The seed block is intentionally sparse and unbalanced,
including seed 1208 at two different costs; the exact case table defines the cohort.
These runs belong to campaign 014's trajectories and must not be pooled as new
replicates. Conditional selection enriches for unusually persistent labels.

Primary endpoints: A-only, B-only, both present or extinct at 30000; first A/B loss
and extinction ticks. Report each case separately, including all failures.
Secondary: group/population snapshots at 3000,10000,30000 and per-tick full metrics.
Retain prefix hashes and source provenance. No full spatial/event history is saved.

Both-present at a longer finite endpoint still does not prove stable coexistence.
Earlier label loss does not show functional superiority because all traits remain
identical. This is a study of observed lineage-label persistence, not species,
functional innovation, equilibrated rare invasion or a significance test.

```sh
python scripts/run_v0_neutral_followup.py --output data/campaign-015
```

Commit before running; use a new output directory. Add to formal execution totals
only after complete cohort verification. Preserve the four identities and the
conditional-cohort interpretation in all summaries.
