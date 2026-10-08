"""Persist removal/sham continuations of independently verified growing runs."""
from hashlib import sha256
import json
from pathlib import Path
import platform
from random import Random
import subprocess

from .growing import step
from .growing_audit import audit
from .growing_runner import encode, save, snapshot
from .local import Unit
from .perturbation import remove


def tuples(value):
    return tuple(map(tuples, value)) if isinstance(value, list) else value


def run(output, origin, steps, sites=(), threshold=None, max_site_records=1000000):
    if type(steps) is not int or not 0 <= steps <= 100000 or type(max_site_records) is not int:
        raise ValueError('invalid branch horizon or budget')
    source_root = Path(origin)
    checked = audit(source_root)
    source_meta = json.loads((source_root/'metadata.json').read_text(encoding='utf-8'))
    before = json.loads((source_root/'final.json').read_text(encoding='utf-8'))
    keys = ('width','height','drive_per_thousand','drive_amount','capacity','leak',
            'bond_cost','exchange','threshold','construction_cost')
    config = {k: source_meta[k] for k in keys}
    if threshold is not None:
        config['threshold'] = threshold
    if type(config['threshold']) is not int or config['threshold'] < config['construction_cost']+2:
        raise ValueError('invalid branch formation threshold')
    if max_site_records < config['width']*config['height']*(steps+1):
        raise ValueError('branch recording budget exceeded')
    units = [None if u is None else Unit(**u) for u in before['units']]
    units, raw, boundary = remove(units, before['raw'], sites)
    drive, direction = Random(), Random()
    drive.setstate(tuples(before['drive_rng']))
    direction.setstate(tuples(before['direction_rng']))
    root = Path(output)
    root.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).parent
    try:
        revision = subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()
        dirty = bool(subprocess.check_output(['git','status','--porcelain'],cwd=source,text=True).strip())
    except (OSError, subprocess.CalledProcessError):
        revision = dirty = None
    meta = dict(schema='v4-branch-1',rules='v4-growing-1',status='running',
                start_tick=before['tick'],steps=steps,config=config,max_site_records=max_site_records,
                sites=boundary['sites'],python=platform.python_version(),git_commit=revision,git_dirty=dirty,
                origin_metadata_sha256=sha256((source_root/'metadata.json').read_bytes()).hexdigest(),
                origin_output_sha256=checked['output_sha256'],
                source_sha256={p.name:sha256(p.read_bytes()).hexdigest() for p in sorted(source.glob('*.py'))})
    save(root/'metadata.json',meta)
    try:
        save(root/'origin-audit.json',checked)
        save(root/'before.json',before)
        save(root/'boundary.json',boundary)
        save(root/'initial.json',dict(tick=before['tick'],units=snapshot(units),raw=raw,
                                     drive_rng=drive.getstate(),direction_rng=direction.getstate()))
        initial_energy = sum(u.energy for u in units if u is not None)
        energy = initial_energy
        mass = sum(raw)+sum(u is not None for u in units)
        spent = imported = formations = dissolutions = 0
        with (root/'steps.jsonl').open('w',encoding='utf-8') as stream:
            for tick in range(before['tick']+1,before['tick']+steps+1):
                proposals = [config['drive_amount'] if drive.randrange(1000)<config['drive_per_thousand'] else 0 for _ in units]
                directions = [direction.randrange(4) for _ in units]
                units,raw,record = step(units,raw,config['width'],config['height'],proposals,directions,
                    config['capacity'],config['leak'],config['bond_cost'],config['exchange'],
                    config['threshold'],config['construction_cost'])
                energy += record['imported']-record['spent']
                imported += record['imported']
                spent += record['spent']
                formations += sum(p['reason']=='formed' for p in record['material']['proposals'])
                dissolutions += len(record['material']['dissolved'])
                stream.write(encode(dict(tick=tick,units=snapshot(units),raw=raw,energy=energy,
                                         directions=directions,**record)))
        save(root/'final.json',dict(tick=before['tick']+steps,units=snapshot(units),raw=raw,
                                   drive_rng=drive.getstate(),direction_rng=direction.getstate()))
        summary = dict(steps=steps,initial_energy=initial_energy,final_energy=energy,
                       initial_material=mass,final_material=sum(raw)+sum(u is not None for u in units),
                       imported=imported,spent=spent,formations=formations,dissolutions=dissolutions,
                       units=sum(u is not None for u in units),exported_energy=boundary['exported_energy'],
                       exported_material=boundary['exported_material'])
        save(root/'summary.json',summary)
        names = ('origin-audit.json','before.json','boundary.json','initial.json','steps.jsonl','final.json','summary.json')
        meta.update(status='complete',output_sha256={n:sha256((root/n).read_bytes()).hexdigest() for n in names})
        save(root/'metadata.json',meta)
        return summary
    except BaseException as error:
        meta.update(status='failed',error=f'{type(error).__name__}: {error}')
        save(root/'metadata.json',meta)
        raise
