"""Benchmark: python3 bench.py --seeds A-B [--hmax 3 --wmax 7] [--set NAME=VALUE ...]"""
import argparse
import time

import gen
import score
import solution


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', default='1-10')
    ap.add_argument('--hmax', type=int, default=3)
    ap.add_argument('--wmin', type=int, default=3)
    ap.add_argument('--wmax', type=int, default=7)
    ap.add_argument('--small', action='store_true',
                    help='sample-like instances: 2-3 pages, W 20-30, H 4-6')
    ap.add_argument('--set', action='append', default=[], metavar='NAME=VALUE')
    a = ap.parse_args()
    for kv in a.set:
        k, v = kv.split('=', 1)
        if not hasattr(solution, k):
            raise SystemExit('unknown constant %s' % k)
        setattr(solution, k, eval(v, {}, {}))
    lo, _, hi = a.seeds.partition('-')
    seeds = range(int(lo), int(hi or lo) + 1)
    scores = []
    worst = 0.0
    for seed in seeds:
        kw = dict(wlim=(20, 30), hlim=(4, 6), plim=(2, 3)) if a.small else {}
        pieces, truth = gen.generate(seed, hmax=a.hmax, wmin=a.wmin, wmax=a.wmax, **kw)
        t = time.perf_counter()
        res = solution.assemble(pieces)
        dt = time.perf_counter() - t
        s = score.score(pieces, truth, res)
        scores.append(s)
        worst = max(worst, dt)
        print('seed %3d  N=%4d  score=%.4f  %.2fs' % (seed, len(pieces), s, dt))
    print('mean score %.4f  max seconds %.2f' % (sum(scores) / len(scores), worst))


if __name__ == '__main__':
    main()
