from checker import read_file_safely
from executor import load_function_from_code
from scorer import score_test_cases


def evaluate_python_file(file_path: str, function_name: str, test_cases: list[tuple]) -> dict:
    read_result = read_file_safely(file_path)
    if not read_result["ok"]:
        return {
            "ok": False,
            "stage": "file_check",
            "error": read_result["error"],
        }

    load_result = load_function_from_code(read_result["content"], function_name)
    if not load_result["ok"]:
        return {
            "ok": False,
            "stage": "load_function",
            "error": load_result["error"],
        }

    score_result = score_test_cases(load_result["function"], test_cases)

    return {
        "ok": True,
        "stage": "scoring_complete",
        "summary": score_result,
    }


if __name__ == "__main__":
    tests = [
        ((1,), 2),
        ((5,), 6),
        ((-1,), 0),
    ]

    result =  evaluate_python_file("BenchmarkDesign/submission.py", "solve", tests)
    print(result)