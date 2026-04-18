def score_output(actual, expected) -> dict:
    passed = actual == expected
    reward = 1.0 if passed else 0.0

    return {
        "passed": passed,
        "reward": reward,
        "expected": expected,
        "actual": actual,
    }


def score_test_cases(fn, test_cases: list[tuple]) -> dict:
    results = []
    total_reward = 0.0

    for i, (inputs, expected) in enumerate(test_cases, start=1):
        try:
            if not isinstance(inputs, tuple):
                inputs = (inputs,)

            actual = fn(*inputs)
            case_result = score_output(actual, expected)
            case_result["case_id"] = i
        except Exception as e:
            case_result = {
                "case_id": i,
                "passed": False,
                "reward": 0.0,
                "expected": expected,
                "actual": None,
                "error": f"runtime_error: {e}",
            }

        total_reward += case_result["reward"]
        results.append(case_result)

    pass_rate = sum(r["passed"] for r in results) / len(results) if results else 0.0

    return {
        "results": results,
        "total_reward": total_reward,
        "pass_rate": pass_rate,
    }