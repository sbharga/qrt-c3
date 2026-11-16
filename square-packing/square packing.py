
#!/bin/python3
import math
import os
import random
import sys
import time


def pack_squares(squares):
    n = len(squares)
    if n == 0:
        return []

    start = time.monotonic()
    deadline = start + 1.35

    g = 0
    for s in squares:
        g = math.gcd(g, s)

    a = [s // g for s in squares]
    m = max(a)
    S = sum(s * s for s in a)

    if len(set(a)) == 1:
        cols = math.isqrt(n)
        if cols * cols < n:
            cols += 1
        return [
            [(i // cols) * squares[0],
             (i % cols) * squares[0]]
            for i in range(n)
        ]

    # Start with a guaranteed valid packing.
    best = []
    x = 0
    for s in a:
        best.append((x, 0))
        x += s

    best_area = m * x
    best_width = m

    def submit(p):
        nonlocal best, best_area, best_width

        if p is None:
            return

        w = max(
            y + a[i] for i, (x, y) in enumerate(p)
        )
        h = max(
            x + a[i] for i, (x, y) in enumerate(p)
        )

        area = w * h

        if area < best_area:
            best_area = area
            best = p
            best_width = min(w, h)

    order = sorted(range(n), key=lambda i: -a[i])

    # Fast shelf-based packing.
    def shelf_pack(W, ordering, mode):
        shelves = []
        height = 0
        p = [None] * n

        for i in ordering:
            s = a[i]
            chosen = None

            for j, (top, sh, used) in enumerate(shelves):
                if s <= sh and used + s <= W:
                    remain = W - used - s

                    if mode == 0:
                        key = (remain, sh - s, j)
                    else:
                        key = (j, remain)

                    if chosen is None or key < chosen[0]:
                        chosen = (key, j)

            if chosen is not None:
                j = chosen[1]
                top, sh, used = shelves[j]

                p[i] = (top, used)
                shelves[j] = (top, sh, used + s)

            else:
                p[i] = (height, 0)
                shelves.append((height, s, s))
                height += s

        return p

    # MaxRects packing for tighter configurations.
    def maxrect(W, H, ordering, mode, look):
        free = [(0, 0, W, H)]
        p = [None] * n
        remaining = ordering[:]

        for step in range(n):
            if step % 16 == 0:
                if time.monotonic() >= deadline:
                    return None

            if not free:
                return None

            choices = []
            seen_sizes = set()

            for j, i in enumerate(remaining):
                if a[i] not in seen_sizes:
                    choices.append(j)
                    seen_sizes.add(a[i])

                if len(choices) >= look:
                    break

            chosen = None

            for j in choices:
                s = a[remaining[j]]

                for fx, fy, fw, fh in free:
                    if fw < s or fh < s:
                        continue

                    dx = fw - s
                    dy = fh - s
                    waste = fw * fh - s * s

                    if mode == 0:
                        key = (
                            min(dx, dy), max(dx, dy),
                            waste, -s, fx + fy
                        )
                    elif mode == 1:
                        key = (
                            waste, min(dx, dy),
                            max(dx, dy), -s, fx + fy
                        )
                    elif mode == 2:
                        key = (
                            max(dx, dy), min(dx, dy),
                            waste, -s, fx + fy
                        )
                    elif mode == 3:
                        key = (
                            max(fx + s, fy + s),
                            waste, -s
                        )
                    elif mode == 4:
                        key = (
                            fx + s, fy + s, waste, -s
                        )
                    else:
                        key = (
                            fy + s, fx + s, waste, -s
                        )

                    if chosen is None or key < chosen[0]:
                        chosen = (key, j, fx, fy)

            if chosen is None:
                return None

            _, j, x, y = chosen
            i = remaining.pop(j)
            s = a[i]
            p[i] = (x, y)

            if not remaining:
                return p

            smallest = min(a[i] for i in remaining)
            updated = []

            for fx, fy, fw, fh in free:
                if (
                    x >= fx + fw or
                    x + s <= fx or
                    y >= fy + fh or
                    y + s <= fy
                ):
                    updated.append((fx, fy, fw, fh))
                    continue

                if x > fx:
                    updated.append(
                        (fx, fy, x - fx, fh)
                    )

                if x + s < fx + fw:
                    updated.append(
                        (x + s, fy, fx + fw - x - s, fh)
                    )

                if y > fy:
                    updated.append(
                        (fx, fy, fw, y - fy)
                    )

                if y + s < fy + fh:
                    updated.append(
                        (fx, y + s, fw, fy + fh - y - s)
                    )

            updated = [
                r for r in updated
                if r[2] >= smallest and r[3] >= smallest
            ]

            # Eliminate contained free rectangles.
            keep = [True] * len(updated)

            for u, (x1, y1, w1, h1) in enumerate(updated):
                if not keep[u]:
                    continue

                for v in range(u + 1, len(updated)):
                    if not keep[v]:
                        continue

                    x2, y2, w2, h2 = updated[v]

                    if (
                        x1 >= x2 and y1 >= y2 and
                        x1 + w1 <= x2 + w2 and
                        y1 + h1 <= y2 + h2
                    ):
                        keep[u] = False
                        break

                    if (
                        x2 >= x1 and y2 >= y1 and
                        x2 + w2 <= x1 + w1 and
                        y2 + h2 <= y1 + h1
                    ):
                        keep[v] = False

            free = [
                r for k, r in enumerate(updated)
                if keep[k]
            ]

        return p

    # Construct promising bounding widths.
    root = math.isqrt(best_area)
    widths = {m, root, math.isqrt(S)}

    width_count = max(14, min(52, 1200 // n))

    if root - m <= 180:
        widths.update(range(m, root + 1))
    else:
        for j in range(width_count):
            widths.add(
                m + (root - m) * j // (width_count - 1)
            )

    v = 0
    largest = sorted(a, reverse=True)

    for s in largest[:24]:
        v += s
        widths.update((v - 1, v, v + 1))

    large = largest[:10]

    for i in range(len(large)):
        for j in range(i + 1, len(large)):
            v = large[i] + large[j]
            widths.update((v - 1, v, v + 1))

    widths = [
        w for w in widths if m <= w <= root
    ]

    widths.sort(
        key=lambda w: (
            w * max(m, (S + w - 1) // w) - S,
            abs(w - math.isqrt(S))
        )
    )

    if n > 1000:
        widths = widths[:7]

    # Provable lower bound.
    lower = S

    if root - m < 10000:
        lower = min(
            w * max(m, (S + w - 1) // w)
            for w in range(m, root + 1)
        )

    # Phase 1: fast deterministic packing.
    for W in widths:
        if time.monotonic() >= deadline:
            break

        submit(shelf_pack(W, order, 0))

        if n <= 150:
            submit(shelf_pack(W, order, 1))

        if best_area == lower:
            break

    # Phase 2: tighter MaxRects packing.
    if n <= 70 and best_area > lower:
        rules = [
            (0, 1), (1, 1), (2, 1),
            (3, 1), (0, 5), (1, 5), (4, 5)
        ]

        for W in widths:
            if (
                time.monotonic() >= deadline or
                best_area == lower
            ):
                break

            Hmax = (best_area - 1) // W
            Hmin = max(m, (S + W - 1) // W)

            if Hmax < Hmin:
                continue

            for mode, look in rules:
                if (
                    time.monotonic() >= deadline or
                    best_area == lower
                ):
                    break

                for pct in (104, 115, 1000):
                    if pct == 1000:
                        H = Hmax
                    else:
                        H = min(
                            Hmax,
                            max(Hmin, (Hmin * pct + 99) // 100)
                        )

                    submit(
                        maxrect(W, H, order, mode, look)
                    )

                    if (
                        time.monotonic() >= deadline or
                        best_area == lower
                    ):
                        break

    # Phase 3: randomized improvement.
    rng = random.Random(
        sum((i + 1) * s for i, s in enumerate(a))
    )

    attempts = 0

    while (
        time.monotonic() < deadline and
        best_area > lower and n <= 70
    ):
        attempts += 1

        if attempts % 3 == 0:
            W = rng.choice(widths)
        else:
            d = max(1, best_width // 6)
            W = max(
                m, best_width + rng.randint(-d, d)
            )

        if W * W >= best_area:
            continue

        Hmax = (best_area - 1) // W
        Hmin = max(m, (S + W - 1) // W)

        if Hmin > Hmax:
            continue

        pct = rng.choice((102, 106, 112, 125, 1000))

        H = min(
            Hmax,
            max(Hmin, (Hmin * pct + 99) // 100)
        )

        if attempts % 4 == 0:
            ordering = order
        else:
            ordering = sorted(
                range(n),
                key=lambda i:
                -a[i] * rng.randint(75, 125)
            )

        submit(
            maxrect(
                W, H, ordering,
                rng.randrange(6),
                rng.choice((1, 2, 4, 8))
            )
        )

    return [[x * g, y * g] for x, y in best]


if __name__ == '__main__':
    data = list(map(int, sys.stdin.buffer.read().split()))

    if data:
        squares_count = data[0]
        squares = data[1:1 + squares_count]

        result = pack_squares(squares)

        output = '\n'.join(
            f'{x} {y}' for x, y in result
        ) + '\n'

        path = os.environ.get('OUTPUT_PATH')

        if path:
            with open(path, 'w') as fptr:
                fptr.write(output)
        else:
            sys.stdout.write(output)
