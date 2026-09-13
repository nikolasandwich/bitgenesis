# Campaign 015 — Follow-up of neutral two-group endpoints

All four neutral worlds with both labels present at tick 3,000 in campaign 014
lost one group by tick 4,765. The remaining group survived through tick 30,000.
The earlier endpoints were not evidence of stable coexistence.

| Movement cost | Initial B | Seed | A/B at 3,000 | First group loss | A/B at 30,000 |
| --- | ---: | ---: | --- | --- | --- |
| 1 | 72 | 1206 | 38/85 | B at 4,765 | 110/0 |
| 2 | 8 | 1200 | 38/50 | A at 3,625 | 0/79 |
| 2 | 72 | 1208 | 7/67 | B at 4,551 | 118/0 |
| 4 | 72 | 1208 | 29/11 | A at 3,812 | 0/42 |

All four also had just one group at tick 10,000. No world became extinct.
At the final endpoint each world had one founder lineage and one genome value.
A and B are inherited founder labels with the identical fixed movement trait
250 and mutation disabled; they are not species or different functions.

## Design and limits

The [protocol](../../experiments/v0/campaign-015.md) selected **every** qualifying
neutral endpoint before follow-up. Four executions ran the full 30,000 ticks:
120,000 computed ticks, including 12,000 replayed prefix ticks and 108,000
additional observation ticks. These are selected existing worlds, not four
new independent seeds. Seed 1208 occurs in two different conditions. Selection
on prior survival makes this an unbalanced conditional cohort; the four cases
cannot estimate an unconditional coexistence rate or a frequency effect.

The outcomes show loss within these particular finite trajectories. They do
not establish inevitable fixation for every possible world, a critical movement
cost, ecological coexistence, rare invasion, or open-ended evolution.

## Verification and reproduction

Clean execution source: `b5750541063ee8f5e68be0a8964552e95798f6ea`;
rules `v0-darwin-1`, Python 3.12.10. The engine was unchanged.

The independent record verifier checked all **120,004 metric rows** for group,
trait, population, founder and energy consistency, transition bounds and no
reappearance of lost groups. It reconstructed first losses, final outcomes and
all three observation snapshots. All **12,004 prefix rows**, including tick zero,
equal the campaign-014 records exactly; reference hashes equal the prior audit.
This checks recorded consistency, not a full individual/spatial history, which
was not retained. Hashes identify inputs; they are not external authentication.

```sh
python scripts/run_v0_neutral_followup.py --output data/campaign-015-new
python scripts/summarize_v0_neutral_followup.py --input data/campaign-015-new --output data/campaign-015-new-analysis
```

Requires the original campaign-014 raw CSVs under `data/campaign-014` (available
in the fourteen-campaign archive) and an installed local package. Output
directories must be new. The verifier uses only the standard library plus its
sibling verification script. The fifteen-campaign results postdate that archive.

[Compact records](results/campaign-015.csv) ·
[Verification and hashes](results/campaign-015-verification.json)
