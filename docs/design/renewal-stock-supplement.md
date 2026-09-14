# Renewal-stock observation supplement

This separate supplement contains original campaign-020 data and the complete
registered first-100-tick stock replay for all sixty worlds. The full twenty-campaign
archive remains immutable and does not include these later retrospective records.
Earlier campaigns and other retrospective datasets are not part of this supplement.
Tracked source/docs may discuss those datasets without including their raw files.

Read the [Chinese observation report](../research/renewal-stocks-020.md),
[supply-window analysis](../research/supply-windows-020.md), and
[exact capacity calibration](../research/renewal-capacity-020.md).
The replay uses 6,000 supplementary ticks, not new independent worlds. No V1 runtime.

## Build and verification

From a clean committed source tree with both datasets present:

```sh
python scripts/package_v0_renewal_stocks.py --output data/bitgenesis-v0-renewal-stocks-020.zip
```

The packager requires seven exact-report matches before writing a new archive.
It stores file hashes, source revision and an explicit dataset list. It checks
archive integrity after writing. A checksum sidecar is created. Existing outputs
are never silently overwritten.

After extracting into a new folder, run from its `bitgenesis` directory:

```sh
python -S scripts/summarize_v0_renewal_granularity.py --output data/fresh-metrics
python -S scripts/verify_v0_renewal_granularity_observations.py --metrics-verification data/fresh-metrics/summary.json --output data/fresh-observations
python -S scripts/summarize_v0_renewal_granularity_processes.py --output data/fresh-processes
python -S scripts/analyze_v0_supply_windows.py --output data/fresh-supply-windows
python -S scripts/calibrate_v0_renewal_capacity.py --output data/fresh-capacity
python -S scripts/verify_v0_renewal_stocks.py --output data/fresh-stocks
python -S scripts/summarize_v0_renewal_stocks.py --input data/fresh-stocks/summary.json --output data/fresh-stock-summary
```

Compare the outputs as complete parsed JSON with the corresponding committed
reports under `docs/research/results`. These commands use the Python standard
library, including sibling analysis helpers. The exact calibration reads archived
engine source for its hash; it does not import or execute that engine. A fresh
runtime installation, full replay, browser interaction or remote redownload is
not established by these analysis commands.

Delivery status at creation: packaging support prepared; archive creation,
fresh-extraction checks and remote delivery must be recorded separately after
success. Future commits do not modify a fixed source snapshot or archive.
