"""Canonical immutable inputs for study015; no scientific aggregation."""
from pathlib import Path
from hashlib import sha256
from itertools import product
import json
from scripts.verify_v4_study014_summary import required_code,verify_files
from scripts.verify_v4_study012_summary import check_coverage,verify_bindings

OLD_ROOT=Path('data/v4-study-014')
read=lambda p:json.loads(Path(p).read_text())
digest=lambda p:sha256(Path(p).read_bytes()).hexdigest()


def code_paths():
    return required_code()|{Path(p) for p in ('experiments/v4/study-015.md','scripts/history_exchange_branch.py','scripts/history_exchange_audit.py','scripts/study015_inputs.py','scripts/run_v4_study015.py','scripts/verify_v4_study015_summary.py')}


def old_bindings():
    paths=set();names=('metadata','baseline-results','results','summary','aggregation-verification')
    for name in names:
        raw=OLD_ROOT/f'{name}.json';archive=Path(f'docs/research/results/v4-study-014-{name}.json')
        if raw.read_bytes()!=archive.read_bytes():raise ValueError('old archive mismatch')
        paths.update((raw,archive))
    meta=read(OLD_ROOT/'metadata.json');proof=read(OLD_ROOT/'aggregation-verification.json')
    if meta['status']!='complete' or proof['status']!='verified':raise ValueError('old complete proof required')
    for key,name in (('metadata_sha256','metadata'),('baseline_results_sha256','baseline-results'),('results_sha256','results'),('summary_sha256','summary')):
        if proof[key]!=digest(OLD_ROOT/f'{name}.json'):raise ValueError('old proof binding')
    if proof['verifier_sha256']!=digest('scripts/verify_v4_study014_summary.py'):raise ValueError('old verifier changed')
    if meta['output_sha256']!={f:digest(OLD_ROOT/f) for f in ('baseline-results.json','results.json','summary.json')}:raise ValueError('old root outputs')
    verify_bindings(meta['code_sha256'],required_code());paths.update(required_code())
    sources=read(OLD_ROOT/'baseline-results.json');rows=read(OLD_ROOT/'results.json')
    check_coverage(sources,('seed','mutation'),set(product(range(112000,112005),(0,100))))
    check_coverage(rows,('seed','mutation','anchor','exchange'),set(product(range(112000,112005),(0,100),(100,200,300,400),(True,False))))
    basefiles={'metadata.json','initial.json','steps.jsonl','final.json','summary.json','audit.json'}
    for r in sources+rows:
        suffix=f"seed-{r['seed']}-drive-250-mutation-{r['mutation']}"
        if 'anchor' in r:
            if type(r['exchange']) is not bool or r['status']!='complete':raise ValueError('old branch configuration')
            name=f"branches/{suffix}-anchor-{r['anchor']}-exchange-{str(r['exchange']).lower()}";files=basefiles|{'continuity.json'}
        else:name=f'baselines/{suffix}';files=basefiles
        if r['directory']!=name:raise ValueError('old canonical directory')
        directory=OLD_ROOT/name;verify_files(directory,r['files_sha256'],files)
        paths.update(directory/f for f in files)
    for section,index in (('baselines',sources),('branches',rows)):
        if {p.name for p in (OLD_ROOT/section).iterdir()}!={Path(r['directory']).name for r in index}:raise ValueError('old directory inventory')
    return {str(p):digest(p) for p in sorted(paths)}


def verify_old(expected):
    if old_bindings()!=expected:raise ValueError('old input inventory or content changed')
