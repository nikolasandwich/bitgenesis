"""仅调用真实进程检查函数；所有仓库科学函数和随机抽取均设为拒绝入口。"""
import ast
from collections import Counter
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import importlib
import inspect
import json
import os
from pathlib import Path
import random
import re
import shlex
import subprocess
import sys
from unittest.mock import patch

ROOT = Path('/Users/todd/Documents/bitgenesis')
OUT = Path(__file__).resolve().parent / 'probe-output'
OUT.mkdir(exist_ok=False)
sys.dont_write_bytecode = True
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
calls = Counter()
forbidden_calls = []


def write(name, value):
    with (OUT / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def repo_function_guard(frame, event, arg):
    if event != 'call':
        return
    filename = frame.f_code.co_filename
    if filename.startswith((str(ROOT / 'src') + '/', str(ROOT / 'scripts') + '/')):
        # 模块和类声明不是函数；除预检及其唯一合同辅助函数外拒绝全部调用。
        if frame.f_code.co_flags & inspect.CO_OPTIMIZED:
            key = filename + ':' + frame.f_code.co_name
            calls[key] += 1
            if frame.f_code.co_name not in {'check_no_other_process', 'matches', 'require'}:
                forbidden_calls.append(key)
                raise RuntimeError('科学入口被诊断隔离拒绝: ' + key)


def no_random(*args, **kwargs):
    forbidden_calls.append('random_draw')
    raise RuntimeError('诊断禁止任何随机抽取')


self_ps = subprocess.run(['ps', '-p', str(os.getpid()), '-o', 'pid=,command='], capture_output=True)
for name, payload in [('runtime-ps.stdout.bin', self_ps.stdout), ('runtime-ps.stderr.bin', self_ps.stderr)]:
    with (OUT / name).open('xb') as stream:
        stream.write(payload)
assert self_ps.returncode == 0
self_command = self_ps.stdout.decode().strip().split(None, 1)[1]
self_words = shlex.split(self_command)
observed_executable = self_words[0]
write('runtime.json', dict(created_at_utc=datetime.now(timezone.utc).isoformat(), pid=os.getpid(),
                          executable=sys.executable, version=sys.version,
                          ps_command=self_command, ps_executable=observed_executable,
                          ps_basename=Path(observed_executable).name, ps_exit_code=self_ps.returncode,
                          scope='仅当前非科学诊断进程；不是正式研究运行前的历史进程快照'))

routes = ['run_v4_middle_withdrawal', 'verify_v4_middle_withdrawal']
fixtures = []
for executable in ['python', 'Python', 'python3.14', 'Python3.14', 'pypy3', 'PyPy3', observed_executable]:
    for route in routes:
        for label, tail in [('script', f'scripts/{route}.py --mode formal'),
                            ('module', f'-X dev -W error -m scripts.{route} --mode formal')]:
            fixtures.append(dict(id=f'{executable}:{route}:{label}', command=shlex.quote(executable) + ' ' + tail,
                                 expected_block=True))
fixtures.extend([
    dict(id='direct-script', command='scripts/run_v4_middle_withdrawal.py --mode formal', expected_block=True),
    dict(id='attached-module', command='python3 -Is -mscripts.verify_v4_middle_withdrawal', expected_block=True),
    dict(id='uppercase-attached-module', command='Python -Is -mscripts.verify_v4_middle_withdrawal', expected_block=True),
    dict(id='double-dash', command='Python -- scripts/run_v4_middle_withdrawal.py', expected_block=True),
    dict(id='unrelated-python', command='Python unrelated.py', expected_block=False),
    dict(id='unrelated-module', command='python -m unrelated', expected_block=False),
    dict(id='quoted-mentioned-script', command='python -c "print(\'scripts/run_v4_middle_withdrawal.py\')"', expected_block=False),
    dict(id='shell-mention', command='/bin/zsh -c "echo scripts/run_v4_middle_withdrawal.py"', expected_block=False),
    dict(id='own-pid', command='Python scripts/run_v4_middle_withdrawal.py', expected_block=False, own_pid=True),
])
write('fixtures.json', fixtures)

rows = []
with ExitStack() as patches:
    for method in ('random', 'getrandbits', 'randrange', 'sample', 'choice', 'choices', 'randint', 'seed', 'setstate'):
        patches.enter_context(patch.object(random.Random, method, side_effect=no_random))
    for method in ('random', 'getrandbits', 'randrange', 'sample', 'choice', 'choices', 'randint', 'seed', 'setstate'):
        patches.enter_context(patch.object(random, method, side_effect=no_random))
    sys.setprofile(repo_function_guard)
    try:
        modules = [importlib.import_module('scripts.' + route) for route in routes]
        for module in modules:
            for item in fixtures:
                pid = os.getpid() if item.get('own_pid') else os.getpid() + 1000000
                ps = f'{pid} {item["command"]}\n'
                error = None
                with patch.object(module.subprocess, 'check_output', return_value=ps) as mocked_ps:
                    try:
                        module.check_no_other_process()
                    except ValueError as caught:
                        error = dict(type=type(caught).__name__, message=str(caught))
                    mocked_ps.assert_called_once_with(['ps', '-axo', 'pid=,command='], text=True)
                blocked = error is not None
                rows.append(dict(route=module.__name__, fixture=item['id'], raw_mock_ps=ps,
                                 expected_block=item['expected_block'], blocked=blocked, error=error,
                                 requirement_met=blocked == item['expected_block']))
    finally:
        sys.setprofile(None)

# 只从不可变wrapper原文取出process_state声明，不执行模块顶层、initialize或run_route。
wrapper_rows = []
for source in ['docs/research/results/v4-study-047-engineering/raw/execution_runner.py',
               'data/v4-study-047/execution_runner.py']:
    source_bytes = (ROOT / source).read_bytes()
    tree = ast.parse(source_bytes, filename=source)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'process_state')
    for executable in ['python', 'Python', observed_executable]:
        command = shlex.quote(executable) + ' scripts/run_v4_middle_withdrawal.py --mode formal'
        mock_ps = f'{os.getpid() + 1000000} 1 {command}\n'
        namespace = dict(Path=Path, shlex=shlex, command=lambda args, value=mock_ps: value)
        exec(compile(ast.Module(body=[node], type_ignores=[]), source, 'exec'), namespace)
        matched = namespace['process_state']()
        wrapper_rows.append(dict(source=source, source_sha256=hashlib.sha256(source_bytes).hexdigest(),
                                 interpreter=executable, mock_ps=mock_ps, matched=matched,
                                 requirement_met=bool(matched)))

failed = [row for row in rows if not row['requirement_met']]
write('results.json', dict(status='RED' if failed else 'GREEN', cases=rows,
                          required_rejections_missed=len(failed), wrapper_cases=wrapper_rows,
                          repository_function_calls=dict(calls), forbidden_calls=forbidden_calls,
                          actual_physics_steps=0, synthetic_physics_steps=0, future_generator_ticks=0,
                          past_generator_ticks=0, route_cli_invocations=0,
                          source_mutations=0, notes='RED是预检合同反例，不是研究或诊断基础设施失败。'))
print(json.dumps(dict(status='RED' if failed else 'GREEN', guard_cases=len(rows),
                      required_rejections_missed=len(failed), ps_basename=Path(observed_executable).name,
                      wrapper_cases=len(wrapper_rows), wrapper_misses=sum(not x['requirement_met'] for x in wrapper_rows),
                      forbidden_calls=forbidden_calls, actual_physics_steps=0,
                      synthetic_physics_steps=0, future_generator_ticks=0), ensure_ascii=False))
sys.exit(1 if failed else 0)
