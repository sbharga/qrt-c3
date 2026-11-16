"""Document Lego instance generator (mimics the official one).

generate(seed, n_pages=None, hmax=3, wmin=3, wmax=7, extra=None) -> (pieces, truth)
truth = {"pages": [{"W", "H", "lines"}], "pieces": [[page, row, col], ...]}
"""
import argparse
import json
import os
import random
import re
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = ('https://raw.githubusercontent.com/pytorch/examples/main/'
        'word_language_model/data/wikitext-2/')
# test + valid splits only; the solver lexicon is built from the train split
CORPORA = [(os.path.join(HERE, 'data', 'wikitext2_%s.txt' % n), BASE + n + '.txt')
           for n in ('test', 'valid')]
MAX_UNK = 10

_paras = None


def _detok(s):
    s = re.sub(r' +', ' ', s)
    s = s.replace(' @-@ ', '-').replace(' @,@ ', ',').replace(' @.@ ', '.')
    s = re.sub(r" (?=[,.;:!?)]|'s\b|n't\b)", '', s)
    s = s.replace('( ', '(')
    return re.sub(r' +', ' ', s).strip()


def paragraphs():
    global _paras
    if _paras is None:
        out = []
        for path, url in CORPORA:
            if not os.path.exists(path):
                os.makedirs(os.path.dirname(path), exist_ok=True)
                urllib.request.urlretrieve(url, path)
            with open(path, encoding='utf-8') as f:
                lines = f.readlines()
            for line in lines:
                if line.startswith(' =') or len(line.strip()) < 600:
                    continue
                if line.count('<unk>') > MAX_UNK or '_' in line or '|' in line \
                        or not line.isascii():
                    continue
                out.append(_detok(line.replace('<unk>', '')))
        _paras = out
    return _paras


def wrap(words, W, H):
    """Greedy wrap with hyphenation; returns first H lines (unpadded)."""
    lines = []
    cur = ''
    for word in words:
        while word:
            if cur == '':
                if len(word) <= W:
                    cur = word
                    word = ''
                else:
                    lines.append(word[:W])
                    word = word[W:]
            elif len(cur) + 1 + len(word) <= W:
                cur += ' ' + word
                word = ''
            else:
                room = W - len(cur) - 1
                if room >= 3:
                    k = min(room - 1, len(word) - 2)
                    if k >= 2:
                        cur += ' ' + word[:k] + '-'
                        word = word[k:]
                lines.append(cur)
                cur = ''
        if len(lines) >= H:
            return lines[:H]
    if cur:
        lines.append(cur)
    return lines[:H]


def make_page(rng, wlim=(40, 60), hlim=(10, 14)):
    paras = paragraphs()
    W = rng.randint(*wlim)
    H = rng.randint(*hlim)
    i = rng.randrange(len(paras))
    words = []
    while True:
        words.extend(paras[i % len(paras)].split())
        lines = wrap(words, W, H)
        if len(lines) >= H:
            break
        i += 1
    return {'W': W, 'H': H, 'lines': [l.ljust(W) for l in lines]}


def tile(page, rng, hmax, wmin, wmax):
    """Returns [(r, c, h, w)] tiling the page."""
    W, H = page['W'], page['H']
    cov = [[False] * W for _ in range(H)]
    out = []
    for r in range(H):
        for c in range(W):
            if cov[r][c]:
                continue
            R = 0
            while c + R < W and not cov[r][c + R]:
                R += 1
            if R < wmin:
                w = R
            else:
                hi = min(wmax, R)
                ws = [x for x in range(wmin, hi + 1) if R - x == 0 or R - x >= wmin]
                w = rng.choice(ws) if ws else hi
            maxh = 1
            while (maxh < hmax and r + maxh < H
                   and not any(cov[r + maxh][c:c + w])):
                maxh += 1
            h = rng.randint(1, maxh)
            for rr in range(r, r + h):
                for cc in range(c, c + w):
                    cov[rr][cc] = True
            out.append((r, c, h, w))
    return out


def cut(page, r, c, h, w):
    return [page['lines'][r + i][c:c + w] for i in range(h)]


def generate(seed, n_pages=None, hmax=3, wmin=3, wmax=7, extra=None,
             wlim=(40, 60), hlim=(10, 14), plim=(3, 6)):
    rng = random.Random(seed)
    if n_pages is None:
        n_pages = rng.randint(*plim)
    pages = [make_page(rng, wlim, hlim) for _ in range(n_pages)]
    items = []  # (rows, [page, r, c])
    for p, pg in enumerate(pages):
        for r, c, h, w in tile(pg, rng, hmax, wmin, wmax):
            rows = cut(pg, r, c, h, w)
            if any(x.strip() for x in rows):
                items.append((rows, [p, r, c]))
    if extra is None:
        extra = rng.randint(1, 5)
    xp = make_page(rng, wlim, hlim)
    xs = [cut(xp, r, c, h, w) for r, c, h, w in tile(xp, rng, hmax, wmin, wmax)]
    xs = [rows for rows in xs if any(x.strip() for x in rows)]
    rng.shuffle(xs)
    for rows in xs[:extra]:
        items.append((rows, [-1, 0, 0]))
    rng.shuffle(items)
    pieces = ['|'.join(rows).replace(' ', '_') for rows, _ in items]
    truth = {'pages': pages, 'pieces': [t for _, t in items]}
    return pieces, truth


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, required=True)
    ap.add_argument('--pages', type=int)
    ap.add_argument('--hmax', type=int, default=3)
    ap.add_argument('--wmin', type=int, default=3)
    ap.add_argument('--wmax', type=int, default=7)
    ap.add_argument('--out-dir', required=True)
    a = ap.parse_args()
    pieces, truth = generate(a.seed, a.pages, a.hmax, a.wmin, a.wmax)
    os.makedirs(a.out_dir, exist_ok=True)
    with open(os.path.join(a.out_dir, 'in_%d.txt' % a.seed), 'w') as f:
        f.write('%d\n' % len(pieces) + '\n'.join(pieces) + '\n')
    with open(os.path.join(a.out_dir, 'truth_%d.json' % a.seed), 'w') as f:
        json.dump(truth, f)


if __name__ == '__main__':
    main()
