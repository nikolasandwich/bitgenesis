"""Historical input-tape interventions; final-sampled material continuity only."""
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path

from .hereditary_growing import step
from .heredity import HeritableUnit
from .hereditary_runner import save, encode
from .hereditary_audit import audit as source_audit
from .structure import snapshot
from .structure_continuity import follow

FILES = ('initial.json', 'steps.jsonl', 'final.json', 'continuity.json', 'summary.json')


def hashes(root):
    return {p.name: sha256(p.read_bytes()).hexdigest() for p in sorted(Path(root).iterdir()) if p.is_file()}


def summarize(records):
    eligible = [r for r in records if r['anchor_size'] >= 2 and not r['whole_world_anchor']]
    n = len(eligible)
    continuous = sum(r['continuous_closed_multi'] for r in eligible)
    replaced = sum(r['primary'] for r in eligible)
    return dict(eligible_components=n, continuous_closed_multi=continuous,
                continuous_fraction=continuous/n if n else None, continuous_replacement=replaced,
                continuous_replacement_fraction=replaced/n if n else None)


def run(output, source, anchor, horizon=100, exchange=True):
    """Return {summary, records}; physical.tick is absolute, outer tick relative."""
    if type(anchor) is not int or anchor < 0 or type(horizon) is not int or horizon < 1 or type(exchange) is not bool:
        raise ValueError('nonnegative anchor, positive horizon and boolean exchange required')
    root, source = Path(output), Path(source)
    root.mkdir(parents=True, exist_ok=False)
    meta = dict(schema='v4-exchange-branch-1', status='running', anchor=anchor, horizon=horizon,
                exchange=exchange, source=str(source))
    save(root/'metadata.json', meta)
    try:
        meta['source'] = str(source.resolve())
        meta['source_sha256'] = hashes(source)
        meta['code_sha256'] = {p.name:sha256(p.read_bytes()).hexdigest()
                               for p in sorted(Path(__file__).parent.glob('*.py'))}
        meta['source_audit'] = source_audit(source)
        config = json.loads((source/'metadata.json').read_text())
        if config['exchange'] is not True:
            raise ValueError('historical source must retain exchange')
        history = [json.loads(line) for line in (source/'steps.jsonl').read_text().splitlines()]
        if anchor+horizon > len(history):
            raise ValueError('source horizon insufficient')
        origin = history[anchor-1] if anchor else json.loads((source/'initial.json').read_text())
        units = [None if u is None else HeritableUnit(u['material'],u['energy'],tuple(u['program'])) for u in origin['units']]
        raw = list(origin['raw'])
        ids = [None]*len(units)
        parents, deaths = [], []
        for i,u in enumerate(units):
            if u is not None:
                ids[i] = len(parents)
                parents.append(None)
                deaths.append(None)
        def observed():
            return snapshot(json.loads(encode([None if u is None else asdict(u) for u in units])),ids,config['width'],config['height'],phase='final')
        initial_observation = observed()
        save(root/'initial.json',dict(tick=0,source_tick=anchor,units=origin['units'],raw=raw,site_ids=ids,observation=initial_observation))
        series = {0:initial_observation['components']['material']}
        keys = ('capacity','leak','bond_cost','threshold','construction_cost','copy_cost','mutation_per_thousand')
        with (root/'steps.jsonl').open('w') as stream:
            for tick, tape in enumerate(history[anchor:anchor+horizon],1):
                units,raw,record = step(units,raw,config['width'],config['height'],
                    [i['proposed'] for i in tape['driven']['inputs']],tape['directions'],[tuple(t) for t in tape['mutation_tickets']],
                    exchange=exchange,**{k:config[k] for k in keys})
                physical = json.loads(encode(dict(tick=anchor+tick,units=[None if u is None else asdict(u) for u in units],
                    raw=raw,energy=record['energy_after'],directions=tape['directions'],mutation_tickets=tape['mutation_tickets'],**record)))
                if exchange and physical != tape:
                    raise ValueError('baseline full physical replay mismatch')
                for site in record['material']['dissolved']:
                    deaths[ids[site]] = tick
                    ids[site] = None
                for proposal in record['material']['proposals']:
                    if proposal['reason'] == 'formed':
                        parent = ids[proposal['source']]
                        ids[proposal['target']] = len(parents)
                        parents.append(parent)
                        deaths.append(None)
                observation = observed()
                series[tick] = observation['components']['material']
                stream.write(encode(dict(tick=tick,source_tick=anchor+tick,physical=physical,site_ids=list(ids),observation=observation)))
        records = follow(series,parents,0,[horizon])[horizon]
        summary = summarize(records)
        save(root/'final.json',dict(tick=horizon,source_tick=anchor+horizon,units=physical['units'],raw=raw,site_ids=ids,parents=parents,death_ticks=deaths))
        save(root/'continuity.json',records)
        save(root/'summary.json',summary)
        meta['source_sha256_after'] = hashes(source)
        if meta['source_sha256_after'] != meta['source_sha256']:
            raise ValueError('source changed during branch')
        meta.update(status='complete',output_sha256={name:sha256((root/name).read_bytes()).hexdigest() for name in FILES})
        save(root/'metadata.json',meta)
        from .exchange_branch_audit import audit
        save(root/'audit.json',audit(root,source))
        return dict(summary=summary,records=records)
    except BaseException as error:
        meta.update(status='failed',error=f'{type(error).__name__}: {error}')
        try:
            meta['source_sha256_after'] = hashes(source)
        except OSError as hash_error:
            meta['source_hash_error'] = str(hash_error)
        save(root/'metadata.json',meta)
        raise
