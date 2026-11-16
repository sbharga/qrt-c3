import random
import sys
import time

from solution import generate_grid, _validate

ALPHA = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
DIRS = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0)]


def brute_occurs(rows, word):
    n = len(rows)
    for r in range(n):
        for c in range(n):
            for dr, dc in DIRS:
                if all(rows[(r + k * dr) % n][(c + k * dc) % n] == word[k]
                       for k in range(len(word))):
                    return True
    return False


def brute_valid(rows, req, forb):
    n = len(rows)
    L = max((len(w) for w in req), default=1)
    if n == 0 or n < L or any(len(r) != n for r in rows):
        return False
    if any(ch not in ALPHA for r in rows for ch in r):
        return False
    return all(brute_occurs(rows, w) for w in req) and not any(
        brute_occurs(rows, w) for w in forb)


def crosscheck():
    assert brute_occurs(['AB', 'CD'], 'ABABA')
    assert not _validate(['AB', 'CD'], set(), {'ABABA'}, 1)
    grid = ['QATSUR', 'YFLRUB', 'ILJAVA', 'UREUCW', 'GELLSS', 'YPNOHT']
    req = {'PYTHON', 'JAVA', 'RUBY', 'PERL', 'RUST', 'SWIFT', 'SCALA', 'LUA'}
    assert _validate(grid, req, set(), 6)
    assert brute_valid(grid, req, set())
    rr = random.Random(7)
    for _ in range(300):
        n = rr.randint(1, 4)
        rows = [''.join(rr.choice('ABC') for _ in range(n)) for _ in range(n)]
        w = ''.join(rr.choice('ABC') for _ in range(rr.randint(1, 9)))
        assert _validate(rows, set(), {w}, 1) == (not brute_occurs(rows, w)), (rows, w)


def rand_word(rng, lo, hi, alpha=ALPHA):
    return ''.join(rng.choice(alpha) for _ in range(rng.randint(lo, hi)))


def ok_forb(f, req):
    return not any(f in w or f[::-1] in w for w in req)


def gen_forb(rng, count, lo, hi, req, alpha=ALPHA):
    out = []
    while len(out) < count:
        f = rand_word(rng, lo, hi, alpha)
        if ok_forb(f, req):
            out.append(f)
    return out


def build_cases():
    cases = []
    cases.append(('tiny_single', ['A'], [], 1))
    cases.append(('statement_example', ['ACE', 'FIG', 'OAK'], [], 3))
    cases.append(('statement_langs',
                  ['PYTHON', 'JAVA', 'RUBY', 'PERL', 'RUST', 'SWIFT', 'SCALA', 'LUA'], [], None))
    cases.append(('reverse_impossible', ['ABC'], ['CBA'], None))

    rng = random.Random(1)
    req = [rand_word(rng, 3, 9) for _ in range(40)]
    cases.append(('no_forbidden', req, [], None))

    rng = random.Random(2)
    req = [rand_word(rng, 3, 9) for _ in range(40)]
    cases.append(('forbidden_light', req, gen_forb(rng, 30, 3, 4, req), None))

    rng = random.Random(3)
    req = [rand_word(rng, 4, 7) for _ in range(25)]
    forb = gen_forb(rng, 60, 2, 3, req)
    covered = {ch for f in forb for ch in f}
    for c in ALPHA:
        if c not in covered and ok_forb(c * 2, req):
            forb.append(c * 2)
    cases.append(('no_safe_letter', req, forb, None))

    rng = random.Random(4)
    req = [rand_word(rng, 4, 6, 'ABCDE') for _ in range(20)]
    forb = [f for f in ('AB' * 15 + 'A', 'ABC' * 4) if ok_forb(f, req)]
    cases.append(('long_forbidden', req, forb, None))

    rng = random.Random(5)
    src = rand_word(rng, 60, 60)
    req = []
    for _ in range(40):
        m = rng.randint(4, 10)
        i = rng.randint(0, 60 - m)
        req.append(src[i:i + m])
    cases.append(('overlap_rich', req, [], None))

    rng = random.Random(6)
    req = [rand_word(rng, 5, 12) for _ in range(150)]
    cases.append(('large', req, gen_forb(rng, 50, 3, 5, req), None))

    rng = random.Random(8)
    cases.append(('many_short', [rand_word(rng, 3, 4) for _ in range(300)], [], None))
    rng = random.Random(9)
    cases.append(('small_alpha', [rand_word(rng, 4, 8, 'ABCD') for _ in range(100)], [], None))
    rng = random.Random(10)
    req = [rand_word(rng, 3, 8) for _ in range(100)]
    cases.append(('mid_mix', req, gen_forb(rng, 20, 3, 4, req), None))
    rng = random.Random(12)
    n0 = 14
    grid = [[rng.choice(ALPHA) for _ in range(n0)] for _ in range(n0)]
    req = []
    for _ in range(120):
        m = rng.randint(4, 10)
        dr, dc = rng.choice(DIRS)
        r, c = rng.randrange(n0), rng.randrange(n0)
        req.append(''.join(grid[(r + k * dr) % n0][(c + k * dc) % n0] for k in range(m)))
    cases.append(('planted', req, [], None))
    return cases


def main():
    crosscheck()
    print('cross-checks passed')
    fail = False
    scores = []
    for name, req, forb, expect_n in build_cases():
        t = time.perf_counter()
        rows = generate_grid(req, forb)
        dt = time.perf_counter() - t
        S = sum(len(w) for w in req)
        L = max(len(w) for w in req)
        N = len(rows)
        C = 0
        while 17 * (C + 1) ** 2 <= 10 * S:
            C += 1
        target = max(L, C)
        score = 100 * min(1, S / (1.7 * N * N))
        valid = brute_valid(rows, req, forb)
        if name != 'reverse_impossible':
            scores.append(score if valid else 0.0)
        print(f'{name}: S={S} L={L} N={N} target={target} score={score:.1f} '
              f'valid={valid} seconds={dt:.2f}')
        if name != 'reverse_impossible' and not valid:
            print('  FAIL: invalid')
            fail = True
        if dt > 9.0:
            print('  FAIL: too slow')
            fail = True
        if expect_n is not None and N != expect_n:
            print(f'  FAIL: expected N={expect_n}')
            fail = True
    print(f'AVERAGE score over {len(scores)} feasible cases: {sum(scores) / len(scores):.2f}')
    sys.exit(1 if fail else 0)


if __name__ == '__main__':
    main()
