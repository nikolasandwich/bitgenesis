"""独立2.1审查：仅合成故障/物理；真实047未来抽签和物理均0。"""
import importlib.util
import json
from pathlib import Path
import signal
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from scripts import middle_withdrawal_inputs as inputs
from scripts import run_v4_middle_withdrawal as producer
from bitgenesis.v4.heredity import HeritableUnit
HERE = Path(__file__).resolve().parent
OBSERVATIONS = []
PHYSICS = 0

def record(name, **data):
    OBSERVATIONS.append(dict(name=name, **data))
    print(json.dumps(OBSERVATIONS[-1], ensure_ascii=False))

def verify_bindings():
    current = inputs.bindings(include_verifier=False)
    validation = inputs.read('docs/research/results/v4-study-047-producer-implementation/final-validation.json')
    inputs.same(validation['code_sha256'], validation['final_code_sha256'])
    for p, h in validation['code_sha256'].items(): inputs.same(inputs.digest(p), h, p)
    inputs.same(current, validation['all_input_sha256_after'], 'current full closure')
    inputs.same(current, validation['full_source_bindings_before'], 'before full closure')
    paths = set(current) | set(validation['code_sha256']) | {
        str(p) for p in Path('docs/research/results/v4-study-047-producer-implementation').glob('*') if p.is_file()}
    hashes, errors, first = inputs.capture(paths)
    assert not errors and first is None
    (HERE / 'initial-bindings.json').write_text(json.dumps(hashes, indent=2) + '\n')
    record('current_evidence', source_bindings=len(current), initial_review_bindings=len(hashes),
           method_review_bindings=len(inputs.read(inputs.REVIEW)['files_sha256']),
           full_regression_same_code=validation['runs'][-1], real_future_directory_exists=Path('data/v4-study-047').exists())

def check_proposal_gates():
    global PHYSICS
    units = [None] * 256
    for site, energy in ((0, 2), (50, 40), (51, 10), (100, 40), (102, 40), (200, 40), (16, 40), (17, 1)):
        units[site] = HeritableUnit(0, energy, (0, 1, 2, 3))
    raw = [0] * 256
    raw[1] = raw[101] = 1
    directions = [0] * 256
    directions[102] = 1
    _, stock, event = producer.step(units, raw, proposals=[0] * 256, directions=directions,
        mutation_tickets=[(999, 0, 1)] * 256, exchange=False, **inputs.CONFIG)
    PHYSICS += 1
    physical = producer.normalized(dict(raw=stock, mutation_tickets=inputs.fixed_tickets(), **event))
    gates = producer.proposal_gates(physical)
    for gate in gates:
        expected = ('energy' if not gate['energy_sufficient'] else
                    'occupied' if not gate['target_empty'] else
                    'raw_material' if not gate['raw_available'] else
                    'collision' if not gate['no_collision'] else 'formed')
        assert gate['reason'] == expected, gate
    assert {g['reason'] for g in gates} == set(producer.REASONS)
    formed = next(g for g in gates if g['source'] == 16)
    assert formed['target'] == 17 and formed['reason'] == 'formed' and 17 in event['material']['dissolved']
    record('proposal_gates_all_reasons_and_post_dissolution', passed=True, gates=gates)

def check_absent_sigalrm_regression():
    spec = importlib.util.spec_from_file_location('review_producer_tests', ROOT / 'tests/test_v4_middle_withdrawal.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    names = ('test_post_ownership_git_failure_has_failed_metadata', 'test_signal_setup_failure_after_ownership_is_retained')
    cases = [module.EarlyAndEnvironmentFaultTests(names[0]), module.AdditionalFailureTests(names[1])]
    saved = signal.SIGALRM
    try:
        del signal.SIGALRM
        result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(cases))
    finally:
        signal.SIGALRM = saved
    record('windows_signal_surface_existing_new_tests', ran=result.testsRun,
           failures=len(result.failures), errors=len(result.errors), passed=result.wasSuccessful())

def check_tape_state_capture_failure():
    first = SystemExit('synthetic getstate failure')
    class BadState:
        def __init__(self): self.rng = inputs.new_stream(987654, 'directions')
        def randrange(self, n): return self.rng.randrange(n)
        def getstate(self): raise first
    with tempfile.TemporaryDirectory() as d:
        epoch = producer.Epoch(Path(d) / 'epoch')
        epoch.active_environment = dict(seed=987654, natural_tape=[])
        def work():
            producer.future_tape(dict(directions=BadState(), feeds=inputs.new_stream(987654, 'feeds')),
                epoch.budget, epoch.meta, epoch.active_environment['natural_tape'], epoch.active_environment)
        try: epoch.execute(work)
        except SystemExit as caught: assert caught is first
        else: raise AssertionError('missing original getstate exception')
        meta = inputs.read(epoch.root / 'metadata.json')
        partial = inputs.read(epoch.root / 'partial-environment.json')
        record('failed_checkpoint_nested_complete', epoch_status=meta['status'],
               checkpoint_status=partial['status'], tickets=len(partial['natural_tape']),
               state_capture_error=partial['state_capture_error'], has_current_states='current_stream_states' in partial)

def check_process_tokens():
    commands = (
        '999991 /usr/bin/python3 -m scripts.run_v4_middle_withdrawal --mode engineering --output x',
        '999992 /usr/bin/python3 -u -B scripts/run_v4_middle_withdrawal.py --mode engineering --output x',
        '999993 /usr/bin/python3 scripts/run_v4_middle_withdrawal.py --mode engineering --output x')
    for command in commands:
        rejected = False
        with patch.object(producer.subprocess, 'check_output', return_value=command):
            try: producer.check_no_other_process()
            except ValueError: rejected = True
        record('process_preflight', command=command, rejected=rejected)

def check_closing_alarm():
    # 第一次来源采集前中断；不读取/恢复研究状态，不调用future_tape或step。
    first = RuntimeError('synthetic work stop before input capture')
    observations = {}
    def stop_capture(self, *a, **kw): raise first
    def slow_output_hash(self):
        observations['timer_at_output_hash'] = signal.getitimer(signal.ITIMER_REAL)
        start = time.monotonic()
        time.sleep(0.12)
        observations['uninterrupted_closing_seconds'] = time.monotonic() - start
    with tempfile.TemporaryDirectory() as d, \
         patch.object(producer, 'check_no_other_process'), \
         patch.object(inputs, 'execution_gates', return_value=['synthetic-p', 'synthetic-v']), \
         patch.object(inputs, 'approved_gate'), \
         patch.object(producer.subprocess, 'check_output', return_value='synthetic-commit'), \
         patch.object(inputs, 'SECONDS', 0.05), \
         patch.object(producer.Epoch, 'capture', stop_capture), \
         patch.object(producer.Epoch, 'output_hashes', slow_output_hash):
        try: producer.run('engineering', Path(d) / 'epoch')
        except RuntimeError as caught: assert caught is first
        else: raise AssertionError('first error missing')
        observations['epoch_status'] = inputs.read(Path(d) / 'epoch' / 'metadata.json')['status']
    record('closing_has_no_active_timeout', **observations)

if __name__ == '__main__':
    verify_bindings()
    check_proposal_gates()
    check_absent_sigalrm_regression()
    check_tape_state_capture_failure()
    check_process_tokens()
    check_closing_alarm()
    (HERE / 'adversarial-observations.json').write_text(json.dumps(dict(
        observations=OBSERVATIONS, synthetic_physical_steps=PHYSICS,
        synthetic_future_generator_ticks=32, synthetic_rng_seed=987654,
        real_study047_future_physical_steps=0, real_study047_future_generator_ticks=0), indent=2, ensure_ascii=False) + '\n')
