import random


# ---------------------------
# Toy agent behaviors
# ---------------------------
def run_agent(case_name):
    if case_name == "pass":
        return {"file": "def solve(x):\n    return x + 1"}

    if case_name == "malformed":
        return {"file": "def solve(x)\n    return x + 1"}

    if case_name == "wrong_signature":
        return {"file": "def solve(a, b):\n    return a + 1"}

    if case_name == "partial":
        return {"file": "def solve(x):\n    return x"}

    if case_name == "timeout":
        return None

    if case_name == "nondeterministic":
        k = random.randint(0, 1)
        return {"file": f"def solve(x):\n    return x + {k}"}

    if case_name == "crash":
        raise RuntimeError("Agent crashed midway")


# ---------------------------
# Judge
# ---------------------------
def judge(output):
    if output is None:
        return {"status": "timeout", "pass": False, "reward": -1.0}

    code = output.get("file", "")

    if "def solve(x)\n" in code:
        return {"status": "malformed", "pass": False, "reward": -1.0}

    if "def solve(a, b)" in code:
        return {"status": "wrong_signature", "pass": False, "reward": -0.8}

    if "return x\n" in code:
        return {"status": "partial", "pass": False, "reward": -0.5}

    if "return x + 0" in code:
        return {"status": "nondeterministic", "pass": False, "reward": -0.9}

    if "return x + 1" in code:
        return {"status": "pass", "pass": True, "reward": 1.0}

    return {"status": "unknown_failure", "pass": False, "reward": -1.0}


# ---------------------------
# Evaluation harness
# ---------------------------
def evaluate(cases):
    results = []

    for case in cases:
        try:
            output = run_agent(case)
            result = judge(output)
        except Exception:
            result = {"status": "crash", "pass": False, "reward": -1.0}

        results.append({
            "case": case,
            "status": result["status"],
            "pass": result["pass"],
            "reward": result["reward"],
        })

    total_reward = sum(r["reward"] for r in results)
    pass_rate = sum(r["pass"] for r in results) / len(results)

    summary = {
        "num_cases": len(results),
        "pass_rate": pass_rate,
        "total_reward": total_reward,
        "results": results,
    }

    return summary


# ---------------------------
# Run harness
# ---------------------------
cases = [
    "pass",
    "malformed",
    "wrong_signature",
    "partial",
    "timeout",
    "nondeterministic",
    "crash",
]

summary = evaluate(cases)

for r in summary["results"]:
    print(r)

print("\nSummary:")
print("Cases:", summary["num_cases"])
print("Pass rate:", summary["pass_rate"])
print("Total reward:", summary["total_reward"])