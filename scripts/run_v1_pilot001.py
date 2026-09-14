"""Execute the fixed V1 pilot-001 grid, retaining all failures and outcomes."""
import json
from hashlib import sha256
from pathlib import Path
import subprocess

from bitgenesis.v1.runner import run, save
from bitgenesis.v1.world import Config
from bitgenesis.v1.audit import audit


def main():
    root = Path('data/v1-pilot-001')
    if subprocess.check_output(['git','status','--porcelain'], text=True).strip():
        raise ValueError('pilot requires clean source')
    commit = subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip()
    protocol = Path('experiments/v1/pilot-001.md')
    root.mkdir(parents=True, exist_ok=False)
    metadata = {'status': 'running', 'git_commit': commit,
                'protocol_sha256': sha256(protocol.read_bytes()).hexdigest(),
                'planned_runs': 20, 'completed_runs': 0}
    save(root/'metadata.json', metadata)
    results = []
    try:
        for threshold, renewal in ((40,15),(80,15),(40,30),(80,30)):
            for seed in range(71000,71005):
                if sum(p.stat().st_size for p in root.rglob('*') if p.is_file()) >= 4*1024**3:
                    metadata['status'] = 'storage_limit'
                    save(root/'metadata.json', metadata)
                    return
                output = root/f'threshold-{threshold}-renewal-{renewal}-seed-{seed}'
                config = Config(width=16,height=16,founders=32,birth_threshold=threshold,
                                renewal_per_thousand=renewal)
                summary = run(output,config,seed,1000,max_actor_records=256000)
                verification = audit(output)
                save(output/'audit.json', verification)
                final = json.loads((output/'final.json').read_text())
                extinction = None
                with (output/'steps.jsonl').open() as stream:
                    for line in stream:
                        row = json.loads(line)
                        if row['population'] == 0 and extinction is None:
                            extinction = row['tick']
                results.append({'seed': seed,'threshold':threshold,'renewal':renewal,
                    **summary,'extinction_tick':extinction,
                    'max_generation':max((o['generation'] for o in final['lineage']),default=0),
                    'bytes':sum(p.stat().st_size for p in output.iterdir() if p.is_file())})
                save(root/'results.json', results)
                metadata['completed_runs'] = len(results)
                save(root/'metadata.json',metadata)
                print(json.dumps(results[-1]), flush=True)
        metadata['status'] = 'complete'
    except BaseException as error:
        metadata.update(status='failed',error=f'{type(error).__name__}: {error}')
        raise
    finally:
        save(root/'metadata.json',metadata)


if __name__ == '__main__':
    main()
