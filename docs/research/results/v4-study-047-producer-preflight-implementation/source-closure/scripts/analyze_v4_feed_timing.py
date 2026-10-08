"""Extract the complete saved feed window at the original child's fixed site."""
from copy import deepcopy
from pathlib import Path
import subprocess
import time

from scripts.run_v4_north_energy import SELECTION_KEYS, ordered_selection, require

OUTPUT = Path('data/v4-study-030')
TOTAL_KEYS = ('steps','proposal_events','before_death_events','death_events','after_death_events',
              'proposed','before_death_proposed','death_proposed','after_death_proposed',
              'site_accepted','child_accepted','other_accepted','rejected')
ROW_KEYS = ('tick','phase','identity_before','identity_after','proposed','site_accepted','child_accepted','other_accepted','rejected')
RECORD_KEYS = ('selection','child_identity','child_site','birth_tick','death_tick','rows','totals',
               'first_proposed_tick','first_proposed_phase','first_after_death_tick')
PHASES = ('before_death','death','after_death')


def phase(tick, death):
    return 'before_death' if tick<death else 'death' if tick==death else 'after_death'


def totals(rows):
    result=dict(steps=len(rows),proposal_events=sum(r['proposed']>0 for r in rows))
    result.update({p+'_events':sum(r['proposed']>0 and r['phase']==p for r in rows) for p in PHASES})
    result['proposed']=sum(r['proposed'] for r in rows)
    result.update({p+'_proposed':sum(r['proposed'] for r in rows if r['phase']==p) for p in PHASES})
    result.update({k:sum(r[k] for r in rows) for k in TOTAL_KEYS[-4:]})
    return result


def firsts(rows):
    supplied=[r for r in rows if r['proposed']>0]
    after=[r for r in supplied if r['phase']=='after_death']
    return dict(first_proposed_tick=supplied[0]['tick'] if supplied else None,
                first_proposed_phase=supplied[0]['phase'] if supplied else None,
                first_after_death_tick=after[0]['tick'] if after else None)


def validate_record(record):
    require(set(record)==set(RECORD_KEYS) and set(record['selection'])==set(SELECTION_KEYS),'record fields')
    require(all(type(record[k]) is int and record[k]>=0 for k in ('child_identity','child_site','birth_tick','death_tick')),'record integers')
    child=record['child_identity']; birth=record['birth_tick']; death=record['death_tick']
    require(birth==record['selection']['tick'] and birth<death<=32 and record['child_site']<256,'child lifetime')
    rows=record['rows']; require([r['tick'] for r in rows]==list(range(birth+1,33)),'complete ordered site window')
    previous=child
    for row in rows:
        require(set(row)==set(ROW_KEYS),'row fields')
        require(all(type(row[k]) is int and row[k]>=0 for k in ROW_KEYS if k not in ('phase','identity_before','identity_after')),'row integer types')
        require(all(row[k] is None or type(row[k]) is int and row[k]>=0 for k in ('identity_before','identity_after')),'identity types')
        tick=row['tick']; before=row['identity_before']; after=row['identity_after']
        require(before==previous and row['phase']==phase(tick,death),'identity continuity and phase')
        require((before==child)==(tick<=death) and (after==child)==(tick<death),'original child lifetime')
        require(row['proposed'] in (0,8) and row['site_accepted']+row['rejected']==row['proposed'],'proposal conservation')
        require(before is not None or row['site_accepted']==0,'empty site rejects input')
        require(row['child_accepted']==(row['site_accepted'] if before==child else 0) and
                row['other_accepted']==row['site_accepted']-row['child_accepted'],'identity-bounded acceptance')
        previous=after
    require(set(record['totals'])==set(TOTAL_KEYS) and all(type(v) is int for v in record['totals'].values()) and
            record['totals']==totals(rows),'exact13 totals')
    require(all(record[k]==v and type(record[k]) is type(v) for k,v in firsts(rows).items()),'first proposal fields')


def analyze_branch(branch, energy):
    initial=branch['initial']; child=initial['injected_child']; ids=initial['site_ids']
    require(type(child) is int and ids.count(child)==1,'unique initial child')
    site=ids.index(child); birth=initial['tick']; fate=branch['child_fate']; death=fate['death_tick']
    require(fate['identity']==child and fate['birth_tick']==birth and fate['alive_final'] is False,'saved child fate')
    require(energy['selection']==branch['selection'] and energy['child_identity']==child and
            energy['child_site']==site and energy['birth_tick']==birth and energy['death_tick']==death,'corresponding029 identity')
    require([r['tick'] for r in energy['rows']]==list(range(birth+1,death+1)),'complete029 lifecycle')
    energy_rows={r['tick']:r for r in energy['rows']}; rows=[]
    for saved in branch['rows']:
        tick=saved['tick']; physical=saved['physical']; require(physical['tick']==tick,'physical tick')
        supplied=physical['driven']['inputs'][site]; require(supplied['site']==site,'fixed input site')
        after=saved['site_ids']; before=ids[site]
        require(ids.count(child)==(1 if tick<=death else 0) and after.count(child)==(1 if tick<death else 0),'child cannot move or resurrect')
        row=dict(tick=tick,phase=phase(tick,death),identity_before=before,identity_after=after[site],
                 proposed=supplied['proposed'],site_accepted=supplied['accepted'],
                 child_accepted=supplied['accepted'] if before==child else 0,
                 other_accepted=supplied['accepted'] if before!=child else 0,rejected=supplied['rejected'])
        if tick<=death:
            old=energy_rows[tick]
            require(type(old['proposed']) is int and type(old['accepted']) is int and
                    (row['proposed'],row['child_accepted'])==(old['proposed'],old['accepted']),'row matches029 lifecycle')
        rows.append(row); ids=after
    result=dict(selection=deepcopy(branch['selection']),child_identity=child,child_site=site,birth_tick=birth,
                death_tick=death,rows=rows,totals=totals(rows),**firsts(rows))
    validate_record(result)
    require(type(energy['totals']['accepted']) is int and result['totals']['child_accepted']==energy['totals']['accepted'],'accepted matches029 total')
    return result


def summarize(records):
    for record in records:validate_record(record)
    ordered_selection([r['selection'] for r in records]); cells=[]
    for genotype in ('homogeneous','heterogeneous'):
        for exchange in (False,True):
            chosen=[r for r in records if (r['selection']['genotype'],r['selection']['exchange'])==(genotype,exchange)]
            cells.append(dict(genotype=genotype,exchange=exchange,n=len(chosen),totals={k:sum(r['totals'][k] for r in chosen) for k in TOTAL_KEYS},
                no_proposal=sum(r['first_proposed_tick'] is None for r in chosen),
                first_before_death=sum(r['first_proposed_phase']=='before_death' for r in chosen),
                first_at_death=sum(r['first_proposed_phase']=='death' for r in chosen),
                first_after_death=sum(r['first_proposed_phase']=='after_death' for r in chosen),
                any_after_death=sum(r['first_after_death_tick'] is not None for r in chosen),
                any_child_accepted=sum(r['totals']['child_accepted']>0 for r in chosen),
                any_other_accepted=sum(r['totals']['other_accepted']>0 for r in chosen)))
    pair_keys=tuple(k for k in SELECTION_KEYS if k!='genotype')
    def key(r):return tuple(r['selection'][k] for k in pair_keys)
    hetero={key(r):i for i,r in enumerate(records) if r['selection']['genotype']=='heterogeneous'}
    require(len(hetero)==26,'unique heterogeneous pairs');pairs=[];used=set()
    for i,r in enumerate(records):
        if r['selection']['genotype']!='homogeneous':continue
        match=key(r);require(match in hetero and match not in used,'complete unique paired identity');used.add(match)
        j=hetero[match];other=records[j]
        require((r['child_site'],r['birth_tick'])==(other['child_site'],other['birth_tick']) and
                [(x['tick'],x['proposed']) for x in r['rows']]==[(x['tick'],x['proposed']) for x in other['rows']],'paired fixed site and complete tickets')
        pairs.append(dict(selection={k:r['selection'][k] for k in pair_keys},homogeneous_index=i,heterogeneous_index=j,
            delta={k:other['totals'][k]-r['totals'][k] for k in TOTAL_KEYS},
            phase_shift_ticks=[a['tick'] for a,b in zip(r['rows'],other['rows']) if a['proposed']>0 and a['phase']!=b['phase']]))
    require(len(pairs)==26 and used==set(hetero),'complete26 pairs')
    return dict(cells=cells,pairs=pairs)


def main():
    from scripts.feed_timing_inputs import bindings, source_cases, input_paths, read, save, digest
    require(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'clean launch')
    OUTPUT.mkdir(exist_ok=False)
    started=time.monotonic();records=[];inventory=[]
    meta=dict(status='running',planned_branches=52,completed_branches=0,saved_world_steps=0,site_steps=0,live_start_steps=0,
              new_full_world_steps=0,new_phase_transitions=0,new_environment_sources=0,reused_environment_sources=20,
              selected_environment_sources=11,new_independent_initial_worlds=0,time_limit_seconds=300,storage_limit_bytes=33554432)
    def budget():
        require(time.monotonic()-started<300 and sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())<33554432,'bounded execution')
    def hashes():
        return {str(p.relative_to(OUTPUT)):digest(p) for p in sorted(OUTPUT.rglob('*.json')) if p!=OUTPUT/'metadata.json'}
    def input_hashes(error_key):
        values={};meta[error_key]={}
        for path in inventory:
            try:values[path]=digest(path)
            except BaseException as exc:meta[error_key][path]=repr(exc)
        return values
    try:
        meta['git_commit']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
        meta['input_inventory_errors']={};inventory=input_paths(meta['input_inventory_errors']);meta['input_paths']=inventory
        meta['input_sha256']=input_hashes('input_read_errors_before')
        save(OUTPUT/'metadata.json',meta);save(OUTPUT/'records.json',records)
        before=bindings();require(before==meta['input_sha256'] and len(before)==491,'validated491 initial inputs');budget()
        paths=list(source_cases());energies=read(Path('data/v4-study-029/records.json'))
        require(len(paths)==len(energies)==52,'complete52 sources and energy records')
        for path,energy in zip(paths,energies):
            budget();branch=read(path);record=analyze_branch(branch,energy);records.append(record)
            meta.update(completed_branches=len(records),saved_world_steps=meta['saved_world_steps']+len(branch['rows']),
                        site_steps=meta['site_steps']+len(record['rows']),
                        live_start_steps=meta['live_start_steps']+sum(r['identity_before']==record['child_identity'] for r in record['rows']),
                        elapsed_seconds=time.monotonic()-started)
            save(OUTPUT/'records.json',records);save(OUTPUT/'metadata.json',meta);budget()
        require(meta['saved_world_steps']==meta['site_steps']==996 and meta['live_start_steps']==268,'fixed996 site and268 live steps')
        save(OUTPUT/'summary.json',summarize(records))
        meta['input_sha256_after']=bindings();require(before==meta['input_sha256_after'],'unchanged inputs')
        meta.update(status='complete',elapsed_seconds=time.monotonic()-started,output_sha256=hashes())
        budget();save(OUTPUT/'metadata.json',meta);budget()
    except BaseException as exc:
        meta.update(status='failed',error=repr(exc),elapsed_seconds=time.monotonic()-started)
        try:
            meta['input_sha256_after']=bindings()
            if meta.get('input_sha256')!=meta['input_sha256_after']:meta['finalization_error']='inputs changed during failure'
        except BaseException as err:
            meta['finalization_error']=repr(err);meta['input_sha256_after']=input_hashes('input_read_errors')
        try:meta['output_sha256']=hashes()
        except BaseException as err:meta['output_hash_error']=repr(err)
        save(OUTPUT/'metadata.json',meta)
        raise


if __name__=='__main__':main()
