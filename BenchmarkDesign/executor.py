import types


def load_function_from_code(code: str, function_name: str) -> dict:
    namespace = {}

    try:
        exec(code, namespace)
    except Exception as e:
        return {"ok": False, "function": None, "error": f"exec_error: {e}"}

    fn = namespace.get(function_name)

    if fn is None:
        return {"ok": False, "function": None, "error": "function_not_found"}

    if not isinstance(fn, types.FunctionType):
        return {"ok": False, "function": None, "error": "not_a_function"}

    return {"ok": True, "function": fn, "error": None}


def execute_function_safely(fn, *args, **kwargs) -> dict:
    try:
        output = fn(*args, **kwargs)
        return {"ok": True, "output": output, "error": None}
    except Exception as e:
        return {"ok": False, "output": None, "error": f"runtime_error: {e}"}