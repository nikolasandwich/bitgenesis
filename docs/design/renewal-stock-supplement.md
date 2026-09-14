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

## Verified delivery

Download the [renewal-stock draft](https://github.com/nikolasandwich/bitgenesis/releases/tag/untagged-b2e03308b93632de29aa)
with an authorized GitHub account. Source `99c4f62` is fixed: 824 payload files /
40,157,090 bytes. SHA-256:

```text
4d1482c8f49192c4f039d2599cbb4a142db3bc5c2c30400615aa9743038bd17d
```

All seven reports reproduce exactly in a fresh extraction. GitHub API sizes and
hashes match the local archive and sidecar. Source CI 34822173518 passed.
Evidence: [fresh extraction](../research/results/renewal-supplement-020.json) and
[remote assets](../research/results/release-renewal-020.json). No independent remote
redownload, fresh runtime installation or full replay is claimed for this delivery.
The archived guide predates this upload result; future commits do not change the
fixed source snapshot or archive.
