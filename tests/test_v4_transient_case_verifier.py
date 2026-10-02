import unittest
from scripts.verify_v4_transient_case import reconstruct

def unit(e):return {'energy':e}
def fixture(foreign=False):
    initial=dict(site_ids=[0,1,2,None],units=[unit(1 if foreign else 10),unit(5 if foreign else 10),unit(20 if foreign else 5),None])
    if foreign:
        ids=[3,1,2,None];inter=[unit(0),unit(5),unit(20),None];after=[unit(7),unit(5),unit(8),None]
        bonds=[];transfers=[];proposal=dict(reason='formed',source=2,target=0,cost=5,child_energy=7,parent_energy=8)
        groups=[[3],[1],[2]];parents=[None,None,None,2];deaths=[1,None,None,None];dissolved=[0]
    else:
        ids=[0,1,2,3];inter=[unit(7),unit(11),unit(5),None];after=[unit(7),unit(3),unit(5),unit(3)]
        bonds=[[0,1]];transfers=[dict(donor=0,recipient=1,amount=2)];proposal=dict(reason='formed',source=1,target=3,cost=5,child_energy=3,parent_energy=3)
        groups=[[0,1,3],[2]];parents=[None,None,None,1];deaths=[None]*4;dissolved=[]
    physical=dict(units=after,interaction_units=inter,interaction_components=[[0],[1],[2]] if foreign else [[0,1],[2]],driven=dict(inputs=[dict(site=i,accepted=0,leakage=int(foreign and i==0)) for i in range(4)],interaction=dict(bonds=bonds,transfers=transfers)),material=dict(proposals=[proposal],dissolved=dissolved))
    rows=[dict(tick=1,site_ids=ids,physical=physical,observation={'components':{'material':groups}})]
    final=dict(parents=parents,death_ticks=deaths,site_ids=ids,units=after)
    return initial,rows,final,dict(bond_cost=1,construction_cost=4,copy_cost=1)

class CaseReconstructionTests(unittest.TestCase):
    def test_internal_exchange_and_child_allocation(self):
        bios,steps=reconstruct(*fixture(),anchor_members=(0,1));x=steps[0]
        self.assertEqual((x['ledger']['energy_before'],x['ledger']['energy_after'],x['ledger']['internal_transfer']),(20,13,2))
        self.assertEqual(x['ledger']['formation_cost'],5)
        self.assertEqual(x['births'],[dict(identity=3,parent=1,founder=1,site=3,energy=3)])
        self.assertEqual(x['members'][1]['energy_to_child'],3)
        self.assertEqual(next(b for b in bios if b['identity']==3)['born_tick'],1)
    def test_same_site_foreign_birth_not_family_resurrection(self):
        bios,steps=reconstruct(*fixture(True),anchor_members=(0,1));x=steps[0]
        self.assertEqual(x['deaths'],[0]);self.assertEqual(x['births'],[])
        self.assertEqual(x['interaction']['population'],2);self.assertEqual(x['material_final']['population'],1)
        self.assertEqual(x['members'][0]['energy_after'],0)
        self.assertEqual([b['identity'] for b in bios],[0,1])
    def test_broken_energy_and_parent_claim_rejected(self):
        args=fixture();args[1][0]['physical']['units'][0]['energy']=8
        with self.assertRaises(AssertionError):reconstruct(*args,anchor_members=(0,1))
        args=fixture();args[2]['parents'][3]=0
        with self.assertRaises(AssertionError):reconstruct(*args,anchor_members=(0,1))
