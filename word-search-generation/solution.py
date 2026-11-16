#!/bin/python3

import math
import os
import random
import re
import sys
import time

TIME_LIMIT = 8.0
ALPHA = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
ALPHA_SET = frozenset(ALPHA)
BLANK = '.'
TEMP = 1.5


class SizeData:
    __slots__ = ('n', 'lines', 'cell_line', 'ext', 'pset', 'plens', 'M',
                 'freq', 'safe', 'wild', 'pad')


def _reduce(p, n):
    if len(p) <= n:
        return p
    for i in range(n, len(p)):
        if p[i] != p[i - n]:
            return None
    return p[:n]


def _build_size(n, forb, L):
    sd = SizeData()
    sd.n = n
    sd.pad = L - 1
    lines = []
    for f in range(4):
        for k in range(n):
            if f == 0:
                lines.append([k * n + j for j in range(n)])
            elif f == 1:
                lines.append([j * n + k for j in range(n)])
            elif f == 2:
                lines.append([j * n + (k + j) % n for j in range(n)])
            else:
                lines.append([j * n + (k - j) % n for j in range(n)])
    sd.lines = lines
    cell_line = [[None] * (n * n) for _ in range(4)]
    for r in range(n):
        for c in range(n):
            x = r * n + c
            cell_line[0][x] = (r, c)
            cell_line[1][x] = (n + c, r)
            cell_line[2][x] = (2 * n + (c - r) % n, r)
            cell_line[3][x] = (3 * n + (c + r) % n, r)
    sd.cell_line = cell_line
    sd.ext = [li * 3 for li in lines]
    pset = set()
    for p in forb:
        q = _reduce(p, n)
        if q is not None:
            pset.add(q)
            pset.add(q[::-1])
    sd.pset = pset
    sd.plens = sorted(set(map(len, pset)))
    sd.M = max(sd.plens) if sd.plens else 0
    freq = dict.fromkeys(ALPHA, 0)
    for p in pset:
        for ch in p:
            freq[ch] += 1
    sd.freq = freq
    sd.safe = [ch for ch in ALPHA if freq[ch] == 0]
    sd.wild = None
    return sd


def _build_wild(sd):
    wild = {}
    for p in sd.pset:
        for j in range(len(p)):
            wild.setdefault(p[:j] + '?' + p[j + 1:], set()).add(p[j])
    sd.wild = wild


def _window(sd, g, x, f):
    lid, pos = sd.cell_line[f][x]
    M = sd.M
    a = sd.n + pos - (M - 1)
    return ''.join([g[i] for i in sd.ext[lid][a:a + 2 * M - 1]])


def _completes_forbidden(sd, g, x):
    M = sd.M
    pset = sd.pset
    plens = sd.plens
    for f in range(4):
        w = _window(sd, g, x, f)
        for m in plens:
            for s in range(M - m, M):
                if w[s:s + m] in pset:
                    return True
    return False


def _banned(sd, g, x):
    M = sd.M
    plens = sd.plens
    wild = sd.wild
    out = set()
    for f in range(4):
        w = _window(sd, g, x, f)
        w = w[:M - 1] + '?' + w[M:]
        for m in plens:
            for s in range(M - m, M):
                b = wild.get(w[s:s + m])
                if b:
                    out |= b
    return out


def _place_one(sd, g, lstr, wt, rng, explore):
    """Find or place one word. Returns (cells, new_cells) or None."""
    n = sd.n
    w, m, rx_fwd, rx_rev = wt
    lines = sd.lines
    buckets = {}
    big = ''.join(lstr)
    stride = n + sd.pad + 1
    for rx, rev in ((rx_fwd, False), (rx_rev, True)):
        if rx is None:
            continue
        for mt in rx.finditer(big):
            p = mt.start()
            lid, s = divmod(p, stride)
            if s >= n:
                continue
            ov = m - mt.group(1).count('.')
            buckets.setdefault(ov, []).append((lid, s, rev))
    if not buckets:
        return None
    keys = sorted(buckets, reverse=True)
    if keys[0] == m:
        lid, s, rev = rng.choice(buckets[m])
        li = lines[lid]
        return [li[(s + k) % n] for k in range(m)], []
    groups = [buckets[k] for k in keys]
    if len(groups) >= 2 and rng.random() < explore:
        groups[:2] = [groups[0] + groups[1]]
    has_forb = bool(sd.pset)
    tries = 0
    for grp in groups:
        rng.shuffle(grp)
        for lid, s, rev in grp:
            if tries >= 200:
                return None
            tries += 1
            li = lines[lid]
            letters = w[::-1] if rev else w
            cells = [li[(s + k) % n] for k in range(m)]
            new = []
            for k in range(m):
                x = cells[k]
                if g[x] == BLANK:
                    g[x] = letters[k]
                    new.append(x)
            if has_forb and any(_completes_forbidden(sd, g, x) for x in new):
                for x in new:
                    g[x] = BLANK
                continue
            return cells, new
    return None


def _sync(sd, g, lstr, cells):
    seen = set()
    for x in cells:
        for f in range(4):
            lid = sd.cell_line[f][x][0]
            if lid not in seen:
                seen.add(lid)
                t = ''.join([g[i] for i in sd.lines[lid]])
                lstr[lid] = t + t[:sd.pad] + '|'


def _lns(sd, pw, rng, deadline, hard):
    """Large-neighbourhood search: place every word; returns grid list or None."""
    n = sd.n
    g = [BLANK] * (n * n)
    nl = len(sd.lines)
    lstr = [(BLANK * n) + BLANK * sd.pad + '|'] * nl
    cnt = [0] * (n * n)
    placed = {}
    P = len(pw)

    def try_place(idxs):
        J = rng.choices([0.5, 3.0, 100.0], weights=[6, 3, 1])[0]
        explore = rng.choices([0.0, 0.2, 0.5], weights=[5, 3, 2])[0]
        order = sorted(idxs, key=lambda i: -(pw[i][1] + rng.random() * J))
        failed = []
        for pos, i in enumerate(order):
            if time.perf_counter() > hard:
                failed.extend(order[pos:])
                break
            res = _place_one(sd, g, lstr, pw[i], rng, explore)
            if res is None:
                failed.append(i)
                continue
            cells, new = res
            placed[i] = cells
            for x in cells:
                cnt[x] += 1
            if new:
                _sync(sd, g, lstr, new)
        return failed

    def remove(idxs):
        changed = []
        for i in idxs:
            for x in placed.pop(i):
                cnt[x] -= 1
                if cnt[x] == 0:
                    g[x] = BLANK
                    changed.append(x)
        _sync(sd, g, lstr, changed)

    unplaced = try_place(range(P))
    cost = sum(pw[i][1] for i in unplaced)
    while unplaced:
        if time.perf_counter() > deadline or not placed:
            return None
        sg, sl, sc, sp = g[:], lstr[:], cnt[:], dict(placed)
        keys = list(placed)
        r = min(len(keys), rng.choice([1, 1, 2, 2, 3, 4, 6]))
        removed = rng.sample(keys, r)
        remove(removed)
        failed = try_place(unplaced + removed)
        new_cost = sum(pw[i][1] for i in failed)
        if new_cost <= cost or rng.random() < math.exp((cost - new_cost) / TEMP):
            cost = new_cost
            unplaced = failed
        else:
            g[:], lstr[:], cnt[:] = sg, sl, sc
            placed.clear()
            placed.update(sp)
    return g


def _fill(sd, g, rng, deadline):
    blanks = [i for i, ch in enumerate(g) if ch == BLANK]
    if not blanks:
        return True
    if sd.safe:
        z = rng.choice(sd.safe)
        for i in blanks:
            g[i] = z
        return True
    if sd.wild is None:
        _build_wild(sd)
    letter_order = sorted(ALPHA, key=lambda ch: sd.freq[ch] + rng.random() * 0.5)
    keyed = [(26 - len(_banned(sd, g, x)), rng.random(), x) for x in blanks]
    keyed.sort()
    order = [t[2] for t in keyed]
    B = len(order)
    opts = [None] * B
    ptr = [0] * B
    k = 0
    nodes = 0
    budget = 50 * B + 1000
    while 0 <= k < B:
        x = order[k]
        if opts[k] is None:
            g[x] = BLANK
            ban = _banned(sd, g, x)
            opts[k] = [c for c in letter_order if c not in ban]
            ptr[k] = 0
        if ptr[k] < len(opts[k]):
            g[x] = opts[k][ptr[k]]
            ptr[k] += 1
            k += 1
            nodes += 1
            if nodes > budget or (nodes & 127 == 0 and time.perf_counter() > deadline):
                return False
        else:
            opts[k] = None
            g[x] = BLANK
            k -= 1
    return k == B


def _validate(rows, req_set, forb_set, L):
    n = len(rows)
    if n == 0 or n < L:
        return False
    if any(len(r) != n for r in rows):
        return False
    if set(''.join(rows)) - ALPHA_SET:
        return False
    lines = list(rows)
    lines += [''.join(rows[j][k] for j in range(n)) for k in range(n)]
    lines += [''.join(rows[j][(k + j) % n] for j in range(n)) for k in range(n)]
    lines += [''.join(rows[j][(k - j) % n] for j in range(n)) for k in range(n)]
    maxlen = max((len(w) for w in req_set | forb_set), default=1)
    reps = (2 * n + maxlen - 2) // n
    big = '|'.join(line * reps for line in lines)
    for w in req_set:
        if w not in big and w[::-1] not in big:
            return False
    for w in forb_set:
        if w in big or w[::-1] in big:
            return False
    return True


def generate_grid(required_words, forbidden_words):
    start = time.perf_counter()
    deadline = start + TIME_LIMIT
    rng = random.Random(0x5EED)

    req = [w for w in required_words if w]
    forb = [w for w in forbidden_words if w]
    S = sum(len(w) for w in required_words)
    L = max((len(w) for w in req), default=1)
    C = math.isqrt(10 * S // 17)
    while 17 * (C + 1) * (C + 1) <= 10 * S:
        C += 1
    while C > 0 and 17 * C * C > 10 * S:
        C -= 1
    target = max(L, C)
    seed = max(L, math.isqrt(5 * S // 4))
    while 4 * seed * seed < 5 * S:
        seed += 1
    while seed > L and 4 * (seed - 1) * (seed - 1) >= 5 * S:
        seed -= 1
    req_set = set(req)
    forb_set = set(forb)

    if req:
        Nb = max(L, len(req))
        base = [(w + 'A' * Nb)[:Nb] for w in req] + ['A' * Nb] * (Nb - len(req))
    else:
        base = ['A']

    for f in forb:
        if any(f in w or f in w[::-1] for w in req):
            return base

    pw = []
    for w in sorted(set(req), key=lambda s: -len(s)):
        if any(w in u or w in u[::-1] for u, *_ in pw):
            continue
        rx_f = re.compile('(?=(' + ''.join('[' + ch + '.]' for ch in w) + '))')
        rv = w[::-1]
        rx_r = None if rv == w else re.compile(
            '(?=(' + ''.join('[' + ch + '.]' for ch in rv) + '))')
        pw.append((w, len(w), rx_f, rx_r))

    sd_cache = {}

    def attempt(n, limit):
        sd = sd_cache.get(n)
        if sd is None:
            sd = sd_cache[n] = _build_size(n, forb, L)
        g = _lns(sd, pw, rng, min(deadline, time.perf_counter() + limit), deadline)
        if g is None:
            return None
        for _ in range(3):
            h = g[:]
            if _fill(sd, h, rng, deadline):
                rows = [''.join(h[r * n:(r + 1) * n]) for r in range(n)]
                if _validate(rows, req_set, forb_set, L):
                    return rows
        return None

    if _validate(base, req_set, forb_set, L):
        inc, inc_n = base, len(base)
    else:
        inc, inc_n = None, float('inf')

    if target < min(seed, inc_n):
        found = attempt(target, 1.0)
        if found is not None:
            inc, inc_n = found, target

    n = seed
    while time.perf_counter() < deadline and n < inc_n:
        found = attempt(n, 0.7)
        if found is not None:
            inc, inc_n = found, n
            break
        n += max(1, n // 8)

    step = 1
    while time.perf_counter() < deadline and inc is not None and inc_n > target:
        tgt = max(target, inc_n - step)
        found = attempt(tgt, TIME_LIMIT if tgt == inc_n - 1 else 1.0)
        if found is not None:
            inc, inc_n = found, tgt
            step *= 2
        else:
            step = 1

    return inc if inc is not None else base


if __name__ == '__main__':
    fptr = open(os.environ['OUTPUT_PATH'], 'w')

    required_words_count = int(input().strip())
    required_words = []
    for _ in range(required_words_count):
        required_words.append(input())

    forbidden_words_count = int(input().strip())
    forbidden_words = []
    for _ in range(forbidden_words_count):
        forbidden_words.append(input())

    result = generate_grid(required_words, forbidden_words)

    fptr.write('\n'.join(' '.join(x) for x in result))
    fptr.write('\n')

    fptr.close()
