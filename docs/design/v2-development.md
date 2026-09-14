# V2 exploratory development component

Status: deterministic component and engineering fixtures only. V1 study001 has
only three surviving training sources, below its preregistered positive-stage
gate. V2 exploration is authorized independently; it does not certify V1 success.

## Question and supplied structure

Can a compact inherited developmental program generate a useful controller under
explicit construction costs, relative to direct encoding at matched budgets?

The first component holds the V1 seven-input/five-output interface fixed. Its
developmental sheet has5 rows and7 columns, one potential action/input coefficient
per site. Ten genes encode three initial site/amplitude pairs, diffusion, decay,
expression threshold and number of rounds. This deliberately supplies the sheet,
input/output roles and expression rule. It is not emergence of cells or sensors.

Sources initialize signed integer values, clipped sequentially to[-100,100].
Every synchronous round uses only self and four neighboring values from the
previous round. Missing neighbors at the closed sheet boundary equal self.
Mixing is ((16-4d)*self+d*neighbor_sum)/16, truncated toward zero; decay moves
toward zero. After1..16 rounds, nonzero sites reaching the inherited absolute
threshold become expressed connections. Others have zero weight. Locality is
on this engineered coefficient sheet, not the organism's world torus.

Each cell update costs1, so each round costs35. Each expressed connection costs1.
Insufficient round/expression budget yields an invalid zero-output structure,
with actual spent cost and history retained. Empty structures are invalid. These
are explicit conventions to test, not physical CPU-to-biological energy units.

## Next integration and controls

The world must eventually charge development to a declared resource budget and
distinguish unsuccessful births/development from ecological death. Existing V1
worlds and reproduction semantics will remain preserved. Do not simply deduct
35+ units from the pilot's24-unit founder energy and interpret inevitable failure
as evidence against development. Declare a development energy allocation and
match total starting resources in the direct-encoding control before outcomes.

Compare the developed coefficients against a direct representation of the same
coefficients to verify action equivalence first. Scientific comparisons must
report both genome dimensions and search-space differences; ten developmental
parameters and35 direct weights are different parameterizations. Budget-matched
controls must not quietly give direct encoding free construction.

Genomic initialization now samples each parameter uniformly across its declared
integer bounds. Each birth draws a probability ticket; default100/1000 mutates
one uniform coordinate by an integer in[-10,10] for amplitudes/threshold or[-1,1]
for other parameters, clipped to bounds. Silent mutations are retained.

A direct-construction component charges35 reading units plus nonzero expression
count. Optional explicit padding can match a reference development's spending;
the engineered equivalence test uses35*(rounds-1). This is an accounting/action
control, not an independently evolved direct-encoding population. Invalid read,
expression or padding budgets retain actual incurred costs and yield no controller.
World-level controls still need their own fixed matching policy before outcomes.

An [in-memory world](v2-world.md) now charges construction at founder and child
attempts and retains persisted invalid-attempt records. Still outstanding:
independent audit, matched direct-encoding cost
contract, pilot registration, behavioral/fitness assays and multiple-seed results.
The current fixtures are hand-designed arithmetic examples, not evolved organisms.
