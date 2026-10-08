"""Bounded records of driven local material formation and dissolution."""
import argparse
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import platform
from random import Random
import subprocess

from .local import Unit
from .growing import step,RULES_VERSION


def encode(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'))+'\n'


def save(path,value):
    path.write_text(encode(value),encoding='utf-8')


def snapshot(units):
    return [None if unit is None else asdict(unit) for unit in units]


def run(output,seed,steps=100,width=16,height=16,occupancy=750,max_energy=64,
        bond_cost=1,exchange=True,max_site_records=1000000,
        drive_per_thousand=500,drive_amount=8,capacity=64,leak=1,
        initial_raw=1,threshold=16,construction_cost=4):
    values=(seed,steps,width,height,occupancy,max_energy,bond_cost,max_site_records,
            drive_per_thousand,drive_amount,capacity,leak,initial_raw,threshold,construction_cost)
    if any(type(v) is not int for v in values):
        raise ValueError('integer configuration required')
    if min(width,height)<3 or not 0<=steps<=100000 or not 0<=occupancy<=1000 or min(max_energy,bond_cost)<0:
        raise ValueError('invalid local-unit configuration')
    if max_site_records<width*height*(steps+1) or type(exchange) is not bool:
        raise ValueError('recording budget or exchange flag invalid')
    if not 0<=drive_per_thousand<=1000 or min(drive_amount,capacity,leak)<0 or max_energy>capacity:
        raise ValueError('invalid energy drive or capacity')
    if min(initial_raw,construction_cost)<0 or threshold<construction_cost+2:
        raise ValueError('invalid material or formation settings')
    direction_rng=Random(int.from_bytes(sha256(f'v4-growing-1:{seed}:directions'.encode('ascii')).digest(),'big'))
    drive=Random(int.from_bytes(sha256(f'v4-driven-1:{seed}:drive'.encode('ascii')).digest(),'big'))
    rng=Random(seed)
    units=[Unit(rng.randrange(4),rng.randrange(max_energy+1)) if rng.randrange(1000)<occupancy else None
           for _ in range(width*height)]
    raw=[initial_raw]*len(units)
    root=Path(output)
    root.mkdir(parents=True,exist_ok=False)
    source=Path(__file__).parent
    try:
        revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()
        dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=source,text=True).strip())
    except (OSError,subprocess.CalledProcessError):
        revision=dirty=None
    meta=dict(schema='v4-growing-run-1',rules=RULES_VERSION,status='running',seed=seed,steps=steps,
              width=width,height=height,occupancy=occupancy,max_energy=max_energy,
              bond_cost=bond_cost,exchange=exchange,max_site_records=max_site_records,
              drive_per_thousand=drive_per_thousand,drive_amount=drive_amount,capacity=capacity,leak=leak,initial_raw=initial_raw,threshold=threshold,construction_cost=construction_cost,
              python=platform.python_version(),git_commit=revision,git_dirty=dirty,
              source_sha256={p.name:sha256(p.read_bytes()).hexdigest() for p in sorted(source.glob('*.py'))})
    save(root/'metadata.json',meta)
    try:
        save(root/'initial.json',dict(tick=0,units=snapshot(units),raw=raw,rng_state=rng.getstate(),drive_rng=drive.getstate(),direction_rng=direction_rng.getstate()))
        energy=sum(u.energy for u in units if u is not None)
        initial_energy=energy
        spent=imported=rejected=leakage=0
        initial_material=sum(raw)+sum(u is not None for u in units)
        formations=dissolutions=construction_spent=0
        with (root/'steps.jsonl').open('w',encoding='utf-8') as stream:
            for tick in range(1,steps+1):
                proposals=[drive_amount if drive.randrange(1000)<drive_per_thousand else 0 for _ in units]
                directions=[direction_rng.randrange(4) for _ in units]
                units,raw,record=step(units,raw,width,height,proposals,directions,capacity,leak,bond_cost,exchange,threshold,construction_cost)
                energy+=record['imported']-record['spent']
                imported+=record['imported']
                rejected+=record['rejected_import']
                leakage+=record['driven']['leakage']
                spent+=record['spent']
                formations+=sum(p['reason']=='formed' for p in record['material']['proposals'])
                dissolutions+=len(record['material']['dissolved'])
                construction_spent+=record['material']['spent']
                stream.write(encode(dict(tick=tick,units=snapshot(units),energy=energy,
                                         raw=raw,directions=directions,**record)))
        save(root/'final.json',dict(tick=steps,units=snapshot(units),raw=raw,drive_rng=drive.getstate(),direction_rng=direction_rng.getstate()))
        summary=dict(steps=steps,units=sum(u is not None for u in units),initial_energy=initial_energy,
                     final_energy=energy,spent=spent,imported=imported,rejected_import=rejected,leakage=leakage,construction_spent=construction_spent,
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


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--seed',type=int,required=True)
    parser.add_argument('--steps',type=int,default=100)
    parser.add_argument('--no-exchange',action='store_true')
    parser.add_argument('--no-drive',action='store_true')
    args=parser.parse_args()
    try:
        print(encode(run(args.output,args.seed,args.steps,exchange=not args.no_exchange,drive_per_thousand=0 if args.no_drive else 500)),end='')
    except (OSError,ValueError,TypeError) as error:
        parser.error(str(error))


if __name__=='__main__':
    main()
