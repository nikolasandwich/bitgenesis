"""父层仅核验已保存正式证据；不导入科学模块、不抽票或执行物理。"""
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
FORMAL = BASE / "v4-study-047-formal"
RAW = FORMAL / "raw"
ARMS = ("continue_north", "withdraw_to_natural")


def read(p):
    return json.loads(Path(p).read_text())


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def hashes(mapping):
    for p, h in mapping.items():
        assert sha(ROOT / p) == h, p
    return len(mapping)


def strict(a, b):
    assert type(a) is type(b)
    if isinstance(a, dict):
        assert a.keys() == b.keys()
        for k in a:
            strict(a[k], b[k])
    elif isinstance(a, list):
        assert len(a) == len(b)
        for x, y in zip(a, b):
            strict(x, y)
    else:
        assert a == b


def main():
    start = time.monotonic()
    gates = {}
    for label, task in (("producer", "2.1"), ("verifier", "2.2"), ("engineering", "2.3"), ("formal", "3.1")):
        p = BASE / ("v4-study-047-" + label + "-review.json")
        o = read(p)
        assert o["task"] == task and o["independent_author_review"] is True
        assert o["verdict"] in (("APPROVED", "REJECTED") if label == "formal" else ("APPROVED",))
        strict(o["files_sha256"], o["files_sha256_after"])
        gates[label] = {"path": str(p.relative_to(ROOT)), "sha256": sha(p), "verdict": o["verdict"], "bindings": hashes(o["files_sha256"])}
        if label == "formal":
            gates[label]["scientific_evidence_verdict"] = o["scientific_evidence_verdict"]
            assert o["scientific_evidence_verdict"] == "PASS"
    seal = read(FORMAL / "validation-summary.json")
    assert seal["status"] == "READY_FOR_REVIEW"
    strict(seal["files_sha256"], seal["files_sha256_after"])
    sealed_count = hashes(seal["files_sha256"])
    manifest = read(FORMAL / "archive-manifest.json")
    archive = ROOT / manifest["archive_path"]
    assert sha(archive) == manifest["archive_sha256"]
    assert archive.stat().st_size == 4004651 and len(manifest["entries"]) == 325
    total = 0
    with tarfile.open(archive, "r:gz") as tar, tempfile.TemporaryDirectory(prefix="study047-formal-parent-") as tmp:
        members = {m.name: m for m in tar.getmembers()}
        assert set(members) == {e["member"] for e in manifest["entries"]}
        for e in manifest["entries"]:
            name = e["member"]
            assert not Path(name).is_absolute() and ".." not in Path(name).parts and members[name].isfile()
            content = tar.extractfile(members[name]).read()
            dest = Path(tmp) / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(content)
            assert dest.read_bytes() == (ROOT / e["source"]).read_bytes() == (ROOT / e["archive_copy"]).read_bytes()
            assert len(content) == e["bytes"] and sha(dest) == e["sha256"]
            total += len(content)
    assert total == manifest["original_bytes"] == 119528074
    routes = {}
    for route, status, source_count, size in (("producer", "complete", 1195, 57932524), ("verifier", "verified", 1241, 58047692)):
        meta = read(RAW / route / "metadata.json")
        strict([meta[k] for k in ("status", "mode", "completed_pairs", "physical_steps", "future_generator_ticks", "reconstructed_past_generator_ticks")], [status, "formal", 28, 1792, 448, 640])
        strict(meta["input_sha256"], meta["input_sha256_after"])
        assert hashes(meta["input_sha256"]) == source_count
        assert meta["time_limit_seconds"] == 600 and meta["storage_limit_bytes"] == 134217728
        assert len(meta["output_sha256"]) == 45
        for name, h in meta["output_sha256"].items():
            assert sha(RAW / route / name) == h
        request = read(RAW / "execution" / route / "request.json")
        result = read(RAW / "execution" / route / "result.json")
        assert request["scientific_invocation_ordinal"] == 1 and result["exit_code"] == 0
        assert request["git_before"]["status"] == result["git_after"]["status"] == ""
        assert request["git_before"]["commit"] == meta["git_commit"] == "a9efac4e57fd90e70ec3dbc33099b2f2a1272b4f"
        assert result["all_git_tracked_unchanged"] is True
        strict(request["source_sha256_before"], result["source_sha256_after"])
        assert hashes(request["source_sha256_before"]) == 201
        for name, h in result["raw_output_sha256"].items():
            assert sha(RAW / "execution" / route / name) == h
        actual_size = sum(p.stat().st_size for p in (RAW / route).rglob("*") if p.is_file())
        assert actual_size == size < 134217728
        assert 0 < result["wall_seconds"] < 600
        routes[route] = {"status": status, "steps": 1792, "future_generator_ticks": 448, "past_generator_ticks": 640, "input_bindings": source_count, "bytes": size, "wall_seconds": result["wall_seconds"]}
    names = list(read(RAW / "producer/metadata.json")["output_sha256"])
    for name in names:
        a, b = RAW / "producer" / name, RAW / "verifier" / name
        strict(read(a), read(b))
        assert a.read_bytes() == b.read_bytes()
    records = read(RAW / "producer/records.json")
    index = read(RAW / "producer/index.json")
    assert len(records) == 28 and len(index) == 100
    assert Counter(x["future_status"] for x in index) == {"complete": 28, "not_applicable_original_32_no_trigger": 72}
    assert all(x["future"] is None for x in index if not x["trigger"])
    assert len({x["seed"] for x in records}) == 14
    assert [sum(x["encoding"] == e for x in records) for e in ("east", "west", "south", "north", "homogeneous")] == [5, 3, 0, 9, 11]
    totals = {arm: Counter() for arm in ARMS}
    changed_q, changed_intervals, changed_metrics = [], [], []
    for record in records:
        case = read(RAW / "producer" / record["case"])
        for arm in ARMS:
            saved = case[arm]
            q = saved["new_copy_counts"]
            assert len(q) == 32 and all(type(n) is int and n >= 0 for n in q)
            assert q == [row["new_copy_count"] for row in saved["rows"]]
            assert [row["tick"] for row in saved["rows"]] == list(range(33, 65))
            runs = []
            for tick, n in zip(range(33, 65), q):
                if n >= 2:
                    if runs and runs[-1][1] == tick - 1:
                        runs[-1][1] = tick
                    else:
                        runs.append([tick, tick])
            expected = [{"start": a, "end": b, "length": b-a+1, "left_censored_at_boundary": a == 33 and saved["tick32_diagnostic"]["new_copy_count"] >= 2, "right_censored": b == 64} for a,b in runs]
            strict(saved["intervals"], expected)
            strict(record["intervals"][arm], expected)
            longest = max((b-a+1 for a,b in runs), default=0)
            assert saved["future_persistent10"] is (longest >= 10)
            assert record[arm + "_metrics"]["future_persistent10"] == int(longest >= 10)
            assert record[arm + "_metrics"]["longest_double"] == longest
            for k,v in record[arm + "_metrics"].items():
                totals[arm][k] += v
            totals[arm]["interval_count"] += len(runs)
            totals[arm]["qualified_endstates"] += sum(n >= 2 for n in q)
            totals[arm]["left_censored_intervals"] += sum(x["left_censored_at_boundary"] for x in expected)
            totals[arm]["right_censored_intervals"] += sum(x["right_censored"] for x in expected)
        for k, value in record["delta"].items():
            assert value == record[ARMS[1] + "_metrics"][k] - record[ARMS[0] + "_metrics"][k]
        label = record["encoding"] + "-" + str(record["seed"])
        if case[ARMS[0]]["new_copy_counts"] != case[ARMS[1]]["new_copy_counts"]:
            changed_q.append(label)
        if record["intervals"][ARMS[0]] != record["intervals"][ARMS[1]]:
            changed_intervals.append(label)
        if any(record["delta"].values()):
            changed_metrics.append(label)
    assert [totals[a]["future_persistent10"] for a in ARMS] == [0,0]
    assert [totals[a]["double_new_ever"] for a in ARMS] == [8,9]
    assert [totals[a]["after32_formation_supported"] for a in ARMS] == [1,2]
    assert [len(changed_q), len(changed_intervals), len(changed_metrics)] == [9,3,18]
    f = BASE / "v4-study-047-preflight-joint-validation/full-revalidated/execution.json"
    suite = read(f)
    assert suite["exit_code"] == 0
    strict(suite["files_sha256"], suite["files_sha256_after"])
    assert hashes(suite["files_sha256"]) == 5
    for name,h in suite["raw_output_sha256"].items():
        assert sha(f.parent / name) == h
    assert "Ran 1070 tests" in (f.parent / "stderr.bin").read_text()
    diagnostic = read(BASE / "v4-study-047-process-guard-diagnostic/epoch-3/probe-output/results.json")
    assert diagnostic["status"] == "RED" and diagnostic["required_rejections_missed"] == 36
    assert diagnostic["forbidden_calls"] == [] and diagnostic["route_cli_invocations"] == 0
    assert subprocess.run(["git","diff","--exit-code","HEAD","--","src","scripts","tests"], cwd=ROOT, capture_output=True).returncode == 0
    return {"scientific_saved_evidence_status": "PASS", "created_at_utc": datetime.now(timezone.utc).isoformat(), "claim_type": "SCIENTIFIC_EVIDENCE_ONLY", "task_completion_or_feature_go_claimed": False, "reviews": gates, "author_bindings": sealed_count, "restored_files": 325, "restored_bytes": total, "tar_sha256": sha(archive), "strict_scientific_files": len(names), "routes": routes, "arm_totals": totals, "changed_q_pairs": changed_q, "changed_interval_pairs": changed_intervals, "changed_metric_pairs": changed_metrics, "full_suite_reused_tests": 1070, "new_full_suite_run": False, "known_control_contract": "RED: uppercase Python process detection unresolved", "this_check_new_physical_steps": 0, "this_check_new_future_generator_ticks": 0, "elapsed_seconds": time.monotonic()-start}


if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=2))
