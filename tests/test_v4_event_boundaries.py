import unittest
from scripts.map_v4_study011_events import transition, selected_events


class EventBoundariesTests(unittest.TestCase):
    def test_birth_merge(self):
        r=transition([[1,2],[3]],[[1,2,3,4]],'birth',4,1)
        self.assertEqual(r['gained'],[3,4])
        self.assertEqual(r['lost'],[])
        self.assertEqual(r['after_components'],[[1,2,3,4]])

    def test_death_split_and_missing(self):
        r=transition([[1,2,3]],[[1],[3]],'death',2,None)
        self.assertEqual(r['lost'],[2])
        self.assertEqual(r['after_components'],[[1],[3]])
        self.assertIsNone(transition([[1,2]],None,'death',2,None))
        with self.assertRaises(ValueError): transition([[1]],[[1]],'death',2,None)

    def test_dedup_keeps_references_and_event_kind(self):
        rec=dict(component=0,whole_world_anchor=False,birth_ids=[5],death_ids=[5])
        panels=[dict(phase=p,boundary='material',anchor=100,horizon=100,records=[rec]) for p in ('interaction','final')]
        r=selected_events(panels,[(101,5)],[(102,5)])
        self.assertEqual(len(r),2)
        self.assertTrue(all(len(x['references'])==2 for x in r))
        with self.assertRaises(ValueError): selected_events(panels,[],[(102,5)])


if __name__=='__main__': unittest.main()
