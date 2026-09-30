import csv
import hashlib
import os
import sys
from collections import defaultdict
from pathlib import Path

p010_path = Path(sys.argv[1])
plan_path = Path(sys.argv[2])
register_path = Path(sys.argv[3])
run_dir = Path(sys.argv[4])

run_dir.mkdir(parents=True, exist_ok=True)

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
        )
        writer.writeheader()
        writer.writerows(rows)

def file_sha256(path):
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while True:
            block = handle.read(1024 * 1024)

            if not block:
                break

            digest.update(block)

    return digest.hexdigest()

protected_signals = (
    "/00_CONTROL/",
    "/09_REPAIR_QUEUE/",
    "/13_HUMAN_GATE_DECISIONS/",
    "/28_BACKGROUND_PRODUCTION_CONTROL/",
    "/29_ACTIVE_DAEMON_SWARM/",
    "/30_SSOT_10_STAGE_PIPELINE/",
    "/31_DUPLICATE_DELETE_PROTOCOL/",
    "/.ssh/",
)

p010_rows = read_psv(p010_path)
plan_rows = read_psv(plan_path)
register_rows = read_psv(register_path)

plan_by_path = {
    row.get("FullPath", ""): row
    for row in plan_rows
    if row.get("FullPath", "")
}

register_by_path = {
    row.get("FullPath", ""): row
    for row in register_rows
    if row.get("FullPath", "")
}

groups = defaultdict(list)

for row in plan_rows:
    group_id = row.get("GroupID", "").strip()

    if group_id:
        groups[group_id].append(row)

delete_paths = {
    row.get("FullPath", "")
    for row in p010_rows
    if row.get("StageResult", "") ==
       "DELETE_CANDIDATE_HUMAN_GATE_PENDING"
}

candidate_rows = [
    row
    for row in p010_rows
    if row.get("StageResult", "") ==
       "DELETE_CANDIDATE_HUMAN_GATE_PENDING"
]

keeper_cache = {}
candidate_cache = {}

def inspect_file(path_text, expected_size, expected_hash):
    result = {
        "Present": "NO",
        "ActualSizeBytes": "",
        "SizeMatch": "NO",
        "ActualSHA256": "",
        "HashMatch": "NO",
        "ReadError": "",
    }

    path = Path(path_text)

    try:
        if not path.is_file():
            return result

        result["Present"] = "YES"
        actual_size = path.stat().st_size
        result["ActualSizeBytes"] = str(actual_size)

        try:
            expected_size_int = int(expected_size)
        except Exception:
            expected_size_int = -1

        result["SizeMatch"] = (
            "YES"
            if actual_size == expected_size_int
            else "NO"
        )

        actual_hash = file_sha256(path)
        result["ActualSHA256"] = actual_hash

        result["HashMatch"] = (
            "YES"
            if actual_hash.lower() == expected_hash.lower()
            else "NO"
        )

    except Exception as exc:
        result["ReadError"] = (
            f"{type(exc).__name__}:{exc}"
        )

    return result

final_rows = []
group_proof_rows = []

counts = defaultdict(int)
bytes_ready = 0

for index, p010 in enumerate(candidate_rows, start=1):
    candidate_path = p010.get("FullPath", "")
    group_id = p010.get("GroupID", "")
    expected_hash = p010.get("SHA256", "")
    expected_size = p010.get("SizeBytes", "")

    plan = plan_by_path.get(candidate_path, {})
    register = register_by_path.get(candidate_path, {})

    if not expected_hash:
        expected_hash = (
            plan.get("SHA256", "") or
            register.get("SHA256", "")
        )

    if not expected_size:
        expected_size = (
            plan.get("SizeBytes", "") or
            register.get("SizeBytes", "")
        )

    keeper_rows = [
        row
        for row in groups.get(group_id, [])
        if row.get("Decision", "") == "KEEP_PRIMARY"
    ]

    keeper_path = (
        keeper_rows[0].get("FullPath", "")
        if len(keeper_rows) == 1
        else ""
    )

    candidate_key = (
        candidate_path,
        expected_size,
        expected_hash,
    )

    if candidate_key not in candidate_cache:
        candidate_cache[candidate_key] = inspect_file(
            candidate_path,
            expected_size,
            expected_hash,
        )

    candidate_check = candidate_cache[candidate_key]

    keeper_check = {
        "Present": "NO",
        "ActualSizeBytes": "",
        "SizeMatch": "NO",
        "ActualSHA256": "",
        "HashMatch": "NO",
        "ReadError": "",
    }

    if keeper_path:
        keeper_key = (
            keeper_path,
            expected_size,
            expected_hash,
        )

        if keeper_key not in keeper_cache:
            keeper_cache[keeper_key] = inspect_file(
                keeper_path,
                expected_size,
                expected_hash,
            )

        keeper_check = keeper_cache[keeper_key]

    candidate_protected = any(
        signal in candidate_path
        for signal in protected_signals
    )

    keeper_protected = any(
        signal in keeper_path
        for signal in protected_signals
    )

    distinct_paths = bool(
        candidate_path and
        keeper_path and
        candidate_path != keeper_path
    )

    keeper_outside_delete_set = (
        keeper_path not in delete_paths
        if keeper_path
        else False
    )

    p011 = (
        candidate_check["Present"] == "YES" and
        candidate_check["SizeMatch"] == "YES" and
        candidate_check["HashMatch"] == "YES"
    )

    p012 = (
        len(keeper_rows) == 1 and
        keeper_check["Present"] == "YES" and
        keeper_check["SizeMatch"] == "YES" and
        keeper_check["HashMatch"] == "YES"
    )

    p013 = (
        not candidate_protected and
        distinct_paths
    )

    p014 = (
        keeper_outside_delete_set and
        keeper_check["ActualSHA256"] ==
        candidate_check["ActualSHA256"] and
        keeper_check["ActualSHA256"] != ""
    )

    p015 = p011 and p012 and p013 and p014

    reasons = []

    if not p011:
        reasons.append(
            "CANDIDATE_CURRENT_HASH_OR_SIZE_NOT_VERIFIED"
        )

    if not p012:
        reasons.append(
            "EXACTLY_ONE_VERIFIED_KEEPER_NOT_PROVEN"
        )

    if candidate_protected:
        reasons.append("CANDIDATE_PATH_PROTECTED")

    if keeper_protected:
        reasons.append(
            "KEEPER_IS_PROTECTED_ACCEPTABLE_BUT_RECORDED"
        )

    if not distinct_paths:
        reasons.append("CANDIDATE_AND_KEEPER_PATH_CONFLICT")

    if not keeper_outside_delete_set:
        reasons.append("KEEPER_IS_INSIDE_DELETE_SET")

    if not p014:
        reasons.append("SURVIVING_IDENTICAL_COPY_NOT_PROVEN")

    readiness = (
        "DELETE_READY_PENDING_EXPLICIT_HUMAN_GATE"
        if p015
        else "HOLD_REVIEW"
    )

    if p015:
        try:
            bytes_ready += int(expected_size)
        except Exception:
            pass

    counts[readiness] += 1

    final_rows.append({
        "DeleteItemID": f"DELETE_ITEM_{index:06d}",
        "GroupID": group_id,
        "ExpectedSHA256": expected_hash,
        "ExpectedSizeBytes": expected_size,
        "CandidatePath": candidate_path,
        "KeeperPath": keeper_path,
        "P011CandidatePresent": candidate_check["Present"],
        "P011CandidateSizeMatch": candidate_check["SizeMatch"],
        "P011CandidateHashMatch": candidate_check["HashMatch"],
        "CandidateActualSHA256": candidate_check["ActualSHA256"],
        "P012KeeperCount": len(keeper_rows),
        "P012KeeperPresent": keeper_check["Present"],
        "P012KeeperSizeMatch": keeper_check["SizeMatch"],
        "P012KeeperHashMatch": keeper_check["HashMatch"],
        "KeeperActualSHA256": keeper_check["ActualSHA256"],
        "P013CandidateProtected": (
            "YES" if candidate_protected else "NO"
        ),
        "P013KeeperProtected": (
            "YES" if keeper_protected else "NO"
        ),
        "P013DistinctPaths": (
            "YES" if distinct_paths else "NO"
        ),
        "P014KeeperOutsideDeleteSet": (
            "YES" if keeper_outside_delete_set else "NO"
        ),
        "P014SurvivalProof": (
            "PASS" if p014 else "FAIL"
        ),
        "P015Readiness": readiness,
        "P016DeleteApproved": "NO",
        "HumanGateStatus": "PENDING",
        "HoldReason": ";".join(reasons),
    })

group_ids = sorted({
    row["GroupID"]
    for row in final_rows
})

for group_id in group_ids:
    group_items = [
        row
        for row in final_rows
        if row["GroupID"] == group_id
    ]

    ready_items = [
        row
        for row in group_items
        if row["P015Readiness"] ==
           "DELETE_READY_PENDING_EXPLICIT_HUMAN_GATE"
    ]

    keeper_paths = sorted({
        row["KeeperPath"]
        for row in group_items
        if row["KeeperPath"]
    })

    group_proof_rows.append({
        "GroupID": group_id,
        "CandidateFiles": len(group_items),
        "ReadyCandidateFiles": len(ready_items),
        "HoldCandidateFiles": (
            len(group_items) - len(ready_items)
        ),
        "KeeperCount": len(keeper_paths),
        "KeeperPaths": " || ".join(keeper_paths),
        "GroupDeleteApproved": "NO",
        "HumanGateStatus": "HOLD",
    })

fields = [
    "DeleteItemID",
    "GroupID",
    "ExpectedSHA256",
    "ExpectedSizeBytes",
    "CandidatePath",
    "KeeperPath",
    "P011CandidatePresent",
    "P011CandidateSizeMatch",
    "P011CandidateHashMatch",
    "CandidateActualSHA256",
    "P012KeeperCount",
    "P012KeeperPresent",
    "P012KeeperSizeMatch",
    "P012KeeperHashMatch",
    "KeeperActualSHA256",
    "P013CandidateProtected",
    "P013KeeperProtected",
    "P013DistinctPaths",
    "P014KeeperOutsideDeleteSet",
    "P014SurvivalProof",
    "P015Readiness",
    "P016DeleteApproved",
    "HumanGateStatus",
    "HoldReason",
]

final_path = run_dir / "P016_FINAL_DELETE_GATE.psv"
ready_path = run_dir / "DELETE_READY_PENDING_HUMAN_GATE.psv"
hold_path = run_dir / "DELETE_HOLD_REVIEW.psv"

write_psv(final_path, final_rows, fields)

write_psv(
    ready_path,
    [
        row for row in final_rows
        if row["P015Readiness"] ==
           "DELETE_READY_PENDING_EXPLICIT_HUMAN_GATE"
    ],
    fields,
)

write_psv(
    hold_path,
    [
        row for row in final_rows
        if row["P015Readiness"] == "HOLD_REVIEW"
    ],
    fields,
)

group_fields = [
    "GroupID",
    "CandidateFiles",
    "ReadyCandidateFiles",
    "HoldCandidateFiles",
    "KeeperCount",
    "KeeperPaths",
    "GroupDeleteApproved",
    "HumanGateStatus",
]

write_psv(
    run_dir / "GROUP_SURVIVAL_PROOF.psv",
    group_proof_rows,
    group_fields,
)

final_hash = file_sha256(final_path)
ready_hash = file_sha256(ready_path)

approval_template = f"""============================================================
FREYA DUPLICATE DELETE — HUMAN GATE APPROVAL TEMPLATE
============================================================

HUMAN_GATE=Danijela_Djurovic_Keskin
PROTOKOL=888

DECISION=NOT_APPROVED

FINAL_GATE_REGISTER={final_path}
FINAL_GATE_REGISTER_SHA256={final_hash}

DELETE_READY_REGISTER={ready_path}
DELETE_READY_REGISTER_SHA256={ready_hash}

DELETE_SCOPE=ONLY_ROWS_WITH_P015Readiness_DELETE_READY
DELETE_MODE=NOT_AUTHORIZED
DELETE_EXECUTED=NO

Required future approval must contain:

DECISION=APPROVED
APPROVED_BY=Danijela_Djurovic_Keskin
FINAL_GATE_REGISTER_SHA256={final_hash}
DELETE_READY_REGISTER_SHA256={ready_hash}
APPROVED_ITEM_COUNT={counts['DELETE_READY_PENDING_EXPLICIT_HUMAN_GATE']}
APPROVAL_TOKEN=<NEW_RANDOM_HUMAN_GATE_TOKEN>
APPROVED_AT=<DATE_AND_TIME>

Without an exact matching approval:
DELETE=BLOCKED
============================================================
"""

(run_dir / "HUMAN_GATE_DELETE_APPROVAL_TEMPLATE.txt").write_text(
    approval_template,
    encoding="utf-8",
)

status_lines = [
    "FREYA ANDROID — STRENGTHENED DUPLICATE DELETE PROTOCOL",
    "",
    f"P010_SOURCE={p010_path}",
    f"HUMAN_GATE_PLAN={plan_path}",
    f"DUPLICATE_REGISTER={register_path}",
    "",
    f"DELETE_CANDIDATES_RECHECKED={len(candidate_rows)}",
    f"DELETE_READY_PENDING_HUMAN_GATE={counts['DELETE_READY_PENDING_EXPLICIT_HUMAN_GATE']}",
    f"HOLD_REVIEW={counts['HOLD_REVIEW']}",
    f"DELETE_READY_BYTES={bytes_ready}",
    f"DELETE_READY_GIB={bytes_ready / (1024**3):.4f}",
    "",
    f"FINAL_GATE_REGISTER={final_path}",
    f"FINAL_GATE_REGISTER_SHA256={final_hash}",
    f"DELETE_READY_REGISTER={ready_path}",
    f"DELETE_READY_REGISTER_SHA256={ready_hash}",
    "",
    "P011=CANDIDATE_HASH_RECHECK_COMPLETE",
    "P012=KEEPER_HASH_RECHECK_COMPLETE",
    "P013=PROTECTED_PATH_GATE_COMPLETE",
    "P014=SURVIVING_COPY_PROOF_COMPLETE",
    "P015=DELETE_READINESS_CLASSIFICATION_COMPLETE",
    "P016=LOCKED_PENDING_EXPLICIT_HUMAN_GATE_APPROVAL",
    "",
    "DELETE_APPROVED=NO",
    "FILES_DELETED=NO",
    "FILES_MOVED=NO",
    "FILES_RENAMED=NO",
    "BACKGROUND_PROCESS_LEFT_RUNNING=NO",
    "FINAL_STATUS=STRENGTHENED_DELETE_PROTOCOL_COMPLETE_P016_LOCKED",
]

status_text = "\n".join(status_lines) + "\n"

(run_dir / "DELETE_PROTOCOL_STATUS.txt").write_text(
    status_text,
    encoding="utf-8",
)

print(status_text)
