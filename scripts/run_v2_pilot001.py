"""Run all fixed V2 pilot001 cells and audit every retained run."""
from collections import Counter
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import subprocess
from bitgenesis.v2.runner import run,save
from bitgenesis.v2.world import Config
from bitgenesis.v2.audit import audit


def main():
    if subprocess.check_output(['git','status','--porcelain'],text=True).strip():
        raise ValueError('clean source required')
    root=Path('data/v2-pilot-001')
    root.mkdir(parents=True,exist_ok=False)
    meta={'status':'running','planned_runs':40,'completed_runs':0,
          'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
          'protocol_sha256':sha256(Path('experiments/v2/pilot-001.md').read_bytes()).hexdigest()}
    save(root/'metadata.json',meta)
    results=[]
    try:
        for energy,renewal,encoding,seed in product((640,1280),(15,30),('developmental','direct'),range(82000,82005)):
            if sum(p.stat().st_size for p in root.rglob('*') if p.is_file())>=4*1024**3:
                meta['status']='storage_limit'
                return
            output=root/f'energy-{energy}-renewal-{renewal}-{encoding}-seed-{seed}'
            config=Config(width=16,height=16,founders=32,initial_energy=energy,
                          birth_threshold=2*energy,renewal_per_thousand=renewal)
            summary=run(output,config,seed,1000,encoding=encoding,max_actor_records=256000)
            save(output/'audit.json',audit(output))
            final=json.loads((output/'final.json').read_text())
            extinction=None
            initial=json.loads((output/'initial.json').read_text())
            if not initial['lineage']:
                extinction=0
            with (output/'steps.jsonl').open() as stream:
                for line in stream:
                    row=json.loads(line)
                    if not row['population'] and extinction is None:
                        extinction=row['tick']
            reasons={kind:dict(Counter(a['reason'] for a in final['attempts'] if not a['valid'] and
                     (a['parent'] is None)==(kind=='founder'))) for kind in ('founder','offspring')}
            results.append(dict(energy=energy,renewal=renewal,encoding=encoding,seed=seed,
                extinction_tick=extinction,max_generation=max((o['generation'] for o in final['lineage']),default=None),
                failed_reasons=reasons,**summary))
            save(root/'results.json',results)
            meta['completed_runs']=len(results)
            save(root/'metadata.json',meta)
            print(f'{len(results)}/40 {output.name}',flush=True)
        meta['status']='complete'
    except BaseException as error:
        meta.update(status='failed',error=f'{type(error).__name__}: {error}')
        raise
    finally:
        save(root/'metadata.json',meta)


if __name__=='__main__':
    main()
