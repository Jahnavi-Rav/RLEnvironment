"""
robust_judges.py — Adversarial-aware judge extensions.
Handles: junk files, faked outputs, data leakage, crashes,
formatting variance, and numerical instability.
"""
 
import re, ast, math, inspect, traceback, statistics
from pathlib import Path
from JudgeDesign import JudgeResult, UnitCase, run_pipeline
 
 
# ── 1. File exists but contains junk ──────────────────────────────────────────
 
def judge_file_quality(path: str, min_bytes=10, require_parseable=True) -> JudgeResult:
    p = Path(path)
    if not p.exists():
        return JudgeResult("file_quality", False, 0.0, "File missing")
    content = p.read_text(errors="replace").strip()
    if len(content) < min_bytes:
        return JudgeResult("file_quality", False, 0.0,
                           f"File too small ({len(content)} bytes) — likely junk")
    if require_parseable:
        try:
            ast.parse(content)
        except SyntaxError as e:
            return JudgeResult("file_quality", False, 0.0, f"Unparseable: {e}")
    return JudgeResult("file_quality", True, 1.0, f"OK ({len(content)} bytes)")
 
 
# ── 2. Output faked without solving the task ───────────────────────────────────
# Strategy: probe with randomized / unseen inputs the candidate couldn't memorize.
 
def judge_no_faking(fn, input_factory, reference_fn, n=20, tolerance=0.0) -> JudgeResult:
    """
    Generate fresh random inputs at judge-time. If outputs consistently match
    reference, faking is implausible.
    """
    failures = []
    for _ in range(n):
        args = input_factory()
        args = args if isinstance(args, tuple) else (args,)
        try:
            got, exp = fn(*args), reference_fn(*args)
            ok = (abs(got - exp) <= tolerance) if tolerance else (got == exp)
            if not ok:
                failures.append(f"args={args} got={got!r} exp={exp!r}")
        except Exception as e:
            failures.append(f"args={args} raised {type(e).__name__}: {e}")
    score = 1 - len(failures) / n
    return JudgeResult("no_faking", not failures, score,
                       f"Passed {n - len(failures)}/{n} random probes"
                       + (f" | {failures[0]}" if failures else ""))
 
 
# ── 3. Evaluation data leaked into source ─────────────────────────────────────
 
def judge_no_leakage(source_path: str, test_inputs: list) -> JudgeResult:
    """Fail if literal test values appear hardcoded in the source file."""
    source = Path(source_path).read_text(errors="replace")
    leaked = [v for v in test_inputs
              if str(v) in source and not str(v) in ("0", "1", "True", "False")]
    return JudgeResult("no_leakage", not leaked, 1.0 if not leaked else 0.0,
                       "No leakage detected" if not leaked
                       else f"Leaked test values found in source: {leaked[:3]}")
 
 
# ── 4. Judge crash guard ───────────────────────────────────────────────────────
 
def safe(judge_fn) -> "Callable[[], JudgeResult]":
    """Wrap any zero-arg judge lambda so crashes become failed JudgeResults."""
    def _safe():
        try:
            return judge_fn()
        except Exception:
            tb = traceback.format_exc().strip().splitlines()[-1]
            return JudgeResult("CRASHED:" + getattr(judge_fn, "__name__", "judge"),
                               False, 0.0, f"Judge itself crashed: {tb}")
    return _safe
 
 
# ── 5. Formatting-tolerant output comparison ──────────────────────────────────
 
def normalize(v):
    """Strip whitespace/case/punctuation for lenient string comparison."""
    if isinstance(v, str):
        return re.sub(r"[\s\-_,.]", "", v).lower()
    return v
 
 
def judge_unit_tests_lenient(cases: list[UnitCase], numeric_tol=1e-9) -> JudgeResult:
    """
    Like judge_unit_tests but:
    • Normalizes strings before comparing
    • Applies numeric tolerance for floats
    • Catches all exceptions per-case
    """
    failures, passes = [], 0
    for c in cases:
        try:
            got = c.fn(*c.args, **c.kwargs)
            if c.predicate:
                ok = c.predicate(got)
            elif isinstance(c.expected, float) or isinstance(got, float):
                ok = math.isclose(got, c.expected, rel_tol=numeric_tol, abs_tol=numeric_tol)
            elif isinstance(c.expected, str):
                ok = normalize(got) == normalize(c.expected)
            else:
                ok = got == c.expected
            passes += ok
            if not ok:
                failures.append(f"'{c.description}': got {got!r} expected {c.expected!r}")
        except Exception as e:
            failures.append(f"'{c.description}': {type(e).__name__}: {e}")
    score = passes / len(cases) if cases else 1.0
    return JudgeResult("unit_tests_lenient", not failures, score,
                       f"All {passes} passed" if not failures else failures[0])
 
 
# ── 6. Numerical stability judge ──────────────────────────────────────────────
 
def judge_numerical_stability(fn, reference_fn, stress_inputs: list,
                              rel_tol=1e-6, abs_tol=1e-9) -> JudgeResult:
    """
    Compare on numerically difficult inputs (large, tiny, inf, nan edge cases).
    Uses relative + absolute tolerance. Reports instability separately from bugs.
    """
    failures, unstable, passes = [], [], 0
    for args in stress_inputs:
        args = args if isinstance(args, tuple) else (args,)
        try:
            got, exp = fn(*args), reference_fn(*args)
            if math.isnan(exp) and math.isnan(got):
                passes += 1
            elif math.isinf(exp) and math.isinf(got) and (exp > 0) == (got > 0):
                passes += 1
            elif math.isclose(got, exp, rel_tol=rel_tol, abs_tol=abs_tol):
                passes += 1
            else:
                rel_err = abs(got - exp) / (abs(exp) + 1e-300)
                unstable.append(f"args={args} got={got} exp={exp} rel_err={rel_err:.2e}")
        except (OverflowError, ZeroDivisionError, ValueError) as e:
            unstable.append(f"args={args} numeric exception: {e}")
        except Exception as e:
            failures.append(f"args={args} crash: {type(e).__name__}: {e}")
 
    total = len(stress_inputs)
    score = passes / total if total else 1.0
    issues = failures + unstable
    return JudgeResult("numerical_stability", not issues, score,
                       f"Stable on {passes}/{total} stress inputs"
                       + (f" | {issues[0]}" if issues else ""),
                       metadata={"unstable": unstable, "crashes": failures})
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Demo
# ─────────────────────────────────────────────────────────────────────────────
 
if __name__ == "__main__":
    import random, math, tempfile, os
 
    # Candidate functions ──────────────────────────────────────────────────────
    def good_add(a, b):   return a + b
    def faked_add(a, b):  return {(2,3):5,(0,0):0,(1,1):2}.get((a,b), 99)  # hardcoded
    def bad_format(a, b): return f"  {a+b}  "   # right answer, wrong format
    def unstable_sqrt(x): return math.sqrt(x) if x > 1e-10 else 0.0  # truncates near 0
 
    # Junk / leakage test files ────────────────────────────────────────────────
    junk_file    = tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w")
    junk_file.write("???junk???"); junk_file.close()
    leaked_file  = tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w")
    leaked_file.write("def add(a,b):\n    if a==42 and b==7: return 49\n    return a+b")
    leaked_file.close()
 
    # Stress inputs for numerical stability ────────────────────────────────────
    stress = [(0,),(1e-15,),(1e308,),(float("inf"),),(0.0,),(1.0,)]
 
    print("\n" + "═"*52)
    print("  ROBUST JUDGE DEMO")
    print("═"*52 + "\n")
 
    run_pipeline([
        # 1. Junk file
        safe(lambda: judge_file_quality(junk_file.name)),
 
        # 2. Good file (this script)
        safe(lambda: judge_file_quality(__file__)),
 
        # 3. Faking detection
        safe(lambda: judge_no_faking(
            faked_add,
            input_factory=lambda: (random.randint(-100,100), random.randint(-100,100)),
            reference_fn=good_add
        )),
 
        # 4. Good candidate passes faking check
        safe(lambda: judge_no_faking(
            good_add,
            input_factory=lambda: (random.randint(-100,100), random.randint(-100,100)),
            reference_fn=good_add
        )),
 
        # 5. Data leakage
        safe(lambda: judge_no_leakage(leaked_file.name, [42, 7, 49])),
 
        # 6. Crash guard (bad lambda)
        safe(lambda: 1 / 0),   # type: ignore — intentional crash
 
        # 7. Lenient: formatting difference accepted
        safe(lambda: judge_unit_tests_lenient([
            UnitCase("formatted output", bad_format, (3, 4), expected="7"),
            UnitCase("float tolerance",  lambda: 0.1 + 0.2, (), expected=0.3),
        ])),
 
        # 8. Numerical stability
        safe(lambda: judge_numerical_stability(
            unstable_sqrt, math.sqrt, stress
        )),
    ])
 
    os.unlink(junk_file.name)
    os.unlink(leaked_file.name)