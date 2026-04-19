"""
judges.py — Modular evaluation judges for automated code assessment.
Each judge returns a JudgeResult: (passed, score, details).
Compose them into pipelines with run_pipeline().
"""

import os
import sys
import ast
import time
import inspect
import importlib
import importlib.util
import subprocess
import traceback
import statistics
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


# ─────────────────────────────────────────────
# Core result type
# ─────────────────────────────────────────────

@dataclass
class JudgeResult:
    name: str
    passed: bool
    score: float          # 0.0 – 1.0
    details: str
    metadata: dict = field(default_factory=dict)

    def __repr__(self):
        icon = "✅" if self.passed else "❌"
        return f"{icon} [{self.name}] score={self.score:.2f} | {self.details}"


# ─────────────────────────────────────────────
# 1. File existence judge
# ─────────────────────────────────────────────

def judge_file_exists(paths: list[str]) -> JudgeResult:
    """Check that every required file is present on disk."""
    missing = [p for p in paths if not Path(p).exists()]
    found   = len(paths) - len(missing)
    score   = found / len(paths) if paths else 1.0
    return JudgeResult(
        name    = "file_exists",
        passed  = not missing,
        score   = score,
        details = (f"All {len(paths)} file(s) found"
                   if not missing else
                   f"Missing: {missing}"),
        metadata= {"missing": missing, "found": found},
    )


# ─────────────────────────────────────────────
# 2. Importability judge
# ─────────────────────────────────────────────

def judge_importable(module_path: str) -> JudgeResult:
    """
    Attempt to import a .py file as a module.
    Catches syntax errors, missing deps, and runtime import errors.
    """
    path = Path(module_path)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    try:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return JudgeResult(
            name    = "importable",
            passed  = True,
            score   = 1.0,
            details = f"'{path.name}' imported successfully",
            metadata= {"module": mod},
        )
    except SyntaxError as e:
        return JudgeResult("importable", False, 0.0,
                           f"SyntaxError at line {e.lineno}: {e.msg}")
    except ImportError as e:
        return JudgeResult("importable", False, 0.0, f"ImportError: {e}")
    except Exception as e:
        return JudgeResult("importable", False, 0.0,
                           f"{type(e).__name__}: {e}")


# ─────────────────────────────────────────────
# 3. Function signature judge
# ─────────────────────────────────────────────

@dataclass
class SigSpec:
    """Expected signature for one function."""
    name: str
    params: list[str]               # required parameter names (order-insensitive)
    return_annotation: type = None   # optional return-type check


def judge_signatures(module_path: str, specs: list[SigSpec]) -> JudgeResult:
    """
    Load module and verify each function has the expected parameters
    and (optionally) return annotation.
    """
    import_result = judge_importable(module_path)
    if not import_result.passed:
        return JudgeResult("signatures", False, 0.0,
                           f"Cannot import module: {import_result.details}")

    mod      = import_result.metadata["module"]
    failures = []
    passes   = 0

    for spec in specs:
        fn = getattr(mod, spec.name, None)
        if fn is None:
            failures.append(f"'{spec.name}' not found in module")
            continue
        sig    = inspect.signature(fn)
        params = list(sig.parameters.keys())

        missing = [p for p in spec.params if p not in params]
        extra   = [p for p in params if p not in spec.params and p != "self"]

        if missing:
            failures.append(f"'{spec.name}' missing params: {missing}")
        if spec.return_annotation and (
            sig.return_annotation is inspect.Parameter.empty or
            sig.return_annotation != spec.return_annotation
        ):
            failures.append(
                f"'{spec.name}' return annotation: "
                f"expected {spec.return_annotation}, got {sig.return_annotation}"
            )
        if not missing and not (spec.return_annotation and sig.return_annotation != spec.return_annotation):
            passes += 1

    score = passes / len(specs) if specs else 1.0
    return JudgeResult(
        name    = "signatures",
        passed  = not failures,
        score   = score,
        details = ("All signatures match" if not failures
                   else "; ".join(failures)),
        metadata= {"failures": failures},
    )


# ─────────────────────────────────────────────
# 4. Unit test judge
# ─────────────────────────────────────────────

@dataclass
class UnitCase:
    description: str
    fn: Callable            # the function under test
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)
    expected: Any = None
    predicate: Callable = None   # predicate(output) → bool, overrides expected


def judge_unit_tests(cases: list[UnitCase]) -> JudgeResult:
    """Run a list of unit test cases. Supports exact-match or custom predicates."""
    failures = []
    passes   = 0

    for case in cases:
        try:
            result = case.fn(*case.args, **case.kwargs)
            ok = (case.predicate(result) if case.predicate
                  else result == case.expected)
            if ok:
                passes += 1
            else:
                failures.append(
                    f"FAIL '{case.description}': "
                    f"got {result!r}, expected {case.expected!r}"
                )
        except Exception as e:
            failures.append(f"ERROR '{case.description}': {type(e).__name__}: {e}")

    score = passes / len(cases) if cases else 1.0
    return JudgeResult(
        name    = "unit_tests",
        passed  = not failures,
        score   = score,
        details = (f"All {passes} unit tests passed" if not failures
                   else f"{len(failures)}/{len(cases)} failed: {failures[0]}"),
        metadata= {"failures": failures, "passes": passes},
    )


# ─────────────────────────────────────────────
# 5. Integration test judge
# ─────────────────────────────────────────────

def judge_integration(
    script: str,
    args: list[str] = None,
    timeout: float = 30.0,
    expect_exit_code: int = 0,
    expect_stdout_contains: list[str] = None,
) -> JudgeResult:
    """
    Run an external script as a subprocess and evaluate its output.
    Useful for end-to-end / integration checks.
    """
    cmd = [sys.executable, script] + (args or [])
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return JudgeResult("integration", False, 0.0,
                           f"Timed out after {timeout}s")
    except FileNotFoundError:
        return JudgeResult("integration", False, 0.0,
                           f"Script not found: {script}")

    issues = []
    if proc.returncode != expect_exit_code:
        issues.append(
            f"Exit code {proc.returncode} (expected {expect_exit_code})\n"
            f"stderr: {proc.stderr.strip()[:300]}"
        )
    for phrase in (expect_stdout_contains or []):
        if phrase not in proc.stdout:
            issues.append(f"stdout missing: {phrase!r}")

    score = 1.0 - (len(issues) / (1 + len(expect_stdout_contains or [])))
    return JudgeResult(
        name    = "integration",
        passed  = not issues,
        score   = max(0.0, score),
        details = ("Integration passed" if not issues
                   else " | ".join(issues)),
        metadata= {"stdout": proc.stdout, "stderr": proc.stderr},
    )


# ─────────────────────────────────────────────
# 6. Performance metrics judge
# ─────────────────────────────────────────────

def judge_performance(
    fn: Callable,
    args: tuple = (),
    kwargs: dict = None,
    n_runs: int = 50,
    max_mean_ms: float = 100.0,
    max_p99_ms: float = 500.0,
) -> JudgeResult:
    """
    Benchmark a function over n_runs, check mean and p99 latency.
    Returns timing stats in metadata.
    """
    kwargs  = kwargs or {}
    timings = []

    for _ in range(n_runs):
        t0 = time.perf_counter()
        fn(*args, **kwargs)
        timings.append((time.perf_counter() - t0) * 1000)  # ms

    mean_ms = statistics.mean(timings)
    p99_ms  = sorted(timings)[int(0.99 * len(timings))]
    stdev   = statistics.stdev(timings) if len(timings) > 1 else 0.0

    issues = []
    if mean_ms > max_mean_ms:
        issues.append(f"mean {mean_ms:.1f}ms > limit {max_mean_ms}ms")
    if p99_ms > max_p99_ms:
        issues.append(f"p99 {p99_ms:.1f}ms > limit {max_p99_ms}ms")

    score = 1.0 if not issues else (
        0.5 if len(issues) == 1 else 0.0
    )
    return JudgeResult(
        name    = "performance",
        passed  = not issues,
        score   = score,
        details = (f"mean={mean_ms:.1f}ms p99={p99_ms:.1f}ms over {n_runs} runs"
                   + (" ⚠ " + ", ".join(issues) if issues else "")),
        metadata= {
            "mean_ms": mean_ms, "p99_ms": p99_ms,
            "stdev_ms": stdev, "n_runs": n_runs,
        },
    )


# ─────────────────────────────────────────────
# 7. Reference behavior judge
# ─────────────────────────────────────────────

def judge_reference_behavior(
    candidate_fn: Callable,
    reference_fn: Callable,
    test_inputs: list[tuple],
    tolerance: float = 0.0,   # for numeric outputs; 0 = exact match
    comparator: Callable = None,  # custom(candidate_out, ref_out) → bool
) -> JudgeResult:
    """
    Compare candidate function outputs against a reference implementation
    across a suite of inputs. Supports exact, numeric-tolerance, and
    custom comparators.
    """
    failures = []
    passes   = 0

    for i, inp in enumerate(test_inputs):
        args = inp if isinstance(inp, tuple) else (inp,)
        try:
            cand_out = candidate_fn(*args)
            ref_out  = reference_fn(*args)

            if comparator:
                ok = comparator(cand_out, ref_out)
            elif tolerance > 0 and isinstance(ref_out, (int, float)):
                ok = abs(cand_out - ref_out) <= tolerance
            else:
                ok = cand_out == ref_out

            if ok:
                passes += 1
            else:
                failures.append(
                    f"input={args!r}: candidate={cand_out!r} ref={ref_out!r}"
                )
        except Exception as e:
            failures.append(f"input={args!r}: {type(e).__name__}: {e}")

    score = passes / len(test_inputs) if test_inputs else 1.0
    return JudgeResult(
        name    = "reference_behavior",
        passed  = not failures,
        score   = score,
        details = (f"Matches reference on all {passes} inputs" if not failures
                   else f"{len(failures)} mismatches: {failures[0]}"),
        metadata= {"failures": failures, "passes": passes},
    )


# ─────────────────────────────────────────────
# Pipeline runner
# ─────────────────────────────────────────────

def run_pipeline(
    judges: list[Callable[[], JudgeResult]],
    fail_fast: bool = False,
    verbose: bool = True,
) -> dict:
    """
    Execute a list of zero-arg callables that each return a JudgeResult.
    Returns an aggregated summary dict.

    Example:
        results = run_pipeline([
            lambda: judge_file_exists(["model.py"]),
            lambda: judge_importable("model.py"),
            lambda: judge_unit_tests(cases),
        ])
    """
    results     = []
    total_score = 0.0

    for judge_fn in judges:
        result = judge_fn()
        results.append(result)
        total_score += result.score
        if verbose:
            print(result)
        if fail_fast and not result.passed:
            print("  ↳ fail_fast: stopping pipeline")
            break

    passed     = [r for r in results if r.passed]
    failed     = [r for r in results if not r.passed]
    mean_score = total_score / len(results) if results else 0.0

    summary = {
        "passed"    : len(passed),
        "failed"    : len(failed),
        "total"     : len(results),
        "mean_score": round(mean_score, 3),
        "results"   : results,
    }

    if verbose:
        print(f"\n{'─'*50}")
        print(f"  Pipeline: {summary['passed']}/{summary['total']} passed"
              f"  |  mean score: {mean_score:.2f}")
        print(f"{'─'*50}")

    return summary


# ─────────────────────────────────────────────
# Demo
# ─────────────────────────────────────────────

if __name__ == "__main__":

    # ── Toy functions to evaluate ──────────────
    def add(a: int, b: int) -> int:
        return a + b

    def slow_add(a: int, b: int) -> int:
        time.sleep(0.005)   # simulate latency
        return a + b

    def buggy_add(a: int, b: int) -> int:
        return a + b + 1    # off-by-one bug

    # ── Reference implementation ───────────────
    def reference_add(a: int, b: int) -> int:
        return a + b

    # ── Unit test cases ────────────────────────
    cases = [
        UnitCase("add positive", add, (2, 3), expected=5),
        UnitCase("add zeros",    add, (0, 0), expected=0),
        UnitCase("add negative", add, (-1, 1), expected=0),
        UnitCase("predicate: result > 0", add, (3, 4),
                 predicate=lambda x: x > 0),
    ]

    # ── Buggy unit test cases ──────────────────
    buggy_cases = [
        UnitCase("buggy add", buggy_add, (2, 3), expected=5),
    ]

    print("\n" + "═"*50)
    print("  JUDGE PIPELINE DEMO")
    print("═"*50 + "\n")

    run_pipeline([
        # 1. File check (this file itself)
        lambda: judge_file_exists([__file__, "nonexistent.py"]),

        # 2. Importability (this module)
        lambda: judge_importable(__file__),

        # 3. Unit tests (passing)
        lambda: judge_unit_tests(cases),

        # 4. Unit tests (failing — buggy)
        lambda: judge_unit_tests(buggy_cases),

        # 5. Performance
        lambda: judge_performance(
            add, args=(100, 200),
            n_runs=200, max_mean_ms=50.0, max_p99_ms=100.0
        ),

        # 6. Performance (slow — will flag p99)
        lambda: judge_performance(
            slow_add, args=(1, 2),
            n_runs=20, max_mean_ms=1.0, max_p99_ms=10.0
        ),

        # 7. Reference behavior (correct)
        lambda: judge_reference_behavior(
            add, reference_add,
            test_inputs=[(0,0),(1,2),(10,-3),(-5,-5),(100,200)]
        ),

        # 8. Reference behavior (buggy)
        lambda: judge_reference_behavior(
            buggy_add, reference_add,
            test_inputs=[(0,0),(1,2),(10,-3)]
        ),
    ])