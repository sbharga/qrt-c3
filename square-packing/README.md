# Square Packing++

You are given a list of positive integers `[a₀, a₁, ..., aₙ]`, where each integer represents the side length of a square. Your task is to arrange these squares on a two-dimensional grid such that:

1. No two squares overlap.
2. All square corners have integer coordinates.
3. All sides are parallel to the X and Y axes.
4. The bounding rectangle that contains all squares and has horizontal and vertical sides has the smallest possible area.

The coordinate system is defined as follows:

- The X-axis increases downward.
- The Y-axis increases to the right.

Your program should output a list of tuples `[(X₀, Y₀), ..., (Xₙ, Yₙ)]`, where each tuple represents the coordinates of the top-left corner of the square with side length `aᵢ`.

## Examples

```text
1. input:  [1]
   output: [(0, 0)]

2. input:  [1, 2]
   output: [(0, 2), (0, 0)]

3. input:  [1, 2, 3]
   output: [(2, 3), (0, 3), (0, 0)]

4. input:  [1, 2, 3, 4]
   output: [(3, 4), (3, 5), (0, 4), (0, 0)]
```

## Goal

Implement an algorithm that:

- Generates valid coordinates for all squares satisfying the constraints.
- Minimizes the total area of the bounding rectangle.
- Returns the coordinates in the same order as the input list.

## Scoring

After submitting, the checker returns a message like:

```text
Valid packing. BoundingArea=1260,
LowerBound=1200, Ratio=0.9524, Score=0.3769
```

**BoundingArea `A`** is the area of the smallest axis-aligned rectangle that encloses all your squares.

**LowerBound `L`** is a provable lower bound on the bounding area of any valid packing. With `m` the largest side and `S` the sum of the squared sides:

```text
L = min over integers W ≥ m of W × max(m, ⌈S / W⌉)
```

**Score** is between 0 and 1 for each test case:

```text
Score = (L / A) ^ 20
```

- A score of 1 means `A = L`, which proves your packing is optimal.
- The true optimum can be above `L`, in which case nobody can reach 1 on that test case; the test cases are chosen so that `L` is close to achievable.
- An invalid packing—overlapping squares, non-integer coordinates, or the wrong number of lines—scores 0.

Your total is the sum over the hidden test cases; the sample test cases are not scored.

## Tips

- Squares may be placed in any order, not necessarily by size.
- The optimal bounding rectangle is often not unique in shape, but its area is.
- Test your non-overlap check carefully; off-by-one errors are common.

## Running

`solution.py` reads `n` followed by the `n` side lengths from stdin, and prints one `X Y` line per square (written to `$OUTPUT_PATH` if set).

```bash
printf '4\n1\n2\n3\n4\n' | python solution.py
```
