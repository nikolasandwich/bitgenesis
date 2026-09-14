"""Bounded records of fixed-site local-unit dynamics."""
import argparse
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import platform
from random import Random
import subprocess

from .local import Unit,interact,components,RULES_VERSION


def encode(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'))+'\n'


def save(path,value):
    path.write_text(encode(value),encoding='utf-8')


def snapshot(units):
    return [None if unit is None else asdict(unit) for unit in units]


def run(output,seed,steps=100,width=16,height=16,occupancy=750,max_energy=64,
        bond_cost=1,exchange=True,max_site_records=1000000):
    values=(seed,steps,width,height,occupancy,max_energy,bond_cost,max_site_records)
    if any(type(v) is not int for v in values):
        raise ValueError('integer configuration required')
    if min(width,height)<3 or not 0<=steps<=100000 or not 0<=occupancy<=1000 or min(max_energy,bond_cost)<0:
        raise ValueError('invalid local-unit configuration')
    if max_site_records<width*height*(steps+1) or type(exchange) is not bool:
        raise ValueError('recording budget or exchange flag invalid')
    rng=Random(seed)
    units=[Unit(rng.randrange(4),rng.randrange(max_energy+1)) if rng.randrange(1000)<occupancy else None
           for _ in range(width*height)]
    root=Path(output)
    root.mkdir(parents=True,exist_ok=False)
    source=Path(__file__).parent
    try:
        revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()
        dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=source,text=True).strip())
    except (OSError,subprocess.CalledProcessError):
        revision=dirty=None
    meta=dict(schema='v4-run-1',rules=RULES_VERSION,status='running',seed=seed,steps=steps,
              width=width,height=height,occupancy=occupancy,max_energy=max_energy,
              bond_cost=bond_cost,exchange=exchange,max_site_records=max_site_records,
              python=platform.python_version(),git_commit=revision,git_dirty=dirty,
              source_sha256={p.name:sha256(p.read_bytes()).hexdigest() for p in sorted(source.glob('*.py'))})
    save(root/'metadata.json',meta)
    try:
        save(root/'initial.json',dict(tick=0,units=snapshot(units),rng_state=rng.getstate()))
        energy=sum(u.energy for u in units if u is not None)
        initial_energy=energy
        spent=0
        bonds=[]
        with (root/'steps.jsonl').open('w',encoding='utf-8') as stream:
            for tick in range(1,steps+1):
                units,record=interact(units,width,height,bond_cost,exchange)
                energy-=record['spent']
                spent+=record['spent']
                bonds=record['bonds']
                stream.write(encode(dict(tick=tick,units=snapshot(units),energy=energy,
                                         components=components(units,bonds),**record)))
        save(root/'final.json',dict(tick=steps,units=snapshot(units)))
        summary=dict(steps=steps,units=sum(u is not None for u in units),initial_energy=initial_energy,
                     final_energy=energy,spent=spent,last_transition_bonds=len(bonds) if steps else None,
                     last_transition_components=len(components(units,bonds)) if steps else None)
        save(root/'summary.json',summary)
        meta.update(status='complete',output_sha256={name:sha256((root/name).read_bytes()).hexdigest()
                    for name in ('initial.json','steps.jsonl','final.json','summary.json')})
        save(root/'metadata.json',meta)
        return summary
    except BaseException as error:
        meta.update(status='failed',error=f'{type(error).__name__}: {error}')
        save(root/'metadata.json',meta)
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--seed',type=int,required=True)
    parser.add_argument('--steps',type=int,default=100)
    parser.add_argument('--no-exchange',action='store_true')
    args=parser.parse_args()
    try:
        print(encode(run(args.output,args.seed,args.steps,exchange=not args.no_exchange)),end='')
    except (OSError,ValueError,TypeError) as error:
        parser.error(str(error))
