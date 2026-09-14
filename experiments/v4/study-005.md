# V4 study005: inherited program variation and persistence

Preregister before seeds96000..96004. Cross five sources with mutation0/100 per
thousand and drive250/500 per thousand:20 ordinary hereditary runs. Use500 steps,
16x16 sites,occupancy250,max_energy64,initial_raw1,program_mode random,capacity64,
drive_amount8,leak1,bond_cost1,exchangeTrue,threshold16,construction_cost4,copy_cost1.
No seed replacement, survivor filtering or individual horizon extensions.

Lower input is an explicit energy comparison, not selected after inspecting these
sources. All four cases of a source share initial hereditary states and all
initial/final random stream states. Mutation0 is a negative control: surviving
programs must belong to the initial occupied-program set. A mutation may produce
an already present program, so event counts are not novel-program counts.

Primary descriptive endpoint: final units carrying a program absent from the
initial occupied-program set divided by256 sites. Empty worlds contribute0.
Report mutation100-minus0 per source at each drive level (10 contrasts), exact
rational source means, no significance/graduation threshold. This is bounded
variation persistence, not fitness improvement or open-ended innovation. Program
equality is not lineage identity; independent recurrence and reversion can occur.

For windows1..100 and101..500 inclusive, report mean occupied fraction, mean
distinct surviving programs, mean units carrying an initially absent program,
formation/dissolution/mutation counts, accepted/rejected input, leakage, bond,
construction and copy costs. Save exact initial/final program-count tables and
final material-label counts. Exclude programs sampled for initially empty sites
from the reference set: those programs never entered the world.

Require full independent hereditary audit, exact20-case configuration coverage,
frozen source/protocol binding, matched RNG states, full windows and independent
program counting without runtime expression code. Budget128256 site records/run;
2GiB cohort soft limit checked between runs, bounded overshoot possible. Stop
incomplete on error/limit; retain all outcomes. Scientific cases have not run.
Adaptive value requires a separately specified matched ancestral comparison.
