"""Complete Python 3 submission. Replace the editor contents with this file."""

import sys
import time
from collections import deque


def solve(grid):
    started = time.perf_counter()
    hard_deadline = started + 8.5
    deadline = hard_deadline
    rows, cols = len(grid), len(grid[0])
    size = rows * cols
    sys.setrecursionlimit(max(sys.getrecursionlimit(), size * 3 + 1000))

    # Direction bits are N, E, S, W. Domain bits select these seven shapes.
    shapes = (0, 10, 5, 3, 9, 6, 12)
    symbols = ".-|LJF7"
    straight = (1 << 1) | (1 << 2)
    corners = sum(1 << k for k in range(3, 7))
    cells = "".join(grid)
    pearls = [i for i, cell in enumerate(cells) if cell != "."]
    coordinates = [divmod(i, cols) for i in range(size)]
    neighbours = []
    for r, c in coordinates:
        neighbours.append((
            (r - 1) * cols + c if r else -1,
            r * cols + c + 1 if c + 1 < cols else -1,
            (r + 1) * cols + c if r + 1 < rows else -1,
            r * cols + c - 1 if c else -1,
        ))

    options = [[k for k in range(7) if domain & (1 << k)]
               for domain in range(128)]
    possible = [0] * 128
    forced = [0] * 128
    for domain in range(1, 128):
        all_edges = 15
        for k in options[domain]:
            possible[domain] |= shapes[k]
            all_edges &= shapes[k]
        forced[domain] = all_edges

    edge_domains = [sum(1 << k for k in range(7)
                        if shapes[k] & (1 << direction))
                    for direction in range(4)]

    # Compatibility tables enforce matching edges and the black-pearl rule.
    support = {}
    for black_here in (False, True):
        for black_there in (False, True):
            for direction in range(4):
                edge, opposite = 1 << direction, 1 << ((direction + 2) % 4)
                axial_shape = 5 if direction % 2 == 0 else 10
                single = []
                for a in shapes:
                    allowed = 0
                    for k, b in enumerate(shapes):
                        connected = bool(a & edge)
                        if connected != bool(b & opposite):
                            continue
                        if connected and black_here and b != axial_shape:
                            continue
                        if connected and black_there and a != axial_shape:
                            continue
                        allowed |= 1 << k
                    single.append(allowed)
                table = [0] * 128
                for domain in range(1, 128):
                    for k in options[domain]:
                        table[domain] |= single[k]
                support[black_here, black_there, direction] = table

    arcs = [[] for _ in range(size)]
    white_watchers = [[] for _ in range(size)]
    domains = [127] * size
    for i in range(size):
        if cells[i] == "W":
            domains[i] = straight
        elif cells[i] == "B":
            domains[i] = corners
        for direction, j in enumerate(neighbours[i]):
            if j < 0:
                domains[i] &= 127 ^ edge_domains[direction]
            else:
                arcs[i].append((j, support[cells[i] == "B",
                                           cells[j] == "B", direction]))
                if cells[j] == "W":
                    white_watchers[i].append(j)
        if cells[i] == "W":
            white_watchers[i].append(i)

    class SearchExpired(Exception):
        pass

    activity = [1] * size
    best = None
    best_length = size + 1
    pearl_rows = [coordinates[i][0] for i in pearls]
    pearl_cols = [coordinates[i][1] for i in pearls]
    geometric_bound = max(4, 2 * (max(pearl_rows) - min(pearl_rows)
                                  + max(pearl_cols) - min(pearl_cols)))

    def propagate(state, seeds, local_only=False, connectivity=True):
        queue = deque(seeds)
        queued = bytearray(size)
        for i in queue:
            queued[i] = 1

        def restrict(i, allowed):
            reduced = state[i] & allowed
            if not reduced:
                activity[i] += 1
                return False
            if reduced != state[i]:
                state[i] = reduced
                if not queued[i]:
                    queued[i] = 1
                    queue.append(i)
            return True

        while True:
            while queue:
                i = queue.popleft()
                queued[i] = 0
                if not state[i]:
                    return None
                for j, table in arcs[i]:
                    if not restrict(j, table[state[i]]):
                        return None
                for white in white_watchers[i]:
                    for shape_index, first, second in ((1, 1, 3), (2, 0, 2)):
                        bit = 1 << shape_index
                        if not state[white] & bit:
                            continue
                        a, b = neighbours[white][first], neighbours[white][second]
                        if a < 0 or b < 0:
                            if not restrict(white, 127 ^ bit):
                                return None
                            continue
                        turn_a = state[a] & corners & edge_domains[(first + 2) % 4]
                        turn_b = state[b] & corners & edge_domains[(second + 2) % 4]
                        if not turn_a and not turn_b:
                            if not restrict(white, 127 ^ bit):
                                return None
                        else:
                            if not turn_a and not restrict(b, 127 ^ bit):
                                return None
                            if not turn_b and not restrict(a, 127 ^ bit):
                                return None

            if time.perf_counter() >= deadline:
                raise SearchExpired
            if local_only:
                return state

            required = [i for i, domain in enumerate(state) if not domain & 1]
            if len(required) >= best_length:
                return None
            parent = list(range(size))
            component_size = [1] * size

            def root(i):
                while i != parent[i]:
                    parent[i] = parent[parent[i]]
                    i = parent[i]
                return i

            fixed = [forced[domain] for domain in state]
            cycle_root = -1
            for i in required:
                for direction in (1, 2):
                    if not fixed[i] & (1 << direction):
                        continue
                    j = neighbours[i][direction]
                    a, b = root(i), root(j)
                    if a == b:
                        cycle_root = a
                    else:
                        if component_size[a] < component_size[b]:
                            a, b = b, a
                        parent[b] = a
                        component_size[a] += component_size[b]
            roots = parent
            for i in required:
                roots[i] = root(i)

            if cycle_root >= 0:
                cycle_root = root(cycle_root)
                if any(roots[i] != cycle_root for i in required):
                    return None
                # A completed cycle fixes every remaining cell to empty.
                for i in range(size):
                    if roots[i] != cycle_root and not restrict(i, 1):
                        return None
                if queue:
                    continue
                return state, roots, required, True

            # A candidate shape may not close a component prematurely.
            required_count = len(required)
            cycle_candidates = {j for i in required if fixed[i].bit_count() == 1
                                for j in neighbours[i] if j >= 0}
            for i in cycle_candidates:
                domain = state[i]
                if domain & (domain - 1) == 0:
                    continue
                allowed = domain
                for k in options[domain]:
                    if k == 0:
                        continue
                    ends = [neighbours[i][d] for d in range(4)
                            if shapes[k] & (1 << d)]
                    a, b = ends
                    component = roots[a]
                    if component != roots[b]:
                        continue
                    covered = component_size[component]
                    if roots[i] != component and not domain & 1:
                        covered += 1
                    if covered < required_count:
                        allowed &= ~(1 << k)
                if not restrict(i, allowed):
                    return None
            if queue:
                continue
            if not connectivity:
                return state, roots, required, False

            # A simple loop cannot cross a bridge or occupy both sides of
            # an articulation point. Iterative Tarjan DFS avoids deep recursion.
            discovery = [-1] * size
            low = [0] * size
            subtree_required = [0] * size
            dfs_parent = [-1] * size
            order = [pearls[0]]
            discovery[pearls[0]] = 0
            subtree_required[pearls[0]] = 1
            stack = [(pearls[0], 0)]
            excluded = [0] * (size + 1)
            bridges = []
            while stack:
                i, direction = stack[-1]
                if direction < 4:
                    stack[-1] = (i, direction + 1)
                    if not possible[state[i]] & (1 << direction):
                        continue
                    j = neighbours[i][direction]
                    if discovery[j] < 0:
                        dfs_parent[j] = i
                        discovery[j] = low[j] = len(order)
                        subtree_required[j] = int(not state[j] & 1)
                        order.append(j)
                        stack.append((j, 0))
                    elif j != dfs_parent[i]:
                        low[i] = min(low[i], discovery[j])
                    continue
                stack.pop()
                p = dfs_parent[i]
                if p < 0:
                    continue
                low[p] = min(low[p], low[i])
                subtree_required[p] += subtree_required[i]
                if low[i] < discovery[p]:
                    continue
                inside = subtree_required[i]
                outside = required_count - inside - int(not state[p] & 1)
                if inside and outside:
                    activity[p] += 1
                    activity[i] += 1
                    return None
                begin, end = discovery[i], len(order)
                if not inside:
                    excluded[begin] += 1
                    excluded[end] -= 1
                elif not outside:
                    excluded[0] += 1
                    excluded[begin] -= 1
                    excluded[end] += 1
                    excluded[size] -= 1
                    excluded[discovery[p]] -= 1
                    excluded[discovery[p] + 1] += 1
                if low[i] > discovery[p]:
                    direction = neighbours[p].index(i)
                    bridges.append((p, direction))
            if any(discovery[i] < 0 for i in required):
                return None
            for p, direction in bridges:
                if not restrict(p, 127 ^ edge_domains[direction]):
                    return None
            count = 0
            for index, i in enumerate(order):
                count += excluded[index]
                if count and not restrict(i, 1):
                    return None
            for i in range(size):
                if discovery[i] < 0 and not restrict(i, 1):
                    return None
            if queue:
                continue
            return state, roots, required, False

    def search(state, seeds, depth=0):
        nonlocal best, best_length, deadline
        result = propagate(state, seeds, connectivity=size < 200 or depth % 4 == 0)
        if result is None:
            if len(seeds) == 1:
                activity[seeds[0]] += 1
            return
        state, roots, required, complete = result
        if complete:
            if best is None:
                deadline = min(deadline, max(started + 0.9, time.perf_counter() + 0.15))
            best = state[:]
            best_length = len(required)
            return

        fixed = [forced[domain] for domain in state]
        endpoints = []
        for i in required:
            missing = 2 - fixed[i].bit_count()
            endpoints.extend([i] * missing)

        # Every open end needs a connection. Half the sum is a lower bound
        # on the number of additional cells, even if connections share cells.
        if best is not None and len(endpoints) <= 80:
            multiple = len({roots[i] for i in required}) > 1
            distance_sum = 0
            for i in endpoints:
                r, c = coordinates[i]
                distances = [abs(r - coordinates[j][0]) + abs(c - coordinates[j][1])
                             for j in endpoints if j != i
                             and (not multiple or roots[j] != roots[i])]
                if not distances:
                    return
                distance_sum += max(0, min(distances) - 1)
            lower_bound = max(geometric_bound,
                              len(required) + (distance_sum + 1) // 2)
            if lower_bound >= best_length:
                return

        candidates = [i for i in required if state[i].bit_count() > 1]
        if not candidates:
            return
        chosen = min(candidates, key=lambda i: (
            (state[i].bit_count() - 1) /
            (activity[i] + sum(activity[j] for j in neighbours[i] if j >= 0)),
            -fixed[i].bit_count(),
            -sum(cells[j] != "." for j in neighbours[i] if j >= 0), i))
        targets = list({i for i in endpoints if roots[i] != roots[chosen]})
        if not targets:
            targets = list({i for i in endpoints if i != chosen})

        def priority(k):
            cost = 0
            for direction in range(4):
                if not shapes[k] & (1 << direction) or fixed[chosen] & (1 << direction):
                    continue
                j = neighbours[chosen][direction]
                r, c = coordinates[j]
                if targets:
                    cost += min(abs(r - coordinates[t][0]) + abs(c - coordinates[t][1])
                                for t in targets)
                cost += bool(state[j] & 1) * 0.25
            return cost

        for k in sorted(options[state[chosen]], key=priority):
            if time.perf_counter() >= deadline:
                raise SearchExpired
            child = state[:]
            child[chosen] = 1 << k
            search(child, [chosen], depth + 1)
            if best_length == geometric_bound:
                return

    try:
        initial = propagate(domains, range(size))
        if initial is not None:
            domains = initial[0]
            probe_limit = min(deadline, started + 0.7)
            changed = True
            while changed and time.perf_counter() < probe_limit:
                changed = False
                for i in pearls:
                    if time.perf_counter() >= probe_limit:
                        break
                    if domains[i].bit_count() != 2:
                        continue
                    branches = []
                    for k in options[domains[i]]:
                        child = domains[:]
                        child[i] = 1 << k
                        child = propagate(child, [i], local_only=True)
                        if child is not None:
                            branches.append(child)
                    if not branches:
                        raise RuntimeError("The puzzle constraints are inconsistent")
                    deduced = False
                    if len(branches) == 1:
                        domains = branches[0]
                        deduced = True
                    else:
                        merged = [a | b for a, b in zip(*branches)]
                        if merged != domains:
                            domains = merged
                            deduced = True
                    if deduced:
                        changed = True
                        reduced = propagate(domains, range(size))
                        if reduced is None:
                            raise RuntimeError("The puzzle constraints are inconsistent")
                        domains = reduced[0]
            # Restart with the accumulated conflict activity when a search
            # stalls. The complete task still has one shared time budget.
            for slice_seconds in (3.0, 2.5, 3.0):
                deadline = min(hard_deadline, time.perf_counter() + slice_seconds)
                try:
                    search(domains[:], range(size))
                    break
                except SearchExpired:
                    if best is not None or time.perf_counter() >= hard_deadline:
                        break
    except SearchExpired:
        pass
    if best is None:
        raise RuntimeError("No valid loop found within the search budget")
    answer = "".join(symbols[domain.bit_length() - 1] for domain in best)
    return [answer[r * cols:(r + 1) * cols] for r in range(rows)]


if __name__ == "__main__":
    data = sys.stdin.read().split()
    row_count = int(data[0])
    print("\n".join(solve(data[1:row_count + 1])))
