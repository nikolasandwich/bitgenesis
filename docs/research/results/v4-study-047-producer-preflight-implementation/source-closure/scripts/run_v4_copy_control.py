"""Artificial input-tape controls for the existing structural-copy observer."""
from pathlib import Path
from dataclasses import asdict
import hashlib,json,subprocess,time
from bitgenesis.v4.hereditary_growing import step
from bitgenesis.v4.heredity import HeritableUnit
from bitgenesis.v4.lineage import Observer
from bitgenesis.v4.structure import snapshot
from scripts.analyze_v4_structure_copies import analyze

NAMES=('constructed-off','constructed-on','no-raw-off')
CONFIG=dict(width=16,height=16,capacity=64,leak=1,bond_cost=1,threshold=16,construction_cost=4,copy_cost=1,mutation_per_thousand=0)
OUTPUT=Path('data/v4-copy-control')

def normalize(value):return json.loads(json.dumps(value))
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def bindings():
    paths=list(Path('src/bitgenesis/v4').glob('*.py'))
    paths += [Path(p) for p in ('scripts/analyze_v4_structure_copies.py','scripts/verify_v4_structure_copies.py','scripts/structure_copy_inputs.py','scripts/horizon_fate_inputs.py','docs/design/v4-structure-copy-control.zh-CN.md','scripts/run_v4_copy_control.py','scripts/verify_v4_copy_control.py')]
    return {str(p):digest(p) for p in sorted(paths)}

def run_case(name):
    if name not in NAMES:raise ValueError('unknown fixed control')
    exchange=name=='constructed-on';raw_tokens=0 if name=='no-raw-off' else 4
    units=[None]*256;raw=[0]*256
    for site,material in ((85,0),(86,0),(204,3)):units[site]=HeritableUnit(material,64,(material,)*4)
    if raw_tokens:
        for site in (101,102,117,118):raw[site]=1
    def serialized():return normalize([None if u is None else asdict(u) for u in units])
    observer=Observer(serialized())
    initial=dict(tick=0,units=serialized(),raw=list(raw),site_ids=list(observer.alive),observation=snapshot(serialized(),observer.alive,16,16,phase='final'))
    rows=[]
    for tick in range(1,33):
        proposals=[8 if site in (85,86,117,118) else 0 for site in range(256)]
        directions=[1 if site%16==6 else 0 for site in range(256)]
        if tick==1:
            for site in (85,86):directions[site]=2
        if tick==2:
            for site in (101,102):directions[site]=2
        tickets=[(999,0,1)]*256
        units,raw,record=step(units,raw,proposals=proposals,directions=directions,mutation_tickets=tickets,exchange=exchange,**CONFIG)
        physical=normalize(dict(tick=tick,units=serialized(),raw=list(raw),energy=sum(u.energy for u in units if u is not None),directions=directions,mutation_tickets=tickets,**record))
        observer.accept(physical)
        rows.append(dict(tick=tick,site_ids=list(observer.alive),physical=physical,observation=snapshot(physical['units'],observer.alive,16,16,phase='final')))
    lineage=observer.result()
    final=dict(tick=32,units=serialized(),raw=list(raw),site_ids=list(observer.alive),parents=[v['parent'] for v in lineage['individuals']])
    copies=analyze(initial,rows,final)
    assert len(copies)==1 and copies[0]['component']==0 and copies[0]['anchor_members']==[0,1]
    copy=copies[0]
    summary=dict(name=name,exchange=exchange,raw_tokens=raw_tokens,steps=32,births=lineage['summary']['births'],deaths=lineage['summary']['deaths'],initial_energy=192,final_energy=sum(u.energy for u in units if u is not None),imported=sum(r['physical']['imported'] for r in rows),spent=sum(r['physical']['spent'] for r in rows),initial_mass=3+raw_tokens,final_mass=sum(raw)+sum(u is not None for u in units),genetic_counts=copy['series']['descendant_genetic'],episodes=copy['episodes']['descendant_genetic'],longest=copy['longest']['descendant_genetic'],persistent10=copy['longest']['descendant_genetic']>=10)
    assert summary['final_energy']==summary['initial_energy']+summary['imported']-summary['spent'] and summary['initial_mass']==summary['final_mass']
    return dict(name=name,exchange=exchange,raw_tokens=raw_tokens,config=dict(CONFIG),initial=initial,rows=rows,final=final,copy_parents=copies,summary=summary)

def save(path,value):path.write_text(json.dumps(value,separators=(',',':'))+'\n')
def main():
    if subprocess.check_output(['git','status','--porcelain'],text=True).strip():raise ValueError('clean launch required')
    OUTPUT.mkdir(exist_ok=False);started=time.monotonic();cases=[];summary=[]
    meta=dict(status='running',planned_cases=3,completed_cases=0,new_simulation_steps=0,new_independent_sources=0,artificial_control=True,time_limit_seconds=60,storage_limit_bytes=32*1024**2)
    save(OUTPUT/'metadata.json',meta);save(OUTPUT/'cases.json',cases);save(OUTPUT/'summary.json',summary)
    def budget():
        if time.monotonic()-started>=60 or sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())>=32*1024**2:raise ValueError('control budget exceeded')
    try:
        meta['git_commit']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();meta['input_sha256']=bindings()
        for name in NAMES:
            budget();assert bindings()==meta['input_sha256']
            case=run_case(name);cases.append(case);summary.append(case['summary'])
            meta.update(completed_cases=len(cases),new_simulation_steps=32*len(cases))
            save(OUTPUT/'cases.json',cases);save(OUTPUT/'summary.json',summary);save(OUTPUT/'metadata.json',meta)
            print(f'{len(cases)}/3 physical controls saved',flush=True)
        meta.update(status='complete',expectations_met=summary[0]['persistent10'] and summary[2]['births']==0)
        budget();assert bindings()==meta['input_sha256']
    except BaseException as error:
        meta.update(status='failed',error=f'{type(error).__name__}: {error}');raise
    finally:
        failure=None
        try:
            meta['input_sha256_after']=bindings()
            if meta.get('input_sha256')!=meta['input_sha256_after']:failure='bound control inputs changed'
            budget()
        except BaseException as error:failure=f'{type(error).__name__}: {error}'
        if failure is not None:meta.update(status='failed',finalization_error=failure)
        meta['elapsed_seconds']=time.monotonic()-started
        meta['output_sha256']={n:digest(OUTPUT/n) for n in ('cases.json','summary.json')}
        save(OUTPUT/'metadata.json',meta)
        if failure is not None:raise ValueError(failure)

if __name__=='__main__':main()
