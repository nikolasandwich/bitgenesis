"""Passive unique-birth identities reconstructed from audited hereditary events."""
from hashlib import sha256
import json
from pathlib import Path
from .hereditary_audit import audit


class Observer:
    """Event consumer; use trace() to require an independent dynamics audit."""
    def __init__(self, units):
        self.individuals=[]
        self.alive=[None]*len(units)
        self.tick=0
        for site,u in enumerate(units):
            if u is not None:
                self._birth(site,0,u['material'],u['program'],u['energy'],None,False)
        self.founders=len(self.individuals)

    def _birth(self,site,tick,material,program,energy,parent,mutated):
        identity=len(self.individuals)
        ancestor=self.individuals[parent] if parent is not None else None
        self.individuals.append(dict(id=identity,site=site,birth_tick=tick,death_tick=None,
            parent=parent,founder=ancestor['founder'] if ancestor else identity,
            generation=ancestor['generation']+1 if ancestor else 0,material=material,
            program=list(program),birth_energy=energy,mutated=mutated,offspring=0))
        self.alive[site]=identity
        if ancestor is not None:
            ancestor['offspring']+=1

    def accept(self,row):
        if row['tick']!=self.tick+1:
            raise ValueError('lineage tick order')
        tick=row['tick']
        for site in row['material']['dissolved']:
            identity=self.alive[site]
            if identity is None:
                raise ValueError('dissolution without living unit')
            self.individuals[identity]['death_tick']=tick
            self.alive[site]=None
        for p in row['material']['proposals']:
            if p['reason']!='formed':
                continue
            parent=self.alive[p['source']]
            if parent is None or self.alive[p['target']] is not None:
                raise ValueError('invalid lineage formation sites')
            original=self.individuals[parent]
            if original['birth_tick']==tick or original['program']!=p['parent_program']:
                raise ValueError('newborn cascade or parent program mismatch')
            self._birth(p['target'],tick,p['material'],p['child_program'],p['child_energy'],parent,p['mutated'])
        if len(row['units'])!=len(self.alive):
            raise ValueError('lineage geometry mismatch')
        for identity,u in zip(self.alive,row['units']):
            if (identity is None)!=(u is None):
                raise ValueError('lineage occupation mismatch')
            if u is not None:
                record=self.individuals[identity]
                if (record['program'],record['material'])!=(u['program'],u['material']):
                    raise ValueError('living program/material mismatch')
        self.tick=tick

    def result(self):
        return dict(individuals=self.individuals,final_site_ids=list(self.alive),
            summary=dict(tick=self.tick,founders=self.founders,births=len(self.individuals)-self.founders,
                deaths=sum(r['death_tick'] is not None for r in self.individuals),
                living=sum(i is not None for i in self.alive),
                max_generation=max((r['generation'] for r in self.individuals),default=0),
                mutation_births=sum(r['mutated'] for r in self.individuals)))


def trace(directory):
    root=Path(directory)
    checked=audit(root)
    initial=json.loads((root/'initial.json').read_text(encoding='utf-8'))
    observer=Observer(initial['units'])
    with (root/'steps.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            observer.accept(json.loads(line))
    result=observer.result()
    expected=checked['summary']
    if (result['summary']['births'],result['summary']['deaths'],result['summary']['living'],result['summary']['mutation_births'])!=(expected['formations'],expected['dissolutions'],expected['units'],expected['mutations']):
        raise ValueError('lineage/dynamics totals mismatch')
    return dict(scope='passive unit ancestry on independently audited hereditary trajectories; not group identity',
        dynamics_audit=checked,observer_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),**result)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=trace(args.directory)
    with args.output.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2)
        stream.write('\n')
    print(json.dumps(result['summary']))
