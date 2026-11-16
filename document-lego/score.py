"""Exact scorer for Document Lego outputs.

score(pieces, truth, lines) -> float in [0, 1].
CLI: python3 score.py INPUT TRUTH OUTPUT
"""
import json
import sys
from collections import Counter, defaultdict


def _parse_piece(s):
    return s.replace('_', ' ').split('|')


def _parse_line(x):
    if isinstance(x, str):
        parts = x.split()
    else:
        parts = list(x)
    if len(parts) != 4:
        return None
    try:
        out = []
        for p in parts:
            if isinstance(p, bool):
                return None
            if isinstance(p, str):
                out.append(int(p))
            elif isinstance(p, int):
                out.append(p)
            else:
                return None
        return tuple(out)
    except ValueError:
        return None


def score(pieces, truth, lines):
    n = len(pieces)
    parsed = []
    for x in lines:
        t = _parse_line(x)
        if t is None or not (0 <= t[0] < n):
            return 0.0
        parsed.append(t)

    rows = [_parse_piece(s) for s in pieces]
    seen = set()
    rects = defaultdict(list)  # label -> [(r0, c0, r1, c1)]
    cells = defaultdict(list)  # label -> [(r, c, ch)]
    for pid, label, r, c in parsed:
        if pid in seen:
            continue
        h = len(rows[pid])
        w = max(len(x) for x in rows[pid])
        r1, c1 = r + h, c + w
        if any(r < b1 and r1 > b0 and c < d1 and c1 > d0
               for b0, d0, b1, d1 in rects[label]):
            continue
        seen.add(pid)
        rects[label].append((r, c, r1, c1))
        for dr, row in enumerate(rows[pid]):
            for dc, ch in enumerate(row):
                if ch != ' ':
                    cells[label].append((r + dr, c + dc, ch))

    pages = truth['pages']
    P = len(pages)
    total = 0
    index = []
    for pg in pages:
        idx = defaultdict(list)
        for r, line in enumerate(pg['lines']):
            for c, ch in enumerate(line):
                if ch != ' ':
                    idx[ch].append((r, c))
                    total += 1
        index.append(idx)
    if total == 0:
        return 0.0

    labels = list(cells)
    count = {}  # (label, page) -> int
    for L in labels:
        for p in range(P):
            votes = Counter()
            idx = index[p]
            for r, c, ch in cells[L]:
                for pr, pc in idx.get(ch, ()):
                    votes[(pr - r, pc - c)] += 1
            count[L, p] = max(votes.values()) if votes else 0

    cand = set()
    for p in range(P):
        top = sorted(labels, key=lambda L: -count[L, p])[:P]
        cand.update(L for L in top if count[L, p] > 0)
    cand = sorted(cand)
    best = [0] * (1 << P)
    for L in cand:
        new = best[:]
        for mask in range(1 << P):
            for p in range(P):
                if not mask >> p & 1:
                    v = best[mask] + count[L, p]
                    if v > new[mask | 1 << p]:
                        new[mask | 1 << p] = v
        best = new
    return max(best) / total


def main(argv):
    pieces = open(argv[1]).read().split('\n')
    n = int(pieces[0])
    pieces = pieces[1:n + 1]
    truth = json.load(open(argv[2]))
    lines = [l for l in open(argv[3]).read().split('\n') if l.strip()]
    print('%.4f' % (100 * score(pieces, truth, lines)))


if __name__ == '__main__':
    main(sys.argv)
