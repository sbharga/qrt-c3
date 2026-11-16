import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gen import generate


class GenTest(unittest.TestCase):
    def test_seeds(self):
        for seed in range(20):
            pieces, truth = generate(seed)
            pages = truth['pages']
            grids = [[[None] * p['W'] for _ in range(p['H'])] for p in pages]
            self.assertEqual(len(pieces), len(truth['pieces']))
            for s, (pg, r, c) in zip(pieces, truth['pieces']):
                rows = s.replace('_', ' ').split('|')
                self.assertTrue(s.strip('_|'), 'all-space piece')
                self.assertEqual(len({len(x) for x in rows}), 1, 'not rectangular')
                if pg < 0:
                    continue
                for dr, row in enumerate(rows):
                    for dc, ch in enumerate(row):
                        self.assertIsNone(grids[pg][r + dr][c + dc], 'overlap')
                        grids[pg][r + dr][c + dc] = ch
            for pg, g in zip(pages, grids):
                self.assertTrue(40 <= pg['W'] <= 60 and 10 <= pg['H'] <= 14)
                self.assertEqual(len(pg['lines']), pg['H'])
                for r, line in enumerate(pg['lines']):
                    self.assertEqual(len(line), pg['W'])
                    for c, ch in enumerate(line):
                        if g[r][c] is None:
                            self.assertEqual(ch, ' ', 'uncovered non-space')
                        else:
                            self.assertEqual(g[r][c], ch)
                    self.assertNotEqual(line[0], ' ')
                for a, b in zip(pg['lines'], pg['lines'][1:]):
                    if a.rstrip().endswith('-'):
                        continue
                    self.assertGreater(len(a.rstrip()) + 1 + len(b.split(' ')[0]), pg['W'])


if __name__ == '__main__':
    unittest.main()
