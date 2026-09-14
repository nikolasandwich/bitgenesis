# V4 study003: refill versus material-pattern recovery

Preregister before seeds93000..93004. For each source run a300-step growing prefix
with16x16 periodic sites,occupancy250,max_energy64,initial_raw1,drive500/1000,
drive_amount8,capacity64,leak1,bond_cost1,exchangeTrue,threshold16,construction_cost4.
These are study002 driven/formation/exchange settings, without selecting successful
prefixes. Retain empty or partially occupied reference patches without replacement.

From each verified endpoint run four200-step branches: sham/removal crossed with
threshold16/65. Sham selects no removal sites. Removal selects x=6..9,y=6..9,
inclusive (16 sites). Extract units and their energy; leave raw stocks unchanged.
Formation-disabled branches change threshold only after the prefix. No other
parameter overrides. Preserve absolute ticks301..500 and both continued RNG streams.
Total planned:5 prefixes,20 branches. No source replacement or horizon extension.

The fixed reference is the prefix endpoint. On the16 patch sites, report initial
occupied count, boundary exports and each branch's occupied fraction. On the subset
occupied in the reference, report refill fraction and material-label matching
fraction. Empty reference denominators are null and remain in the cohort; conditional
means must state the number of defined sources. Empty current states count as zero
when the reference denominator is nonempty.

Primary descriptive endpoint is tick500 material-match fraction relative to the
reference. Per source report removal-minus-sham at each threshold, and threshold16
minus65 under removal. Give exact rational differences and source means (three
sets of five contrasts), without significance or graduation claims. Refill fraction
is secondary: restored occupancy must not be described as restored pattern.

Additionally report all three fractions at tick300 after the boundary and at
absolute ticks310,350,400,500. At each checkpoint compare each removal branch's
labels with its threshold-matched contemporaneous sham on reference-occupied sites;
a match requires both sites occupied and equal material. Also report outside-patch
reference matching to expose nonlocal consequences. All these comparisons use fixed
sites; label matches do not establish ancestry, function or shape equivalence.

Require independent full-prefix and branch reconstruction, exact cohort/configuration
coverage, boundary selection, matched before states and final RNGs. The cohort
observer must independently count matching/refilled sites without calling runtime
recovery.observe. Bind protocol, clean launch commit and source hashes. Archive all
cases including zeros/nulls. Site-record budgets:77056 per prefix,51456 per branch.
Check2GiB cohort output between bounded runs; stop incomplete on limit or errors.
One run can overshoot. No recovery experiment has been executed under this protocol.
