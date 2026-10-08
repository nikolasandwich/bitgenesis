"""独立审查：只读取真实过去票和保存的身份/组件前缀，禁止未来与物理。"""
import hashlib,json,sys,time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path.cwd()))
from scripts import middle_withdrawal_inputs as inputs
from scripts import verify_v4_middle_withdrawal as verifier
out=Path(__file__).parent
start=time.monotonic()
before=inputs.bindings(True)
source=inputs.read(inputs.SOURCES); census=inputs.read(inputs.CENSUS)
rows=[]; environment_rows=[]
with patch.object(verifier,'draw_future',side_effect=AssertionError('真实未来抽签禁止')) as future, patch.object(verifier,'physical_step',side_effect=AssertionError('真实或重放物理禁止')) as physics:
    for env in census['environments']:
        originals={k:inputs.read(inputs.source_path(p)) for k,p in env['origin_paths'].items()}
        streams=verifier.restore_environment(env,originals,source['runtime'])
        environment_rows.append({'seed':env['seed'],'past_ticks':len(originals['random-direction']['rows']),'state_sha256':{k:inputs.object_hash(verifier.json_value(v.getstate())) for k,v in streams.items()}})
    for item in census['cases']:
        if not item['trigger']: continue
        boundary=inputs.load_boundary(item)
        prefix=verifier.reconstruct_prefix(boundary)
        rows.append({'encoding':item['encoding'],'seed':item['seed'],'original_t0':item['t0'],'saved_prefix_ticks':len(boundary['prefix_rows']),'prefix_start':boundary['prefix_rows'][0]['tick'] if boundary['prefix_rows'] else None,'prefix_end':boundary['prefix_rows'][-1]['tick'] if boundary['prefix_rows'] else None,'reconstructed_prefix_sha256':inputs.object_hash(prefix),'boundary_final_sha256':inputs.object_hash(boundary['initial']),'full_individuals':len(boundary['initial']['individuals'])})
    future.assert_not_called(); physics.assert_not_called()
    calls={'draw_future':future.call_count,'physical_step':physics.call_count}
after=inputs.bindings(True); inputs.same(before,after,'审查只读来源前后一致')
result={'status':'PASS','environment_count':len(environment_rows),'past_generator_ticks':sum(r['past_ticks'] for r in environment_rows),'saved_prefix_count':len(rows),'saved_prefix_ticks':sum(r['saved_prefix_ticks'] for r in rows),'environments':environment_rows,'prefixes':rows,'forbidden_calls':calls,'real_study047_future_ticks':0,'new_or_replayed_physical_steps':0,'files_sha256':before,'files_sha256_after':after,'elapsed_seconds':time.monotonic()-start,'data_v4_study047_exists':Path('data/v4-study-047').exists()}
with (out/'saved-input-check.json').open('x') as f: json.dump(result,f,sort_keys=True,separators=(',',':'));f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('files_sha256','files_sha256_after','environments','prefixes')},sort_keys=True))
