# ============================================================
# TITAN_KERNEL: 58_operator_binder_builder.py
# PURPOSE: Build one operator binder Markdown from key TXT/MD reports
# VERSION: v1.0
# STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE
# ============================================================

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

EXIT_OK = 0
EXIT_WRITE_ERROR = 2

CANON = {
    "SYSTEM_STATUS": "SYSTEM RED",
    "STEP102": "LOCKED / NOT ACCEPTED",
    "FINAL_USE_ALLOWED": "NO",
    "SSOT_WRITE_ALLOWED": "NO",
    "EVIDENCE_APPROVAL_ALLOWED": "NO",
    "GATE_CLOSURE_ALLOWED": "NO",
}

DEFAULT_DOCS = [
    "safe_chronological_runbook.md",
    "operator_status_snapshot.txt",
    "next_actions.md",
    "execution_receipt.txt",
    "no_release_memorandum.md",
]

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def read_text(path):
    try:
        return Path(path).read_text(encoding="utf-8-sig", errors="replace")
    except Exception as exc:
        return f"UNREADABLE: {exc}"

def find_doc(root, name):
    root = Path(root)
    direct = root / name
    if direct.exists():
        return direct
    matches = list(root.rglob(name)) if root.exists() else []
    return matches[0] if matches else None

def main():
    parser = argparse.ArgumentParser(description="TITAN operator binder builder")
    parser.add_argument("--reports-root", required=True)
    parser.add_argument("--extra-docs", nargs="*", default=[])
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    doc_names = DEFAULT_DOCS + args.extra_docs
    sections = []
    manifest = []

    for name in doc_names:
        path = find_doc(args.reports_root, name)
        if path is None:
            manifest.append({"name": name, "path": "MISSING", "included": False})
            sections.append(f"\n## {name}\n\nMISSING\n")
            continue

        manifest.append({"name": name, "path": str(path), "included": True})
        content = read_text(path)
        sections.append(f"\n## {name}\n\n```text\n{content}\n```\n")

    header = [
        "# TITAN Operator Binder",
        "",
        f"Generated At: {now_iso()}",
        "",
        "STATUS: SYSTEM RED — STEP102 LOCKED — NO FINAL USE",
        "",
        "This binder is a read-only operator package. It does not approve evidence, close gates, write canonical SSoT, unlock STEP102, or allow final use.",
        "",
        "## Canonical Locks",
        ""
    ]

    for k, v in CANON.items():
        header.append(f"- `{k}` = `{v}`")

    binder = "\n".join(header) + "\n" + "\n".join(sections) + "\n\nSYSTEM RED — STEP102 LOCKED — NO FINAL USE\n"

    payload = {
        "timestamp": now_iso(),
        "component": "OPERATOR_BINDER_BUILDER",
        "version": "1.0",
        "status": "REVIEW_REQUIRED",
        "documents": manifest,
        "decision": "Operator binder is documentation only.",
        **CANON
    }

    try:
        Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_md).write_text(binder, encoding="utf-8")
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"❌ Write error: {exc}")
        return EXIT_WRITE_ERROR

    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"✅ Operator binder: {args.out_md}")
    print("SYSTEM RED — STEP102 LOCKED — NO FINAL USE")
    return EXIT_OK

if __name__ == "__main__":
    sys.exit(main())
