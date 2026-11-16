# Word Search Generation

## Problem statement

You are given two lists of words:

- **Required words** — every word in this list must appear somewhere in your grid, readable in a straight line in any of the 8 compass directions (horizontal, vertical, or diagonal; forwards or backwards).
- **Forbidden words** — none of these words may appear anywhere in your grid in any direction.

The grid wraps around at the edges (**torus topology**): a word may begin near one edge and continue from the opposite edge, in any of the 8 directions.

Your task is to produce the **smallest possible square grid** (side length `N`) that satisfies both constraints. All cells must be filled with uppercase letters `A`–`Z`.

### Illustrative grid

The following 6×6 toroidal grid illustrates wrap-around. The highlighted words in the original diagram are `PYTHON`, `JAVA`, `RUBY`, `PERL`, `RUST`, `SWIFT`, `SCALA`, and `LUA`.

```text
Q A T S U R
Y F L R U B
I L J A V A
U R E U C W
G E L L S S
Y P N O H T
```

## Function signature

```python
def generate_grid(
    required_words: list[str],
    forbidden_words: list[str]
) -> list[str]:
```

## Example

Required words:

```text
ACE
FIG
OAK
```

Forbidden words: none.

Output (one valid 3×3 grid):

```text
ACE
FIG
OAK
```

## Scoring

Each test case is scored by how densely your grid packs the required letters:

```text
S       = total number of letters in the required words
density = S / N²
score   = 100 × min(1, density / 1.7)
```

Here, `N` is your submitted grid size. Full marks need every cell to be used by two required words on average, so words must share letters heavily.

Example: `S = 500` letters in a 25×25 grid gives density `0.8` and score approximately `47.06`; the same words in a 20×20 grid give density `1.25` and score `73.53`.

An invalid grid scores `0`. A grid is invalid if it:

- Is missing a required word.
- Contains a forbidden word.
- Is not square.
- Contains non-letter cells.
- Has `N` smaller than the longest required word.
