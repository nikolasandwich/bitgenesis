"""Run all fixed V3 pilot002 cells and audit every retained run."""
from collections import Counter
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import subprocess
from bitgenesis.v3.runner import run,save
from bitgenesis.v3.world import Config
from bitgenesis.v3.audit import audit


def main():
    if subprocess.check_output(['git','status','--porcelain'],text=True).strip():
        raise ValueError('clean source required')
    root=Path('data/v3-pilot-002')
    root.mkdir(parents=True,exist_ok=False)
    meta={'status':'running','planned_runs':40,'completed_runs':0,
          'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
          'protocol_sha256':sha256(Path('experiments/v3/pilot-002.md').read_bytes()).hexdigest()}
    save(root/'metadata.json',meta)
    results=[]
    initial_pairs={}
    try:
        for feeding,renewal,seed,recycling in product((8,16),(30,60),range(87000,87005),(1,0)):
            if sum(p.stat().st_size for p in root.rglob('*') if p.is_file())>=8*1024**3:
                meta['status']='storage_limit'
                return
            output=root/f'feeding-{feeding}-renewal-{renewal}-seed-{seed}-recycling-{recycling}'
            config=Config(width=16,height=16,founders=32,feeding_limit=feeding,renewal_per_thousand=renewal,recycling=recycling)
            summary=run(output,config,seed,1000,max_actor_records=256000)
            save(output/'audit.json',audit(output))
            final=json.loads((output/'final.json').read_text())
            extinction=None
            initial=json.loads((output/'initial.json').read_text())
            if recycling:
                initial_pairs[(feeding,renewal,seed)]=initial
            elif initial!=initial_pairs.pop((feeding,renewal,seed)):
                raise ValueError('paired initial state mismatch')
            if not initial['lineage']:
                extinction=0
            with (output/'steps.jsonl').open() as stream:
                for line in stream:
                    row=json.loads(line)
                    if not row['population'] and extinction is None:
                        extinction=row['tick']
            reasons={kind:dict(Counter(a['reason'] for a in final['attempts'] if not a['valid'] and
                     (a['parent'] is None)==(kind=='founder'))) for kind in ('founder','offspring')}
            results.append(dict(feeding=feeding,renewal=renewal,recycling=recycling,seed=seed,
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
