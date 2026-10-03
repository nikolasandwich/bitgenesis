"""Independent replay of retained source tickets and paired program comparisons."""
from fractions import Fraction
from itertools import product
import json
import math
from pathlib import Path
import platform
import re
from scripts.program_direction_inputs import bindings, read, digest, source_cases
from bitgenesis.v4.exchange_branch_audit import physical_step
from bitgenesis.v4.structure_audit import reconstruct
from scripts.verify_v4_structure_copies import recount

OUTPUT=Path('data/v4-study-023')
GRID=tuple(product(range(120000,120020),(False,True)))
METRICS=('genetic_persistent10','genetic_ever','material_persistent10','material_ever',
         'longest_genetic','births','deaths','living','imported','spent','final_energy',
         'nonzero_births','north_births')


def set_as_list(value):
    return sorted(value)


def require(value,message):
    if not value:raise ValueError(message)


def same(actual,expected,message):
    require(json.dumps(actual,sort_keys=True,separators=(',',':'))==json.dumps(expected,sort_keys=True,separators=(',',':')),message)


def verify_case(case,source):
    same(set_as_list(case),set_as_list(source),"case schema")
    same([case[k] for k in ("seed","mode","exchange")], [source[k] for k in ("seed","mode","exchange")], "source identity")
    seed,mode,exchange=case['seed'],case['mode'],case['exchange']
    require(type(seed) is int and seed in range(120000,120020) and type(exchange) is bool and mode=='random-direction','fixed case identity')
    config=dict(width=16,height=16,capacity=64,leak=1,bond_cost=1,threshold=16,construction_cost=4,copy_cost=1,mutation_per_thousand=0)
    same(case['config'],config,'fixed configuration')
    units=[None]*256;raw=[0]*256;ids=[None]*256
    for identity,(x,y,material) in enumerate(((5,5,0),(6,5,0),(12,12,3))):
        site=16*y+x;units[site]=dict(material=material,energy=64,program=([0,0,0,identity+1] if identity<2 else [3]*4));ids[site]=identity
    for x,y in ((5,6),(6,6),(5,7),(6,7)):raw[16*y+x]=1
    initial=dict(tick=0,units=units,raw=raw,site_ids=ids.copy(),observation=reconstruct(units,ids,16,16,'final'))
    same(case['initial'],initial,'fixed initial snapshot')
    initial_energy=sum(u['energy'] for u in units if u is not None)
    initial_mass=sum(raw)+sum(u is not None for u in units)
    parents=[None,None,None];rows=[];births=deaths=imported=rejected=spent=0
    require(len(source['rows'])==32,'all source steps')
    require(len(case['rows'])==32,'all thirty-two steps')
    for tick in range(1,33):
        saved=source['rows'][tick-1]['physical']
        require(saved['tick']==tick,'source tick')
        directions=saved['directions'];tickets=saved['mutation_tickets']
        require(len(directions)==len(tickets)==len(saved['driven']['inputs'])==256,'complete source tickets')
        require(all(type(d) is int and 0<=d<4 for d in directions),'source directions')
        same(tickets,[[999,0,1] for _ in range(256)],'source mutation tickets')
        proposals=[entry['proposed'] for entry in saved['driven']['inputs']]
        same(proposals,[8 if site in (85,86,117,118) else 0 for site in range(256)],'source fixed feed')
        tape=dict(tick=tick,directions=directions,mutation_tickets=tickets,
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


def metrics(case):
    summary=case['summary'];copy=case['copy_parents'][0]
    longest=copy['longest']['descendant_genetic']
    material=copy['longest']['descendant_material']
    formed=[proposal for row in case['rows'] for proposal in row['physical']['material']['proposals'] if proposal['reason']=='formed']
    values=dict(genetic_persistent10=int(longest>=10),genetic_ever=int(longest>0),
                material_persistent10=int(material>=10),material_ever=int(any(n>=2 for n in copy['series']['descendant_material'])),
                longest_genetic=longest,
                **{key:summary[key] for key in ('births','deaths','living','imported','spent','final_energy')},
                nonzero_births=sum(p['material']!=0 for p in formed),north_births=sum(p['direction']==3 for p in formed))
    check_metrics(values)
    return values


def check_metrics(values):
    require(type(values) is dict and set(values)==set(METRICS),'exact metric fields')
    require(all(type(v) is int and v>=0 for v in values.values()),'native nonnegative metric integers')
    require(all(values[k] in (0,1) for k in METRICS[:4]),'binary event metrics')
    require(values['longest_genetic']<=32,'bounded genetic duration')
    require(values['genetic_persistent10']==int(values['longest_genetic']>=10) and values['genetic_ever']==int(values['longest_genetic']>0),'genetic indicators')
    require(values['material_persistent10']<=values['material_ever'] and values['genetic_persistent10']<=values['material_persistent10'] and values['genetic_ever']<=values['material_ever'],'material containment')
    require(values['living']==3+values['births']-values['deaths'] and values['living']<=7,'population balance')
    require(values['imported']<=1024 and 192+values['imported']-values['spent']==values['final_energy'],'energy balance')
    require(values['north_births']<=values['births'] and values['nonzero_births']<=values['births'],'formed counts')


def pair_record(case,source):
    same([case[k] for k in ('seed','mode','exchange')],[source[k] for k in ('seed','mode','exchange')],'paired identity')
    old,new=metrics(source),metrics(case)
    return dict(seed=case['seed'],exchange=case['exchange'],homogeneous=old,heterogeneous=new,
                delta={key:new[key]-old[key] for key in METRICS})


def aggregate(records):
    require(type(records) is list and len(records)==40,'complete forty pairs')
    index={}
    for record in records:
        require(set(record)=={'seed','exchange','homogeneous','heterogeneous','delta'},'exact paired record')
        seed,exchange=record['seed'],record['exchange']
        require(type(seed) is int and type(exchange) is bool and (seed,exchange) in GRID and (seed,exchange) not in index,'unique fixed identity')
        for genotype in ('homogeneous','heterogeneous'):check_metrics(record[genotype])
        same(record['delta'],{key:record['heterogeneous'][key]-record['homogeneous'][key] for key in METRICS},'paired delta')
        index[seed,exchange]=record
    cells=[];contrasts=[]
    for genotype,exchange in product(('homogeneous','heterogeneous'),(False,True)):
        totals={key:sum(index[seed,exchange][genotype][key] for seed in range(120000,120020)) for key in METRICS}
        cells.append(dict(genotype=genotype,exchange=exchange,n=20,totals=totals,
                          means={key:str(Fraction(value,20)) for key,value in totals.items()}))
    for exchange in (False,True):
        differences={key:[index[seed,exchange]['delta'][key] for seed in range(120000,120020)] for key in METRICS}
        contrasts.append(dict(exchange=exchange,n=20,
                              mean_delta={key:str(Fraction(sum(v),20)) for key,v in differences.items()},
                              positive={key:sum(n>0 for n in v) for key,v in differences.items()},
                              negative={key:sum(n<0 for n in v) for key,v in differences.items()},
                              tie={key:sum(n==0 for n in v) for key,v in differences.items()}))
    return dict(cells=cells,contrasts=contrasts)


def main():
    root=OUTPUT
    require(not (root/'independent-verification.json').exists(),'proof already exists')
    files=('metadata.json','results.json','summary.json')
    before={name:digest(root/name) for name in files};meta=read(root/'metadata.json');bound=bindings()
    require(len(bound)==229,'229 bound inputs')
    same(digest(Path(__file__)),bound['scripts/verify_v4_program_direction.py'],'running verifier matches bound hash')
    for key,value in dict(status='complete',planned_cases=40,completed_cases=40,new_simulation_steps=1280,
                          new_environment_sources=0,reused_environment_sources=20,new_independent_initial_worlds=0,
                          artificial_initial_state=True,time_limit_seconds=600,storage_limit_bytes=134217728).items():
        same(meta[key],value,'metadata '+key)
    require(type(meta['git_commit']) is str and re.fullmatch('[0-9a-f]{40}',meta['git_commit']) is not None,'recorded git commit')
    require(type(meta['elapsed_seconds']) in (float,int) and math.isfinite(meta['elapsed_seconds']) and 0<=meta['elapsed_seconds']<600,'time budget')
    require(sum(p.stat().st_size for p in root.rglob('*') if p.is_file())<134217728,'storage budget')
    same(meta['input_sha256'],bound,'bound inputs');same(meta['input_sha256_after'],bound,'after inputs')
    sources=list(source_cases())
    paths=[f'cases/seed-{seed}-random-direction-exchange-{str(exchange).lower()}.json' for seed,exchange in GRID]
    same([str(p) for p in sources],['data/v4-study-019/'+p for p in paths],'fixed source paths')
    expected=set(paths+['results.json','summary.json'])
    require(set(meta['output_sha256'])==expected,'output inventory')
    require({str(p.relative_to(root)) for p in (root/'cases').iterdir()}==set(paths),'case inventory')
    hashes={name:digest(root/name) for name in expected};same(meta['output_sha256'],hashes,'all output hashes')
    records=[]
    for number,((seed,exchange),path,source_path) in enumerate(zip(GRID,paths,sources),1):
        case=read(root/path);source=read(source_path)
        same([case['seed'],case['exchange']],[seed,exchange],'case filename identity')
        verify_case(case,source);records.append(pair_record(case,source))
        if number%10==0:print(f'{number}/40 independently verified program-direction cases',flush=True)
    same(read(root/'results.json'),records,'all pairs');same(read(root/'summary.json'),aggregate(records),'all paired statistics')
    same(bindings(),bound,'inputs unchanged');same({name:digest(root/name) for name in files},before,'root files unchanged')
    same({name:digest(root/name) for name in expected},hashes,'case files unchanged')
    proof=dict(status='verified',cases=40,saved_steps=1280,new_simulation_steps=1280,new_environment_sources=0,
               reused_environment_sources=20,new_independent_initial_worlds=0,input_files=len(bound),
               files_sha256={**hashes,'metadata.json':before['metadata.json']},verifier_sha256=digest(Path(__file__)),
               python_version=platform.python_version(),
               scope='independent saved input tapes, dictionary physics, ancestry, all four translated copy series and exact paired program statistics; artificial initial state')
    with (root/'independent-verification.json').open('x') as stream:stream.write(json.dumps(proof,indent=2)+'\n')
    print('verified 40 cases, 1280 steps and 229 bindings')


if __name__=='__main__':
    try:main()
    except BaseException as error:
        path=OUTPUT/'verification-failure.json'
        if path.parent.is_dir() and not path.exists():
            with path.open('x') as stream:stream.write(json.dumps(dict(status='failed',error=f'{type(error).__name__}: {error}'))+'\n')
        raise
