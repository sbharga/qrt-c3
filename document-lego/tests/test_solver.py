import json
import os
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import gen
import score
import solution

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def check_valid(tc, pieces, res):
    tc.assertEqual(sorted(r[0] for r in res), list(range(len(pieces))))
    rects = {}
    for pid, label, r, c in res:
        rows = pieces[pid].split('|')
        h, w = len(rows), len(rows[0])
        for r0, c0, r1, c1 in rects.get(label, []):
            tc.assertFalse(r < r1 and r + h > r0 and c < c1 and c + w > c0, 'overlap')
        rects.setdefault(label, []).append((r, c, r + h, c + w))


class SolverTest(unittest.TestCase):
    def test_sample(self):
        with open(os.path.join(HERE, 'samples', 'sample.txt')) as f:
            pieces = f.read().split('\n')[1:35]
        with open(os.path.join(HERE, 'samples', 'sample_truth.json')) as f:
            truth = json.load(f)
        res = solution.assemble(pieces)
        check_valid(self, pieces, res)
        # regression floor (measured 0.247)
        self.assertGreaterEqual(score.score(pieces, truth, res), 0.20)

    def test_generated(self):
        tot = 0.0
        for seed in (1, 2, 3):
            pieces, truth = gen.generate(seed)
            t = time.perf_counter()
            res = solution.assemble(pieces)
            self.assertLess(time.perf_counter() - t, 9.0)
            check_valid(self, pieces, res)
            tot += score.score(pieces, truth, res)
        # regression floor (measured ~0.12)
        self.assertGreaterEqual(tot / 3, 0.08)


if __name__ == '__main__':
    unittest.main()
