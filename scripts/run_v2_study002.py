"""Execute the preregistered paired V2 population cohort, retaining failures."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess

from bitgenesis.v2.audit import audit
from bitgenesis.v2.runner import run, save
from bitgenesis.v2.world import Config


def main():
    if subprocess.check_output(['git', 'status', '--porcelain'], text=True).strip():
        raise ValueError('clean source required')
    root = Path('data/v2-study-002')
    root.mkdir(parents=True, exist_ok=False)
    metadata = {
        'status': 'running', 'planned_runs': 20, 'completed_runs': 0,
        'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        'protocol_sha256': sha256(Path('experiments/v2/study-002.md').read_bytes()).hexdigest(),
    }
    save(root / 'metadata.json', metadata)
    results = []
    try:
        for seed in range(84000, 84010):
            paired_initial = None
            for mutation in (100, 0):
                if sum(p.stat().st_size for p in root.rglob('*') if p.is_file()) >= 8 * 1024**3:
                    metadata['status'] = 'storage_limit'
                    return
                output = root / f'seed-{seed}-mutation-{mutation}'
                config = Config(width=16, height=16, founders=32,
                                mutation_per_thousand=mutation)
                summary = run(output, config, seed, 3000, max_actor_records=768000)
                save(output / 'audit.json', audit(output))
                initial = json.loads((output / 'initial.json').read_text(encoding='utf-8'))
                if paired_initial is None:
                    paired_initial = initial
                elif initial != paired_initial:
                    raise ValueError('paired initial states differ')
                results.append({'seed': seed, 'mutation_per_thousand': mutation, **summary})
                save(root / 'results.json', results)
                metadata['completed_runs'] = len(results)
                save(root / 'metadata.json', metadata)
                print(f'{len(results)}/20 {output.name}: population={summary["population"]}', flush=True)
        metadata['status'] = 'complete'
    except BaseException as error:
        metadata.update(status='failed', error=f'{type(error).__name__}: {error}')
        raise
    finally:
        save(root / 'metadata.json', metadata)


if __name__ == '__main__':
    main()
