"""
scoring.py — Threshold-based accuracy scoring.
Weighted composite + piecewise reward functions.
"""

from dataclasses import dataclass
from typing import Callable


@dataclass
class Score:
    name:  str
    value: float          # 0.0 – 1.0
    passed: bool

    def __repr__(self):
        bar = "█" * round(self.value * 10) + "░" * (10 - round(self.value * 10))
        return f"{'✅' if self.passed else '❌'}  {self.name:<24} [{bar}] {self.value:.3f}"


# ── Piecewise reward: define behavior by threshold breakpoints ─────────────────

def piecewise(value: float, breakpoints: list[tuple[float, float]]) -> float:
    """
    Map a raw value to a reward using linear interpolation between breakpoints.
    breakpoints: [(raw, reward), ...] sorted ascending by raw.

    Example: piecewise(0.75, [(0,0),(0.5,0.2),(0.8,0.9),(1.0,1.0)])
    """
    if value <= breakpoints[0][0]:  return breakpoints[0][1]
    if value >= breakpoints[-1][0]: return breakpoints[-1][1]
    for (x0, y0), (x1, y1) in zip(breakpoints, breakpoints[1:]):
        if x0 <= value <= x1:
            return y0 + (y1 - y0) * (value - x0) / (x1 - x0)


def piecewise_score(name: str, value: float,
                    breakpoints: list[tuple[float, float]],
                    threshold: float = 0.5) -> Score:
    reward = piecewise(value, breakpoints)
    return Score(name, reward, reward >= threshold)


# ── Weighted composite: merge multiple scores into one signal ──────────────────

def composite(scores: list[Score],
              weights: list[float] = None,
              threshold: float = 0.5) -> Score:
    """
    Weighted mean of scores. Equal weights if none given.
    Fails if any required score is 0.0 (hard gate).
    """
    weights = weights or [1.0] * len(scores)
    assert len(scores) == len(weights), "scores and weights must match"
    total  = sum(s.value * w for s, w in zip(scores, weights))
    value  = total / sum(weights)
    gated  = any(s.value == 0.0 for s in scores)   # hard failure propagates
    return Score("composite", 0.0 if gated else round(value, 4),
                 False if gated else value >= threshold)


# ── Adaptive threshold: tightens as baseline improves ─────────────────────────

class AdaptiveThreshold:
    """
    Tracks a rolling baseline and raises the pass threshold
    as performance improves — prevents reward inflation.
    """
    def __init__(self, initial: float = 0.5, rate: float = 0.1, window: int = 10):
        self.threshold = initial
        self.rate      = rate
        self.history   = []
        self.window    = window

    def update(self, value: float) -> float:
        self.history.append(value)
        if len(self.history) >= self.window:
            baseline       = sum(self.history[-self.window:]) / self.window
            self.threshold = min(0.95, self.threshold + self.rate * (baseline - self.threshold))
            self.history   = self.history[-self.window:]
        return self.threshold

    def judge(self, name: str, value: float) -> Score:
        t = self.update(value)
        return Score(f"{name} [t={t:.2f}]", value, value >= t)


# ── Demo ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    # Piecewise: steep climb to 0.6, plateau, then sharp final gain
    strict_curve   = [(0, 0.0), (0.5, 0.1), (0.6, 0.5), (0.8, 0.85), (1.0, 1.0)]
    lenient_curve  = [(0, 0.0), (0.3, 0.5), (0.6, 0.8), (1.0, 1.0)]

    print("\n── Piecewise ──────────────────────────────────────")
    for v in [0.0, 0.3, 0.55, 0.65, 0.8, 0.95, 1.0]:
        print(piecewise_score(f"strict  raw={v}", v, strict_curve,  threshold=0.6))
        print(piecewise_score(f"lenient raw={v}", v, lenient_curve, threshold=0.6))
        print()

    # Composite: accuracy matters most, speed and format less so
    print("── Composite ──────────────────────────────────────")
    accuracy = Score("accuracy", 0.91, True)
    speed    = Score("speed",    0.55, True)
    format_  = Score("format",   0.80, True)
    broken   = Score("accuracy", 0.00, False)   # hard gate demo

    print(composite([accuracy, speed, format_], weights=[0.6, 0.2, 0.2]))
    print(composite([broken,   speed, format_], weights=[0.6, 0.2, 0.2]))  # gated

    # Adaptive threshold over a simulated improving run
    print("\n── Adaptive Threshold ─────────────────────────────")
    judge = AdaptiveThreshold(initial=0.5, rate=0.2, window=5)
    scores = [0.55, 0.60, 0.65, 0.70, 0.72, 0.75, 0.78, 0.80, 0.83, 0.85]
    for s in scores:
        print(judge.judge("accuracy", s))