# Local material conversion

`v4-material-1` is a separate deterministic primitive. It does not change the
closed or driven V4 baselines. It has not yet been composed into a persisted
driven runner or evaluated as a scientific cohort.

Each occupied site contains one unit, with one of four inherited material labels
and nonnegative energy. Each site can also store nonnegative integer raw tokens.
One unit and one raw token represent equal amounts of material. Raw tokens do
not carry energy in this abstraction.

The conversion boundary proceeds as follows:

1. Every zero-energy unit dissolves into one raw token at its site.
2. Each remaining unit receives an external direction ticket (east, west, south,
   north). Geometry is periodic. A proposal is eligible when the parent meets
   the energy threshold, the neighboring site is empty and it contains raw material.
3. All proposals aimed at the same target are rejected when more than one is
   eligible. There is no site-order winner and unsuccessful proposals cost nothing.
4. A unique eligible proposal consumes one target raw token and the construction
   energy cost. The remaining parent energy is split: floor-half goes to the
   new unit, the remainder stays with the parent. The new unit inherits the
   parent's material label. New units cannot propose within the same boundary.

Defaults are threshold 16 and construction cost 4. The threshold must be at
least cost + 2 so both resulting units retain positive energy. A site dissolved
in step 1 may be reused in step 4. All eligibility decisions precede formation.
The primitive draws no random numbers and does not modify its inputs.

The exact ledgers are:

    raw tokens + occupied sites = constant
    final energy = initial energy - successful formations * construction cost

The transition record retains dissolution sites and every proposal with its
outcome, plus energy and material totals. There is no material mutation yet.

Local templating is an engineered rule, including inheritance and the condition
for forming a unit. It is not evidence that replication emerged. There is no
group identity, group-copy command, prescribed organism boundary or group-level
selection in this primitive. A connected component splitting into two is not
by itself reproduction; it could simply be fragmentation or loss of a bridge.
Four fixed material labels also cannot support a claim of unlimited novelty.

The next composed dynamics must receive a new rules version, explicitly order
input, leakage, interaction and conversion, and retain direction RNG provenance.
Transition bonds refer to the pre-conversion interaction; they must not be
misreported as connectivity of the post-conversion population. Independent
reconstruction and material accounting should precede scientific experiments.
Any later structural replication assay needs temporal evidence of growth,
separation and persistence using observer-only measurements, with fragmentation
and disabled-conversion controls.
