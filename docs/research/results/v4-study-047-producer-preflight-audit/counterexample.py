"""生产依赖只读审查：可中断阶段预检的绝对预算/失败证据反例。"""
import json,signal,sys,time,traceback
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path.cwd()))
from scripts import run_v4_middle_withdrawal as producer
from scripts import middle_withdrawal_inputs as inputs
root=Path(__file__).parent;output=root/'failed-epoch'
limit=.2;delay=.5;error=None;observed=[];real_epoch=producer.Epoch
files=['scripts/run_v4_middle_withdrawal.py','scripts/middle_withdrawal_inputs.py','tests/test_v4_middle_withdrawal.py','docs/research/results/v4-study-047-producer-review.json']
before={p:inputs.digest(p) for p in files}
handler_before=signal.getsignal(signal.SIGALRM)
def gate(mode):
    time.sleep(delay)
    return []
def epoch(*args,**kwargs):
    deadline=kwargs['deadline']
    observed.append({'epoch_seconds':kwargs['seconds'],'deadline_seconds':deadline.seconds,'reserve_seconds':deadline.reserve,'deadline_minus_start':deadline.end-deadline.started,'installed_before_epoch':deadline.installed})
    assert kwargs['seconds']==deadline.seconds==limit
    return real_epoch(*args,**kwargs)
start=time.monotonic()
with patch.object(inputs,'SECONDS',limit),patch.object(producer,'Epoch',side_effect=epoch),patch.object(producer,'check_no_other_process'),patch.object(inputs,'execution_gates',side_effect=gate),patch.object(producer,'future_tape',side_effect=AssertionError('future forbidden')) as future,patch.object(producer,'step',side_effect=AssertionError('physics forbidden')) as physics,patch.object(producer,'run_pair',side_effect=AssertionError('science forbidden')) as pair:
    try:producer.run('engineering',output)
    except BaseException as e:error={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}
    future.assert_not_called();physics.assert_not_called();pair.assert_not_called()
elapsed=time.monotonic()-start
after={p:inputs.digest(p) for p in files};inputs.same(before,after,'生产代码和原批准字节不变')
assert signal.getsignal(signal.SIGALRM)==handler_before
assert signal.getitimer(signal.ITIMER_REAL)==(0.,0.)
result={'status':'FAIL' if elapsed>limit*1.5 else 'PASS','configured_total_seconds':limit,'ordinary_interruptible_gate_sleep_seconds':delay,'elapsed_seconds':elapsed,'observed_budget_dimensions':observed,'error':error,'output_exists':output.exists(),'output_files':[str(p.relative_to(output)) for p in output.rglob('*') if p.is_file()],'calls':{'future_tape':future.call_count,'step':physics.call_count,'run_pair':pair.call_count},'real_study047_future_ticks':0,'real_new_or_replayed_physical_steps':0,'synthetic_future_ticks':0,'synthetic_physical_steps':0,'files_sha256':before,'files_sha256_after':after,'data_v4_study047_exists':Path('data/v4-study-047').exists()}
with (root/'counterexample-result.json').open('x') as f:f.write(inputs.canonical(result)+'\n')
print(json.dumps(result,ensure_ascii=False))
assert result['status']=='PASS','生产阶段预检在安装deadline前超出统一总预算并留下空epoch'
