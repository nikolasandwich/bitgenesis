"""审查反例：可中断的阶段预检仍在安装预算计时器前无界执行。"""
import json,sys,time,traceback
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path.cwd()))
from scripts import verify_v4_middle_withdrawal as v
from scripts import middle_withdrawal_inputs as inputs
base=Path(__file__).parent; out=base/'preflight-expired-epoch'
limit=.2;delay=.5;error=None
start=time.monotonic()
def slow_gate(mode):
    time.sleep(delay)
    return []
with patch.object(inputs,'SECONDS',limit),patch.object(v,'check_no_other_process'),patch.object(inputs,'execution_gates',side_effect=slow_gate),patch.object(v,'draw_future',side_effect=AssertionError('no future')) as future,patch.object(v,'physical_step',side_effect=AssertionError('no physics')) as physics:
    try:v.run('engineering',base/'absent-synthetic-producer',out)
    except BaseException as e:error={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}
    future.assert_not_called();physics.assert_not_called()
elapsed=time.monotonic()-start
record={'configured_route_seconds':limit,'interruptible_gate_delay_seconds':delay,'elapsed_seconds':elapsed,'error':error,'output_exists':out.exists(),'output_files':[str(p.relative_to(out)) for p in out.rglob('*') if p.is_file()],'future_calls':future.call_count,'physical_calls':physics.call_count,'expectation':'可中断预检应受同一总预算约束并为阶段失败保留错误证据','status':'FAIL' if elapsed>limit*1.5 else 'PASS'}
(base/'preflight-deadline-counterexample.json').write_text(inputs.canonical(record)+'\n')
print(json.dumps(record,ensure_ascii=False))
assert record['status']=='PASS','阶段预检未受run开始的绝对预算中断'
