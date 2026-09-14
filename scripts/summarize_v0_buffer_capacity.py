"""Independently verify campaign-021 initialization, metrics and observations."""

import argparse
import csv
import hashlib
from itertools import product
import json
from pathlib import Path

if __package__:
    from .summarize_v0_food_geometry import BASE, INITIAL, verify_initial as verify_geometry
else:
    from summarize_v0_food_geometry import BASE, INITIAL, verify_initial as verify_geometry


REGIMES = {"frequent-small": (60,1), "reference": (15,4), "rare-large": (5,12)}


def verify_initial(initial, arm, threshold, renewal, capacity, seed):
    if arm != "block" or threshold not in (40,160) or renewal not in REGIMES or type(capacity) is not int or capacity not in (24,96):
        raise ValueError("Undeclared treatment")
    probability, amount = REGIMES[renewal]
    expected={**BASE,"seed":seed,"initial_food":0,"regrowth_probability":probability,
              "regrowth_amount":amount,"mutation_probability":0,"birth_threshold":threshold,
              "movement_cost":0,"birth_cost":0,"food_capacity":capacity}
    if (initial.get("birth_threshold") != threshold or initial.get("renewal") != renewal
            or initial.get("birth_cost") != 0 or initial.get("movement_cost") != 0
            or initial.get("food_capacity") != capacity or initial["config"] != expected):
        raise ValueError("Initial treatment/configuration differs")
    # Renewal settings do not consume construction draws; validate actual settings first.
    normalized={**initial,"config":{**expected,"birth_threshold":40,"movement_cost":1,
        "birth_cost":4,"regrowth_probability":15,"regrowth_amount":4,"food_capacity":24}}
    return verify_geometry(normalized,arm,seed)


def verify_rows(rows, amount, capacity, steps=10000):
    if type(capacity) is not int or capacity not in (24,96):
        raise ValueError("Undeclared food capacity")
    if type(amount) is not int or amount not in (1,4,12):
        raise ValueError("Undeclared renewal packet")
    previous, extinction, count = None, None, 0
    for tick, row in enumerate(rows):
        count += 1
        if set(row) != set(INITIAL) or row["tick"] != tick:
            raise ValueError("Metric schema or tick sequence differs")
        if any(type(v) is not int or v < 0 for k,v in row.items() if k not in ("mean_genome","max_generation")):
            raise ValueError("Invalid integer metric")
        n = row["population"]
        if n != 80+row["births"]-row["deaths"] or not 0 <= n <= 1024:
            raise ValueError("Population accounting mismatch")
        if (row["food_energy"] > 1024*capacity or row["organism_energy"] < n
                or row["organism_energy"]+row["food_energy"]+row["dissipated_energy"] != row["supplied_energy"]):
            raise ValueError("Energy accounting mismatch")
        if (row["mean_genome"] != (250 if n else None) or row["genome_variants"] != int(n>0)
                or not int(n>0) <= row["founder_lineages"] <= min(80,n)):
            raise ValueError("Fixed trait or founder bounds differ")
        if (n and (type(row["max_generation"]) is not int or row["max_generation"] < 0)) or (
                not n and (row["max_generation"] is not None or row["organism_energy"] != 0)):
            raise ValueError("Invalid living generation or extinct energy")
        if tick == 0:
            if row != INITIAL:
                raise ValueError("Initial metric differs")
        else:
            births, deaths = row["births"]-previous["births"], row["deaths"]-previous["deaths"]
            supply, dissipated = row["supplied_energy"]-previous["supplied_energy"], row["dissipated_energy"]-previous["dissipated_energy"]
            if (min(births,deaths,supply,dissipated) < 0 or births+deaths > previous["population"]
                    or supply > 1024*amount or dissipated != previous["population"]
                    or row["founder_lineages"] > previous["founder_lineages"]):
                raise ValueError("Per-tick transition bounds differ")
            if previous["population"] == 0 and n:
                raise ValueError("Population reappeared after extinction")
            if n and row["max_generation"] > previous["max_generation"]+1:
                raise ValueError("Generation jump")
        if previous is not None:
            uptake = row["supplied_energy"]-previous["supplied_energy"]+previous["food_energy"]-row["food_energy"]
            if not 0 <= uptake <= 8*previous["population"]:
                raise ValueError("Per-tick uptake bounds differ")
        if not n and extinction is None:
            extinction = tick
        previous = row
    if count != steps+1:
        raise ValueError("Truncated metric series")
    return {**previous,"extinction_tick":extinction,"right_censored":extinction is None}



def early_observations(rows):
    if len(rows)<101 or [r["tick"] for r in rows[:101]]!=list(range(101)):
        raise ValueError("Incomplete early window")
    peak=max(rows[:101],key=lambda r:r["population"])
    eaten=0
    for previous,current in zip(rows[:100],rows[1:101]):
        delta=current["supplied_energy"]-previous["supplied_energy"]+previous["food_energy"]-current["food_energy"]
        if not 0<=delta<=8*previous["population"] or delta != (
                current["organism_energy"]-previous["organism_energy"]+
                current["dissipated_energy"]-previous["dissipated_energy"]):
            raise ValueError("Invalid early food uptake")
        eaten+=delta
    return dict(population_at_100=rows[100]["population"],births_at_100=rows[100]["births"],
        early_peak_population=peak["population"],first_peak_tick=peak["tick"],
        food_eaten_by_100=eaten,food_at_100=rows[100]["food_energy"],
        organism_energy_at_100=rows[100]["organism_energy"])


def resource_checkpoints(rows):
    result={}
    for tick in (100,500,5000,10000):
        row=rows[tick]
        result[f"resources_added_by_{tick}"]=row["supplied_energy"]-7040
        result[f"cumulative_uptake_by_{tick}"]=row["supplied_energy"]-7040+5120-row["food_energy"]
    return result


def window_observations(rows):
    end=next((r for r in rows if r['population']==0),rows[-1])
    return dict(active_start_ticks=end['tick'],empty_start_ticks=rows[-1]['tick']-end['tick'],
        food_at_active_window_end=end['food_energy'],
        resources_added_during_active_start_ticks=end['supplied_energy']-7040,
        cumulative_uptake_at_active_window_end=end['supplied_energy']-7040+5120-end['food_energy'],
        resources_added_after_extinction=rows[-1]['supplied_energy']-end['supplied_energy'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path('data/campaign-021'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
    metadata=json.loads((args.input/'metadata.json').read_text(encoding='utf-8'))
    expected=dict(protocol='campaign-021-buffer-capacity-1',rules_version='v0-darwin-1',
        seeds=list(range(1800,1810)),arms=['block'],thresholds=[40,160],capacities=[24,96],
        renewal_regimes={k:list(v) for k,v in REGIMES.items()},movement_cost=0,birth_cost=0,steps=10000,
        observation_schemas=dict(feeding=3,terminal=1,energy=1),early_window=[0,100],baseline_config=BASE,
        initial_food_energy=5120,initial_total_energy=7040,layout_seed_offset=1000000,founder_trait=250,
        nominal_supply_per_thousand=60,mutation_probability=0,status='complete',completed_runs=120,git_dirty=False)
    if any(metadata.get(k)!=v for k,v in expected.items()):raise ValueError('Expected complete registered campaign')
    if metadata['protocol_sha256']!=digest(root/'experiments/v0/campaign-021.md'):raise ValueError('Protocol changed')
    records=json.loads((args.input/'results.json').read_text(encoding='utf-8'))
    fields=('arm','birth_threshold','renewal','food_capacity','seed')
    grid=list(product(('block',),(40,160),REGIMES,(24,96),range(1800,1810)))
    index={tuple(r[k] for k in fields):r for r in records}
    if len(records)!=120 or set(index)!=set(grid):raise ValueError('Incomplete or duplicate grid')
    verified={};initials={};hashes={}
    for arm,threshold,renewal,capacity,seed in grid:
        prefix=f'{arm}-threshold-{threshold}-renewal-{renewal}-capacity-{capacity}-seed-{seed}'
        ip=args.input/(prefix+'-initial.json');mp=args.input/(prefix+'.csv')
        initial=json.loads(ip.read_text(encoding='utf-8'))
        exposure=verify_initial(initial,arm,threshold,renewal,capacity,seed)
        paired=(initial['founders'],initial['food'],initial['rng_sha256'])
        if seed in initials and paired!=initials[seed]:raise ValueError('Twelve-way initialization mismatch')
        initials[seed]=paired
        with mp.open(encoding='utf-8',newline='') as f:
            rows=[{k:None if v=='' else float(v) if k=='mean_genome' else int(v) for k,v in r.items()} for r in csv.DictReader(f)]
        result=dict(arm=arm,birth_threshold=threshold,renewal=renewal,food_capacity=capacity,movement_cost=0,birth_cost=0,seed=seed,
            **verify_rows(rows,REGIMES[renewal][1],capacity),**early_observations(rows),**resource_checkpoints(rows),
            **window_observations(rows),**exposure,population_at_500=rows[500]['population'],population_at_5000=rows[5000]['population'])
        key=(arm,threshold,renewal,capacity,seed)
        if result!=index[key]:raise ValueError('Recorded endpoints differ from metrics')
        verified[key]=result
        for p in (ip,mp):hashes[p.name]=digest(p)
    with (args.input/'results.csv').open(encoding='utf-8',newline='') as f:csv_rows=list(csv.DictReader(f))
    if csv_rows!=[{k:'' if v is None else str(v) for k,v in r.items()} for r in records]:raise ValueError('CSV/JSON mismatch')
    for name in ('results.json','results.csv'):hashes[name]=digest(args.input/name)
    pairs=[];comparisons=[];groups=[]
    for threshold,renewal in product((40,160),REGIMES):
        statuses={k:0 for k in ('both_alive','capacity_96_only','capacity_24_only','both_extinct')}
        for seed in range(1800,1810):
            small,large=(verified['block',threshold,renewal,c,seed] for c in (24,96))
            status=('both_alive' if large['population'] else 'capacity_24_only') if small['population'] else ('capacity_96_only' if large['population'] else 'both_extinct')
            statuses[status]+=1
            pairs.append(dict(birth_threshold=threshold,renewal=renewal,seed=seed,status=status,
                capacity_24_population=small['population'],capacity_96_population=large['population']))
        comparisons.append(dict(birth_threshold=threshold,renewal=renewal,**statuses,
            signed_discordance=statuses['capacity_96_only']-statuses['capacity_24_only']))
        for capacity in (24,96):
            selected=[verified['block',threshold,renewal,capacity,s] for s in range(1800,1810)]
            extinct=[r['extinction_tick'] for r in selected if r['extinction_tick'] is not None]
            keys=list(early_observations(rows))+list(resource_checkpoints(rows))+list(window_observations(rows))
            groups.append(dict(birth_threshold=threshold,renewal=renewal,food_capacity=capacity,runs=10,
                alive_at_500=sum(r['population_at_500']>0 for r in selected),alive_at_5000=sum(r['population_at_5000']>0 for r in selected),
                alive_at_10000=sum(r['population']>0 for r in selected),extinct_only_range=[min(extinct),max(extinct)] if extinct else None,
                ranges={k:[min(r[k] for r in selected),max(r[k] for r in selected)] for k in keys}))
    report=dict(runs=list(verified.values()),groups=groups,capacity_pairs=pairs,capacity_comparisons=comparisons,
        initial_states_checked=120,matched_seed_twelve_way_groups=10,metric_rows_checked=1200120,
        uptake_transitions_checked=1200000,input_sha256=hashes,metadata_sha256=digest(args.input/'metadata.json'),
        script_sha256=digest(Path(__file__)),geometry_helper_sha256=digest(Path(__file__).with_name('summarize_v0_food_geometry.py')),
        scope='Independent initialization, full metric accounting, fixed endpoints/window partitions and capacity pairs. Early actor records need separate verification. No independent dynamic replay, pure cap-loss mediation or permanent-survival claim.')
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(comparisons,indent=2))


if __name__=='__main__':main()
