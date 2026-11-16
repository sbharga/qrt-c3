import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from score import score

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIECES = open(os.path.join(HERE, 'samples', 'sample.txt')).read().split('\n')[1:35]
TRUTH = json.load(open(os.path.join(HERE, 'samples', 'sample_truth.json')))
TP = TRUTH['pieces']


def nonspace(i):
    return sum(ch not in '_|' for ch in PIECES[i])


class ScoreTest(unittest.TestCase):
    def test_truth_is_perfect(self):
        lines = [(i, p, r, c) for i, (p, r, c) in enumerate(TP) if p >= 0]
        self.assertEqual(score(PIECES, TRUTH, lines), 1.0)

    def test_shift_invariant(self):
        lines = [(i, p, r + (5 if p == 0 else 0), c - (3 if p == 0 else 0))
                 for i, (p, r, c) in enumerate(TP) if p >= 0]
        self.assertEqual(score(PIECES, TRUTH, lines), 1.0)

    def test_split_page_counts_best_part(self):
        lines = []
        c7 = c8 = 0
        for i, (p, r, c) in enumerate(TP):
            if p == 0:
                left = c < 12
                lines.append((i, 7 if left else 8, r, c))
                if left:
                    c7 += nonspace(i)
                else:
                    c8 += nonspace(i)
            elif p == 1:
                lines.append((i, 9, r, c))
        self.assertAlmostEqual(score(PIECES, TRUTH, lines), (75 + max(c7, c8)) / 178)

    def test_duplicates_and_overlaps_ignored(self):
        base = [(i, p, r, c) for i, (p, r, c) in enumerate(TP) if p >= 0]
        # piece 24 at (0,0); piece 25 listed again elsewhere; a later overlapping piece
        extra = [(24, 0, 9, 9), (10, 0, 0, 0)]
        self.assertEqual(score(PIECES, TRUTH, base + extra), score(PIECES, TRUTH, base))
        self.assertEqual(score(PIECES, TRUTH, base + extra), 1.0)

    def test_malformed(self):
        self.assertEqual(score(PIECES, TRUTH, ['1 2 3']), 0.0)
        self.assertEqual(score(PIECES, TRUTH, ['34 0 0 0']), 0.0)
        self.assertEqual(score(PIECES, TRUTH, ['a 0 0 0']), 0.0)


if __name__ == '__main__':
    unittest.main()
