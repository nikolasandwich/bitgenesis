"""父层工程验收：只读保存文件，不导入科学模块或生成随机数/物理步。"""
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import tarfile
import tempfile
import time

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / "docs/research/results"
ENGINEERING = BASE / "v4-study-047-engineering"
RAW = ENGINEERING / "raw"


def read(path):
    return json.loads(Path(path).read_text())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_hashes(mapping):
    for name, expected in mapping.items():
        assert digest(ROOT / name) == expected, name
    return len(mapping)


def strict(a, b):
    assert type(a) is type(b)
    if isinstance(a, dict):
        assert a.keys() == b.keys()
        for key in a:
            strict(a[key], b[key])
    elif isinstance(a, list):
        assert len(a) == len(b)
        for x, y in zip(a, b):
            strict(x, y)
    else:
        assert a == b


def verify():
    started = time.monotonic()
    reviews = {}
    for label, task in (("producer", "2.1"), ("verifier", "2.2"), ("engineering", "2.3")):
        path = BASE / f"v4-study-047-{label}-review.json"
        gate = read(path)
        assert [gate["verdict"], gate["task"], gate["independent_author_review"]] == ["APPROVED", task, True]
        strict(gate["files_sha256"], gate["files_sha256_after"])
        reviews[label] = {"sha256": digest(path), "current_bindings_verified": check_hashes(gate["files_sha256"])}
        if label == "engineering":
            for route in ("producer", "verifier"):
                expected = f"docs/research/results/v4-study-047-engineering/raw/{route}/metadata.json"
                assert gate["engineering_evidence"][route] == expected
                assert expected in gate["files_sha256"]
            for name in ("middle_withdrawal_inputs.py", "run_v4_middle_withdrawal.py", "verify_v4_middle_withdrawal.py"):
                assert "scripts/" + name in gate["files_sha256"]
    seal = read(ENGINEERING / "validation-summary.json")
    sealed_files = check_hashes(seal["files_sha256"])
    manifest = read(ENGINEERING / "archive-manifest.json")
    archive = ROOT / manifest["archive_path"]
    assert digest(archive) == manifest["archive_sha256"] == seal["archive_sha256"]
    assert archive.stat().st_size == manifest["archive_bytes"]
    assert len(manifest["entries"]) == 236
    total_bytes = 0
    with tarfile.open(archive, "r:gz") as stream, tempfile.TemporaryDirectory(prefix="study047-parent-restore-") as tmp:
        members = {member.name: member for member in stream.getmembers()}
        assert set(members) == {entry["member"] for entry in manifest["entries"]}
        for entry in manifest["entries"]:
            name = entry["member"]
            assert not Path(name).is_absolute() and ".." not in Path(name).parts
            assert members[name].isfile()
            content = stream.extractfile(members[name]).read()
            restored = Path(tmp) / name
            restored.parent.mkdir(parents=True, exist_ok=True)
            restored.write_bytes(content)
            assert restored.read_bytes() == (ROOT / entry["source"]).read_bytes() == (ROOT / entry["archive_copy"]).read_bytes()
            assert len(content) == entry["bytes"] and digest(restored) == entry["sha256"]
            total_bytes += len(content)
    assert total_bytes == manifest["original_bytes"] == 8251010
    route_results = {}
    for route, status in (("producer", "complete"), ("verifier", "verified")):
        meta = read(RAW / route / "metadata.json")
        assert [meta["status"], meta["mode"], meta["physical_steps"], meta["completed_pairs"], meta["future_generator_ticks"], meta["reconstructed_past_generator_ticks"]] == [status, "engineering", 64, 1, 32, 640]
        assert meta["time_limit_seconds"] == 600 and meta["storage_limit_bytes"] == 134217728
        strict(meta["input_sha256"], meta["input_sha256_after"])
        n = check_hashes(meta["input_sha256"])
        assert n == (1194 if route == "producer" else 1200)
        for name, h in meta["output_sha256"].items():
            assert digest(RAW / route / name) == h
        request = read(RAW / "execution" / route / "request.json")
        result = read(RAW / "execution" / route / "result.json")
        assert request["scientific_invocation_ordinal"] == 1
        assert request["git_before"]["status"] == result["git_after"]["status"] == ""
        assert request["git_before"]["commit"] == meta["git_commit"] == "931dd9e70f6b89813635f7d25e74cdc8cf42e0bf"
        assert result["exit_code"] == 0 and result["all_git_tracked_unchanged"] is True
        strict(request["source_sha256_before"], result["source_sha256_after"])
        assert check_hashes(request["source_sha256_before"]) == 201
        for name, h in result["raw_output_sha256"].items():
            assert digest(RAW / "execution" / route / name) == h
        storage = seal["storage"][route]
        actual_bytes = sum(p.stat().st_size for p in (RAW / route).rglob("*") if p.is_file())
        assert actual_bytes == storage["actual_route_bytes"] < 134217728
        projected = storage["case_bytes"] * 28 + storage["environment_bytes"] * 14 + storage["index_records_summary_bytes"] * 28 + storage["final_administrative_bytes"] * 4
        assert projected == storage["conservative_projected_full_storage_bytes"] < 134217728
        route_results[route] = {"status": status, "exit_code": 0, "wall_seconds": result["wall_seconds"], "source_bindings": n, "physical_steps": 64, "future_generator_ticks": 32, "past_generator_ticks": 640, "actual_bytes": actual_bytes, "projected_bytes": projected}
    scientific_files = ["cases/east-120005.json", "environments/120005.json", "records.json", "index.json", "summary.json"]
    for name in scientific_files:
        a, b = RAW / "producer" / name, RAW / "verifier" / name
        strict(read(a), read(b))
        assert a.read_bytes() == b.read_bytes()
    index = read(RAW / "producer/index.json")
    statuses = Counter(row["future_status"] for row in index)
    assert len(index) == 100 and statuses["not_run_engineering"] == 27 and statuses["not_applicable_original_32_no_trigger"] == 72
    assert all(row["future"] is None for row in index if row["future_status"].startswith("not_"))
    record, = read(RAW / "producer/records.json")
    assert (record["encoding"], record["seed"]) == ("east", 120005)
    assert all(value == 0 for value in record["delta"].values())
    for arm in ("continue_north", "withdraw_to_natural"):
        assert record[arm + "_metrics"]["future_persistent10"] == 0
        assert record["intervals"][arm] == [{"end": 48, "left_censored_at_boundary": False, "length": 5, "right_censored": False, "start": 44}]
    fullpath = BASE / "v4-study-047-preflight-joint-validation/full-revalidated/execution.json"
    full = read(fullpath)
    assert full["exit_code"] == 0
    strict(full["files_sha256"], full["files_sha256_after"])
    assert check_hashes(full["files_sha256"]) == 5
    for name, h in full["raw_output_sha256"].items():
        assert digest(fullpath.parent / name) == h
    stderr = (fullpath.parent / "stderr.bin").read_text()
    assert "Ran 1070 tests" in stderr and stderr.rstrip().endswith("OK")
    assert not (ROOT / "data/v4-study-047").exists()
    assert read(RAW / "post-check/execution.json")["exit_code"] == 1
    assert read(RAW / "post-check-v2/execution.json")["exit_code"] == 0
    source_diff = subprocess.run(["git", "diff", "--exit-code", "HEAD", "--", "src", "scripts", "tests"], cwd=ROOT, capture_output=True)
    assert source_diff.returncode == 0
    return {"status": "PASS", "created_at_utc": datetime.now(timezone.utc).isoformat(), "claim_type": "TASK", "task": "2.3", "reviews": reviews, "author_sealed_files_verified": sealed_files, "restored_files": 236, "restored_bytes": total_bytes, "archive_sha256": digest(archive), "scientific_files_equal": scientific_files, "routes": route_results, "saved_index_statuses": dict(statuses), "regression": {"tests": 1070, "original_exit_code": 0, "current_source_hashes_verified": 5, "reexecuted": False}, "source_diff_exit_code": source_diff.returncode, "formal_directory_exists": False, "this_parent_check_new_physical_steps": 0, "this_parent_check_new_future_generator_ticks": 0, "elapsed_seconds": time.monotonic() - started}


if __name__ == "__main__":
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
