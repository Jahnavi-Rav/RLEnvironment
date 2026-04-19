"""
scoring_robust.py — Fixes for four reward scoring failure modes.
  1. Threshold too strict      → percentile-calibrated threshold
  2. Easy submetric dominance  → variance-penalized weighting
  3. Easy partial solutions    → nonlinear partial credit (convex penalty)
  4. Overfitting reward        → held-out generalization gap penalty
"""

import math, statistics
from dataclasses import dataclass, field


@dataclass
class Score:
    name: str; value: float; passed: bool
    def __repr__(self):
        bar = "█" * round(self.value * 10) + "░" * (10 - round(self.value * 10))
        return f"{'✅' if self.passed else '❌'}  {self.name:<32} [{bar}] {self.value:.3f}"


# ── 1. Threshold too strict ────────────────────────────────────────────────────
# Fix: set threshold from empirical score distribution, not gut feel.
# Pass = top-k percentile of observed scores, not a fixed cutoff.

class PercentileThreshold:
    def __init__(self, percentile: float = 50.0):
        self.percentile = percentile   # e.g. 50 = top half passes
        self.history: list[float] = []

    def judge(self, name: str, value: float) -> Score:
        self.history.append(value)
        if len(self.history) < 2:
            return Score(name, value, True)   # no data yet, optimistic
        threshold = statistics.quantiles(self.history, n=100)[int(self.percentile) - 1]
        return Score(f"{name} [p{self.percentile:.0f}={threshold:.2f}]",
                     value, value >= threshold)


# ── 2. Easy submetric dominates composite ─────────────────────────────────────
# Fix: penalize weights proportional to low variance across candidates.
# Low variance = easy = less informative = downweighted automatically.

def variance_weights(score_matrix: list[list[float]]) -> list[float]:
    """
    score_matrix: rows=candidates, cols=submetrics.
    Returns weights inversely proportional to each submetric's variance.
    Low-variance (easy) submetrics get lower weight.
    """
    n_metrics = len(score_matrix[0])
    variances  = [statistics.variance(row[i] for row in score_matrix)
                  for i in range(n_metrics)]
    # avoid zero-division; clamp minimum variance
    variances  = [max(v, 1e-6) for v in variances]
    total      = sum(variances)
    return [v / total for v in variances]   # normalize


def composite(scores: list[float], weights: list[float],
              threshold: float = 0.5, name="composite") -> Score:
    value = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
    return Score(name, round(value, 4), value >= threshold)


# ── 3. Easy partial solutions get too much reward ──────────────────────────────
# Fix: convex penalty — partial credit grows slowly at first, accelerates
# near completion. Trivial solutions earn almost nothing.

def partial_credit(raw: float, exponent: float = 2.5) -> float:
    """
    Reward = raw ^ exponent.  exponent > 1 = convex = penalizes easy partials.
    raw=0.5 → 0.177 (exp=2.5)  vs  0.5 (linear)  vs  0.25 (exp=2)
    """
    return raw ** exponent

def partial_score(name: str, raw: float,
                  exponent: float = 2.5, threshold: float = 0.5) -> Score:
    value = partial_credit(raw, exponent)
    return Score(f"{name} [exp={exponent}]", round(value, 4), value >= threshold)


# ── 4. Rewarding overfitting rather than generalization ────────────────────────
# Fix: score = train_score - λ * generalization_gap
# If train >> holdout, penalize. Forces judge to care about held-out performance.

def generalization_score(name: str,
                         train_score: float,
                         holdout_score: float,
                         penalty: float = 2.0,
                         threshold: float = 0.6) -> Score:
    """
    gap     = train - holdout  (positive = overfitting)
    reward  = holdout - penalty * max(0, gap)
    A model that generalizes: gap≈0, reward≈holdout.
    A model that overfits:    gap large, reward heavily penalized.
    """
    gap   = max(0.0, train_score - holdout_score)
    value = max(0.0, holdout_score - penalty * gap)
    return Score(f"{name} [gap={gap:.2f} λ={penalty}]",
                 round(value, 4), value >= threshold)


# ── Demo ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    # 1. Percentile threshold — calibrates to actual distribution
    print("── Percentile Threshold ────────────────────────────")
    judge = PercentileThreshold(percentile=60)
    for s in [0.3, 0.4, 0.5, 0.55, 0.7, 0.85, 0.9]:
        print(judge.judge("accuracy", s))

    # 2. Variance-based weights — suppresses easy submetrics
    print("\n── Variance Weights ────────────────────────────────")
    # 4 candidates, 3 submetrics: [hard, hard, trivial]
    # trivial = everyone scores ~1.0 → low variance → low weight
    matrix = [
        [0.4, 0.6, 0.99],
        [0.7, 0.3, 0.98],
        [0.5, 0.8, 1.00],
        [0.6, 0.5, 0.97],
    ]
    weights = variance_weights(matrix)
    print(f"Submetric weights: {[round(w,3) for w in weights]}")
    print("  → trivial submetric (col 3) gets lowest weight")
    for i, row in enumerate(matrix):
        print(composite(row, weights, name=f"candidate_{i+1}"))

    # 3. Convex partial credit — punishes easy partial solutions
    print("\n── Partial Credit (convex) ─────────────────────────")
    print(f"  {'raw':>5}  {'linear':>8}  {'exp=2':>8}  {'exp=2.5':>9}")
    for raw in [0.1, 0.3, 0.5, 0.7, 0.9, 1.0]:
        print(f"  {raw:>5.1f}  {raw:>8.3f}  {raw**2:>8.3f}  {raw**2.5:>9.3f}")

    # 4. Generalization gap penalty
    print("\n── Generalization Gap ──────────────────────────────")
    cases = [
        ("generalizes well", 0.85, 0.83),
        ("slight overfit",   0.90, 0.75),
        ("severe overfit",   0.97, 0.60),
        ("underfit",         0.55, 0.53),
    ]
    for name, train, holdout in cases:
        print(generalization_score(name, train, holdout, penalty=2.0))