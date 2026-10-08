"""Independent recount of saved study010 records and hierarchical aggregates."""
import json
from fractions import Fraction
from pathlib import Path
from hashlib import sha256
from collections import defaultdict
root=Path('data/v4-study-010')
load=lambda p:json.loads(p.read_text())
meta=load(root/'metadata.json')
assert meta['status']=='complete' and meta['completed_sources']==20
rows=load(root/'results.json'); totals=0; per_source={}; panels_count=0
fields=('primary','continuous_closed_multi','complete_replacement','endpoint_closed_after_break','endpoint_closed_multi','endpoint_extinct','whole_world_anchor')
for source in rows:
 path=root/source['file'];assert sha256(path.read_bytes()).hexdigest()==source['sha256']
 data=load(path); summary={(s['phase'],s['boundary'],s['anchor'],s['horizon'],s['stratum']):s for s in source['summary']}
 collectors=defaultdict(list)
 for panel in data['panels']:
  panels_count+=1;totals+=len(panel['records'])
  for stratum in ('singleton','multi'):
   records=[r for r in panel['records'] if (r['anchor_size']==1)==(stratum=='singleton')]
   key=(panel['phase'],panel['boundary'],panel['anchor'],panel['horizon'],stratum)
   actual=summary[key];assert actual['components']==len(records)
   for field in fields:
    if field in ('endpoint_closed_multi','endpoint_extinct'):
     n=sum(r['endpoint']['state']==field[len('endpoint_'):] for r in records)
    else:n=sum(r[field] for r in records)
    expected=Fraction(n,len(records)) if records else None
    assert actual['counts'][field]==n
    assert actual['fractions'][field]==(str(expected) if expected is not None else None)
    collectors[(panel['phase'],panel['boundary'],panel['horizon'],stratum,field)].append(expected)
   for name, get in [('anchor_members',lambda r:r['anchor_size']),('original_survivors',lambda r:r['endpoint']['original_survivors']),('represented_anchor_members',lambda r:r['endpoint']['represented_anchor_members']),('descendants',lambda r:r['endpoint']['descendants']),('all_anchor_members_represented',lambda r:r['endpoint']['represented_anchor_members']==r['anchor_size']),('non_world_primary',lambda r:r['primary'] and not r['whole_world_anchor'])]:
    assert actual[name]==sum(get(r) for r in records)
 for key,values in collectors.items():
  assert len(values)==4
  available=[v for v in values if v is not None]
  per_source[(source['seed'],source['drive'],source['mutation'],*key)]=(sum(available)/len(available) if available else None,len(available))
report=load(root/'summary.json')
for row in report['source_means']:
 for field in fields:
  value,n=per_source[(row['seed'],row['drive'],row['mutation'],row['phase'],row['boundary'],row['horizon'],row['stratum'],field)]
  assert row['metrics'][field]==dict(mean=str(value) if value is not None else None,available=n,missing=4-n)
for row in report['groups']:
 for field in fields:
  values=[per_source[(s,row['drive'],row['mutation'],row['phase'],row['boundary'],row['horizon'],row['stratum'],field)][0] for s in range(96000,96005)]
  available=[v for v in values if v is not None]
  assert row['metrics'][field]==dict(mean=str(sum(available)/len(available)) if available else None,available=len(available),missing=5-len(available))
proof=dict(status='complete',sources=len(rows),panels=panels_count,component_windows=totals,
 summary_sha256=sha256((root/'summary.json').read_bytes()).hexdigest(),results_sha256=sha256((root/'results.json').read_bytes()).hexdigest(),
 verifier_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),scope='independent saved-record recount and exact anchor/source/group aggregation')
with (root/'aggregation-verification.json').open('x', encoding='utf-8') as stream:
    stream.write(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof))
