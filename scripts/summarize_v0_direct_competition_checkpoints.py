"""All registered direct-competition checkpoints after full cohort verification."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
if __package__:
    from .verify_v0_direct_competition_histories import source_contrasts
else:
    from verify_v0_direct_competition_histories import source_contrasts

CHECKPOINTS=(0,100,500,1000,5000,10000)


def summarize(observations,sources):
    expected={(s,r,w,t) for s in sources for r in range(5) for w in (0,1) for t in CHECKPOINTS}
    if len(observations)!=len(expected) or {(r['source_seed'],r['replicate'],r['swap'],r['tick']) for r in observations}!=expected:
        raise ValueError('Incomplete or duplicate checkpoint grid')
    checkpoints=[]
    for tick in CHECKPOINTS:
        selected=[r for r in observations if r['tick']==tick]
        comparison=source_contrasts(selected,sources)
        counts={status:sum(r['status']==status for r in comparison['runs']) for status in
                ('both_present','sampled_only','ancestor_only','both_extinct')}
        checkpoints.append(dict(tick=tick,**comparison,status_counts=counts))
    return checkpoints


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path('data/campaign-024'))
    parser.add_argument('--verification',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    load=lambda p:json.loads(p.read_text(encoding='utf-8'))
    mp=root/'docs/research/results/campaign-023-samples.json'
    manifest=load(mp);gate=load(args.verification)
    sources={s['source_seed'] for s in manifest['samples'] if s['available']}
    if gate['manifest_sha256']!=sha(mp) or gate['metric_rows_checked']!=len(sources)*10*10001 or gate['input_sha256']['metadata.json']!=sha(args.input/'metadata.json'):
        raise ValueError('Full verification linkage differs')
    grid={(s,r,w) for s in sources for r in range(5) for w in (0,1)}
    for rows in (gate['histories'],gate['runs']):
        if len(rows)!=len(grid) or {(r['source_seed'],r['replicate'],r['swap']) for r in rows}!=grid:
            raise ValueError('Incomplete verification grid')
    observations=[];hashes={}
    identity=('source_seed','replicate','swap','seed','sampled_trait','ancestor_trait','sampled_individual_id','source_founder_id')
    for source,replicate,swap in sorted(grid):
        relative=f'source-{source}-replicate-{replicate}-swap-{swap}/result.json'
        p=args.input/relative;digest=sha(p)
        if gate['input_sha256'][relative]!=digest:raise ValueError('Verified checkpoint input changed')
        hashes[relative]=digest;result=load(p)
        for tick,obs in result['observations'].items():
            if int(tick)!=obs['tick']:raise ValueError('Checkpoint key differs')
            observations.append(dict(**{k:result[k] for k in identity},**obs))
    checkpoints=summarize(observations,sources)
    last=checkpoints[-1]
    for key in ('runs','pairs','sources','mean_source_contrast','positive_sources','negative_sources','zero_sources'):
        if last[key]!=gate[key]:raise ValueError('Terminal checkpoint differs from primary analysis')
    report=dict(scope='All six preregistered checkpoints; every source, repeat, allocation and extinct group retained. Intermediate abundance contrasts are secondary; terminal10000 remains primary. Repeats and swaps are nested, not independent evolutionary samples.',
        observations=observations,checkpoints=checkpoints,input_sha256=hashes,
        verification_sha256=sha(args.verification),script_sha256=sha(Path(__file__)))
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    compact=[]
    for r in observations:
        row={k:v for k,v in r.items() if k!='groups' and not k.endswith('_histogram')}
        for group,values in r['groups'].items():
            row.update({group+'_'+k:v for k,v in values.items() if not k.endswith('_histogram')})
        compact.append(row)
    if compact:
        with (args.output/'checkpoints.csv').open('w',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(compact[0]));writer.writeheader();writer.writerows(compact)
    print(f'Summarized {len(observations)} observations across six registered checkpoints')


if __name__=='__main__':main()
