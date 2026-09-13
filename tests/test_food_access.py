import unittest

from scripts.analyze_v0_food_access import distances


class FoodAccessTests(unittest.TestCase):
    def test_shortest_paths_match_independent_toroidal_distance(self):
        for width,height,sources in ((5,4,(0,)),(7,6,(0,17)),(2,3,(1,))):
            food = [int(p in sources) for p in range(width*height)]
            actual = distances(food,width,height)
            expected = []
            for p in range(width*height):
                x,y = p%width,p//width
                expected.append(min(min(abs(x-q%width),width-abs(x-q%width)) +
                                    min(abs(y-q//width),height-abs(y-q//width)) for q in sources))
            self.assertEqual(actual,expected)

    def test_all_food_means_zero_distance(self):
        self.assertEqual(distances([5]*12,4,3),[0]*12)

    def test_missing_food_and_invalid_maps_are_rejected(self):
        for food,width,height in (([0]*4,2,2),([1]*3,2,2),([1,-1,0,0],2,2),
                                  ([True,0,0,0],2,2)):
            with self.subTest(food=food), self.assertRaises(ValueError):
                distances(food,width,height)
