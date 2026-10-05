import unittest
from scripts import verify_v4_policy_component_timing as v

def row(t,ids,copy=False,double=False):
 return dict(tick=t,slots=[dict(identities=ids,birth_ticks=[1 if i is not None else None for i in ids],new_copy=copy)],new_copy_count=2 if double else 0,births=[],deaths=[])
class TimingVerifierTests(unittest.TestCase):
 def test_diagnostic_copresence_not_future_copy(self):
  diag=row(5,[3,4],True,True);future=[row(6,[3,4]),row(7,[3,4],True,True)]
  out=v.pair_history(diag,future)
  p=out['upper_identity_pairs'][0]
  self.assertEqual(p['first_copresence_tick'],5)
  self.assertEqual(p['first_future_copresence_tick'],6)
  self.assertEqual(p['first_upper_new_copy_tick'],7)
  self.assertEqual(p['first_double_new_tick'],7)
  self.assertEqual(out['upper_identity_changes'],[])
 def test_partial_pairs_changes_and_return(self):
  diag=row(5,[None,None]);future=[row(6,[3,None]),row(7,[3,4]),row(8,[3,None]),row(9,[3,4])]
  result=v.pair_history(diag,future)
  self.assertEqual(len(result['upper_identity_changes']),4)
  self.assertEqual(len(result['upper_identity_pairs']),1)
  self.assertEqual(result['upper_identity_pairs'][0]['first_copresence_tick'],7)
  self.assertIsNone(result['upper_identity_pairs'][0]['first_upper_new_copy_tick'])
 def test_numeric_nested_delta_preserves_zero(self):
  self.assertEqual(v.difference({'x':{'z':2,'n':0}},{'x':{'z':5,'n':0}}),{'x':{'z':-3,'n':0}})
if __name__=='__main__':unittest.main()
