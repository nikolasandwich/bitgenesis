"""独立复审：只用合成故障与过去不可变证据；没有真实047未来。"""
import json
from pathlib import Path
import signal
import sys
import tempfile
import time
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from scripts import middle_withdrawal_inputs as i
from scripts import run_v4_middle_withdrawal as p
HERE=Path(__file__).resolve().parent
observations=[]
def record(name,**values):
    result=dict(name=name,**values); observations.append(result)
    print(json.dumps(result,ensure_ascii=False))

def bindings():
    report=i.read('docs/research/results/v4-study-047-producer-review-initial.json')
    preserved=i.read('docs/research/results/v4-study-047-producer-implementation/rejected-epoch-1/preservation.json')
    mapping={f['source']:f['archive'] for f in preserved['files']}
    i.same(i.digest(preserved['review']),preserved['review_sha256'])
    for path,h in report['files_sha256'].items(): i.same(i.digest(mapping.get(path,path)),h,path)
    for path,h in report['review_evidence_sha256'].items(): i.same(i.digest(path),h,path)
    current=i.bindings(include_verifier=False)
    validation=i.read('docs/research/results/v4-study-047-producer-implementation/final-validation-remediated.json')
    i.same(current,validation['full_source_bindings_before'])
    i.same(current,validation['all_input_sha256_after'])
    i.same(validation['code_sha256'],validation['final_code_sha256'])
    for path,h in validation['code_sha256'].items(): i.same(i.digest(path),h,path)
    paths=set(current)|set(validation['code_sha256'])|{preserved['review']}
    for dirname in ('docs/research/results/v4-study-047-producer-implementation','docs/research/results/v4-study-047-producer-review-run'):
        paths.update(str(q) for q in Path(dirname).rglob('*') if q.is_file() and '__pycache__' not in str(q))
    hashes,errors,first=i.capture(paths)
    assert first is None and not errors
    (HERE/'initial-bindings.json').write_text(json.dumps(hashes,indent=2)+'\n')
    record('immutable_history_and_current',prior_bindings=len(report['files_sha256']),prior_review_evidence=len(report['review_evidence_sha256']),mapping_count=len(mapping),current_source_bindings=len(current),review_bindings=len(hashes))

def check_processes():
    for command in ('python -m scripts.run_v4_middle_withdrawal --mode formal','python -u -B scripts/run_v4_middle_withdrawal.py','python -X dev -W ignore -m scripts.verify_v4_middle_withdrawal','python unrelated.py scripts/run_v4_middle_withdrawal.py'):
        rejected=False
        with patch.object(p.subprocess,'check_output',return_value='999999 '+command):
            try: p.check_no_other_process()
            except ValueError: rejected=True
        record('process_guard',command=command,rejected=rejected)

def failed_release_and_recovery():
    first=SystemExit('synthetic release restore failure')
    later=KeyboardInterrupt('synthetic recovery install failure')
    count=0
    def handler(*args):
        nonlocal count
        count+=1
        if count==2: raise first
        if count==3: raise later
    backend=SimpleNamespace(SIGALRM=14,ITIMER_REAL=0,getsignal=lambda _:None,signal=handler,
                            setitimer=lambda *args:None,getitimer=lambda _:(0.0,0.0))
    with tempfile.TemporaryDirectory() as d,patch.object(p,'signal',backend):
        deadline=p.RouteDeadline(time.monotonic(),2)
        epoch=p.Epoch(Path(d)/'epoch',seconds=2,deadline=deadline)
        try: epoch.execute(lambda:None)
        except SystemExit as caught: assert caught is first
        else: raise AssertionError('missing first release failure')
        disk=i.read(epoch.root/'metadata.json')
        record('release_and_recovery_failure',in_memory_status=epoch.meta['status'],disk_status=disk['status'],
               failure_file_exists=(epoch.root/'failure.json').exists(),timer_handler_calls=count,
               retry_release_succeeded=not deadline.installed,errors=epoch.meta['finalization_errors'])
        (HERE/'release-recovery-disk-metadata.json').write_text(json.dumps(disk,indent=2)+'\n')
        (HERE/'release-recovery-memory-metadata.json').write_text(json.dumps(epoch.meta,indent=2)+'\n')

def bounded_closing():
    with tempfile.TemporaryDirectory() as d:
        started=time.monotonic(); deadline=p.RouteDeadline(started,0.3)
        epoch=p.Epoch(Path(d)/'epoch',seconds=0.3,deadline=deadline)
        first=ValueError('original work failure')
        def work(): raise first
        with patch.object(epoch,'output_hashes',side_effect=lambda:time.sleep(1)):
            try: epoch.execute(work)
            except ValueError as caught: assert caught is first
            else: raise AssertionError('missing work failure')
        elapsed=time.monotonic()-started
        meta=i.read(epoch.root/'metadata.json')
        assert elapsed<0.3 and meta['status']=='failed' and 'output_hashes' in meta['finalization_errors']
        record('bounded_closing_hash',elapsed_seconds=elapsed,budget_seconds=0.3,status=meta['status'],first_exception_preserved=True)

def checkpoint_failure():
    first=KeyboardInterrupt('state capture')
    rng=i.new_stream(987654,'directions')
    class Bad:
        def randrange(self,n): return rng.randrange(n)
        def getstate(self): raise first
    streams=dict(directions=Bad(),feeds=i.new_stream(987654,'feeds'))
    state=dict(natural_tape=[])
    try: p.future_tape(streams,partial=state['natural_tape'],checkpoint=state)
    except KeyboardInterrupt as caught: assert caught is first
    else: raise AssertionError('missing state failure')
    assert state['status']=='failed' and 'feeds' in state['current_stream_states']
    record('checkpoint_failure',status=state['status'],completed_synthetic_ticks=len(state['natural_tape']),preserved_states=list(state['current_stream_states']),errors=state['state_capture_errors'])

bindings()
check_processes()
bounded_closing()
checkpoint_failure()
failed_release_and_recovery()
(HERE/'observations.json').write_text(json.dumps(dict(observations=observations,synthetic_physical_steps=0,
    synthetic_future_generator_ticks=32,synthetic_rng_seed=987654,real_study047_future_physical_steps=0,
    real_study047_future_generator_ticks=0),ensure_ascii=False,indent=2)+'\n')
