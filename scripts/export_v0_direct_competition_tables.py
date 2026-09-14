"""Export complete verified competition comparisons as human-readable CSV tables."""
import argparse
from collections import Counter
from fractions import Fraction
import csv
import hashlib
import json
from pathlib import Path
if __package__:
    from .verify_v0_direct_competition_histories import source_contrasts
else:
    from verify_v0_direct_competition_histories import source_contrasts


def tables(gate,manifest):
    samples={s['source_seed']:s['selected'] for s in manifest['samples'] if s['available']}
    if gate['available_sources']!=len(samples) or gate['metric_rows_checked']!=len(samples)*100010:
        raise ValueError('Incomplete cohort evidence')
    raw=[dict(source_seed=r['source_seed'],replicate=r['replicate'],swap=r['swap'],
        groups={'sampled':{'population':r['sampled_population']},'ancestor':{'population':r['ancestor_population']}}) for r in gate['runs']]
    checked=source_contrasts(raw,set(samples))
    if any(gate[k]!=v for k,v in checked.items()):raise ValueError('Comparison data differs')
    rows=[]
    for item in checked['sources']:
        source=item['source_seed'];sample=samples[source]
        counts=Counter(r['status'] for r in checked['runs'] if r['source_seed']==source)
        rows.append(dict(source_seed=source,sampled_trait=sample['genome'],ancestor_trait=sample['founder_genome'],
            sampled_individual_id=sample['id'],source_founder_id=sample['founder_id'],
            **{k:counts[k] for k in ('both_present','sampled_only','ancestor_only','both_extinct')},
            source_contrast=item['contrast']))
    return {'sources':rows,'pairs':checked['pairs'],'runs':checked['runs']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verification',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    mp=root/'docs/research/results/campaign-023-samples.json'
    manifest=json.loads(mp.read_text(encoding='utf-8'));gate=json.loads(args.verification.read_text(encoding='utf-8'))
    if gate['manifest_sha256']!=sha(mp):raise ValueError('Manifest linkage differs')
    exported=tables(gate,manifest)
    args.output.mkdir(parents=True,exist_ok=False)
    for name,rows in exported.items():
        if rows:
            with (args.output/f'{name}.csv').open('w',encoding='utf-8',newline='') as stream:
                writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    mean=gate['mean_source_contrast']
    interpretation='undefined: no available source' if mean is None else 'positive directional prediction supported in this finite cohort' if Fraction(mean)>0 else 'positive directional prediction unsupported in this finite cohort'
    report=dict(scope='Complete tabular export of all verified source, allocation-pair and run comparisons. Exact rational strings retained; no subset selection or statistical significance claim.',
        available_sources=gate['available_sources'],mean_source_contrast=mean,interpretation=interpretation,
        rows={k:len(v) for k,v in exported.items()},verification_sha256=sha(args.verification),manifest_sha256=sha(mp),
        output_sha256={p.name:sha(p) for p in sorted(args.output.glob('*.csv'))},script_sha256=sha(Path(__file__)))
    (args.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report['rows']))


if __name__=='__main__':main()
