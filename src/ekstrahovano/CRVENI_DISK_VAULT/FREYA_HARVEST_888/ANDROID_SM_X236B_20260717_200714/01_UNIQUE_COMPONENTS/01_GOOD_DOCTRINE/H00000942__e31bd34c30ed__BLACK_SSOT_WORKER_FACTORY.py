import csv
import hashlib
import os
import re
import stat
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

system_register = Path(sys.argv[1])
lineage_register = Path(sys.argv[2])
doctrine_register = Path(sys.argv[3])
safe_knowledge = Path(sys.argv[4])
unsafe_hold = Path(sys.argv[5])
workers_dir = Path(sys.argv[6])
master_register = Path(sys.argv[7])
role_summary = Path(sys.argv[8])
unsafe_linkage = Path(sys.argv[9])
syntax_errors = Path(sys.argv[10])
status_path = Path(sys.argv[11])

workers_dir.mkdir(parents=True, exist_ok=True)

def read_psv(path):
    with path.open(
        "r",
        encoding="utf-8",
        errors="replace",
        newline=""
    ) as handle:
        return list(csv.DictReader(handle, delimiter="|"))

def write_psv(path, rows, fields):
    with path.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            delimiter="|",
            quoting=csv.QUOTE_MINIMAL,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)

def sha256_file(path):
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while True:
            block = handle.read(1024 * 1024)

            if not block:
                break

            digest.update(block)

    return digest.hexdigest()

def safe_name(value):
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value)
    return cleaned[:120]

system_rows = read_psv(system_register)
lineage_rows = read_psv(lineage_register)
doctrine_rows = read_psv(doctrine_register)
safe_rows = read_psv(safe_knowledge)
unsafe_rows = read_psv(unsafe_hold)

system_by_id = {
    row.get("CanonScriptID", ""): row
    for row in system_rows
    if row.get("CanonScriptID", "").startswith("CANON_SCRIPT_")
}

lineage_counts = Counter(
    row.get("CanonScriptID", "")
    for row in lineage_rows
)

safe_by_id = defaultdict(list)

for row in safe_rows:
    canon_id = row.get("CanonScriptID", "")

    if canon_id:
        safe_by_id[canon_id].append(row)

unsafe_by_id = defaultdict(list)

for row in unsafe_rows:
    canon_id = row.get("CanonScriptID", "")

    if canon_id:
        unsafe_by_id[canon_id].append(row)

def determine_role(doctrine, safe_statements, system):
    categories = {
        item.strip()
        for item in doctrine.get("DoctrineCategories", "").split(",")
        if item.strip()
    }

    combined = " ".join(
        row.get("DoctrineText", "")
        for row in safe_statements
    ).lower()

    extension = system.get("Extension", "").lower()
    script_type = system.get("ScriptType", "").upper()

    if (
        "HASH_AND_VERIFICATION" in categories
        or "sha256" in combined
        or "checksum" in combined
    ):
        if (
            "COPY_AND_TRANSFER" in categories
            or "copy" in combined
            or "transfer" in combined
        ):
            return "VERIFIED_COPY_WORKER"

        return "HASH_VERIFICATION_WORKER"

    if (
        "SSOT_AND_LINEAGE" in categories
        or "manifest" in combined
        or "lineage" in combined
        or "canonical" in combined
    ):
        return "MANIFEST_LINEAGE_WORKER"

    if (
        "DOCUMENT_AND_REPORT" in categories
        or any(
            signal in combined
            for signal in (
                "pdf",
                "document",
                "csv",
                "register",
                "report",
                "vdr",
            )
        )
    ):
        return "DOCUMENT_INVENTORY_WORKER"

    if (
        "COPY_AND_TRANSFER" in categories
        or "copy" in combined
        or "transfer" in combined
        or "ingest" in combined
    ):
        return "COPY_INTAKE_WORKER"

    if (
        extension in {
            ".zip", ".rar", ".7z", ".tar", ".gz", ".tgz"
        }
        or "archive" in combined
        or "arhiv" in combined
    ):
        return "ARCHIVE_INSPECTION_WORKER"

    if (
        script_type in {"PYTHON", "SHELL", "POWERSHELL"}
        and "ERROR_AND_FAIL_SAFE" in categories
    ):
        return "STATIC_SCRIPT_AUDIT_WORKER"

    if "FINANCE_AND_BASELINE" in categories:
        return "FINANCE_EVIDENCE_WORKER"

    if "HUMAN_GATE" in categories:
        return "HUMAN_GATE_REGISTER_WORKER"

    return "STATIC_CLASSIFICATION_WORKER"

def worker_body(
    worker_id,
    canon_id,
    sha256,
    role,
    represented,
    unsafe_count,
):
    common = f'''#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
umask 077

SOURCE_ROOT="${{1:-}}"
BLACK_SSOT_ROOT="${{2:-}}"

echo "============================================================"
echo "FREYA BLACK SSOT SAFE WORKER"
echo "============================================================"
echo "WORKER_ID={worker_id}"
echo "CANON_SCRIPT_ID={canon_id}"
echo "SOURCE_SHA256={sha256}"
echo "ASSIGNED_ROLE={role}"
echo "ORIGINAL_RECORDS_REPRESENTED={represented}"
echo "UNSAFE_DIRECTIVES_LINKED={unsafe_count}"
echo "HUMAN_GATE=ACTIVE"
echo "PROTOKOL=888"
echo "DELETE=NO"
echo "MOVE_SOURCE=NO"
echo "RENAME_SOURCE=NO"
echo "OVERWRITE=NO"
echo "AUTO_INTERNET=NO"
echo "PERSISTENT_DAEMON=NO"
echo "SOURCE_EXECUTION=NO"
echo

if [ -z "$SOURCE_ROOT" ] || [ -z "$BLACK_SSOT_ROOT" ]; then
    echo "USAGE=$0 SOURCE_ROOT BLACK_SSOT_ROOT"
    echo "FINAL_STATUS=BLOCKED_ARGUMENTS_REQUIRED"
    exit 2
fi

if [ ! -d "$SOURCE_ROOT" ]; then
    echo "FINAL_STATUS=BLOCKED_SOURCE_ROOT_NOT_FOUND"
    exit 3
fi

if [ ! -d "$BLACK_SSOT_ROOT" ]; then
    echo "FINAL_STATUS=BLOCKED_BLACK_SSOT_ROOT_NOT_FOUND"
    exit 4
fi

echo "SOURCE_ROOT=$SOURCE_ROOT"
echo "BLACK_SSOT_ROOT=$BLACK_SSOT_ROOT"
'''

    role_sections = {
        "VERIFIED_COPY_WORKER": '''
echo "PLANNED_FUNCTION=HASH_SOURCE_COPY_TO_NEW_INTAKE_VERIFY_DESTINATION"
echo "COPY_EXECUTED=NO"
echo "NEXT_STATUS=READY_FOR_SEPARATE_COPY_APPROVAL"
''',
        "HASH_VERIFICATION_WORKER": '''
echo "PLANNED_FUNCTION=SHA256_INVENTORY_AND_INTEGRITY_REPORT"
echo "HASH_RUN_EXECUTED=NO"
echo "NEXT_STATUS=READY_FOR_READ_ONLY_HASH_AUDIT"
''',
        "MANIFEST_LINEAGE_WORKER": '''
echo "PLANNED_FUNCTION=CREATE_MANIFEST_AND_SOURCE_LINEAGE_REGISTER"
echo "MANIFEST_CREATED=NO"
echo "NEXT_STATUS=READY_FOR_STATIC_MANIFEST_BUILD"
''',
        "DOCUMENT_INVENTORY_WORKER": '''
echo "PLANNED_FUNCTION=READ_ONLY_DOCUMENT_PATH_AND_METADATA_INVENTORY"
echo "CONTENT_MODIFIED=NO"
echo "NEXT_STATUS=READY_FOR_DOCUMENT_CLASSIFICATION"
''',
        "COPY_INTAKE_WORKER": '''
echo "PLANNED_FUNCTION=COPY_TO_NEW_TIMESTAMPED_SSOT_INTAKE"
echo "SOURCE_PRESERVED=YES"
echo "COPY_EXECUTED=NO"
echo "NEXT_STATUS=READY_FOR_SEPARATE_COPY_APPROVAL"
''',
        "ARCHIVE_INSPECTION_WORKER": '''
echo "PLANNED_FUNCTION=ARCHIVE_LIST_ONLY_PATH_SAFETY_INSPECTION"
echo "ARCHIVE_EXTRACTION=NO"
echo "NEXT_STATUS=READY_FOR_LIST_ONLY_ARCHIVE_AUDIT"
''',
        "STATIC_SCRIPT_AUDIT_WORKER": '''
echo "PLANNED_FUNCTION=STATIC_SYNTAX_AND_DANGER_SIGNAL_AUDIT"
echo "SCRIPT_EXECUTION=NO"
echo "NEXT_STATUS=READY_FOR_STATIC_SCRIPT_REVIEW"
''',
        "FINANCE_EVIDENCE_WORKER": '''
echo "PLANNED_FUNCTION=FINANCE_DOCUMENT_EVIDENCE_REGISTER"
echo "FINANCIAL_CONCLUSION_AUTOMATIC=NO"
echo "NEXT_STATUS=READY_FOR_EVIDENCE_INVENTORY"
''',
        "HUMAN_GATE_REGISTER_WORKER": '''
echo "PLANNED_FUNCTION=HUMAN_GATE_DECISION_AND_APPROVAL_REGISTER"
echo "AUTOMATIC_APPROVAL=NO"
echo "NEXT_STATUS=READY_FOR_DECISION_RECORD"
''',
        "STATIC_CLASSIFICATION_WORKER": '''
echo "PLANNED_FUNCTION=STATIC_FILE_CLASSIFICATION_AND_ROUTING_PLAN"
echo "ROUTING_EXECUTED=NO"
echo "NEXT_STATUS=READY_FOR_STATIC_CLASSIFICATION"
''',
    }

    ending = '''
echo "FILES_CHANGED=NO"
echo "FILES_DELETED=NO"
echo "FILES_MOVED=NO"
echo "FILES_RENAMED=NO"
echo "FINAL_STATUS=SAFE_BLACK_SSOT_WORKER_VALIDATED_NOT_EXECUTED"
'''

    return common + role_sections[role] + ending

worker_rows = []
syntax_error_rows = []
unsafe_link_rows = []
role_counts = Counter()

expected_ids = {
    row.get("CanonScriptID", "")
    for row in doctrine_rows
}

for index, doctrine in enumerate(doctrine_rows, start=1):
    canon_id = doctrine.get("CanonScriptID", "")
    sha256 = doctrine.get("SHA256", "")

    system = system_by_id.get(canon_id, {})
    represented = lineage_counts.get(canon_id, 0)
    safe_statements = safe_by_id.get(canon_id, [])
    unsafe_statements = unsafe_by_id.get(canon_id, [])

    role = determine_role(
        doctrine,
        safe_statements,
        system,
    )

    role_counts[role] += 1

    worker_id = f"BLACK_SSOT_WORKER_{index:06d}"
    filename = (
        f"{worker_id}__"
        f"{safe_name(canon_id)}__"
        f"{sha256[:16]}.sh"
    )

    worker_path = workers_dir / filename

    worker_path.write_text(
        worker_body(
            worker_id,
            canon_id,
            sha256,
            role,
            represented,
            len(unsafe_statements),
        ),
        encoding="utf-8",
    )

    worker_path.chmod(
        stat.S_IRUSR |
        stat.S_IWUSR
    )

    syntax_result = subprocess.run(
        ["bash", "-n", str(worker_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )

    syntax_status = (
        "PASS"
        if syntax_result.returncode == 0
        else "FAIL"
    )

    worker_hash = sha256_file(worker_path)

    if syntax_status == "FAIL":
        syntax_error_rows.append({
            "WorkerID": worker_id,
            "CanonScriptID": canon_id,
            "WorkerPath": str(worker_path),
            "SyntaxMessage": (
                syntax_result.stderr.strip()
                or syntax_result.stdout.strip()
            )[:2000],
        })

    worker_rows.append({
        "WorkerID": worker_id,
        "CanonScriptID": canon_id,
        "SourceSHA256": sha256,
        "OriginalRecordsRepresented": represented,
        "SafeDoctrineStatements": len(safe_statements),
        "UnsafeDirectiveCount": len(unsafe_statements),
        "AssignedRole": role,
        "WorkerPath": str(worker_path),
        "WorkerSHA256": worker_hash,
        "SyntaxStatus": syntax_status,
        "ExecutablePermission": "NO",
        "ExecutionApproved": "NO",
        "BlackDiskAttached": "NO",
        "HumanGateStatus": "HOLD",
    })

    for unsafe in unsafe_statements:
        unsafe_link_rows.append({
            "WorkerID": worker_id,
            "CanonScriptID": canon_id,
            "SourceSHA256": sha256,
            "RiskCategories": unsafe.get(
                "RiskCategories",
                ""
            ),
            "DoctrineText": unsafe.get(
                "DoctrineText",
                ""
            ),
            "WorkerCapability": "DISABLED",
            "HumanGateStatus": "HOLD",
        })

worker_fields = [
    "WorkerID",
    "CanonScriptID",
    "SourceSHA256",
    "OriginalRecordsRepresented",
    "SafeDoctrineStatements",
    "UnsafeDirectiveCount",
    "AssignedRole",
    "WorkerPath",
    "WorkerSHA256",
    "SyntaxStatus",
    "ExecutablePermission",
    "ExecutionApproved",
    "BlackDiskAttached",
    "HumanGateStatus",
]

role_fields = [
    "AssignedRole",
    "WorkerCount",
    "ExecutionApproved",
    "HumanGateStatus",
]

unsafe_fields = [
    "WorkerID",
    "CanonScriptID",
    "SourceSHA256",
    "RiskCategories",
    "DoctrineText",
    "WorkerCapability",
    "HumanGateStatus",
]

syntax_fields = [
    "WorkerID",
    "CanonScriptID",
    "WorkerPath",
    "SyntaxMessage",
]

write_psv(
    master_register,
    worker_rows,
    worker_fields,
)

write_psv(
    role_summary,
    [
        {
            "AssignedRole": role,
            "WorkerCount": count,
            "ExecutionApproved": "NO",
            "HumanGateStatus": "HOLD",
        }
        for role, count in sorted(role_counts.items())
    ],
    role_fields,
)

write_psv(
    unsafe_linkage,
    unsafe_link_rows,
    unsafe_fields,
)

write_psv(
    syntax_errors,
    syntax_error_rows,
    syntax_fields,
)

worker_count = len(worker_rows)
syntax_pass = sum(
    1
    for row in worker_rows
    if row["SyntaxStatus"] == "PASS"
)

represented_total = sum(
    int(row["OriginalRecordsRepresented"])
    for row in worker_rows
)

complete = all((
    len(expected_ids) == 692,
    worker_count == 692,
    syntax_pass == 692,
    len(syntax_error_rows) == 0,
    represented_total == 3467,
    len(system_by_id) == 692,
))

status_lines = [
    "FREYA ANDROID — BLACK SSOT SAFE WORKER FACTORY",
    "",
    f"UNIQUE_DOCTRINE_FAMILIES={len(expected_ids)}",
    f"SAFE_WORKERS_CREATED={worker_count}",
    f"WORKERS_SYNTAX_PASS={syntax_pass}",
    f"WORKERS_SYNTAX_FAIL={len(syntax_error_rows)}",
    f"ORIGINAL_SCRIPT_RECORDS_REPRESENTED={represented_total}",
    f"UNSAFE_DIRECTIVES_LINKED_AND_DISABLED={len(unsafe_link_rows)}",
    "",
    "ROLE_COUNTS:",
]

for role, count in sorted(role_counts.items()):
    status_lines.append(f"{role}={count}")

status_lines += [
    "",
    f"MASTER_REGISTER={master_register}",
    f"ROLE_SUMMARY={role_summary}",
    f"UNSAFE_LINKAGE={unsafe_linkage}",
    f"SYNTAX_ERRORS={syntax_errors}",
    f"WORKERS_FOLDER={workers_dir}",
    "",
    "ORIGINALS_CHANGED=NO",
    "ORIGINALS_EXECUTED=NO",
    "NEW_WORKERS_EXECUTED=NO",
    "NEW_WORKERS_EXECUTABLE=NO",
    "FILES_DELETED=NO",
    "FILES_MOVED=NO",
    "FILES_RENAMED=NO",
    "BLACK_DISK_ATTACHED=NO",
    "HUMAN_GATE=ACTIVE",
]

if complete:
    status_lines.append(
        "FINAL_STATUS=692_SAFE_BLACK_SSOT_WORKERS_CREATED_LOCKED"
    )
else:
    status_lines.append(
        "FINAL_STATUS=BLACK_SSOT_WORKER_FACTORY_REVIEW_REQUIRED"
    )

status_text = "\n".join(status_lines) + "\n"
status_path.write_text(
    status_text,
    encoding="utf-8",
)
print(status_text)

raise SystemExit(0 if complete else 2)
