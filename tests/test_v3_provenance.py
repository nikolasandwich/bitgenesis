import unittest
from scripts.v3_provenance import trace


class ProvenanceTests(unittest.TestCase):
    def test_self_and_partner_attribution_depend_on_order(self):
        lineage=[dict(id=0,founder=0),dict(id=1,founder=1)]
        def actor(identifier,before,consumed,released,after):
            return dict(id=identifier,feeding=dict(site=0,b_before=before,consumed_b=consumed,
                                                 released_b=released,remaining_b=after))
        steps=[dict(actors=[actor(0,0,0,2,2),actor(1,2,0,2,4),actor(0,4,2,0,2)])]
        old=trace([0],[2],lineage,steps,'oldest_first')
        new=trace([0],[2],lineage,steps,'newest_first')
        self.assertEqual(old['categories']['self'],2)
        self.assertEqual(new['categories']['other_founder'],2)
        self.assertEqual(old['consumed_b'],new['consumed_b'])
        with self.assertRaises(ValueError):
            trace([0],[3],lineage,steps,'oldest_first')

    def test_new_release_cannot_feed_same_event(self):
        steps=[dict(actors=[dict(id=0,feeding=dict(site=0,b_before=1,consumed_b=1,
                                                 released_b=2,remaining_b=2))])]
        result=trace([1],[2],[dict(id=0,founder=0)],steps,'newest_first')
        self.assertEqual(result['categories']['initial'],1)
        self.assertEqual(result['categories']['self'],0)


if __name__=='__main__':
    unittest.main()
