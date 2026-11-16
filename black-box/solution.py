"""Noise-robust maximiser for a black-box payoff function.

`query(x)` takes a list of `dim` floats in [0, 1] and returns a noisy payoff.
`maximize` spends at most `budget` queries and returns the point with the best
estimated noiseless payoff (the mean over repeated queries).
"""

import math
import random


class _Point:
    __slots__ = ("x", "total", "n")

    def __init__(self, x):
        self.x = x
        self.total = 0.0
        self.n = 0

    @property
    def mean(self):
        return self.total / self.n if self.n else -math.inf


def maximize(query, dim=1, budget=1000, seed=0):
    rng = random.Random(seed)
    used = 0

    def sample(p, times=1):
        nonlocal used
        for _ in range(times):
            if used >= budget:
                return
            p.total += query(p.x)
            p.n += 1
            used += 1

    # 1. Explore: one query on each of many uniform random points.
    n0 = max(4, budget // 4)
    pool = [_Point([rng.random() for _ in range(dim)]) for _ in range(n0)]
    for p in pool:
        sample(p)

    # 2. Successive halving: average noise out on the survivors.
    while len(pool) > 1 and used < budget * 3 // 4:
        pool.sort(key=lambda p: p.mean, reverse=True)
        pool = pool[: max(1, len(pool) // 2)]
        per_point = max(1, (budget // 4) // (2 * len(pool)))
        for p in pool:
            sample(p, per_point)
    best = max(pool, key=lambda p: p.mean)

    # 3. Local refinement with shrinking step; accept only on better averages.
    sigma = 0.1
    reps = 3
    while used < budget:
        cand = _Point([min(1.0, max(0.0, v + rng.gauss(0, sigma))) for v in best.x])
        sample(cand, reps)
        if cand.n == 0:
            break
        if cand.mean > best.mean:
            # Re-check the incumbent so a lucky early reading can't block progress.
            sample(best, reps)
            if cand.mean > best.mean:
                best = cand
        else:
            sigma = max(sigma * 0.97, 1e-3)

    return best.x, best.mean


def main():
    # Self-test: noisy payoff peaked at (0.3, 0.7), noise sd 0.5.
    rng = random.Random(1)
    target = [0.3, 0.7]

    def query(x):
        return 10 - 20 * sum((a - b) ** 2 for a, b in zip(x, target)) + rng.gauss(0, 0.5)

    x, est = maximize(query, dim=2, budget=2000)
    print("best x =", [round(v, 3) for v in x], "estimated payoff =", round(est, 3))


if __name__ == "__main__":
    main()
