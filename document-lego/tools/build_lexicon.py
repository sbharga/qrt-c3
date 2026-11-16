"""Build the embedded word-frequency blob and write it into solution.py."""
import base64
import collections
import math
import os
import re
import urllib.request
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAIN = os.path.join(ROOT, 'data', 'wikitext2_train.txt')
URL = ('https://raw.githubusercontent.com/pytorch/examples/main/'
       'word_language_model/data/wikitext-2/train.txt')
SOLUTION = os.path.join(ROOT, 'solution.py')
CAP = 40000


def blob_for(counts, k):
    top = counts.most_common(k)
    mx = top[0][1]
    classes = collections.defaultdict(list)
    for w, n in top:
        classes[min(15, int(math.floor(math.log2(mx / n))))].append(w)
    text = '\n'.join('%d %s' % (c, ' '.join(sorted(ws)))
                     for c, ws in sorted(classes.items()))
    return base64.b64encode(zlib.compress(text.encode(), 9)).decode()


def main():
    if not os.path.exists(TRAIN):
        os.makedirs(os.path.dirname(TRAIN), exist_ok=True)
        urllib.request.urlretrieve(URL, TRAIN)
    with open(TRAIN, encoding='utf-8') as f:
        counts = collections.Counter(t for t in f.read().lower().split()
                                     if re.fullmatch(r'[a-z]+', t))
    for k in range(20000, 4999, -1000):
        blob = blob_for(counts, k)
        if len(blob) <= CAP:
            break
    with open(SOLUTION) as f:
        src = f.read()
    new, n = re.subn(r'(# BEGIN LEXICON\n).*?(\n# END LEXICON)',
                     lambda m: m.group(1) + 'LEXICON = "%s"' % blob + m.group(2),
                     src, count=1, flags=re.S)
    assert n == 1, 'markers not found'
    with open(SOLUTION, 'w') as f:
        f.write(new)
    print('K=%d blob=%d' % (k, len(blob)))


if __name__ == '__main__':
    main()
