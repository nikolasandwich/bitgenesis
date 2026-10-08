"""第三轮独立复审：精确R5反例及原绝对截止时间；0科学物理/随机抽签。"""
import json
from pathlib import Path
import signal
import sys
import tempfile
import time
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts import middle_withdrawal_inputs as i
from scripts import run_v4_middle_withdrawal as p
HERE=Path(__file__).resolve().parent
OBS=[]
def record(name,**data):
    row=dict(name=name,**data);OBS.append(row);print(json.dumps(row,ensure_ascii=False))

def history_and_current():
    histories=[('docs/research/results/v4-study-047-producer-review-initial.json',1),('docs/research/results/v4-study-047-producer-review-round2.json',2)]
    checked=[]
    for reportpath,number in histories:
        report=i.read(reportpath)
        archive=i.read(f'docs/research/results/v4-study-047-producer-implementation/rejected-epoch-{number}/preservation.json')
        src,arc=('source','archive') if number==1 else ('source_path','archive_path')
        mapping={x[src]:x[arc] for x in archive['files']}
        i.same(i.digest(reportpath),archive['review_sha256'])
        i.same(report['files_sha256'],report['files_sha256_after'])
        for filename,h in report['files_sha256'].items():i.same(i.digest(mapping.get(filename,filename)),h,filename)
        for filename,h in report['review_evidence_sha256'].items():i.same(i.digest(filename),h,filename)
        checked.append(dict(round=number,source_evidence=len(report['files_sha256']),review_evidence=len(report['review_evidence_sha256']),mapped=3))
    validation=i.read('docs/research/results/v4-study-047-producer-implementation/final-validation-remediated2.json')
    current=i.bindings(include_verifier=False)
    i.same(current,validation['full_source_bindings_before']);i.same(current,validation['all_input_sha256_after'])
    i.same(validation['code_sha256'],validation['final_code_sha256'])
    for filename,h in validation['code_sha256'].items():i.same(i.digest(filename),h,filename)
    for filename,h in validation['prior_evidence_sha256'].items():i.same(i.digest(filename),h,filename)
    base=Path('docs/research/results/v4-study-047-producer-implementation')
    for run in validation['runs']:
        assert run['exit_code']==0
        err=(base/(run['label']+'.stderr.txt')).read_text()
        if run['label']=='remediation2-full-suite':assert 'Ran 1013 tests in 62.356s' in err and err.rstrip().endswith('OK')
        if run['label']=='remediation2-final-targeted':assert 'Ran 47 tests in 1.169s' in err and err.rstrip().endswith('OK')
    paths=set(current)|set(validation['code_sha256'])|{s for s,_ in histories}
    for dirname in ('docs/research/results/v4-study-047-producer-implementation','docs/research/results/v4-study-047-producer-review-run','docs/research/results/v4-study-047-producer-review-round2-run'):
        paths.update(str(q) for q in Path(dirname).rglob('*') if q.is_file() and '__pycache__' not in str(q))
    hashes,errors,first=i.capture(paths);assert first is None and not errors
    (HERE/'initial-bindings.json').write_text(json.dumps(hashes,indent=2)+'\n')
    record('source_history_and_current',previous=checked,current_sources=len(current),current_review_inputs=len(hashes),same_code_full_suite=1013,same_code_targeted=47)

def exact_r5(earlier=None):
    first=SystemExit('release');later=KeyboardInterrupt('recovery');calls=[]
    def handler(*args):
        calls.append(args)
        if len(calls)==2:raise first
        if len(calls)==3:raise later
    backend=SimpleNamespace(SIGALRM=14,ITIMER_REAL=0,getsignal=lambda _:None,signal=handler,setitimer=lambda *args:None,getitimer=lambda _:(0.,0.))
    with tempfile.TemporaryDirectory() as d,patch.object(p,'signal',backend):
        deadline=p.RouteDeadline(time.monotonic(),2)
        epoch=p.Epoch(Path(d)/'epoch',seconds=2,deadline=deadline)
        def work():
            if earlier is not None:raise earlier
        expected=earlier if earlier is not None else first
        try:epoch.execute(work)
        except BaseException as caught:assert caught is expected
        else:raise AssertionError('first failure not raised')
        meta=i.read(epoch.root/'metadata.json');proof=i.read(epoch.root/'failure.json')
        assert meta['status']==proof['status']=='failed'
        assert meta['error']==proof['error']==repr(expected)
        assert meta['finalization_errors']['deadline_release']==repr(first)
        assert meta['finalization_errors']['deadline_recovery_handler']==repr(later)
        assert len(calls)==6 and not deadline.installed
        record('exact_old_R5',earlier_work_error=repr(earlier),disk_status=meta['status'],proof_status=proof['status'],handler_calls=len(calls),first_preserved=True,secondary_preserved=True)

def native_r5(blocked_proof=False):
    native=signal.signal;first=SystemExit('native release');later=KeyboardInterrupt('native recovery');calls=[]
    def handler(*args):
        calls.append(args)
        if len(calls)==2:raise first
        if len(calls)==3:raise later
        return native(*args)
    with tempfile.TemporaryDirectory() as d:
        started=time.monotonic();deadline=p.RouteDeadline(started,0.4)
        writes=[]
        with patch.object(p.signal,'signal',side_effect=handler):
            epoch=p.Epoch(Path(d)/'epoch',seconds=0.4,deadline=deadline)
            original=epoch._write
            def write(name,value,**kwargs):
                active=signal.getitimer(signal.ITIMER_REAL)[0]>0
                writes.append(dict(name=name,status=value.get('status'),timer_active=active))
                if blocked_proof and name=='failure.json':time.sleep(1)
                return original(name,value,**kwargs)
            with patch.object(epoch,'_write',side_effect=write):
                try:epoch.execute(lambda:None)
                except BaseException as caught:assert caught is first
                else:raise AssertionError('first native release error not raised')
        elapsed=time.monotonic()-started
        meta=i.read(epoch.root/'metadata.json')
        assert meta['status']=='failed' and meta['error']==repr(first)
        assert writes and all(w['timer_active'] for w in writes)
        assert elapsed<0.4 and not deadline.installed and signal.getitimer(signal.ITIMER_REAL)==(0.,0.)
        if blocked_proof:assert 'release_failure_evidence_second' in epoch.meta['finalization_errors']
        else:assert i.read(epoch.root/'failure.json')['status']=='failed'
        label='native_R5_blocked_failure_proof' if blocked_proof else 'native_R5_successful_failed_persistence'
        record(label,elapsed_seconds=elapsed,total_budget=0.4,original_end_unchanged=deadline.end==started+0.4,
               disk_status=meta['status'],first_preserved=True,all_writes_protected=True,
               writes=writes,proof_exists=(epoch.root/'failure.json').exists(),errors=epoch.meta['finalization_errors'])
        (HERE/(label+'-metadata.json')).write_text(json.dumps(meta,indent=2)+'\n')
        (HERE/(label+'-memory.json')).write_text(json.dumps(epoch.meta,indent=2)+'\n')

def expired_action():
    start=time.monotonic();deadline=p.RouteDeadline(start,0.05);deadline.install()
    calls=[]
    try:
        try:deadline.perform(lambda:calls.append('unsafe'), 'already_expired', start-1)
        except i.DeadlineExpired:pass
        else:raise AssertionError('expired action accepted')
    finally:deadline.release()
    assert not calls
    record('expired_action_is_not_started',passed=True,total_budget=0.05,extra_budget=0)

history_and_current()
exact_r5()
exact_r5(ValueError('earlier work failure'))
native_r5()
native_r5(blocked_proof=True)
expired_action()
assert not Path('data/v4-study-047').exists()
(HERE/'observations.json').write_text(json.dumps(dict(observations=OBS,synthetic_physical_steps=0,synthetic_future_generator_ticks=0,real_study047_future_physical_steps=0,real_study047_future_generator_ticks=0),indent=2,ensure_ascii=False)+'\n')
