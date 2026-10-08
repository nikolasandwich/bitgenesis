"""Matched two-founder explicit-program assay records."""
import argparse
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import platform
from random import Random
import subprocess

from .local import Unit
from .hereditary_growing import step,RULES_VERSION
from .heredity import HeritableUnit


def encode(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'))+'\n'


def save(path,value):
    path.write_text(encode(value),encoding='utf-8')


def snapshot(units):
    return [None if unit is None else asdict(unit) for unit in units]


def run(output,seed,programs,steps=100,width=16,height=16,initial_energy=64,initial_material=0,
        bond_cost=1,exchange=True,max_site_records=1000000,
        drive_per_thousand=500,drive_amount=8,capacity=64,leak=1,
        initial_raw=1,threshold=16,construction_cost=4,copy_cost=1,
        initial_sites=None):
    mutation_per_thousand=0
    if type(width) is not int or type(height) is not int:
        raise ValueError('integer geometry required')
    if initial_sites is None:
        initial_sites=((height//2)*width+width//4,(height//2)*width+3*width//4)
    if type(initial_sites) is not tuple or len(initial_sites)!=2 or any(type(i) is not int for i in initial_sites) or len(set(initial_sites))!=2:
        raise ValueError('two distinct integer founder sites required')
    if type(programs) is not tuple or len(programs)!=2:
        raise ValueError('two immutable founder programs required')
    values=(seed,steps,width,height,initial_energy,initial_material,bond_cost,max_site_records,
            drive_per_thousand,drive_amount,capacity,leak,initial_raw,threshold,construction_cost,copy_cost,mutation_per_thousand)
    if any(type(v) is not int for v in values):
        raise ValueError('integer configuration required')
    if min(width,height)<3 or not 0<=steps<=100000 or not 0<=initial_material<4 or not all(0<=i<width*height for i in initial_sites) or min(initial_energy,bond_cost)<0:
        raise ValueError('invalid local-unit configuration')
    if max_site_records<width*height*(steps+1) or type(exchange) is not bool:
        raise ValueError('recording budget or exchange flag invalid')
    if not 0<=drive_per_thousand<=1000 or min(drive_amount,capacity,leak)<0 or initial_energy>capacity:
        raise ValueError('invalid energy drive or capacity')
    if min(initial_raw,construction_cost,copy_cost)<0 or threshold<construction_cost+copy_cost+2:
        raise ValueError('invalid material or formation settings')
    founders=[HeritableUnit(initial_material,initial_energy,p) for p in programs]
    mutation_rng=Random(int.from_bytes(sha256(f'v4-heredity-1:{seed}:mutation'.encode('ascii')).digest(),'big'))
    direction_rng=Random(int.from_bytes(sha256(f'v4-growing-1:{seed}:directions'.encode('ascii')).digest(),'big'))
    drive=Random(int.from_bytes(sha256(f'v4-driven-1:{seed}:drive'.encode('ascii')).digest(),'big'))
    units=[None]*(width*height)
    for site,founder in zip(initial_sites,founders):
        units[site]=founder
    raw=[initial_raw]*len(units)
    root=Path(output)
    root.mkdir(parents=True,exist_ok=False)
    source=Path(__file__).parent
    try:
        revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()
        dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=source,text=True).strip())
    except (OSError,subprocess.CalledProcessError):
        revision=dirty=None
    meta=dict(schema='v4-competition-1',rules=RULES_VERSION,status='running',seed=seed,steps=steps,
              width=width,height=height,initial_energy=initial_energy,initial_material=initial_material,initial_sites=list(initial_sites),programs=[list(p) for p in programs],
              bond_cost=bond_cost,exchange=exchange,max_site_records=max_site_records,
              drive_per_thousand=drive_per_thousand,drive_amount=drive_amount,capacity=capacity,leak=leak,initial_raw=initial_raw,threshold=threshold,construction_cost=construction_cost,copy_cost=copy_cost,mutation_per_thousand=mutation_per_thousand,
              python=platform.python_version(),git_commit=revision,git_dirty=dirty,
              source_sha256={p.name:sha256(p.read_bytes()).hexdigest() for p in sorted(source.glob('*.py'))})
    save(root/'metadata.json',meta)
    try:
        save(root/'initial.json',dict(tick=0,units=snapshot(units),raw=raw,mutation_rng=mutation_rng.getstate(),drive_rng=drive.getstate(),direction_rng=direction_rng.getstate()))
        energy=sum(u.energy for u in units if u is not None)
        initial_energy=energy
        spent=imported=rejected=leakage=0
        initial_material=sum(raw)+sum(u is not None for u in units)
        formations=dissolutions=construction_spent=copy_spent=mutations=0
        with (root/'steps.jsonl').open('w',encoding='utf-8') as stream:
            for tick in range(1,steps+1):
                proposals=[drive_amount if drive.randrange(1000)<drive_per_thousand else 0 for _ in units]
                directions=[direction_rng.randrange(4) for _ in units]
                mutation_tickets=[(mutation_rng.randrange(1000),mutation_rng.randrange(4),mutation_rng.randrange(1,4)) for _ in units]
                units,raw,record=step(units,raw,width,height,proposals,directions,mutation_tickets,capacity,leak,bond_cost,exchange,threshold,construction_cost,copy_cost,mutation_per_thousand)
                energy+=record['imported']-record['spent']
                imported+=record['imported']
                rejected+=record['rejected_import']
                leakage+=record['driven']['leakage']
                spent+=record['spent']
                formations+=sum(p['reason']=='formed' for p in record['material']['proposals'])
                dissolutions+=len(record['material']['dissolved'])
                construction_spent+=record['material']['construction_spent']
                copy_spent+=record['material']['copy_spent']
                mutations+=sum(p.get('mutated',False) for p in record['material']['proposals'])
                stream.write(encode(dict(tick=tick,units=snapshot(units),energy=energy,
                                         raw=raw,directions=directions,mutation_tickets=mutation_tickets,**record)))
        save(root/'final.json',dict(tick=steps,units=snapshot(units),raw=raw,mutation_rng=mutation_rng.getstate(),drive_rng=drive.getstate(),direction_rng=direction_rng.getstate()))
        summary=dict(steps=steps,units=sum(u is not None for u in units),initial_energy=initial_energy,
                     final_energy=energy,spent=spent,imported=imported,rejected_import=rejected,leakage=leakage,construction_spent=construction_spent,copy_spent=copy_spent,mutations=mutations,
                     formations=formations,dissolutions=dissolutions,
                     initial_material=initial_material,final_material=sum(raw)+sum(u is not None for u in units),
                     final_raw=sum(raw))
        save(root/'summary.json',summary)
        meta.update(status='complete',output_sha256={name:sha256((root/name).read_bytes()).hexdigest()
                    for name in ('initial.json','steps.jsonl','final.json','summary.json')})
        save(root/'metadata.json',meta)
        return summary
    except BaseException as error:
        meta.update(status='failed',error=f'{type(error).__name__}: {error}')
        save(root/'metadata.json',meta)
        raise

