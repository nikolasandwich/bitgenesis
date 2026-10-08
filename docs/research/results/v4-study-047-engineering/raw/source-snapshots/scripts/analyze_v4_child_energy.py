"""Extract identity-bounded child energy ledgers from saved Study028 branches."""
from copy import deepcopy
from pathlib import Path
import subprocess
import time

from scripts.run_v4_north_energy import SELECTION_KEYS, ordered_selection, require

OUTPUT = Path('data/v4-study-029')
TOTAL_KEYS = ('steps','proposed','accepted','leakage','bond_cost','exchange_in','exchange_out',
              'formation_spent','offspring_energy','final_energy')
FLOW_KEYS = TOTAL_KEYS[1:-1]
ROW_KEYS = ('tick','energy_before','proposed','accepted','leakage','bond_cost','exchange_in',
            'exchange_out','energy_interaction','formation_spent','offspring_energy','energy_after','dissolved')
RECORD_KEYS = ('selection','child_identity','child_site','birth_tick','death_tick','initial_energy','rows','totals')


def totals(rows):
    return dict(steps=len(rows),**{k:sum(row[k] for row in rows) for k in FLOW_KEYS},
                final_energy=rows[-1]['energy_after'])


def validate_record(record):
    require(set(record)==set(RECORD_KEYS) and set(record['selection'])==set(SELECTION_KEYS),'record fields')
    require(all(type(record[k]) is int and record[k]>=0 for k in
                ('child_identity','child_site','birth_tick','death_tick','initial_energy')),'record integers')
    require(record['initial_energy']==5 and record['birth_tick']==record['selection']['tick'] and
            record['birth_tick']<record['death_tick']<=32 and record['child_site']<256,'child lifetime')
    rows=record['rows']; require(bool(rows),'nonempty child lifetime')
    require([r['tick'] for r in rows]==list(range(record['birth_tick']+1,record['death_tick']+1)),'contiguous child rows')
    energy=record['initial_energy']
    for i,row in enumerate(rows):
        require(set(row)==set(ROW_KEYS),'row fields')
        require(all(type(row[k]) is int and row[k]>=0 for k in ROW_KEYS if k!='dissolved') and
                type(row['dissolved']) is bool,'row types')
        require(row['energy_before']==energy and row['accepted']<=row['proposed'],'before energy and input')
        require(row['energy_interaction']==energy+row['accepted']-row['leakage']-row['bond_cost']+
                row['exchange_in']-row['exchange_out'],'interaction energy ledger')
        require(row['energy_after']==row['energy_interaction']-row['formation_spent']-row['offspring_energy'],
                'formation energy ledger')
        require(row['dissolved']==(i==len(rows)-1) and
                (row['energy_interaction']==0 if row['dissolved'] else row['energy_after']>0),'death energy')
        energy=row['energy_after']
    actual=record['totals']
    require(set(actual)==set(TOTAL_KEYS) and all(type(v) is int for v in actual.values()) and actual==totals(rows),'exact totals')
    require(actual['final_energy']==0 and 5+actual['accepted']-actual['leakage']-actual['bond_cost']+
            actual['exchange_in']-actual['exchange_out']-actual['formation_spent']-actual['offspring_energy']==0,'lifetime energy ledger')


def analyze_branch(branch):
    initial=branch['initial']; child=initial['injected_child']; ids=initial['site_ids']
    require(type(child) is int and ids.count(child)==1,'unique initial child identity')
    site=ids.index(child); unit=initial['units'][site]
    require(unit is not None and unit['energy']==5,'initial child energy')
    require(initial['parents'][child]==branch['selection']['identity'],'initial child parent')
    parents=initial['parents']; ancestor=child
    while parents[ancestor] is not None:
        parent=parents[ancestor]
        require(type(parent) is int and 0<=parent<ancestor,'ordered child ancestry')
        ancestor=parent
    require(ancestor==branch['selection']['root'],'child founder identity')
    energy=unit['energy']; birth=initial['tick']; rows=[]; death=None
    for saved in branch['rows']:
        require(saved['tick']==birth+len(rows)+1 and saved['physical']['tick']==saved['tick'],'ordered physical tick')
        p=saved['physical']; inputs=p['driven']['inputs']; require(inputs[site]['site']==site,'saved input site')
        supplied=inputs[site]; interaction=p['driven']['interaction']; middle=p['interaction_units'][site]
        require(middle is not None,'child interaction identity')
        died=site in p['material']['dissolved']
        after_ids=saved['site_ids']
        require(after_ids.count(child)==(0 if died else 1) and (died or after_ids[site]==child),'fixed child identity and site')
        formed=[v for v in p['material']['proposals'] if v['source']==site and v['reason']=='formed']
        require(not died or not formed,'dead parent cannot form')
        require(all(v['construction_cost']==4 and v['copy_cost']==1 and v['cost']==5 for v in formed),'original formation costs')
        final=p['units'][site]
        require(died or final is not None,'living final unit')
        row=dict(tick=saved['tick'],energy_before=energy,**{k:supplied[k] for k in ('proposed','accepted','leakage')},
                 bond_cost=sum(site in edge for edge in interaction['bonds']),
                 exchange_in=sum(t['amount'] for t in interaction['transfers'] if t['recipient']==site),
                 exchange_out=sum(t['amount'] for t in interaction['transfers'] if t['donor']==site),
                 energy_interaction=middle['energy'],formation_spent=sum(v['construction_cost']+v['copy_cost'] for v in formed),
                 offspring_energy=sum(v['child_energy'] for v in formed),energy_after=0 if died else final['energy'],dissolved=died)
        rows.append(row); energy=row['energy_after']
        if died:
            death=saved['tick']; break
    fate=branch['child_fate']
    require(death is not None and fate['identity']==child and fate['birth_tick']==birth and fate['death_tick']==death and
            fate['alive_final'] is False,'saved child fate')
    record=dict(selection=deepcopy(branch['selection']),child_identity=child,child_site=site,birth_tick=birth,
                death_tick=death,initial_energy=unit['energy'],rows=rows,totals=totals(rows))
    validate_record(record)
    return record


def summarize(records):
    ordered_selection([r['selection'] for r in records])
    for record in records:validate_record(record)
    cells=[]
    for genotype in ('homogeneous','heterogeneous'):
        for exchange in (False,True):
            chosen=[r for r in records if (r['selection']['genotype'],r['selection']['exchange'])==(genotype,exchange)]
            cells.append(dict(genotype=genotype,exchange=exchange,n=len(chosen),
                totals={k:sum(r['totals'][k] for r in chosen) for k in TOTAL_KEYS},
                zero_accepted=sum(r['totals']['accepted']==0 for r in chosen),
                received_exchange=sum(r['totals']['exchange_in']>0 for r in chosen),
                paid_bond=sum(r['totals']['bond_cost']>0 for r in chosen)))
    pair_keys=tuple(k for k in SELECTION_KEYS if k!='genotype')
    def key(record):return tuple(record['selection'][k] for k in pair_keys)
    hetero={key(r):i for i,r in enumerate(records) if r['selection']['genotype']=='heterogeneous'}
    require(len(hetero)==26,'unique heterogeneous pairs')
    pairs=[]; used=set()
    for i,r in enumerate(records):
        if r['selection']['genotype']!='homogeneous':continue
        match=key(r); require(match in hetero and match not in used,'complete unique paired identity'); used.add(match)
        j=hetero[match]
        pairs.append(dict(selection={k:r['selection'][k] for k in pair_keys},homogeneous_index=i,heterogeneous_index=j,
                          delta={k:records[j]['totals'][k]-r['totals'][k] for k in TOTAL_KEYS}))
    require(len(pairs)==26 and used==set(hetero),'complete26 pairs')
    return dict(cells=cells,pairs=pairs)


def main():
    from scripts.child_energy_inputs import bindings, source_cases, input_paths, read, save, digest
    require(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'clean launch')
    OUTPUT.mkdir(exist_ok=False)
    started=time.monotonic(); records=[]; inventory=[]
    meta=dict(status='running',planned_branches=52,completed_branches=0,saved_world_steps=0,child_steps=0,
              new_full_world_steps=0,new_phase_transitions=0,new_environment_sources=0,reused_environment_sources=20,
              selected_environment_sources=11,new_independent_initial_worlds=0,time_limit_seconds=300,storage_limit_bytes=33554432)
    def budget():
        require(time.monotonic()-started<300 and sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())<33554432,'bounded execution')
    def hashes():
        return {str(p.relative_to(OUTPUT)):digest(p) for p in sorted(OUTPUT.rglob('*.json')) if p!=OUTPUT/'metadata.json'}
    def input_hashes(error_key):
        values={}; meta[error_key]={}
        for path in inventory:
            try:values[path]=digest(path)
            except BaseException as exc:meta[error_key][path]=repr(exc)
        return values
    try:
        meta['git_commit']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
        meta['input_inventory_errors']={}; inventory=input_paths(meta['input_inventory_errors']); meta['input_paths']=inventory
        meta['input_sha256']=input_hashes('input_read_errors_before')
        save(OUTPUT/'metadata.json',meta); save(OUTPUT/'records.json',records)
        before=bindings(); require(before==meta['input_sha256'] and len(before)==479,'validated479 initial inputs'); budget()
        paths=list(source_cases()); require(len(paths)==52,'complete52 source branches')
        for path in paths:
            budget(); branch=read(path); record=analyze_branch(branch); records.append(record)
            meta.update(completed_branches=len(records),saved_world_steps=meta['saved_world_steps']+len(branch['rows']),
                        child_steps=meta['child_steps']+len(record['rows']),elapsed_seconds=time.monotonic()-started)
            save(OUTPUT/'records.json',records); save(OUTPUT/'metadata.json',meta); budget()
        require(meta['saved_world_steps']==996 and meta['child_steps']==268,'fixed996 saved and268 child steps')
        summary=summarize(records)
        require([c['totals']['steps'] for c in summary['cells']]==[64,26,129,49],'fixed cell child steps')
        save(OUTPUT/'summary.json',summary)
        meta['input_sha256_after']=bindings(); require(before==meta['input_sha256_after'],'unchanged inputs')
        meta.update(status='complete',elapsed_seconds=time.monotonic()-started,output_sha256=hashes())
        budget(); save(OUTPUT/'metadata.json',meta); budget()
    except BaseException as exc:
        meta.update(status='failed',error=repr(exc),elapsed_seconds=time.monotonic()-started)
        try:
            meta['input_sha256_after']=bindings()
            if meta.get('input_sha256')!=meta['input_sha256_after']:meta['finalization_error']='inputs changed during failure'
        except BaseException as err:
            meta['finalization_error']=repr(err); meta['input_sha256_after']=input_hashes('input_read_errors')
        try:meta['output_sha256']=hashes()
        except BaseException as err:meta['output_hash_error']=repr(err)
        save(OUTPUT/'metadata.json',meta)
        raise


if __name__=='__main__':main()
