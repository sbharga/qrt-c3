# Black box

Query the black box to maximise payoff. Beware the noise.

*Bonus eligibility uses your official final noiseless score for the whole question. Individual noisy feedback values do not determine eligibility. The normalized noisy score is `raw_noisy_score / raw_noiseless_target`, clipped to the range 0–1.*

## Approach

The exact query interface is not specified in the problem statement, so `solution.py` is interface-agnostic: `maximize(query, dim, budget)` takes any callable `query(x) -> noisy payoff` over `x ∈ [0, 1]^dim` and returns the point with the best estimated noiseless payoff. Wire `query` to the real black box in `main()`.

1. Explore: sample the space uniformly.
2. Successive halving: repeatedly re-query the top half so noise averages out.
3. Local refinement: perturb the best point with shrinking step size, accepting a move only when its averaged payoff beats the incumbent's.

Run `python solution.py` for a self-test against a synthetic noisy function.
