# V1 controller component, version v1-linear-1

Status: implemented and unit-tested component; no V1 world, pilot or evolutionary
outcome yet. This fixes the controller-level choices from the candidate design.

- Seven integer inputs: current/east/west/south/north food, post-charge live
  energy, bias. Food uses floor(1000 * food / capacity), with zero for zero
  capacity; energy uses min(1000, floor(1000 * energy / 160)); bias is 1000.
- Five action rows: rest/east/west/south/north, each seven weights in [-100,100].
  Initialization samples every integer weight uniformly and independently.
- Scores are integer dot products. A supplied uniform ticket in 0..59 selects
  a maximum by ticket modulo tie count. All tie counts 1..5 divide 60 exactly.
  The future world must draw a ticket even when there is only one maximum.
- A separate supplied uniform permutation index in 0..23 chooses the
  lexicographic permutation of east/west/south/north readings. The future world
  must draw this for intact and blind decisions too. Blind zeros all five food
  inputs; shuffled retains current-site food and energy/bias. Identity and
  repeated-value multiplicities remain; this does not remove all information.
- Every birth draws an integer in 0..999 from its mutation stream. Default
  threshold 100 selects one uniform coordinate and a uniform integer change
  in [-10,10], clipped to [-100,100]. Zero changes and boundary clipping can
  produce silent mutation attempts. Evaluation threshold zero still draws.
- Immutable genomes may be shared on unmutated births. There is no hidden
  state, lifetime learning, food-seeking reward, or occupied-action masking.

The component accepts externally supplied tickets so fixed-state probes need no
simulation RNG. World stream derivation, action scheduling, energy accounting,
CLI and records remain to be implemented and verified before a viability pilot.
Hand-constructed response fixtures test arithmetic only, not evolved behavior.
The V0 engine and its random-stream semantics are unchanged.
