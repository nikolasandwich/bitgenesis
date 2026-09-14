"""Passive competition counts by founder role, independent of program equality."""
from hashlib import sha256
import json
from pathlib import Path
from .competition_audit import audit
from .lineage import Observer


def trace(directory):
    root=Path(directory)
    checked=audit(root)
    meta=json.loads((root/'metadata.json').read_text(encoding='utf-8'))
    initial=json.loads((root/'initial.json').read_text(encoding='utf-8'))
    observer=Observer(initial['units'])
    founders=[observer.alive[i] for i in meta['initial_sites']]
    rows=[]
    with (root/'steps.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            row=json.loads(line)
            observer.accept(row)
            counts=[0,0]
            for identity in observer.alive:
                if identity is not None:
                    founder=observer.individuals[identity]['founder']
                    counts[founders.index(founder)]+=1
            rows.append(dict(tick=row['tick'],counts=counts))
    result=observer.result()
    if result['summary']['births']!=checked['summary']['formations'] or result['summary']['deaths']!=checked['summary']['dissolutions']:
        raise ValueError('competition ancestry totals')
    return dict(scope='passive role ancestry on independently audited two-founder dynamics',
        founders_by_role=founders,counts=rows,lineage=result,dynamics_audit=checked,
        observer_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        lineage_sha256=sha256(Path(__file__).with_name('lineage.py').read_bytes()).hexdigest())
