# Reconstructing the retained study005 cohort

The 2026-10-02 local checkout did not contain ignored raw study005 data. The user
explicitly authorized replay. Use the original revision, all twenty original
seed/drive/mutation combinations and the original 500-tick horizon. This computes
10,000 replay ticks and contributes **zero new independent samples**.

The archived full verification includes SHA256 digests of each world's initial
state, complete trajectory, final state and summary. Those 80 digests, rather
than summary agreement alone, authenticate reconstructed scientific payloads.

## Procedure

1. Create a clean detached worktree at `07a9ef4d3143e8d9f1f91dd127a31c8f4221c309`.
2. From that worktree, run `PYTHONPATH=src python scripts/run_v4_study005.py`
   with Python 3.12 or newer. Preserve all twenty cases and the original budget.
3. From the current checkout, run
   `python scripts/recover_v4_study005.py /absolute/path/to/worktree/data/v4-study-005`.
   The destination must not exist; failed imports remain explicitly incomplete.
4. Inspect `data/v4-study-005/reconstruction.json` before launching study009.

The importer checks cohort membership, original revision, clean replay source,
source hashes, all archived scientific payload hashes and independent physical
reconstruction. Only a byte-identical payload or the exact archived CRLF encoding
of the same payload is accepted. An arbitrary numerical or textual difference
fails import. The historical protocol hash is checked with the same restricted conversion.
Fresh independent audit results must match every scientific field of the archived
audit. Current and archived auditor code hashes are retained separately: not all
historical working-copy hashes are reproducible from the Git blobs. This is an
explicit provenance difference, not a claim of identical historical auditor bytes.

Per-run metadata records the actual replay Python version and source hashes; it
is regenerated metadata, not a recovered historical file. Original cohort
manifests are restored from Git only after their semantic comparison (allowing
verified protocol line endings) and all per-world checks. The reconstruction
report separately records the timestamp, script/archive hashes, encoding changes
and independent audit checks. Keep that report alongside any scientific results
that use the reconstructed trajectories. Neither replay nor format restoration
creates a new experimental cohort.
