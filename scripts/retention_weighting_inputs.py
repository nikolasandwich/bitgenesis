"""Provenance-only binding for retention weighting; no classification or rates."""
from pathlib import Path
from scripts.population_path_inputs import bindings as population_bindings, read, digest, ROOT

TRADEOFF=Path('data/v4-study-012-tradeoff')
POPULATION=Path('data/v4-study-012-population-paths')


def require(ok,message):
    if not ok:raise ValueError(message)


def verify_inventory(recorded,expected):
    expected={str(p) for p in expected}
    require(bool(expected) and set(recorded)==expected,'binding inventory')
    for path,value in recorded.items():require(value==digest(path),f'binding hash: {path}')


def tradeoff_paths():
    # Reproduce the old verifier's tracked path inventory, independently of its proof.
    paths={str(Path('scripts/verify_v4_tradeoff.py').resolve()),'scripts/analyze_v4_tradeoff.py','docs/design/v4-exchange-tradeoff-supplement.md'}
    paths.update(str(TRADEOFF/f'{n}.json') for n in ('metadata','results','summary'))
    for name in ('metadata','results','summary','aggregation-verification'):
        paths.add(str(ROOT/f'{name}.json'));paths.add(f'docs/research/results/v4-study-012-{name}.json')
        require(digest(ROOT/f'{name}.json')==digest(f'docs/research/results/v4-study-012-{name}.json'),'study012 archive binding')
    meta=read(ROOT/'metadata.json')
    for field in ('bindings_sha256','source_bindings_sha256'):paths.update(meta[field])
    for row in read(ROOT/'results.json'):
        directory=ROOT/row['directory'];branch=read(directory/'metadata.json')
        paths.update(str(directory/f'{n}.json') for n in ('metadata','audit','continuity'))
        paths.update(str(directory/n) for n in branch['output_sha256'])
        paths.update(str(Path('src/bitgenesis/v4')/n) for n in branch['code_sha256'])
    return paths


def bindings():
    base=population_bindings()
    pm=read(POPULATION/'metadata.json');pp=read(POPULATION/'independent-verification.json')
    require(pm['status']=='complete' and pm['completed_branches']==80 and pm['independent_new_samples']==0,'population complete')
    require(pm['input_sha256']==pm['input_sha256_after']==base,'population input inventory')
    outputs={n:digest(POPULATION/n) for n in ('branches.json','summary.json')}
    require(pm['output_sha256']==outputs,'population output inventory')
    require(pp['status']=='verified' and (pp['branches'],pp['branch_steps'],pp['paired_paths'],pp['first_step_pairs_reused'])==(80,8000,40,40) and pp['independent_new_samples']==0,'population proof')
    for name in ('metadata','branches','summary'):require(pp[f'{name}_sha256']==digest(POPULATION/f'{name}.json'),'population proof hash')
    require(pp['verifier_sha256']==digest('scripts/verify_v4_population_paths.py'),'population verifier hash')
    tm=read(TRADEOFF/'metadata.json');tp=read(TRADEOFF/'independent-verification.json')
    require(tm['status']=='complete' and tm['completed_pairs']==tm['planned_pairs']==40 and tm['independent_new_samples']==0,'tradeoff complete')
    require(tp['status']=='verified' and tp['verdict']=='APPROVED' and (tp['pairs'],tp['branches'],tp['components'],tp['component_branch_records'],tp['snapshots'])==(40,80,6212,12424,8000),'tradeoff proof')
    tracked=tradeoff_paths();verify_inventory(tp['binding_sha256'],tracked)
    for key,path in [('script_sha256','scripts/analyze_v4_tradeoff.py'),('design_sha256','docs/design/v4-exchange-tradeoff-supplement.md'),('study012_results_sha256',ROOT/'results.json'),('results_sha256',TRADEOFF/'results.json'),('summary_sha256',TRADEOFF/'summary.json')]:
        require(tm[key]==digest(path),'tradeoff metadata binding')
    paths=set(base)|tracked
    paths.update(str(TRADEOFF/f'{n}.json') for n in ('metadata','results','summary','independent-verification'))
    paths.update(str(POPULATION/f'{n}.json') for n in ('metadata','branches','summary','independent-verification'))
    paths.update(('docs/design/v4-retention-weighting-supplement.md','scripts/retention_weighting_inputs.py','scripts/analyze_v4_retention_weighting.py','scripts/verify_v4_retention_weighting.py'))
    return {p:digest(p) for p in sorted(paths)}
