from __future__ import annotations
import csv, hashlib, os, pathlib, re, sys
from collections import Counter

plan, root, report, summary, contract = sys.argv[1:6]
root_real = os.path.realpath(root)
raw = pathlib.Path(plan).read_bytes()

try:
    text = raw.decode("utf-8-sig")
except UnicodeDecodeError as e:
    print(f"HOLD:PLAN_NOT_UTF8:{e.start}")
    raise SystemExit

rows = list(csv.reader(text.splitlines(), delimiter="\t"))
if not rows:
    print("HOLD:EMPTY_PLAN")
    raise SystemExit

header = [re.sub(r"[^a-z0-9]+", "_", x.strip().lower()).strip("_") for x in rows[0]]
allowed = [
    {"status", "state", "action_status"},
    {"sha256", "sha", "source_sha256"},
    {"bytes", "size", "size_bytes", "source_size", "source_size_bytes"},
    {"source", "source_path", "src", "src_path"},
    {"object", "object_path", "destination", "destination_path", "dest", "dest_path"},
]
if len(header) != 5 or any(header[i] not in allowed[i] for i in range(5)):
    pathlib.Path(summary).write_text(
        "SCHEMA_STATUS=HOLD\nBLOCKED_REASON=HEADER_CONTRACT_MISMATCH\n"
        f"HEADER_FIELD_COUNT={len(header)}\nHEADER_NORMALIZED={'|'.join(header)}\n",
        encoding="utf-8",
    )
    print("HOLD:HEADER_CONTRACT_MISMATCH")
    raise SystemExit

issues = []
destinations = []
counts = Counter()
valid_rows = 0
already = 0
absent = 0
outside = 0
source_bad = 0
hash_bad = 0
size_bad = 0
empty_bad = 0

def under(path: str, base: str) -> bool:
    real = os.path.realpath(path)
    return real == base or real.startswith(base + os.sep)

with open(report, "w", encoding="utf-8", newline="\n") as f:
    f.write("ROW\tSTATUS\tSOURCE\tOBJECT\tSOURCE_STATE\tOBJECT_STATE\tRESULT\tERROR_REASON\n")
    for n, row in enumerate(rows[1:], start=2):
        if not row or all(not x.strip() for x in row):
            continue
        err = []
        if len(row) != 5:
            f.write(f"{n}\t\t\t\t\t\tHOLD\tFIELD_COUNT_{len(row)}\n")
            issues.append(f"ROW_{n}_FIELD_COUNT")
            continue

        state, sha, size_s, source, obj = [x.strip() for x in row]
        counts[state or "EMPTY"] += 1

        if not all((state, sha, size_s, source, obj)):
            err.append("EMPTY_FIELD")
            empty_bad += 1

        if not re.fullmatch(r"[0-9a-f]{64}", sha):
            err.append("SHA256_FORMAT")
            hash_bad += 1

        try:
            expected_size = int(size_s)
            if expected_size < 0:
                raise ValueError
        except ValueError:
            expected_size = -1
            err.append("SIZE_FORMAT")
            size_bad += 1

        src_state = "INVALID"
        if not source.startswith("/root/") or not os.path.isfile(source) or os.path.islink(source):
            err.append("SOURCE_INVALID_OR_OUT_OF_SCOPE")
            source_bad += 1
        else:
            actual_size = os.path.getsize(source)
            actual_sha = hashlib.sha256(pathlib.Path(source).read_bytes()).hexdigest()
            if expected_size >= 0 and actual_size != expected_size:
                err.append("SOURCE_SIZE_CHANGED")
                size_bad += 1
            if re.fullmatch(r"[0-9a-f]{64}", sha) and actual_sha != sha:
                err.append("SOURCE_HASH_CHANGED")
                hash_bad += 1
            src_state = "VALID" if not any(x.startswith("SOURCE_") for x in err) else "CHANGED"

        obj_state = "INVALID"
        if not obj.startswith("/") or not under(obj, root_real):
            err.append("DESTINATION_OUTSIDE_SAFE_BUILD_ROOT")
            outside += 1
            obj_state = "OUTSIDE_BOUNDARY"
        elif os.path.lexists(obj):
            if os.path.isfile(obj) and not os.path.islink(obj):
                d_size = os.path.getsize(obj)
                d_sha = hashlib.sha256(pathlib.Path(obj).read_bytes()).hexdigest()
                if expected_size >= 0 and d_size == expected_size and d_sha == sha:
                    obj_state = "ALREADY_COMPLETE_VALIDATED"
                    already += 1
                else:
                    obj_state = "EXISTS_CONFLICT"
                    err.append("DESTINATION_CONFLICT")
            else:
                obj_state = "EXISTS_INVALID_TYPE"
                err.append("DESTINATION_INVALID_TYPE")
        else:
            obj_state = "ABSENT"
            absent += 1

        destinations.append(os.path.realpath(obj))
        result = "PASS" if not err else "HOLD"
        if result == "PASS":
            valid_rows += 1
        else:
            issues.append(f"ROW_{n}_{err[0]}")
        f.write(f"{n}\t{state}\t{source}\t{obj}\t{src_state}\t{obj_state}\t{result}\t{','.join(err)}\n")

dups = [p for p, c in Counter(destinations).items() if c > 1]
if dups:
    issues.append("DUPLICATE_DESTINATION_CONFLICT")

checkpoint_state = "NO_PARTIAL_COPY_EVIDENCE"
if already:
    checkpoint_state = "EXISTING_DESTINATIONS_VALIDATED"
if issues:
    checkpoint_state = "HOLD_BEFORE_COPY"

with open(summary, "w", encoding="utf-8", newline="\n") as f:
    f.write("SCHEMA_STATUS=PASS\n")
    f.write("HEADER_CONTRACT=STATUS|SHA256|BYTES|SOURCE_PATH|OBJECT_PATH\n")
    f.write(f"PLAN_DATA_ROWS={sum(counts.values())}\n")
    f.write(f"VALID_ROWS={valid_rows}\n")
    f.write(f"ALREADY_COMPLETE_VALIDATED={already}\n")
    f.write(f"DESTINATIONS_ABSENT={absent}\n")
    f.write(f"DESTINATIONS_OUTSIDE_SAFE_BUILD_ROOT={outside}\n")
    f.write(f"DUPLICATE_DESTINATION_COUNT={len(dups)}\n")
    f.write(f"SOURCE_INVALID_COUNT={source_bad}\n")
    f.write(f"HASH_ERROR_COUNT={hash_bad}\n")
    f.write(f"SIZE_ERROR_COUNT={size_bad}\n")
    f.write(f"EMPTY_FIELD_COUNT={empty_bad}\n")
    f.write(f"ISSUE_COUNT={len(issues)}\n")
    f.write("FIRST_ISSUE=" + (issues[0] if issues else "NONE") + "\n")
    f.write(f"CHECKPOINT_STATE={checkpoint_state}\n")
    f.write("STATUS_COUNTS=" + ",".join(f"{k}:{v}" for k,v in sorted(counts.items())) + "\n")

if issues:
    print("HOLD:" + issues[0] + "|" + checkpoint_state)
else:
    pathlib.Path(contract).write_text(
        "CONTRACT_STATUS=PASS\n"
        "PLAN_SCHEMA=STATUS|SHA256|BYTES|SOURCE_PATH|OBJECT_PATH\n"
        f"PLAN_SHA256={hashlib.sha256(raw).hexdigest()}\n"
        f"PLAN_DATA_ROWS={sum(counts.values())}\n"
        f"ALREADY_COMPLETE_VALIDATED={already}\n"
        f"DESTINATIONS_ABSENT={absent}\n"
        "DESTINATION_BOUNDARY=SAFE_BUILD_ROOT_ONLY\n"
        "CONCURRENCY=1\nOVERWRITE=NO\nDELETE=NO\nMOVE_ORIGINALS=NO\n"
        "CHECKPOINT_AFTER_EACH_FILE=REQUIRED\nENGINE_EXECUTED_IN_THIS_BATCH=NO\n"
        "COPY_EXECUTED_IN_THIS_BATCH=NO\nNETWORK_ACTION=NONE\n",
        encoding="utf-8",
    )
    print("PASS|" + checkpoint_state)
