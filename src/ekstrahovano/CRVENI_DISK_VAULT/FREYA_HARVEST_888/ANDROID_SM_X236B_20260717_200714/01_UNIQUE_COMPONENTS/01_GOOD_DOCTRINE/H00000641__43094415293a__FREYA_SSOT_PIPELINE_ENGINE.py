import csv
import hashlib
import mimetypes
import os
import sys
from collections import defaultdict
from pathlib import Path

stage = int(sys.argv[1])
source_plan = Path(sys.argv[2])
source_register = Path(sys.argv[3])
run_dir = Path(sys.argv[4])

run_dir.mkdir(parents=True, exist_ok=True)

def read_psv(path):
    with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        return list(csv.DictReader(f, delimiter="|"))

def write_psv(path, rows, fields):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fields,
            delimiter="|",
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writeheader()
        writer.writerows(rows)

plan_rows = read_psv(source_plan)
register_rows = read_psv(source_register)

register_by_path = {
    row.get("FullPath", ""): row
    for row in register_rows
    if row.get("FullPath", "")
}

protected_signals = (
    "/00_CONTROL/",
    "/09_REPAIR_QUEUE/",
    "/13_HUMAN_GATE_DECISIONS/",
    "/28_BACKGROUND_PRODUCTION_CONTROL/",
    "/29_ACTIVE_DAEMON_SWARM/",
    "/.ssh/",
)

archive_extensions = {
    ".zip", ".rar", ".7z", ".tar", ".gz", ".tgz", ".bz2", ".xz"
}

script_extensions = {
    ".sh", ".bash", ".py", ".ps1", ".bat", ".cmd", ".exe",
    ".msi", ".apk", ".jar", ".js"
}

rows = []

for index, plan in enumerate(plan_rows, start=1):
    path = plan.get("FullPath", "")
    register = register_by_path.get(path, {})

    sha256 = plan.get("SHA256", "") or register.get("SHA256", "")
    size = plan.get("SizeBytes", "") or register.get("SizeBytes", "")
    previous_decision = plan.get("Decision", "")
    suffix = Path(path).suffix.lower()
    mime_type = mimetypes.guess_type(path)[0] or "UNKNOWN"

    exists = Path(path).is_file()
    protected = any(signal in path for signal in protected_signals)

    row = {
        "PipelineItemID": f"SSOT_ITEM_{index:06d}",
        "GroupID": plan.get("GroupID", ""),
        "SHA256": sha256,
        "SizeBytes": size,
        "FullPath": path,
        "SourcePresent": "YES" if exists else "NO",
        "PreviousDecision": previous_decision,
        "Stage": f"P{stage:03d}",
        "StageStatus": "",
        "StageResult": "",
        "HumanGateStatus": "HOLD",
    }

    if stage == 1:
        valid = bool(path and sha256 and size and plan.get("GroupID", ""))
        row["StageStatus"] = "PASS" if valid else "BLOCKED"
        row["StageResult"] = (
            "INTAKE_REGISTERED"
            if valid else
            "MISSING_REQUIRED_REGISTER_FIELDS"
        )

    elif stage == 2:
        valid_hash = (
            len(sha256) == 64 and
            all(ch in "0123456789abcdefABCDEF" for ch in sha256)
        )
        row["StageStatus"] = "PASS" if valid_hash else "BLOCKED"
        row["StageResult"] = (
            "SHA256_FORMAT_VALID"
            if valid_hash else
            "SHA256_INVALID_OR_MISSING"
        )

    elif stage == 3:
        row["StageStatus"] = "PASS"
        row["StageResult"] = (
            f"EXTENSION={suffix or 'NONE'};MIME_SIGNAL={mime_type}"
        )

    elif stage == 4:
        if suffix in script_extensions:
            result = "SCRIPT_OR_EXECUTABLE_HOLD_DO_NOT_RUN"
        elif suffix in archive_extensions:
            result = "ARCHIVE_HOLD_NO_EXTRACTION"
        else:
            result = "STATIC_FILE_SIGNAL"
        row["StageStatus"] = "PASS"
        row["StageResult"] = result

    elif stage == 5:
        if "/06_EXTRACTED_ZIPS_HOLD/" in path:
            lineage = "EXTRACTED_ARCHIVE_DERIVED"
        elif "/08_SORTED_BY_CATEGORY/" in path:
            lineage = "SORTED_DERIVED"
        elif "/09_IMPORTED_MOVED_FROM_00_SREDJEN_SISTEM/" in path:
            lineage = "IMPORTED_SOURCE_LINEAGE"
        elif "/09_REPAIR_QUEUE/" in path:
            lineage = "CONTROL_OR_REPORT"
        else:
            lineage = "OTHER_ANDROID_LINEAGE"
        row["StageStatus"] = "PASS"
        row["StageResult"] = lineage

    elif stage == 6:
        parts = path.split("/")
        category = "UNCLASSIFIED"
        if "08_SORTED_BY_CATEGORY" in parts:
            pos = parts.index("08_SORTED_BY_CATEGORY")
            if pos + 1 < len(parts):
                category = parts[pos + 1]
        row["StageStatus"] = "PASS"
        row["StageResult"] = f"CATEGORY={category}"

    elif stage == 7:
        copy_count = register.get("CopyCount", "")
        valid_duplicate = bool(
            plan.get("GroupID", "") and
            sha256 and
            copy_count
        )
        row["StageStatus"] = "PASS" if valid_duplicate else "BLOCKED"
        row["StageResult"] = (
            f"EXACT_DUPLICATE_GROUP;COPY_COUNT={copy_count}"
            if valid_duplicate else
            "DUPLICATE_PROOF_INCOMPLETE"
        )

    elif stage == 8:
        if previous_decision == "KEEP_PRIMARY":
            result = "CANON_CANDIDATE"
        elif previous_decision == "DELETE_CANDIDATE_PENDING_HUMAN_GATE":
            result = "NON_CANON_DUPLICATE_CANDIDATE"
        elif previous_decision == "HOLD_PROTECTED":
            result = "PROTECTED_COPY_HOLD"
        else:
            result = "CANON_SELECTION_REVIEW_REQUIRED"
        row["StageStatus"] = "PASS"
        row["StageResult"] = result

    elif stage == 9:
        if protected:
            result = "PROTECTED_PATH_BLOCKS_DELETE"
        elif previous_decision == "HOLD_REVIEW":
            result = "ROLE_OR_EVIDENCE_REVIEW_REQUIRED"
        elif not exists:
            result = "SOURCE_NOT_PRESENT_NO_ACTION"
        else:
            result = "PRE_FINAL_GATE_READY"
        row["StageStatus"] = "PASS"
        row["StageResult"] = result

    elif stage == 10:
        if previous_decision == "KEEP_PRIMARY":
            final = "CANON_SSOT_CANDIDATE"
        elif protected:
            final = "HOLD_PROTECTED"
        elif previous_decision == "DELETE_CANDIDATE_PENDING_HUMAN_GATE":
            final = "DELETE_CANDIDATE_HUMAN_GATE_PENDING"
        elif previous_decision == "HOLD_REVIEW":
            final = "HOLD_REVIEW"
        else:
            final = "BLOCKED_WITH_REASON"

        row["StageStatus"] = "PASS"
        row["StageResult"] = final
        row["HumanGateStatus"] = (
            "PENDING"
            if final == "DELETE_CANDIDATE_HUMAN_GATE_PENDING"
            else "HOLD"
        )

    rows.append(row)

fields = [
    "PipelineItemID",
    "GroupID",
    "SHA256",
    "SizeBytes",
    "FullPath",
    "SourcePresent",
    "PreviousDecision",
    "Stage",
    "StageStatus",
    "StageResult",
    "HumanGateStatus",
]

output = run_dir / f"P{stage:03d}_RESULT.psv"
write_psv(output, rows, fields)

counts = defaultdict(int)
for row in rows:
    counts[row["StageResult"]] += 1

status_file = run_dir / f"P{stage:03d}_STATUS.txt"

lines = [
    f"FREYA SSOT PIPELINE STAGE P{stage:03d}",
    "",
    f"ITEMS_PROCESSED={len(rows)}",
    f"OUTPUT={output}",
    "",
]

for key in sorted(counts):
    lines.append(f"{key}={counts[key]}")

lines += [
    "",
    "FILES_DELETED=NO",
    "FILES_MOVED=NO",
    "FILES_RENAMED=NO",
    "BACKGROUND_PROCESS_LEFT_RUNNING=NO",
    f"FINAL_STATUS=P{stage:03d}_FINITE_CYCLE_COMPLETE",
]

status_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
