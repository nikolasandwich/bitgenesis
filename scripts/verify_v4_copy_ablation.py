"""Independent dictionary physics, identity chains, and translated copy matching."""
from hashlib import sha256
import json
import math
import platform
from random import Random
from fractions import Fraction
from itertools import product
from scripts.copy_ablation_inputs import bindings,read,digest
from pathlib import Path

from bitgenesis.v4.exchange_branch_audit import physical_step
from bitgenesis.v4.structure_audit import reconstruct
from scripts.verify_v4_structure_copies import recount

OUTPUT=Path('data/v4-study-019')
MODES=('random-direction','random-feed','random-both')
GRID=tuple(product(range(120000,120020),MODES,(False,True)))


def require(value,message):
    if not value:raise ValueError(message)


def same(actual,expected,message):
    require(json.dumps(actual,sort_keys=True,separators=(',',':'))==json.dumps(expected,sort_keys=True,separators=(',',':')),message)


def verify_case(case):
    seed,mode,exchange=case['seed'],case['mode'],case['exchange']
    require(type(seed) is int and seed in range(120000,120020) and type(exchange) is bool and mode in MODES,'fixed case identity')
    rng_direction=Random(int.from_bytes(sha256(f'v4-copy-ablation-1:{seed}:directions'.encode('ascii')).digest(),'big'))
    rng_feed=Random(int.from_bytes(sha256(f'v4-copy-ablation-1:{seed}:feeds'.encode('ascii')).digest(),'big'))
    config=dict(width=16,height=16,capacity=64,leak=1,bond_cost=1,threshold=16,construction_cost=4,copy_cost=1,mutation_per_thousand=0)
    same(case['config'],config,'fixed configuration')
    units=[None]*256;raw=[0]*256;ids=[None]*256
    for identity,(x,y,material) in enumerate(((5,5,0),(6,5,0),(12,12,3))):
        site=16*y+x;units[site]=dict(material=material,energy=64,program=[material]*4);ids[site]=identity
    for x,y in ((5,6),(6,6),(5,7),(6,7)):raw[16*y+x]=1
    initial=dict(tick=0,units=units,raw=raw,site_ids=ids.copy(),observation=reconstruct(units,ids,16,16,'final'))
    same(case['initial'],initial,'fixed initial snapshot')
    initial_energy=sum(u['energy'] for u in units if u is not None)
    initial_mass=sum(raw)+sum(u is not None for u in units)
    parents=[None,None,None];rows=[];births=deaths=imported=rejected=spent=0
    require(len(case['rows'])==32,'all thirty-two steps')
    for tick in range(1,33):
        directions=[1 if site%16==6 else 0 for site in range(256)]
        if tick in (1,2):
            for x in (5,6):directions[16*(tick+4)+x]=2
        proposals=[8 if (site%16,site//16) in ((5,5),(6,5),(5,7),(6,7)) else 0 for site in range(256)]
        random_directions=[rng_direction.randrange(4) for _ in range(256)]
        random_feed=set(rng_feed.sample(range(256),4))
        if mode in ('random-direction','random-both'):directions=random_directions
        if mode in ('random-feed','random-both'):proposals=[8 if i in random_feed else 0 for i in range(256)]
        require(sum(proposals)==32,'fixed proposed budget')
        tape=dict(tick=tick,directions=directions,mutation_tickets=[[999,0,1] for _ in range(256)],
                  driven=dict(inputs=[dict(proposed=v) for v in proposals]))
        physical=physical_step(units,raw,config,tape,exchange)
        same(case['rows'][tick-1]['physical'],physical,'physical ledger and fixed tape')
        require(physical['energy_after']==physical['energy_before']+physical['imported']-physical['spent'],'step energy balance')
        require(physical['material_before']==physical['material_after']==initial_mass,'step mass conservation')
        prior_ids=ids.copy()
        for site in physical['material']['dissolved']:
            require(ids[site] is not None,'dissolution identity');ids[site]=None;deaths+=1
        for proposal in physical['material']['proposals']:
            if proposal['reason']=='formed':
                parent=prior_ids[proposal['source']];require(parent is not None,'formation parent')
                require(ids[proposal['target']] is None,'formation target vacant')
                ids[proposal['target']]=len(parents);parents.append(parent);births+=1
        units,raw=physical['units'],physical['raw']
        row=dict(tick=tick,site_ids=ids.copy(),physical=physical,observation=reconstruct(units,ids,16,16,'final'))
        same(case['rows'][tick-1],row,'full saved identity and partition row');rows.append(row)
        imported+=physical['imported'];spent+=physical['spent'];rejected+=physical['rejected_import']
    final=dict(tick=32,units=units,raw=raw,site_ids=ids,parents=parents)
    same(case['final'],final,'final units stocks identities ancestry')
    copies=recount(initial,rows,final)
    require(len(copies)==1 and copies[0]['component']==0,'single original eligible component')
    same(case['copy_parents'],copies,'all independent copy counts intervals and longest')
    target=copies[0];longest=target['longest']['descendant_genetic']
    summary=dict(seed=seed,mode=mode,exchange=exchange,steps=32,births=births,deaths=deaths,living=sum(u is not None for u in units),
                 initial_energy=initial_energy,final_energy=sum(u['energy'] for u in units if u is not None),
                 imported=imported,rejected_import=rejected,spent=spent,proposed=1024,initial_mass=initial_mass,final_mass=sum(raw)+sum(u is not None for u in units),
                 genetic_counts=target['series']['descendant_genetic'],episodes=target['episodes']['descendant_genetic'],
                 longest=longest,persistent10=longest>=10,ever=longest>=1)
    same(case['summary'],summary,'independent complete case summary')
    require(summary['initial_energy']+imported-spent==summary['final_energy'],'cumulative energy balance')
    return summary


def aggregate(rows):
    require(len(rows)==120,'complete grid')
    index={}
    for r in rows:
        key=(r['seed'],r['mode'],r['exchange'])
        require(type(r['seed']) is int and type(r['exchange']) is bool and key in GRID and key not in index,'strict unique grid identity')
        index[key]=r
        integers=('steps','births','deaths','living','initial_energy','final_energy','imported','rejected_import','spent','proposed','initial_mass','final_mass','longest')
        require(all(type(r[k]) is int and r[k]>=0 for k in integers),'integer observations')
        require(r['steps']==32 and r['initial_energy']==192 and r['initial_mass']==r['final_mass']==7 and r['proposed']==1024,'fixed initial state and budget')
        require(r['imported']+r['rejected_import']==1024 and 192+r['imported']-r['spent']==r['final_energy'],'energy budget')
        require(r['living']==3+r['births']-r['deaths'] and r['living']<=7,'population and mass')
        counts=r['genetic_counts'];require(len(counts)==32 and all(type(v) is int and 0<=v<=3 for v in counts),'all copy counts')
        runs=[];start=None
        for t,v in enumerate(counts+[0],1):
            if v>=2 and start is None:start=t
            elif v<2 and start is not None:runs.append([start,t-1]);start=None
        longest=max((b-a+1 for a,b in runs),default=0)
        same(r['episodes'],runs,'copy intervals');same(r['longest'],longest,'longest')
        same(r['persistent10'],longest>=10,'persistent');same(r['ever'],longest>0,'ever')
    cells=[];pairs=[];groups=[]
    for mode,exchange in product(MODES,(False,True)):
        selected=[index[s,mode,exchange] for s in range(120000,120020)]
        n=len(selected);success=sum(r['persistent10'] for r in selected);ever=sum(r['ever'] for r in selected)
        c=dict(mode=mode,exchange=exchange,n=n,successes=success,ever_count=ever,success_fraction=str(Fraction(success,n)),ever_fraction=str(Fraction(ever,n)))
        for k in ('longest','births','deaths','living','imported','rejected_import','spent'):c['mean_'+k]=str(Fraction(sum(r[k] for r in selected),n))
        cells.append(c)
    for seed,mode in product(range(120000,120020),MODES):
        off,on=index[seed,mode,False]['persistent10'],index[seed,mode,True]['persistent10']
        pairs.append(dict(seed=seed,mode=mode,off=off,on=on,difference=int(on)-int(off)))
    for mode in MODES:
        selected=[r for r in pairs if r['mode']==mode]
        groups.append(dict(mode=mode,n=20,on_only=sum(r['on'] and not r['off'] for r in selected),off_only=sum(r['off'] and not r['on'] for r in selected),both=sum(r['off'] and r['on'] for r in selected),neither=sum(not r['off'] and not r['on'] for r in selected),mean_difference=str(Fraction(sum(r['difference'] for r in selected),20))))
    return dict(cells=cells,pairs=pairs,groups=groups)

def main():
    root=OUTPUT;files=('metadata.json','results.json','summary.json');before={n:digest(root/n) for n in files};meta=read(root/'metadata.json');bound=bindings()
    for k,v in dict(status='complete',planned_cases=120,completed_cases=120,new_simulation_steps=3840,new_independent_initial_worlds=0,new_environment_sources=20,artificial_initial_state=True,time_limit_seconds=600,storage_limit_bytes=268435456).items():same(meta[k],v,'metadata '+k)
    require(type(meta['python_version']) is str and bool(meta['python_version']),'recorded runtime')
    require(type(meta['elapsed_seconds']) in (float,int) and math.isfinite(meta['elapsed_seconds']) and 0<=meta['elapsed_seconds']<600,'time budget')
    require(sum(p.stat().st_size for p in root.rglob('*') if p.is_file())<268435456,'storage budget')
    same(meta['input_sha256'],bound,'bound inputs');same(meta['input_sha256_after'],bound,'after inputs')
    paths=[f'cases/seed-{s}-{m}-exchange-{str(e).lower()}.json' for s,m,e in GRID]
    expected=set(paths+['results.json','summary.json'])
    require(set(meta['output_sha256'])==expected,'output inventory')
    require({str(p.relative_to(root)) for p in (root/'cases').iterdir()}==set(paths),'case inventory')
    hashes={n:digest(root/n) for n in expected};same(meta['output_sha256'],hashes,'all output hashes')
    summaries=[]
    for j,(key,path) in enumerate(zip(GRID,paths),1):
        c=read(root/path);same([c['seed'],c['mode'],c['exchange']],list(key),'case filename identity')
        summaries.append(verify_case(c))
        if j%10==0:print(f'{j}/120 independently verified input ablations',flush=True)
    same(read(root/'results.json'),summaries,'all summaries');same(read(root/'summary.json'),aggregate(summaries),'all statistics')
    same(bindings(),bound,'inputs unchanged');same({n:digest(root/n) for n in files},before,'root files unchanged')
    same({n:digest(root/n) for n in expected},hashes,'case files unchanged')
    proof=dict(status='verified',cases=120,saved_steps=3840,new_simulation_steps=3840,new_environment_sources=20,new_independent_initial_worlds=0,input_files=len(bound),files_sha256={**hashes,'metadata.json':before['metadata.json']},verifier_sha256=digest(Path(__file__)),python_version=platform.python_version(),scope='independent full environment tapes, dictionary physics, ancestry, material partitions, translated copy counts and paired statistics; artificial initial state')
    with (root/'independent-verification.json').open('x') as f:f.write(json.dumps(proof,indent=2)+'\n')
    print('verified all 120 cases, 3840 steps and 57 bindings')

if __name__=='__main__':
    try:main()
    except BaseException as error:
        p=OUTPUT/'verification-failure.json'
        if p.parent.is_dir() and not p.exists():
            with p.open('x') as f:f.write(json.dumps(dict(status='failed',error=f'{type(error).__name__}: {error}'))+'\n')
        raise
