# Campaign 016: initial food geometry at matched energy

Question: at fixed initial total food, does spatial concentration change
establishment and finite-horizon survival under the same V0 dynamics?

Run seeds 1300–1309 in all three arms, 10,000 ticks each, with no optional
stopping, replacement seeds, rescue or extension. Thirty executions / 300,000
computed ticks. Only ten seed labels are used across the three treatments;
matching initialization does not make their later random draws matched.

Use the 32×32 Darwin baseline, 80 founders, energy 24, fixed trait 250, mutation
disabled and regrowth probability 15/1000. Other baseline settings are unchanged.
Construct the world with initial food zero, then set the specified food map once
before tick zero and add exactly 5,120 to supplied energy. Thus every arm begins
with 1,920 organism energy + 5,120 food energy = 7,040 total. The explicit
initialization intervention overrides the scalar initial-food field; record the
full food map and founding individuals. No intervention occurs after tick zero.

| Arm | Initial food map |
| --- | --- |
| uniform | Five units in all 1,024 cells. |
| dispersed | 213 cells at 24, one cell at 8, and 810 empty cells; assign via an independently seeded random permutation of all cell positions. |
| block | The identical multiset in contiguous row-major positions 0–213, translated on the torus by an independently chosen x/y offset. |

Use a separate `random.Random(1_000_000 + seed)` for layout, never the world's
generator. Dispersed shuffles positions 0–1023 and fills the first 214; block
draws x then y offsets with `randrange(32)` and translates those row-major cells.
Uniform consumes no layout draws. The world's placement, founder-trait draws
(later overwritten to 250), and RNG state therefore match across arms at tick zero.
Store a digest of that initial RNG state to check this pairing.

Primary observations: survival at 500, 5,000 and 10,000 ticks, and first
extinction tick, with every seed reported including failed worlds. Secondary:
final population, every-tick standard metrics, and starting occupied cells with
food / food energy underneath founders. These exposure measures are descriptive,
not independent samples or an isolated causal mechanism.

Dispersed versus block keeps the food-value multiset fixed and changes arrangement.
Uniform versus either concentrated arm also changes local amounts and empty-cell
frequency, so it cannot isolate arrangement alone. Endogenous later resource
replenishment and random draws may diverge. Ten seeds per arm cannot establish a
universal effect, equilibrium or evolved sensing; genomes are fixed throughout.

Save source/config provenance, initial maps and founders, every-tick metrics and
compact outcomes. Drain events to bound event retention; full death/movement
history and spatial replay are not exported. Commit this protocol and runner
before execution. Add totals only after verifying the complete grid and records.

```sh
python scripts/run_v0_food_geometry.py --output data/campaign-016
```
