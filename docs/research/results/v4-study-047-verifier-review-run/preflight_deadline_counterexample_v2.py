"""独立反例v2：显式缩放Guard及Epoch预算；真实可中断预检未被预算覆盖。"""
import functools,json,sys,time,traceback
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path.cwd()))
from scripts import verify_v4_middle_withdrawal as v
from scripts import middle_withdrawal_inputs as inputs
base=Path(__file__).parent; out=base/'preflight-expired-epoch-v2'
limit=.2;delay=.5;error=None;real_epoch=v.Epoch
start=time.monotonic()
def slow_gate(mode):
    time.sleep(delay)
    return []
# Epoch's default seconds is definition-bound, so explicitly scale both guards.
with patch.object(inputs,'SECONDS',limit),patch.object(v,'Epoch',functools.partial(real_epoch,seconds=limit)),patch.object(v,'check_no_other_process'),patch.object(inputs,'execution_gates',side_effect=slow_gate),patch.object(v,'draw_future',side_effect=AssertionError('no future')) as future,patch.object(v,'physical_step',side_effect=AssertionError('no physics')) as physics:
    try:v.run('engineering',base/'absent-synthetic-producer',out)
    except BaseException as e:error={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}
    future.assert_not_called();physics.assert_not_called()
elapsed=time.monotonic()-start
record={'configured_route_seconds':limit,'epoch_route_seconds':limit,'interruptible_gate_delay_seconds':delay,'elapsed_seconds':elapsed,'error':error,'output_exists':out.exists(),'output_files':[str(p.relative_to(out)) for p in out.rglob('*') if p.is_file()],'future_calls':future.call_count,'physical_calls':physics.call_count,'status':'FAIL' if elapsed>limit*1.5 else 'PASS','supersedes_interpretation_only':'v1未显式缩放Epoch定义绑定的默认600s，不能单独证明总预算失败；原证据保留。'}
(base/'preflight-deadline-counterexample-v2.json').write_text(inputs.canonical(record)+'\n')
print(json.dumps(record,ensure_ascii=False))
assert record['status']=='PASS','可中断阶段预检未受同一总预算约束，且预算用尽后错误epoch为空'
