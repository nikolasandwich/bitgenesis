# V2 engineering runs

```console
python -m bitgenesis.v2 --seed 81100 --steps 50 --output data/my-v2-check
python -m bitgenesis.v2 --seed 81100 --steps 50 --encoding direct --output data/my-direct-check
```

Use new directories. Optional JSON config contains V2 Config fields, including
explicit direct_padding_cost. These defaults are engineering choices, not a
registered scientific comparison. Different genotype initialization consumes
different initial draws; source hashes and actual RNG states are recorded.

Records retain every developmental attempt, including failed founders, parent
identity, inherited genome, constructed weights/history, energy allocation,
construction cost and failure loss. Successful lineage IDs need not be contiguous.
Events/actor ledgers are streamed; attempts and lineage stay in memory under the
declared horizon/actor limit. Development histories increase per-attempt size;
the actor limit is not a byte guarantee. Plan dataset budgets before studies.

The summary separates attempted/successful founders, failed attempts, successful
births, ecological deaths and construction/failure losses. Metadata binds V2
sources and the reused V1 controller source, Python version, configuration and
output hashes. Older V0/V1 commands and output schemas are unchanged.

The seed81100/default50-step smoke check recorded80 founder attempts,6 successful,
74 failed, zero offspring births and6 living at the end. This is an engineering
observation from one configuration, not a comparative evolutionary result.
Engineering seeds80000..81102 must be excluded from subsequent unseen evaluation.

Next: independently reconstruct development from genes and recorded budgets,
validate V2 life-history/energy records, then preregister a viability calibration
that retains all failed development rather than analyzing only successful births.
