"""Reaudit the full variation cohort and sample actual descendant/founder pairs."""
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from bitgenesis.v4.lineage import trace


def select(lineage,seed,drive,mutation):
    records=lineage['individuals']
    eligible=[r for r in records if r['death_tick'] is None and r['parent'] is not None]
    def key(r):
        return sha256(f"v4-ancestor-selection-1:{seed}:{drive}:{mutation}:{r['id']}".encode('ascii')).hexdigest(),r['id']
    pairs=[]
    for record in sorted(eligible,key=key)[:3]:
        chain=[]
        cursor=record
        while cursor['parent'] is not None:
            chain.append(cursor['parent'])
            cursor=records[cursor['parent']]
        if cursor['id']!=record['founder']:
            raise ValueError('founder/chain mismatch')
        pairs.append(dict(selection_hash=key(record)[0],descendant=record,founder=cursor,
                          parent_chain=chain,equal_program=record['program']==cursor['program']))
    return dict(eligible=len(eligible),status='available' if eligible else 'unavailable',pairs=pairs)


def main():
    root=Path('data/v4-study-005')
    output=Path('data/v4-study-005-lineage')
    meta=json.loads((root/'metadata.json').read_text())
    rows=json.loads((root/'results.json').read_text())
    if (meta['status'],meta['completed_runs'])!=('complete',20) or len(rows)!=20:
        raise ValueError('incomplete source cohort')
    if {(r['seed'],r['drive'],r['mutation']) for r in rows}!=set(product(range(96000,96005),(250,500),(0,100))):
        raise ValueError('source grid mismatch')
    output.mkdir(parents=True,exist_ok=False)
    selections=[]
    for r in rows:
        name=f"seed-{r['seed']}-drive-{r['drive']}-mutation-{r['mutation']}"
        source=root/name
        m=json.loads((source/'metadata.json').read_text())
        if m['git_commit']!=meta['git_commit'] or m['git_dirty'] is not False:
            raise ValueError('source commit mismatch')
        for file,digest in m['source_sha256'].items():
            if sha256((Path('src/bitgenesis/v4')/file).read_bytes()).hexdigest()!=digest:
                raise ValueError('historical source bytes changed')
        lineage=trace(source)
        if lineage['dynamics_audit']['summary']!=r['summary']:
            raise ValueError('source summary mismatch')
        path=output/(name+'.json')
        path.write_text(json.dumps(lineage,indent=2)+'\n',encoding='utf-8')
        selections.append(dict(seed=r['seed'],drive=r['drive'],mutation=r['mutation'],
            lineage_sha256=sha256(path.read_bytes()).hexdigest(),
            source_output_sha256=lineage['dynamics_audit']['output_sha256'],
            lineage_summary=lineage['summary'],**select(lineage,r['seed'],r['drive'],r['mutation'])))
        print(f'{len(selections)}/20 {name}',flush=True)
    result=dict(status='complete',sources=selections,
        selection_protocol_sha256=sha256(Path('experiments/v4/ancestral-assay-selection.md').read_bytes()).hexdigest(),
        source_results_sha256=sha256((root/'results.json').read_bytes()).hexdigest(),
        script_sha256=sha256(Path(__file__).read_bytes()).hexdigest())
    (output/'selection.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()
