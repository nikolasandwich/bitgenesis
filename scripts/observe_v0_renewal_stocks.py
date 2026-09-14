"""Read-only pre-renewal stock and shadow-arrival observation for fixed V0."""
from fractions import Fraction
import hashlib
from pathlib import Path
import random

from bitgenesis.v0 import engine
from scripts.calibrate_v0_renewal_capacity import REGIMES,law

ENGINE_SHA='8f3ed33ad0ebe802c099e3e6f8ae61f9bcc526b98512f31f48ec40478fbfa7ff'


def check_engine():
    digest=hashlib.sha256(Path(engine.__file__).read_text(encoding='utf-8').encode()).hexdigest()
    if digest!=ENGINE_SHA:raise ValueError('Renewal observer requires reviewed engine')
    return digest


def capture(world):
    """Inspect before step; caller binds actual increment after the unchanged step."""
    c=world.config
    if c.food_capacity!=24 or (c.regrowth_probability,c.regrowth_amount) not in REGIMES.values():
        raise ValueError('Unregistered renewal configuration')
    food=list(world.food)
    if len(food)!=c.width*c.height or any(type(v) is not int or not 0<=v<=24 for v in food):
        raise ValueError('Invalid stock vector')
    histogram=[0]*25
    for stock in food:histogram[stock]+=1
    state=world.rng.getstate()
    shadow=random.Random();shadow.setstate(state)
    successes=admitted=0
    for stock in food:
        if shadow.randrange(1000)<c.regrowth_probability:
            successes+=1;admitted+=min(c.regrowth_amount,24-stock)
    expected={name:sum((count*law(stock,*parameters)['mean'] for stock,count in enumerate(histogram)),Fraction(0))
              for name,parameters in REGIMES.items()}
    current=next(name for name,value in REGIMES.items() if value==(c.regrowth_probability,c.regrowth_amount))
    uncapped=successes*c.regrowth_amount
    return dict(schema=1,tick=world.tick+1,prior_population=len(world.living),
        active_start=bool(world.living),food=food,rng_state=state,histogram=histogram,
        expected_added={name:str(value) for name,value in expected.items()},
        expected_cap_loss=str(Fraction(60*len(food),1000)-expected[current]),
        successful_arrivals=successes,uncapped_arrival_energy=uncapped,
        admitted_energy=admitted,discarded_energy=uncapped-admitted)


def reconcile(observation,before,after):
    if observation['tick']!=after['tick'] or before['tick']+1!=after['tick']:
        raise ValueError('Observation tick mismatch')
    if observation['prior_population']!=before['population'] or sum(observation['food'])!=before['food_energy']:
        raise ValueError('Observation boundary mismatch')
    actual=after['supplied_energy']-before['supplied_energy']
    if actual!=observation['admitted_energy']:
        raise ValueError('Shadow arrival differs from actual supply')
    return {**observation,'actual_supplied_increment':actual}
