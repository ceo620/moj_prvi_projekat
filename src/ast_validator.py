import ast
import sys
from pathlib import Path

def validiraj_python_fajlove(root_dir="src"):
    putanja = Path(root_dir)
    pukle_skripte = []
    
    for py_fajl in putanja.rglob("*.py"):
        try:
            ast.parse(py_fajl.read_text(encoding="utf-8"))
        except SyntaxError as err:
            pukle_skripte.append((str(py_fajl), str(err)))

    if pukle_skripte:
        print("[GRESKA] Pronadjene sintaksne greske:")
        for fajl, err in pukle_skripte:
            print(f"  - {fajl}: {err}")
        return False
    else:
        print(f"[OK] Svi Python fajlovi u '{root_dir}' su sintaksno ispravni (AST Validacija Uspjesna).")
        return True

if __name__ == "__main__":
    is_valid = validiraj_python_fajlove()
    sys.exit(0 if is_valid else 1)
