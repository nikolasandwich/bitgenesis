"""Independent dictionary physics, identity chains, and translated copy matching."""
from hashlib import sha256
import json
import math
from pathlib import Path

from bitgenesis.v4.exchange_branch_audit import physical_step
from bitgenesis.v4.structure_audit import reconstruct
from scripts.verify_v4_structure_copies import recount

OUTPUT=Path('data/v4-copy-control')
NAMES=('constructed-off','constructed-on','no-raw-off')


def require(value,message):
    if not value:raise ValueError(message)


def same(actual,expected,message):
    require(json.dumps(actual,sort_keys=True,separators=(',',':'))==json.dumps(expected,sort_keys=True,separators=(',',':')),message)


def digest(path):return sha256(Path(path).read_bytes()).hexdigest()


def read(path):return json.loads(Path(path).read_text())


def bindings():
    paths=list(Path('src/bitgenesis/v4').glob('*.py'))
    paths.extend(Path('scripts')/(name+'.py') for name in ('analyze_v4_structure_copies','verify_v4_structure_copies','structure_copy_inputs','horizon_fate_inputs','run_v4_copy_control','verify_v4_copy_control'))
    paths.append(Path('docs/design/v4-structure-copy-control.zh-CN.md'))
    return {str(p):digest(p) for p in sorted(paths)}


def verify_case(case):
    name=case['name'];require(name in NAMES,'fixed case name')
    exchange=name=='constructed-on';raw_tokens=0 if name=='no-raw-off' else 4
    same(case['exchange'],exchange,'fixed exchange');same(case['raw_tokens'],raw_tokens,'fixed raw tokens')
    config=dict(width=16,height=16,capacity=64,leak=1,bond_cost=1,threshold=16,construction_cost=4,copy_cost=1,mutation_per_thousand=0)
    same(case['config'],config,'fixed configuration')
    units=[None]*256;raw=[0]*256;ids=[None]*256
    for identity,(x,y,material) in enumerate(((5,5,0),(6,5,0),(12,12,3))):
        site=16*y+x;units[site]=dict(material=material,energy=64,program=[material]*4);ids[site]=identity
    for x,y in ((5,6),(6,6),(5,7),(6,7)):raw[16*y+x]=raw_tokens//4
    initial=dict(tick=0,units=units,raw=raw,site_ids=ids.copy(),observation=reconstruct(units,ids,16,16,'final'))
    same(case['initial'],initial,'fixed initial snapshot')
    initial_energy=sum(u['energy'] for u in units if u is not None)
    initial_mass=sum(raw)+sum(u is not None for u in units)
    parents=[None,None,None];rows=[];births=deaths=imported=spent=0
    require(len(case['rows'])==32,'all thirty-two steps')
    for tick in range(1,33):
        directions=[1 if site%16==6 else 0 for site in range(256)]
        if tick in (1,2):
            for x in (5,6):directions[16*(tick+4)+x]=2
        proposals=[8 if (site%16,site//16) in ((5,5),(6,5),(5,7),(6,7)) else 0 for site in range(256)]
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
        imported+=physical['imported'];spent+=physical['spent']
    final=dict(tick=32,units=units,raw=raw,site_ids=ids,parents=parents)
    same(case['final'],final,'final units stocks identities ancestry')
    copies=recount(initial,rows,final)
    require(len(copies)==1 and copies[0]['component']==0,'single original eligible component')
    same(case['copy_parents'],copies,'all independent copy counts intervals and longest')
    target=copies[0];longest=target['longest']['descendant_genetic']
    summary=dict(name=name,exchange=exchange,raw_tokens=raw_tokens,steps=32,births=births,deaths=deaths,
                 initial_energy=initial_energy,final_energy=sum(u['energy'] for u in units if u is not None),
                 imported=imported,spent=spent,initial_mass=initial_mass,final_mass=sum(raw)+sum(u is not None for u in units),
                 genetic_counts=target['series']['descendant_genetic'],episodes=target['episodes']['descendant_genetic'],
                 longest=longest,persistent10=longest>=10)
    same(case['summary'],summary,'independent complete case summary')
    require(summary['initial_energy']+imported-spent==summary['final_energy'],'cumulative energy balance')
    return summary


def main():
    root=OUTPUT;proof_path=root/'independent-verification.json'
    # A repeated invocation must never overwrite an existing proof.
    if proof_path.exists():raise FileExistsError(proof_path)
    try:
        files=('metadata.json','cases.json','summary.json');before={n:digest(root/n) for n in files}
        metadata=read(root/'metadata.json');bound=bindings()
        same(metadata['status'],'complete','complete execution status')
        for name,value in dict(planned_cases=3,completed_cases=3,new_simulation_steps=96,new_independent_sources=0,
                               artificial_control=True,time_limit_seconds=60,storage_limit_bytes=33554432).items():
            same(metadata[name],value,'fixed metadata '+name)
        commit=metadata['git_commit'];require(type(commit) is str and len(commit)==40 and all(c in '0123456789abcdef' for c in commit),'git commit identity')
        elapsed=metadata['elapsed_seconds'];require(type(elapsed) in (int,float) and math.isfinite(elapsed) and 0<=elapsed<60,'elapsed budget')
        require(sum(p.stat().st_size for p in root.rglob('*') if p.is_file())<33554432,'storage budget')
        same(metadata['input_sha256'],bound,'complete independent input inventory')
        same(metadata['input_sha256_after'],bound,'after input inventory')
        same(metadata['output_sha256'],{n:before[n] for n in files[1:]},'output file binding')
        cases=read(root/'cases.json');require(type(cases) is list and len(cases)==3,'all three cases')
        same([c['name'] for c in cases],list(NAMES),'fixed case order')
        summary=[verify_case(case) for case in cases]
        same(read(root/'summary.json'),summary,'all case summaries')
        expected=summary[0]['persistent10'] and summary[2]['births']==0
        same(metadata['expectations_met'],expected,'expectations match full results')
        same(bindings(),bound,'inputs unchanged during verification')
        same({n:digest(root/n) for n in files},before,'saved files unchanged during verification')
        proof=dict(status='verified',cases=3,saved_steps=96,new_simulation_steps=96,new_independent_sources=0,
                   artificial_control=True,expectations_met=expected,input_files=len(bound),files_sha256=before,
                   verifier_sha256=digest(Path(__file__)),
                   scope='independent fixed inputs, dictionary physical reconstruction, identity ancestry and material partitions; study017 independent translated copy recount')
        with proof_path.open('x') as stream:stream.write(json.dumps(proof,indent=2)+'\n')
        print(json.dumps(proof))
    except BaseException as error:
        failure=root/'verification-failure.json'
        if root.is_dir() and not failure.exists():
            with failure.open('x') as stream:stream.write(json.dumps(dict(status='failed',error=f'{type(error).__name__}: {error}'))+'\n')
        raise


if __name__=='__main__':main()
