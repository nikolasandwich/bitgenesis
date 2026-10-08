"""Independent fixed tapes, dictionary physics, ancestry and full-program matching."""
import json
import math
from pathlib import Path

from bitgenesis.v4.exchange_branch_audit import physical_step
from bitgenesis.v4.structure_audit import reconstruct
from scripts.verify_v4_structure_copies import recount
from scripts.copy_program_inputs import bindings, read, digest

OUTPUT = Path('data/v4-study-022')
NAMES = ('constructed-off', 'constructed-on', 'no-raw-off')
CONFIG = dict(width=16,height=16,capacity=64,leak=1,bond_cost=1,threshold=16,construction_cost=4,copy_cost=1,mutation_per_thousand=0)


def require(value, message):
    if not value:
        raise ValueError(message)


def same(actual, expected, message):
    require(json.dumps(actual,sort_keys=True,separators=(',',':')) ==
            json.dumps(expected,sort_keys=True,separators=(',',':')), message)


def verify_case(case):
    name=case['name'];require(name in NAMES,'fixed case name')
    exchange=name=='constructed-on';raw_tokens=0 if name=='no-raw-off' else 4
    same(case['exchange'],exchange,'fixed exchange');same(case['raw_tokens'],raw_tokens,'fixed raw tokens')
    config=dict(width=16,height=16,capacity=64,leak=1,bond_cost=1,threshold=16,construction_cost=4,copy_cost=1,mutation_per_thousand=0)
    same(case['config'],config,'fixed configuration')
    units=[None]*256;raw=[0]*256;ids=[None]*256
    for identity,(x,y,material) in enumerate(((5,5,0),(6,5,0),(12,12,3))):
        site=16*y+x;units[site]=dict(material=material,energy=64,program=([0,0,0,identity+1] if identity<2 else [3,3,3,3]));ids[site]=identity
    for x,y in ((5,6),(6,6),(5,7),(6,7)):raw[16*y+x]=raw_tokens//4
    initial=dict(tick=0,units=units,raw=raw,site_ids=ids.copy(),observation=reconstruct(units,ids,16,16,'final'))
    same(case['initial'],initial,'fixed initial snapshot')
    initial_energy=sum(u['energy'] for u in units if u is not None)
    initial_mass=sum(raw)+sum(u is not None for u in units)
    parents=[None,None,None];rows=[];births=deaths=imported=spent=0
    require(len(case['rows'])==32,'all thirty-two steps')
    for tick in range(1,33):
        directions=[1 if site%16==6 else 0 for site in range(256)]
        if tick in (1,2):
            for x in (5,6):directions[16*(tick+4)+x]=2
        proposals=[8 if (site%16,site//16) in ((5,5),(6,5),(5,7),(6,7)) else 0 for site in range(256)]
        tape=dict(tick=tick,directions=directions,mutation_tickets=[[999,0,1] for _ in range(256)],
                  driven=dict(inputs=[dict(proposed=v) for v in proposals]))
        physical=physical_step(units,raw,config,tape,exchange)
        same(case['rows'][tick-1]['physical'],physical,'physical ledger and fixed tape')
        require(physical['energy_after']==physical['energy_before']+physical['imported']-physical['spent'],'step energy balance')
        require(physical['material_before']==physical['material_after']==initial_mass,'step mass conservation')
        prior_ids=ids.copy()
        for site in physical['material']['dissolved']:
            require(ids[site] is not None,'dissolution identity');ids[site]=None;deaths+=1
        for proposal in physical['material']['proposals']:
            if proposal['reason']=='formed':
                parent=prior_ids[proposal['source']];require(parent is not None,'formation parent')
                require(ids[proposal['target']] is None,'formation target vacant')
                ids[proposal['target']]=len(parents);parents.append(parent);births+=1
        units,raw=physical['units'],physical['raw']
        row=dict(tick=tick,site_ids=ids.copy(),physical=physical,observation=reconstruct(units,ids,16,16,'final'))
        same(case['rows'][tick-1],row,'full saved identity and partition row');rows.append(row)
        imported+=physical['imported'];spent+=physical['spent']
    final=dict(tick=32,units=units,raw=raw,site_ids=ids,parents=parents)
    same(case['final'],final,'final units stocks identities ancestry')
    copies=recount(initial,rows,final)
    require(len(copies)==1 and copies[0]['component']==0,'single original eligible component')
    same(case['copy_parents'],copies,'all independent copy counts intervals and longest')
    target=copies[0];longest=target['longest']['descendant_genetic']
    summary=dict(name=name,exchange=exchange,raw_tokens=raw_tokens,steps=32,births=births,deaths=deaths,
                 initial_energy=initial_energy,final_energy=sum(u['energy'] for u in units if u is not None),
                 imported=imported,spent=spent,initial_mass=initial_mass,final_mass=sum(raw)+sum(u is not None for u in units),
                 genetic_counts=target['series']['descendant_genetic'],episodes=target['episodes']['descendant_genetic'],
                 longest=longest,persistent10=longest>=10)
    same(case['summary'],summary,'independent complete case summary')
    require(summary['initial_energy']+imported-spent==summary['final_energy'],'cumulative energy balance')
    return summary


def verify_probe(probe, case):
    identity = probe['source_id']
    require(type(identity) is int and identity in (5, 6), 'fixed probe source identity')
    same(case['name'], 'constructed-off', 'probe source case')
    positions = [i for i, value in enumerate(case['final']['site_ids']) if value == identity]
    require(len(positions) <= 1, 'unique probe source identity')
    if not positions:
        expected = dict(source_id=identity, status='unavailable', source=None, initial=None, physical=None)
        same(probe, expected, 'unavailable fixed source')
        return dict(source_id=identity, status='unavailable', formed_materials=[])
    site = positions[0]
    source_unit = case['final']['units'][site]
    require(source_unit is not None, 'living probe source')
    source = dict(site=site, material=source_unit['material'], energy=source_unit['energy'],
                  program=list(source_unit['program']))
    initial = dict(units=[None] * 256, raw=[0] * 256)
    initial['units'][85] = dict(material=0, energy=64, program=list(source['program']))
    initial['raw'][69] = 1
    tape = dict(tick=1, directions=[3] * 256, mutation_tickets=[[999, 0, 1] for _ in range(256)],
                driven=dict(inputs=[dict(proposed=0) for _ in range(256)]))
    physical = physical_step(initial['units'], initial['raw'], CONFIG, tape, False)
    same(probe, dict(source_id=identity, status='complete', source=source, initial=initial, physical=physical),
         'independent probe source, standardized initial state and complete physical ledger')
    materials = sorted(p['material'] for p in physical['material']['proposals'] if p['reason'] == 'formed')
    return dict(source_id=identity, status='complete', formed_materials=materials)


def physical_projection(case):
    def state(units, raw, identities):
        return dict(units=[None if u is None else dict(material=u['material'], energy=u['energy']) for u in units],
                    raw=raw, site_ids=identities)
    initial, final = case['initial'], case['final']
    return dict(initial=state(initial['units'], initial['raw'], initial['site_ids']),
                rows=[state(r['physical']['units'], r['physical']['raw'], r['site_ids']) for r in case['rows']],
                final=dict(**state(final['units'], final['raw'], final['site_ids']), parents=final['parents']))


def aggregate(cases, probes, old_cases):
    same([c['name'] for c in cases], list(NAMES), 'complete fixed case order')
    same([c['name'] for c in old_cases], list(NAMES), 'complete baseline case order')
    same([p['source_id'] for p in probes], [5, 6], 'complete fixed probe order')
    summaries = [verify_case(case) for case in cases]
    probe_summaries = [verify_probe(probe, cases[0]) for probe in probes]
    directions, programs, equivalence = [], [], []
    for case, old_case in zip(cases, old_cases):
        counts = [0] * 4
        program_counts = {}
        for row in case['rows']:
            physical = row['physical']
            for proposal in physical['material']['proposals']:
                if proposal['reason'] == 'formed':
                    counts[physical['directions'][proposal['source']]] += 1
                    program = tuple(proposal['child_program'])
                    program_counts[program] = program_counts.get(program, 0) + 1
        directions.append(dict(name=case['name'], counts=counts))
        programs.append(dict(name=case['name'], counts=[dict(program=list(p), count=n) for p, n in sorted(program_counts.items())]))
        equivalence.append(dict(name=case['name'], equal=physical_projection(case) == physical_projection(old_case)))
    expected = (summaries[0]['persistent10'] and summaries[2]['births'] == 0 and
                all(e['equal'] for e in equivalence) and
                all(p['status'] == 'complete' and p['formed_materials'] == [i] for i, p in enumerate(probe_summaries, 1)))
    return dict(cases=summaries, formation_directions=directions, formed_programs=programs,
                physical_equivalence=equivalence, probes=probe_summaries, expectations_met=expected)


def main():
    root = OUTPUT
    proof_path = root / 'independent-verification.json'
    if proof_path.exists():
        raise FileExistsError(proof_path)
    try:
        files = ('metadata.json', 'cases.json', 'probes.json', 'summary.json')
        before = {name: digest(root / name) for name in files}
        metadata = read(root / 'metadata.json')
        bound = bindings()
        require(len(bound) == 215, 'all 215 frozen input bindings')
        same(digest(Path(__file__)), bound['scripts/verify_v4_copy_program.py'], 'running verifier binding')
        same(metadata['status'], 'complete', 'complete execution status')
        cases, probes = read(root / 'cases.json'), read(root / 'probes.json')
        require(type(cases) is list and len(cases) == 3, 'all three cases')
        require(type(probes) is list and len(probes) == 2, 'both fixed probes')
        summary = aggregate(cases, probes, read('data/v4-copy-control/cases.json'))
        steps = 96 + sum(p['status'] == 'complete' for p in summary['probes'])
        for name, value in dict(planned_cases=3, completed_cases=3, planned_probes=2, completed_probes=2,
                                new_simulation_steps=steps, new_independent_sources=0, artificial_control=True,
                                time_limit_seconds=300, storage_limit_bytes=33554432).items():
            same(metadata[name], value, 'fixed metadata ' + name)
        commit = metadata['git_commit']
        require(type(commit) is str and len(commit) == 40 and all(c in '0123456789abcdef' for c in commit), 'git commit identity')
        elapsed = metadata['elapsed_seconds']
        require(type(elapsed) in (int, float) and math.isfinite(elapsed) and 0 <= elapsed < 300, 'elapsed budget')
        require(sum(p.stat().st_size for p in root.rglob('*') if p.is_file()) < 33554432, 'storage budget')
        same(metadata['input_sha256'], bound, 'complete independent input inventory')
        same(metadata['input_sha256_after'], bound, 'after input inventory')
        same(metadata['output_sha256'], {name: before[name] for name in files[1:]}, 'output file binding')
        same(read(root / 'summary.json'), summary, 'independent full aggregate')
        same(metadata['expectations_met'], summary['expectations_met'], 'expectations match actual results')
        same(bindings(), bound, 'inputs unchanged during verification')
        same({name: digest(root / name) for name in files}, before, 'saved files unchanged during verification')
        proof = dict(status='verified', cases=3, probes=2, saved_steps=steps, new_simulation_steps=steps,
                     new_independent_sources=0, artificial_control=True, expectations_met=summary['expectations_met'],
                     input_files=len(bound), files_sha256=before, verifier_sha256=digest(Path(__file__)),
                     scope='independent fixed programs and tapes, dictionary physics, ancestry, all copy counts, probes and aggregate')
        with proof_path.open('x') as stream:
            stream.write(json.dumps(proof, indent=2) + '\n')
        print(json.dumps(proof))
    except BaseException as error:
        failure = root / 'verification-failure.json'
        if root.is_dir() and not failure.exists():
            with failure.open('x') as stream:
                stream.write(json.dumps(dict(status='failed', error=f'{type(error).__name__}: {error}')) + '\n')
        raise


if __name__ == '__main__':
    main()
