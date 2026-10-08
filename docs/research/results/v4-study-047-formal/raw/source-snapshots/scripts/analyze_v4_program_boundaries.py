"""Join version-bound stage and member observers; never run new physics."""
import subprocess,time
from pathlib import Path
from scripts.analyze_v4_copy_episodes import analyze_case as phases
from scripts.analyze_v4_copy_members import analyze_case as members
OUTPUT=Path('data/v4-study-024')
GRID=[(g,e,s) for g in ('homogeneous','heterogeneous') for e in (False,True) for s in range(120000,120020)]
def require(v,m):
    if not v:raise ValueError(m)
def analyze_case(case,genotype):
    require(genotype in ('homogeneous','heterogeneous'),'genotype')
    label=f"seed-{case['seed']}-random-direction-exchange-{str(case['exchange']).lower()}"
    p=phases(case);m=members(case,label);events=[]
    for row in case['rows']:
        events.append(sorted([dict(child=row['site_ids'][v['target']],parent=case['final']['parents'][row['site_ids'][v['target']]],site=v['target'],material=v['material']) for v in row['physical']['material']['proposals'] if v['reason']=='formed'],key=lambda v:v['child']))
    return dict(genotype=genotype,seed=case['seed'],exchange=case['exchange'],phases=p,members=m,formations=events)
def summarize(records):
    require(all(type(r['seed']) is int and type(r['exchange']) is bool for r in records),'strict identities')
    require([(r['genotype'],r['exchange'],r['seed']) for r in records]==GRID,'complete ordered80 grid')
    out=[]
    for g in ('homogeneous','heterogeneous'):
        for e in (False,True):
            rows=[r for r in records if r['genotype']==g and r['exchange'] is e]
            steps=[s for r in rows for s in r['phases']['steps']];eps=[v for r in rows for v in r['members']['episodes']]
            out.append(dict(genotype=g,exchange=e,cases=len(rows),episodes=len(eps),double_steps=sum(len(s['final'])>=2 for s in steps),stable_pair_episodes=sum(v['stable_pair'] for v in eps),max_same_pair_run=max((v['max_same_pair_run'] for v in eps),default=0),all_new_double_steps=sum(s['new_only_count']>=2 for r in rows for s in r['members']['steps']),**{n:sum(s['crossings'][i] for s in steps) for i,n in enumerate(('dissolution_up','dissolution_down','formation_up','formation_down'))},hidden=sum(s['hidden'] for s in steps),nonzero_births=sum(v['material']!=0 for r in rows for step in r['formations'] for v in step)))
    return out

def main():
    from scripts.program_boundary_inputs import read,save,digest,bindings,source_cases
    require(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'clean launch')
    OUTPUT.mkdir(exist_ok=False);start=time.monotonic();records=[]
    meta=dict(status='running',planned_cases=80,completed_cases=0,saved_steps=0,new_simulation_steps=0,new_environment_sources=0,reused_environment_sources=20,new_independent_initial_worlds=0,time_limit_seconds=300,storage_limit_bytes=33554432,git_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
    try:
        meta['input_sha256']=bindings();save(OUTPUT/'metadata.json',meta)
        for genotype,path in source_cases():
            records.append(analyze_case(read(path),genotype));meta.update(completed_cases=len(records),saved_steps=32*len(records),elapsed_seconds=time.monotonic()-start)
            save(OUTPUT/'records.json',records);save(OUTPUT/'metadata.json',meta)
            require(meta['elapsed_seconds']<300 and sum(p.stat().st_size for p in OUTPUT.iterdir())<33554432,'budget')
        save(OUTPUT/'summary.json',summarize(records));meta['input_sha256_after']=bindings();require(meta['input_sha256']==meta['input_sha256_after'],'unchanged sources')
        meta.update(status='complete',elapsed_seconds=time.monotonic()-start,output_sha256={n:digest(OUTPUT/n) for n in ('records.json','summary.json')})
        require(meta['elapsed_seconds']<300 and sum(p.stat().st_size for p in OUTPUT.iterdir())<33554432,'final budget')
        save(OUTPUT/'metadata.json',meta)
        require(time.monotonic()-start<300 and sum(p.stat().st_size for p in OUTPUT.iterdir())<33554432,'serialized final budget')
    except Exception as exc:
        meta.update(status='failed',error=repr(exc),elapsed_seconds=time.monotonic()-start)
        try:meta['input_sha256_after']=bindings()
        except Exception as other:
            meta['finalization_error']=repr(other);meta['input_sha256_after']={};meta['input_read_errors']={}
            for path in meta.get('input_sha256',{}):
                try:meta['input_sha256_after'][path]=digest(path)
                except Exception as read_error:meta['input_read_errors'][path]=repr(read_error)
        meta['output_sha256']={p.name:digest(p) for p in OUTPUT.iterdir() if p.name!='metadata.json'}
        save(OUTPUT/'metadata.json',meta);raise
if __name__=='__main__':main()
