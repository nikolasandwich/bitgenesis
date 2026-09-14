# Endpoint sampling and fixed-state probes

Implemented analysis components; not a formal outcome study. The first viability
pilot chose threshold80 and renewal15/1000. Its samples are not held-out evidence.

`sample_endpoint` first independently audits the input run, sorts living IDs,
then uses a separate Python Random(analysis_seed) to sample without replacement.
The sample is capped at the survivor count. It records the source hashes, actual
sample size, IDs, genomes, complete parent chain and actual founder genome from
the initial archive. No sample is selected for favorable behavior or ancestry.
Unchanged genomes remain eligible. Extinction returns no samples and a null
conditional estimate; it does not create a replacement controller or zero effect.
The function writes nothing to the source run and consumes no world random draws.

`action_distribution` computes exact rational probabilities from a fixed genome
and normalized input vector. Maximal outputs share probability uniformly. Blind
sets all food channels to zero; shuffled averages all24 permutations, preserving
identity and repeated-value multiplicities. The total-variation distance compares
five-action distributions on the same state. Occupancy is absent from this
controller interface; an occupied-target probe has the same intended-action
distribution, though realized movement in a world can differ.

Hand-designed test controllers establish arithmetic behavior only. Before formal
training, the protocol must freeze sample count, analysis seeds, physical probe
states, transformation/normalization, evaluation seeds and horizons, and nested
aggregation. Reproductive information value still needs matched competition and
ancestor/random-controller controls. These functions do not supply rewards or
change simulator reproduction.

Engineering seeds through70301 are reserved from later held-out evaluation.
