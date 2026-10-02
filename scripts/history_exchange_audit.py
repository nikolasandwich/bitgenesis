"""Independent dictionary-physics audit of both exchange-history directions.

Only independently implemented reconstruction primitives are shared with the
legacy auditor; metadata and complete saved-record validation live here.
"""
from hashlib import sha256
import json
from pathlib import Path
from bitgenesis.v4.exchange_branch_audit import physical_step, continuity, partition, source_audit


def audit(output,source):
    root,source=Path(output),Path(source)
    def read(path):
        return json.loads(path.read_text())
    def hashes(path):
        return {p.name:sha256(p.read_bytes()).hexdigest() for p in sorted(path.iterdir()) if p.is_file()}
    def require(ok,message):
        if not ok:
            raise ValueError(message)
    original_source,original_output=hashes(source),hashes(root)
    meta=read(root/'metadata.json')
    require(meta['schema']=='v4-history-exchange-branch-1' and meta['status']=='complete','branch status/schema')
    require(type(meta['exchange']) is bool and type(meta['anchor']) is int and meta['anchor']>=0 and type(meta['horizon']) is int and meta['horizon']>0,'branch configuration')
    require(meta['source_sha256']==meta['source_sha256_after']==original_source,'source hashes')
    config=read(source/'metadata.json')
    require(type(config.get('exchange')) is bool and type(meta.get('source_exchange')) is bool
            and meta['source_exchange'] == config['exchange'],'source exchange')
    require(meta['source_audit']==source_audit(source),'upstream audit')
    expected_files=('initial.json','steps.jsonl','final.json','continuity.json','summary.json')
    require(meta['output_sha256']=={n:original_output[n] for n in expected_files},'output hashes')
    repo=Path(__file__).resolve().parents[1]
    code_paths=list((repo/'src/bitgenesis/v4').glob('*.py')) + [
        repo/'scripts/history_exchange_branch.py',repo/'scripts/history_exchange_audit.py']
    require(meta['code_sha256']=={str(p.relative_to(repo)):sha256(p.read_bytes()).hexdigest()
                                for p in sorted(code_paths)},'code hashes')
    history=[json.loads(line) for line in (source/'steps.jsonl').read_text().splitlines()]
    anchor,horizon=meta['anchor'],meta['horizon']
    require(anchor+horizon<=len(history),'source horizon')
    origin=history[anchor-1] if anchor else read(source/'initial.json')
    units,raw=origin['units'],origin['raw']
    ids=[]
    parents=[]
    deaths=[]
    for u in units:
        ids.append(len(parents) if u else None)
        if u:
            parents.append(None)
            deaths.append(None)
    observed=partition(units,ids,config['width'],config['height'],'final')
    require(read(root/'initial.json')==dict(tick=0,source_tick=anchor,units=units,raw=raw,site_ids=ids,observation=observed),'initial state/identities')
    series={0:observed['components']['material']}
    rows=[json.loads(line) for line in (root/'steps.jsonl').read_text().splitlines()]
    require(len(rows)==horizon,'branch horizon')
    for tick,(row,tape) in enumerate(zip(rows,history[anchor:anchor+horizon]),1):
        expected=physical_step(units,raw,config,tape,meta['exchange'])
        require(row['physical']==expected,'physical record')
        if meta['exchange'] == meta['source_exchange']:
            require(expected==tape,'baseline physical record')
        old_ids=list(ids)
        for site in expected['material']['dissolved']:
            deaths[ids[site]]=tick
            ids[site]=None
        for p in expected['material']['proposals']:
            if p['reason']=='formed':
                require(old_ids[p['source']] is not None,'birth parent')
                ids[p['target']]=len(parents)
                parents.append(old_ids[p['source']])
                deaths.append(None)
        units,raw=expected['units'],expected['raw']
        observed=partition(units,ids,config['width'],config['height'],'final')
        require(row==dict(tick=tick,source_tick=anchor+tick,physical=expected,site_ids=ids,observation=observed),'identity/observation record')
        series[tick]=observed['components']['material']
    require(read(root/'final.json')==dict(tick=horizon,source_tick=anchor+horizon,units=units,raw=raw,site_ids=ids,parents=parents,death_ticks=deaths),'final identities/ancestry/deaths')
    records=continuity(series,parents)
    require(read(root/'continuity.json')==records,'continuity records')
    eligible=[r for r in records if r['anchor_size']>1 and not r['whole_world_anchor']]
    n=len(eligible)
    c=sum(r['continuous_closed_multi'] for r in eligible)
    r=sum(r['primary'] for r in eligible)
    summary=dict(eligible_components=n,continuous_closed_multi=c,continuous_fraction=c/n if n else None,
        continuous_replacement=r,continuous_replacement_fraction=r/n if n else None)
    require(read(root/'summary.json')==summary,'summary')
    require(hashes(source)==original_source and hashes(root)==original_output,'audit inputs changed')
    return dict(scope='independent physical/hereditary records, birth ancestry, final material partitions and continuity',
        ticks=horizon,components=len(records),summary=summary,input_sha256=original_source,
        output_sha256=meta['output_sha256'],auditor_sha256=sha256(Path(__file__).read_bytes()).hexdigest())
