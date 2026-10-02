import ast
import json
import pathlib
import sys


def call_name(node):
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        parent = call_name(node.value)
        if parent:
            return f"{parent}.{node.attr}"
        return node.attr

    return ""


def main():
    if len(sys.argv) != 2:
        print(json.dumps({
            "status": "FAIL",
            "error": "INVALID_ARGUMENT_COUNT"
        }))
        return 2

    path = pathlib.Path(sys.argv[1])

    try:
        raw = path.read_bytes()
    except Exception as exc:
        print(json.dumps({
            "status": "FAIL",
            "error": f"READ:{type(exc).__name__}:{exc}"
        }))
        return 3

    text = None
    encoding_used = None

    for encoding in (
        "utf-8-sig",
        "utf-8",
        "cp1252",
        "latin-1",
    ):
        try:
            text = raw.decode(encoding)
            encoding_used = encoding
            break
        except UnicodeDecodeError:
            continue

    if text is None:
        print(json.dumps({
            "status": "FAIL",
            "error": "DECODE_FAILED"
        }))
        return 4

    try:
        tree = ast.parse(text, filename=str(path))
        compile(
            text,
            str(path),
            "exec",
            dont_inherit=True,
            optimize=0,
        )
    except SyntaxError as exc:
        print(json.dumps({
            "status": "FAIL",
            "error": "SYNTAX_ERROR",
            "line": exc.lineno,
            "offset": exc.offset,
            "message": exc.msg,
        }))
        return 5
    except Exception as exc:
        print(json.dumps({
            "status": "FAIL",
            "error": f"COMPILE:{type(exc).__name__}:{exc}"
        }))
        return 6

    imports = set()
    calls = set()
    top_level_calls = []
    definitions = []
    has_main_guard = False

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)

        elif isinstance(node, ast.Call):
            name = call_name(node.func)
            if name:
                calls.add(name)

        elif isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
            ),
        ):
            definitions.append(node.name)

    for node in tree.body:
        if isinstance(node, ast.If):
            try:
                test_text = ast.unparse(node.test)
            except Exception:
                test_text = ""

            if "__name__" in test_text and "__main__" in test_text:
                has_main_guard = True

        possible_call = None

        if isinstance(node, ast.Expr):
            possible_call = node.value

        elif isinstance(node, ast.Assign):
            possible_call = node.value

        elif isinstance(node, ast.AnnAssign):
            possible_call = node.value

        elif isinstance(node, ast.AugAssign):
            possible_call = node.value

        if isinstance(possible_call, ast.Call):
            name = call_name(possible_call.func)

            if name:
                top_level_calls.append(name)

    network_prefixes = (
        "requests.",
        "urllib.",
        "socket.",
        "http.client.",
        "ftplib.",
        "smtplib.",
        "paramiko.",
    )

    write_prefixes = (
        "open",
        "pathlib.Path.write_",
        "shutil.copy",
        "shutil.move",
        "shutil.rmtree",
        "os.remove",
        "os.unlink",
        "os.rename",
        "os.replace",
        "os.makedirs",
        "subprocess.",
    )

    scheduler_terms = (
        "schtasks",
        "schedule.",
        "apscheduler.",
        "win32com.client",
    )

    flags = []

    lowered_calls = [item.lower() for item in calls]
    lowered_imports = [item.lower() for item in imports]

    if any(
        item.startswith(tuple(x.lower() for x in network_prefixes))
        for item in lowered_calls
    ):
        flags.append("NETWORK_CAPABLE")

    if any(
        item.startswith(tuple(x.lower() for x in write_prefixes))
        for item in lowered_calls
    ):
        flags.append("WRITE_OR_PROCESS_CAPABLE")

    combined = " ".join(lowered_calls + lowered_imports)

    if any(term in combined for term in scheduler_terms):
        flags.append("SCHEDULER_CAPABLE")

    if top_level_calls:
        flags.append("TOP_LEVEL_CALLS_PRESENT")

    result = {
        "status": "PASS",
        "encoding": encoding_used,
        "imports": sorted(imports),
        "calls": sorted(calls),
        "top_level_calls": sorted(set(top_level_calls)),
        "definitions": sorted(set(definitions)),
        "has_main_guard": has_main_guard,
        "flags": sorted(set(flags)),
        "source_executed": False,
        "module_imported": False,
    }

    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())