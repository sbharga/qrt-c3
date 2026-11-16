import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import solution as S

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class LmTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(HERE, 'samples', 'sample.txt')) as f:
            pieces = f.read().split('\n')[1:35]
        S._build_lm([r for p in pieces for r in p.replace('_', ' ').split('|')])

    def test_true_join_beats_false(self):
        d = S.delta_row
        # "bicycles" is not in the lexicon, so only the ordering is meaningful
        self.assertGreater(d("t bicy", "cles "), d("t bicy", "ndon  "))
        self.assertLess(d("t bicy", "ndon  "), 0)
        self.assertGreater(d("mapmaker glued", " in"), d("mapmaker glued", "ndon"))
        self.assertGreater(d("Jigsa", "w puzzl"), d("Jigsa", "hen a"))
        self.assertGreater(d("mapma", "ker "), d("mapma", "oden"))

    def test_text_after_padding_is_violation(self):
        self.assertEqual(S.delta_row("ndon  ", "x"), S.VIOL)
        self.assertEqual(S.delta_row("ab", "  "), 0.0)


if __name__ == '__main__':
    unittest.main()
