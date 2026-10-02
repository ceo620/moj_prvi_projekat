import ast
import pathlib
import sys

def main() -> int:
    if len(sys.argv) != 2:
        print("STATUS=FAIL")
        print("ERROR=INVALID_ARGUMENT_COUNT")
        return 2

    path = pathlib.Path(sys.argv[1])

    try:
        raw = path.read_bytes()
    except Exception as exc:
        print("STATUS=FAIL")
        print(f"ERROR=READ:{type(exc).__name__}:{exc}")
        return 3

    decoded = None
    selected_encoding = None

    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            decoded = raw.decode(encoding)
            selected_encoding = encoding
            break
        except UnicodeDecodeError:
            continue

    if decoded is None:
        print("STATUS=FAIL")
        print("ERROR=DECODE_FAILED")
        return 4

    try:
        ast.parse(decoded, filename=str(path))
    except SyntaxError as exc:
        print("STATUS=FAIL")
        print(
            "ERROR=SYNTAX:"
            f"LINE={exc.lineno}:OFFSET={exc.offset}:MESSAGE={exc.msg}"
        )
        return 5
    except Exception as exc:
        print("STATUS=FAIL")
        print(f"ERROR=AST:{type(exc).__name__}:{exc}")
        return 6

    print("STATUS=PASS")
    print(f"ENCODING={selected_encoding}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())