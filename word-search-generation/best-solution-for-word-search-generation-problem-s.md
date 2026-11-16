# Recommended solution: an anytime C++ solver

Use **C++ with a protected, independently validated best grid**. First find any valid grid, then spend the remaining time trying smaller ones. The core search should combine:

1. Randomized, overlap-preferring placement of required words.
2. Immediate rejection of placements that complete a forbidden word.
3. Forbidden-aware filling of blank cells.
4. Restarts, with bounded backtracking as an optional upgrade.
5. Independent validation before accepting any result.

This is a practical design, **not a proven smallest-grid algorithm or a benchmarked winning submission**. The available experiments favor some of these ingredients, but none measured a complete C++ solver under the actual two-second limit.

## 1. Optimize the score, not just the side length

Let:

- \(S\) = total length of the original required-word list.
- \(L\) = length of the longest required word.
- \(N\) = grid side length.

The score is:

\[
\text{score}=100\min\left(1,\frac{S}{1.7N^2}\right).
\]

Therefore:

- A grid must have \(N\ge L\).
- If \(N^2\le S/1.7\), a valid grid scores **100**. There is no scoring benefit to making it smaller.
- If \(N=L\), no smaller grid is allowed, even if the score is below 100.

For example, if \(S=500\), a valid \(17\times17\) grid scores 100. A valid \(20\times20\) grid scores about 73.53.

Keep the original list for calculating \(S\), even if the solver removes duplicate constraints internally.

## 2. Use an anytime search

The solver should always distinguish between:

- A **working board**, which may be incomplete.
- An **incumbent**, which is a complete grid that has passed an independent validator.

Never overwrite the incumbent with an unvalidated board.

A reasonable starting schedule is:

```text
L = longest required-word length, or 1 if there are none
C = floor(sqrt(S / 1.7))

Choose an initial, relatively loose size:
    seed = max(L, ceil(sqrt(S / 0.8)))

Try randomized constructions at seed and, if necessary,
at a few nearby or larger sizes until a valid grid is found.

While time remains:
    if incumbent is full-score or incumbent size == L:
        stop

    try a size smaller than the incumbent:
        usually incumbent_size - 1
        sometimes an intermediate size or max(L, C)

    if a complete candidate passes independent validation:
        replace incumbent if it is smaller

Return incumbent.
```

The `0.8` starting density is only a heuristic. It may be too loose or too tight for a particular input. In practice, cap the size and preprocessing work to fit the available time and memory.

**Do not use binary search over sizes.** Feasibility is not necessarily monotone because changing \(N\) changes the periodic strings produced by wraparound. A failed search at one size also says nothing conclusive about whether that size is feasible: the heuristic may simply have missed a solution.

For the stated C++ limit, use a conservative internal deadline below **2 seconds**, and check it inside long placement, filling, and validation loops—not merely between attempts. Reserve time for returning the incumbent. The exact margin must be measured on the actual judge.

## 3. Construct a candidate at a fixed size

Store the board as \(N^2\) cells, initially blank. For each required word, a candidate placement consists of:

```text
(start row, start column, row direction, column direction)
```

where the direction is one of the eight compass directions. Character \(k\) occupies:

\[
((r+k\,dr)\bmod N,\ (c+k\,dc)\bmod N).
\]

A placement is **compatible** if every visited cell is blank or already contains the required letter.

### Baseline placement procedure

1. Deduplicate required words, including a word and its reverse, for feasibility work.
2. Shuffle the words; in some restarts, use longest-first order with randomized ties.
3. For the next word, enumerate compatible placements.
4. Rank placements by how many existing letters they reuse.
5. Randomly choose among the best or near-best placements.
6. Reject a tentative placement if it completes a forbidden occurrence.
7. If no placement works, restart or backtrack within a small budget.
8. Once all words are placed, run the forbidden-aware filler.

Overlap is a useful preference, not a correctness rule: occasionally a word must be placed without overlapping anything. General constraint-search methods such as choosing the most constrained remaining word and checking future options can help, but their overhead must be measured here. [3, 10]

### Optional upgrade: bounded backtracking

Instead of abandoning an attempt immediately, retain a few alternative placements and undo recent choices. A stronger version chooses the remaining word with the fewest compatible placements. However, repeatedly counting every word’s candidates can itself be expensive.

A small research proxy found more completions with branching than with greedy placement, but branching also took substantially longer; the comparison did **not** establish which is better under an equal two-second budget. Start with cheap restarts, then benchmark bounded backtracking as a separate option.

If a cell can be shared by several placed words, maintain either:

- A reference count per cell; or
- An undo trail that records only cells changed from blank to a letter.

Undoing one word must not erase a letter still needed by another word.

## 4. Handle forbidden words exactly

This is the part most likely to invalidate an otherwise good generator.

### Reduce long forbidden words for each candidate size

Every straight path on an \(N\times N\) torus repeats after \(N\) steps. Thus, for a forbidden word `w` longer than \(N\):

- If any `w[i] != w[i-N]`, it **cannot occur at this size**.
- Otherwise, it occurs exactly when its first \(N\) characters occur.

Examples for \(N=2\):

- `ABABA` reduces to `AB`.
- `ABACA` cannot occur: it would require the same cell to be both `B` and `C`.

Recompute this reduction whenever \(N\) changes. Include reversed patterns, or explicitly check both directions.

### Check placements as they are made

If a placement completes a forbidden word using already assigned cells, reject it immediately. Filling the remaining blanks cannot undo that occurrence.

A practical implementation can represent the board as four families of cyclic lines: rows, columns, and the two diagonal families. Check both each reduced forbidden word and its reverse. After a placement, only lines containing newly assigned cells need to be rechecked.

For large forbidden dictionaries, an Aho–Corasick automaton is an option for scanning many patterns at once. When scanning a partially filled line, treat a blank as a separator, not as a matching letter. To catch wraparound, scan the line followed by enough of its beginning to cover the longest reduced pattern. [16]

For a first implementation, a direct checker may be simpler and safer. Choose between direct scanning and an automaton only after measuring the workload; the automaton’s setup cost is not free.

## 5. Fill blanks without creating forbidden words

Filling every blank with a fixed letter is **not generally safe**.

A useful bounded filler is:

```text
fill(board):
    if no blanks remain:
        return success

    For each candidate blank, determine which letters A–Z
    can be assigned without completing a forbidden word.

    Choose a blank with the fewest legal letters.

    Try its legal letters in randomized order:
        assign letter
        if fill(board) succeeds:
            return success
        undo assignment

    return failure
```

Stop at a node or time budget. If filling fails, backtrack some required-word placements or restart.

For speed, first check whether there is a letter absent from **all reduced forbidden patterns**. If so, filling every remaining blank with that letter is safe, provided the partial board already contains no complete forbidden occurrence: every newly created occurrence containing a filled cell would contain a letter absent from the forbidden dictionary.

A more advanced filler can track forbidden occurrences that have only one blank remaining; that occurrence bans one letter at that blank. Such propagation is useful when many filler letters are constrained, but its memory and update costs need careful limits.

## 6. Independently validate the result

Use a validator separate from placement bookkeeping. For the final grid, verify:

1. \(N>0\), there are \(N\) rows, and every row has \(N\) characters.
2. Every character is uppercase `A`–`Z`.
3. \(N\) is at least the longest required-word length.
4. Every original required word occurs in at least one of the eight directions.
5. No original forbidden word occurs in any direction.

The direct reference check for one word is:

```text
occurs(grid, word):
    for each starting cell (r, c):
        for each of the 8 directions (dr, dc):
            if every character k matches
               grid[(r + k*dr) mod N][(c + k*dc) mod N]:
                return true
    return false
```

**Do not stop at one lap for forbidden words.** A forbidden word may be longer than \(N\), and can still occur over multiple laps. For example, `ABABA` occurs in the first row of:

```text
AB
CD
```

In C++, normalize negative modular indices when implementing reverse directions.

An independent validator is worth the cost: an invalid grid scores zero, even if the search’s internal state says all words were placed. Toroidal occurrence rules require checking wraparound in every direction. [2]

## 7. Important edge cases and limits

- **Obvious contradiction:** If a forbidden word is a substring of a required word or its reverse, no valid grid exists.
- **Reversals:** Requiring `ABC` and forbidding `CBA` is impossible, because both directions are allowed.
- **Duplicates:** Under the stated existence rules, one occurrence can satisfy repeated required words. The original duplicates still contribute to the stated \(S\).
- **Other impossible instances exist:** For example, forbidding every single letter `A` through `Z` prevents any positive-sized grid.
- **No failure return is specified:** If no incumbent is found before the deadline, the solver cannot safely claim that the instance is impossible. An empty list would not be a valid grid. The judge must specify whether inputs are guaranteed solvable or provide a failure convention.
- **Empty strings and empty input:** Their semantics are not fully specified. Confirm the judge contract rather than silently inventing one.

For testing, include tiny \(N=1\) and \(N=2\) grids, reverse matches, repeated letters, long forbidden words, dense forbidden sets, and random assignment/undo sequences. Compare the optimized checks against the direct validator on many small random boards.

## New perspectives and ideas

These are improvements to investigate, not established winners for this task.

### 1. Spend search effort according to *why* attempts fail

**Own inference — plausible.** Use failure depth to choose the next action: if many attempts fail early, change the word order or try a larger size; if they fail near completion, spend a limited budget on backtracking or removing and replacing a few words.

**Why it might work:** Early failure suggests a substantially different construction may be needed, while late failure suggests that most of the current board is useful. General restart and repair methods motivate this approach, though they do not establish the right policy here. [6, 12]

**First test:** Log failure depth, time, and final validated score. Compare adaptive switching against restart-only search at the same two-second limit.

### 2. Penalize placements that make filling dangerous

**Own inference — plausible.** Alongside overlap, penalize placements that leave a forbidden pattern almost complete—for example, one with no mismatches and only one or two blanks.

**Why it might work:** Rejecting completed forbidden words is necessary, but a board can already be difficult or impossible to fill before a forbidden word is complete. Anticipating those threats may prevent wasted attempts.

**First test:** Keep the same placement and filler code, add a small near-threat penalty, and compare valid-grid rate, filler backtracks, and final scores on forbidden-heavy cases.

### 3. Use bitsets to test many starts at once

**Plausible optimization.** For \(N\le64\), represent each cyclic line with 64-bit masks for occupied cells and each letter. Intersect rotated masks to find all starts compatible with a word. Bit-parallel string matching provides the underlying technique. [20, 21]

**Why it might work:** One machine operation can eliminate many starts at once. But updating masks, scoring surviving placements, and handling forbidden words still cost time, so a microbenchmark alone is insufficient.

**First test:** Implement this behind the same interface as the scalar checker. First compare candidate sets for correctness, then compare full validated scores and runtime under the actual limit. Special-case shifts by 64 and boards larger than 64.

### 4. Use the geometry of even-sized tori as an optional seed

**Own inference — speculative.** On even-sized boards, a pair of opposite diagonal cycles can intersect twice; on odd-sized boards, they intersect once. Two words that agree at both even-board crossings might form a useful compact seed.

**Why it might work:** A double crossing can provide two shared cells rather than one. But it can also introduce a second conflict, and a small proxy did not show a consistent benefit from making such seeds mandatory.

**First test:** Reserve a small fraction of attempts for double-crossing seeds, leaving the rest unseeded. Compare **final validated score**, not merely the number of words placed.

### 5. Benchmark the portfolio, not individual tricks

**Established as an evaluation principle; the particular portfolio is unproven.** The decisive metric is score including invalid or missing outputs as zero, measured under the real time limit.

**First test:** Build a paired test set containing ordinary word lists, overlap-rich lists, long forbidden words, and forbidden-heavy cases. Compare restart-only, restart-plus-backtracking, and restart-plus-repair with the same validator and deadline. Record score distribution, valid-output rate, time to first valid grid, and peak memory. Related crossword research supports evaluating complete outcomes rather than assuming that a promising partial seed will finish well. [15]

## Sources

- [2] code golf - Word Search on a Torus - Code Golf Stack Exchange — https://codegolf.stackexchange.com/questions/164219/word-search-on-a-torus
- [3] cp-camera.dvi — https://www.cs.toronto.edu/~fbacchus/Papers/BvRCP95.pdf
- [6] Restart Schedules for Ensembles of Problem Instances — https://www.cs.cmu.edu/afs/.cs.cmu.edu/Web/People/dgolovin/papers/aaai07b.pdf
- [10] Crossword - CSCI E-80 — https://cs50.harvard.edu/extension/ai/2020/spring/projects/3/crossword/
- [12] Using Constraint Programming and Local Search Methods to Solve Vehicle Routing Problems — https://doi.org/10.1007/3-540-49481-2_30
- [15] Generating High-Score Crosswords Puzzles With Bi-Objective, Stochastic and Systematic Search — https://journals.sagepub.com/doi/10.1177/13896911251324363
- [16] Programming Techniques Glenn Manacher — https://cr.yp.to/bib/1975/aho.pdf
- [20] Ricardo Baeza-Yates and Gaston H. Gonnet — https://www.cin.ufpe.br/~paguso/courses/if767/bib/Baeza_1992.pdf
- [21] Lecroq, *Twenty Years of Bit-Parallelism in String Matching* — https://www-igm.univ-mlv.fr/~lecroq/articles/BM70.pdf (model-supplied)
