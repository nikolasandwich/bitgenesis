"""Complete two-history provenance, without population accounting."""
from pathlib import Path
from itertools import product
from scripts.study015_inputs import OLD_ROOT,old_bindings,code_paths,read,digest
from scripts.verify_v4_study014_summary import verify_files
from scripts.verify_v4_study012_summary import check_coverage,verify_bindings

NEW_ROOT=Path('data/v4-study-015')


def grid():
    rows=[]
    for history,root in ((True,OLD_ROOT),(False,NEW_ROOT)):
        values=read(root/'results.json')
        check_coverage(values,('seed','mutation','anchor','exchange'),set(product(range(112000,112005),(0,100),(100,200,300,400),(True,False))))
        for r in values:
            if type(r['exchange']) is not bool or r['status']!='complete':raise ValueError('complete boolean branch required')
            name=f"branches/seed-{r['seed']}-drive-250-mutation-{r['mutation']}-anchor-{r['anchor']}-exchange-{str(r['exchange']).lower()}"
            if r['directory']!=name:raise ValueError('canonical branch directory')
            rows.append(dict(history=history,seed=r['seed'],mutation=r['mutation'],anchor=r['anchor'],exchange=r['exchange'],directory=str(root/name)))
    return rows


def bindings():
    bound=old_bindings();paths=set(code_paths())
    for name in ('metadata','baseline-results','results','summary','aggregation-verification'):
        raw=NEW_ROOT/f'{name}.json';archive=Path(f'docs/research/results/v4-study-015-{name}.json')
        if raw.read_bytes()!=archive.read_bytes():raise ValueError('new history archive mismatch')
        paths.update((raw,archive))
    meta=read(NEW_ROOT/'metadata.json');proof=read(NEW_ROOT/'aggregation-verification.json')
    if meta['status']!='complete' or meta['completed_sources']!=10 or meta['completed_branches']!=80 or proof['status']!='verified':raise ValueError('complete history proof')
    if meta['old_sha256']!=bound:raise ValueError('old history binding')
    verify_bindings(meta['code_sha256'],code_paths())
    for key,name in (('metadata_sha256','metadata'),('baseline_results_sha256','baseline-results'),('results_sha256','results'),('summary_sha256','summary')):
        if proof[key]!=digest(NEW_ROOT/f'{name}.json'):raise ValueError('new history proof binding')
    if proof['old_verification_sha256']!=digest(OLD_ROOT/'aggregation-verification.json') or proof['verifier_sha256']!=digest('scripts/verify_v4_study015_summary.py'):raise ValueError('history verifier binding')
    if meta['output_sha256']!={n:digest(NEW_ROOT/n) for n in ('baseline-results.json','results.json','summary.json')}:raise ValueError('history outputs')
    sources=read(NEW_ROOT/'baseline-results.json');rows=read(NEW_ROOT/'results.json')
    check_coverage(sources,('seed','mutation'),set(product(range(112000,112005),(0,100))))
    grid()
    files={'metadata.json','initial.json','steps.jsonl','final.json','summary.json','audit.json'}
    for r in sources+rows:
        expected=files|{'continuity.json'} if 'anchor' in r else files
        if 'anchor' not in r and r['directory']!=f"baselines/seed-{r['seed']}-drive-250-mutation-{r['mutation']}":raise ValueError('canonical baseline directory')
        directory=NEW_ROOT/r['directory'];verify_files(directory,r['files_sha256'],expected);paths.update(directory/n for n in expected)
    for section,index in (('baselines',sources),('branches',rows)):
        if {p.name for p in (NEW_ROOT/section).iterdir()}!={Path(r['directory']).name for r in index}:raise ValueError('history directory inventory')
    paths.update(Path(p) for p in ('docs/design/v4-history-population-paths.md','scripts/history_population_inputs.py','scripts/analyze_v4_history_population.py','scripts/verify_v4_history_population.py'))
    bound.update({str(p):digest(p) for p in paths})
    return dict(sorted(bound.items()))
