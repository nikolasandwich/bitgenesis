"""Extract descriptive report tables only from saved, audited formal objects."""
from pathlib import Path
from collections import Counter
import hashlib,json
R=Path('/Users/todd/Documents/bitgenesis');B=R/'data/v4-study-047';a=json.loads((B/'audit.json').read_bytes());assert a['status']=='PASS'
arms=('continue_north','withdraw_to_natural');pairs=a['pairs'];summary=a['summary']
counts={arm:dict(arm_count=28,intervals=sum(len(p['arms'][arm]['intervals']) for p in pairs),double_ticks=sum(sum(q>=2 for q in p['arms'][arm]['new_copy_counts']) for p in pairs),no_double_window=sum(not p['arms'][arm]['intervals'] for p in pairs),left_censored=sum(i['left_censored_at_boundary'] for p in pairs for i in p['arms'][arm]['intervals']),right_censored=sum(i['right_censored'] for p in pairs for i in p['arms'][arm]['intervals']),cross_boundary=sum(p['arms'][arm]['cross_boundary'] is not None for p in pairs),max_longest=max(p['arms'][arm]['longest_double'] for p in pairs),initial_energy=sum(p['arms'][arm]['ledger']['initial_energy'] for p in pairs),initial_living=sum(p['arms'][arm]['ledger']['initial_living'] for p in pairs),failure_counts=dict(sum((Counter(p['arms'][arm]['failure_counts']) for p in pairs),Counter()))) for arm in arms}
q_differ=[dict(encoding=p['encoding'],seed=p['seed'],ticks=[33+i for i,(x,y) in enumerate(zip(p['arms'][arms[0]]['new_copy_counts'],p['arms'][arms[1]]['new_copy_counts'])) if x!=y]) for p in pairs if p['arms'][arms[0]]['new_copy_counts']!=p['arms'][arms[1]]['new_copy_counts']]
metric_differ=[dict(encoding=p['encoding'],seed=p['seed']) for p in pairs if any(p['delta'].values())]
short=[dict(encoding=x['encoding'],seed=x['seed'],t0=x['t0'],remaining=x['remaining']) for x in json.loads((B/'producer/index.json').read_bytes()) if x['short_window']]
science_nodes=sum(x['compared_nodes'] for x in a['complete_scientific_artifacts'])
source=a['reused_validation'][0]['current_execution_source_bindings']
focus=[]
for p in pairs:
 if p['encoding']=='homogeneous' and p['seed'] in (120003,120011,120015):
  focus.append({k:p[k] for k in ('encoding','seed','case','arms','delta')})
obj=dict(status='PASS',scientific_steps=0,source_audit_sha256=hashlib.sha256((B/'audit.json').read_bytes()).hexdigest(),complete_scientific_object_nodes=science_nodes,all_scientific_original_bytes_equal=all(x['original_bytes_identical'] for x in a['complete_scientific_artifacts']),arm_window_counts=counts,q_sequence_different_pairs=q_differ,any_recorded_metric_different_pairs=metric_differ,original_short_windows=short,current_five_source_hashes=source,focus=focus,interpretation='仅已冻结28条件配对/14共享环境的描述；q差和记录指标差不等同于全部物理轨迹差。')
with (B/'report-analysis.json').open('x') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in obj.items() if k!='focus'},ensure_ascii=False))
