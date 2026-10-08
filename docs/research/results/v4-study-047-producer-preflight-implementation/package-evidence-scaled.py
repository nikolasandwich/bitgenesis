"""逐字节归档临时失败epoch，并将原目录移动至已确认忽略的保留区。"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

base = Path(__file__).resolve().parent
root = base.parents[3]
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
archive = base / 'raw-evidence-scaled.tar.gz'
files = sorted(p for p in base.rglob('*') if p.is_file())
expected = {str(p.relative_to(base)): sha(p) for p in files}
with tarfile.open(archive, 'x:gz') as stream:
    for path in files:
        stream.add(path, arcname=str(path.relative_to(base)), recursive=False)
with tempfile.TemporaryDirectory() as directory:
    restored = Path(directory)
    with tarfile.open(archive, 'r:gz') as stream:
        stream.extractall(restored, filter='data')
    actual = {str(p.relative_to(restored)): sha(p) for p in restored.rglob('*') if p.is_file()}
    assert actual == expected
raw = root / 'data/v4-study-047-implementation-evidence/producer-preflight'
subprocess.run(['git', 'check-ignore', str(raw / 'probe')], cwd=root, check=True, capture_output=True)
moves = []
for path in sorted(base.glob('*/*')):
    if path.is_dir() and path.name in ('failure-epochs', 'all-test-temporary-epochs'):
        destination = raw / path.relative_to(base)
        assert not destination.exists()
        destination.parent.mkdir(parents=True, exist_ok=True)
        original = str(path.relative_to(base))
        path.rename(destination)
        for name, digest in expected.items():
            if name.startswith(original + '/'):
                assert sha(raw / name) == digest
        moves.append(dict(original=str(base.relative_to(root) / original),
                          retained=str(destination.relative_to(root)), archive_prefix=original))
report = dict(archive=str(archive.relative_to(root)), archive_sha256=sha(archive),
              archive_member_sha256=expected, extracted_files_verified=len(actual),
              restored_bytes_verified=True, raw_directory_moves=moves,
              mapping_rule='execution.json旧路径通过归档同名成员恢复；移动只保留原始副本，不作为当前审查闭包依赖',
              data_v4_study047_exists=(root / 'data/v4-study-047').exists())
with (base / 'archive-map-scaled.json').open('x') as stream:
    json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
print(json.dumps(dict(archive=report['archive'], extracted_files_verified=len(actual),
                     moved_directories=len(moves), archive_bytes=archive.stat().st_size)))
