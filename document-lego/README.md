# Bonus: Document Lego

**Optional bonus question:** Its points count towards your team's final total only if your team scores at least 70% of the maximum on **each** of the four main questions. If any one main-question score is below 70%, this bonus contributes 0 points.

Sample test cases carry no points. They are excluded from both your score and the maximum points used to determine bonus eligibility.

You may attempt the bonus at any time. Eligibility is checked at the end of the competition using final scores; the exact thresholds are listed in the Scoring section below.

A few pages of English text have been cut into small rectangular pieces, like Lego bricks, and the pieces have been mixed together. A few extra pieces from another document are mixed in too. Put the pages back together.

## How the pages were made

- Each page is one document, word-wrapped to its own width `W` (between 40 and 60 characters), with words broken at a line end hyphenated, and padded with spaces on the right. Each page has its own height, between 10 and 14 rows.
- Each page was cut into non-overlapping rectangles of various sizes. Pieces are not rotated. Pieces made only of spaces were thrown away.
- You are not told how many pages there are, or how wide or tall each one is.

## Input

The first line holds `N`, the number of pieces. Then `N` lines follow, one per piece (piece IDs `0` to `N-1`, in order).

Each piece is written as its rows separated by `|`, with spaces written as `_` (underscore). For example, `The_|sat_` is a piece 2 rows tall and 4 columns wide.

## Output

One line per piece you place:

```text
piece page row col
```

- `piece`: the piece ID.
- `page`: any integer label; pieces with the same label are on the same page. Labels are just names: their values and the order of your pages don't matter.
- `row`, `col`: the position of the piece's top-left character on that page. Positions within a page do matter: they must put each piece in the right place relative to the other pieces on that page.

Lines can be in any order, except that if two pieces overlap, or a piece is listed twice, the later line is ignored. Pieces you don't list are treated as extra pieces from the other document. A line that is not four integers, or names an unknown piece ID, makes the whole output score 0.

## Example

This small example has two pages (5 rows by 26 columns, and 4 by 24) and one extra piece from a third text: 34 pieces in all. The real test case is much bigger. See `samples/sample.txt` and `samples/sample_truth.json`.

## Scoring

### Bonus eligibility

All four of these thresholds must be met for your bonus points to count:

- Square Packing++: at least **700 / 1000**.
- Word Search Generation: at least **756 / 1080**.
- Black-box: at least **714 / 1020**.
- Masyu: at least **700 / 1000**.

Each threshold applies to the total for that main question across its scored test cases. A 70% average across the four questions is not sufficient. If any threshold is missed, the bonus contributes 0 points to your team's final total, regardless of your reconstruction score.

HackerRank may display a bonus score and include it in your displayed total before eligibility is checked. Those totals are provisional; the eligibility rule above is applied when the final competition results are calculated.

### Reconstruction score

Your reconstruction score is the percentage of the pages' non-space characters that you put in the right place. For an eligible team, bonus points equal that percentage of this question's maximum points.

- Your pages are matched one-to-one to the real pages in whichever way gives the highest score. Each real page counts at most one of your pages, so a page split across two labels only scores its better part.
- Each of your pages may be shifted as a whole to fit its real page, so a correct page scores fully wherever you put its top-left corner (negative positions are fine).
- If two pieces overlap on a page, or a piece is listed twice, the later line is ignored.
- The score shown after you submit is rounded down; the final ranking uses the exact score. 

## Layout

- `solution.py` — the solver (`assemble(pieces)`).
- `gen.py`, `score.py`, `bench.py` — local instance generator, scorer, and benchmark.
- `tools/build_lexicon.py` — builds the embedded lexicon (needs `data/`, which is gitignored).
- `tests/` — unit tests.
