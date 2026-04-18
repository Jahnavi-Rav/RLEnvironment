from pathlib import Path


def check_file_exists(file_path: str) -> dict:
    path = Path(file_path)

    if not path.exists():
        return {"ok": False, "error": "file_not_found"}

    if not path.is_file():
        return {"ok": False, "error": "not_a_file"}

    return {"ok": True, "error": None}


def read_file_safely(file_path: str) -> dict:
    file_check = check_file_exists(file_path)
    if not file_check["ok"]:
        return {"ok": False, "content": None, "error": file_check["error"]}

    try:
        content = Path(file_path).read_text(encoding="utf-8")
        return {"ok": True, "content": content, "error": None}
    except Exception as e:
        return {"ok": False, "content": None, "error": f"read_error: {e}"}