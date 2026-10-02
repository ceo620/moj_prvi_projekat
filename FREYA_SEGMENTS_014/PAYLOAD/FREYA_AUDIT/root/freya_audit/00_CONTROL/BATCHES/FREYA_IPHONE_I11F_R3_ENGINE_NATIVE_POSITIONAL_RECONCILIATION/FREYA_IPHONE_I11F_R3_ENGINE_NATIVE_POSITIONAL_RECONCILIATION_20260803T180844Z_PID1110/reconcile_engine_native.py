from __future__ import annotations

import csv
import hashlib
import os
import pathlib
import re
import sys
from collections import Counter

plan, safe_root, row_report, summary_out, contract_out, header_out = sys.argv[1:7]
safe_root_real = os.path.realpath(safe_root)
raw = pathlib.Path(plan).read_bytes()

try:
    text = raw.decode("utf-8-sig")
except UnicodeDecodeError as exc:
    print(f"HOLD:PLAN_NOT_VALID_UTF8_BYTE_{exc.start}|NOT_EVALUATED")
    raise SystemExit(0)

physical_lines = text.splitlines()
if not physical_lines:
    print("HOLD=EMPTY_PLAN|NOT_EVALUATED")
    raise SystemExit(0)

header_raw = physical_lines[0]
header_fields = next(csv.reader([header_raw], delimiter="\t"))

with open(header_out, "w", encoding="utf-8", newline="\n") as f:
    f.write("HEADER_HANDLING=OPAQUE_SKIP_EXACTLY_ONE_PHYSICAL_LINE\n")
    f.write(f"HEADER_FIELD_COUNT={len(header_fields)}\n")
    f.write("HEADER_ESCAPED=" + header_raw.encode("unicode_escape").decode("ascii") + "\n")
    f.write("DATA_PARSER_FIELDS=STATUS|SHA256|BYTES|SOURCE|OBJECT\n")
    f.write("DATA_DELIMITER=TAB\n")
    f.write("PARSER_SOURCE=EXACT_ENGINE_HASH\n")

issues: list[str] = []
destinations: list[str] = []
status_counts: Counter[str] = Counter()

data_rows = 0
valid_rows = 0
already_complete = 0
destinations_absent = 0
destination_conflicts = 0
destination_outside = 0
source_invalid = 0
source_hash_changed = 0
source_size_changed = 0
field_count_errors = 0
empty_field_errors = 0

def under(path: str, base: str) -> bool:
    real = os.path.realpath(path)
    return real == base or real.startswith(base + os.sep)

with open(row_report, "w", encoding="utf-8", newline="\n") as report:
    report.write(
        "ROW\tSTATUS\tSHA256\tBYTES\tSOURCE\tOBJECT\t"
        "SOURCE_STATE\tOBJECT_STATE\tRESULT\tERROR_REASON\n"
    )

    for row_number, line in enumerate(physical_lines[1:], start=2):
        if not line.strip():
            continue

        row = next(csv.reader([line], delimiter="\t"))
        data_rows += 1

        if len(row) != 5:
            field_count_errors += 1
            issue = f"ROW_{row_number}_FIELD_COUNT_{len(row)}"
            issues.append(issue)
            report.write(
                f"{row_number}\t\t\t\t\t\tINVALID\tNOT_EVALUATED\tHOLD\t{issue}\n"
            )
            continue

        state, expected_sha, expected_size_text, source, obj = [value.strip() for value in row]
        status_counts[state or "EMPTY"] += 1
        errors: list[str] = []

        if not all((state, expected_sha, expected_size_text, source, obj)):
            errors.append("EMPTY_FIELD")
            empty_field_errors += 1

        sha_format_valid = re.fullmatch(r"[0-9a-f]{64}", expected_sha) is not None
        if not sha_format_valid:
            errors.append("SHA256_FORMAT_INVALID")

        try:
            expected_size = int(expected_size_text)
            if expected_size < 0:
                raise ValueError
        except ValueError:
            expected_size = -1
            errors.append("SIZE_FORMAT_INVALID")

        source_state = "INVALID"
        if (
            not source.startswith("/root/")
            or not os.path.isfile(source)
            or os.path.islink(source)
        ):
            errors.append("SOURCE_INVALID_OR_OUTSIDE_ROOT_SCOPE")
            source_invalid += 1
        else:
            actual_size = os.path.getsize(source)
            actual_sha = hashlib.sha256(pathlib.Path(source).read_bytes()).hexdigest()

            if expected_size >= 0 and actual_size != expected_size:
                errors.append("SOURCE_SIZE_CHANGED")
                source_size_changed += 1

            if sha_format_valid and actual_sha != expected_sha:
                errors.append("SOURCE_HASH_CHANGED")
                source_hash_changed += 1

            source_state = (
                "VALID"
                if "SOURCE_SIZE_CHANGED" not in errors
                and "SOURCE_HASH_CHANGED" not in errors
                else "CHANGED"
            )

        object_state = "INVALID"
        if not obj.startswith("/") or not under(obj, safe_root_real):
            errors.append("DESTINATION_OUTSIDE_SAFE_BUILD_ROOT")
            destination_outside += 1
            object_state = "OUTSIDE_BOUNDARY"
        elif os.path.lexists(obj):
            if os.path.isfile(obj) and not os.path.islink(obj):
                destination_size = os.path.getsize(obj)
                destination_sha = hashlib.sha256(pathlib.Path(obj).read_bytes()).hexdigest()

                if (
                    expected_size >= 0
                    and destination_size == expected_size
                    and sha_format_valid
                    and destination_sha == expected_sha
                ):
                    object_state = "ALREADY_COMPLETE_VALIDATED"
                    already_complete += 1
                else:
                    object_state = "EXISTS_CONFLICT"
                    errors.append("DESTINATION_CONFLICT")
                    destination_conflicts += 1
            else:
                object_state = "EXISTS_INVALID_TYPE"
                errors.append("DESTINATION_INVALID_TYPE")
                destination_conflicts += 1
        else:
            object_state = "ABSENT"
            destinations_absent += 1

        destinations.append(os.path.realpath(obj))
        result = "PASS" if not errors else "HOLD"

        if result == "PASS":
            valid_rows += 1
        else:
            issues.append(f"ROW_{row_number}_{errors[0]}")

        report.write(
            f"{row_number}\t{state}\t{expected_sha}\t{expected_size_text}\t"
            f"{source}\t{obj}\t{source_state}\t{object_state}\t"
            f"{result}\t{','.join(errors)}\n"
        )

duplicate_destinations = [
    path for path, count in Counter(destinations).items() if count > 1
]
if duplicate_destinations:
    issues.append("DUPLICATE_DESTINATION_CONFLICT")

if issues:
    checkpoint_state = "HOLD_BEFORE_COPY"
elif already_complete:
    checkpoint_state = "EXISTING_DESTINATIONS_VALIDATED"
else:
    checkpoint_state = "NO_PARTIAL_COPY_EVIDENCE"

with open(summary_out, "w", encoding="utf-8", newline="\n") as f:
    f.write("SCHEMA_STATUS=PASS_ENGINE_NATIVE_POSITIONAL\n")
    f.write("HEADER_VALIDATION=OPAQUE_NOT_SEMANTICALLY_ENFORCED\n")
    f.write(f"HEADER_FIELD_COUNT={len(header_fields)}\n")
    f.write("DATA_FIELD_COUNT_REQUIRED=5\n")
    f.write("DATA_FIELDS=STATUS|SHA256|BYTES|SOURCE|OBJECT\n")
    f.write(f"PLAN_DATA_ROWS={data_rows}\n")
    f.write(f"VALID_ROWS={valid_rows}\n")
    f.write(f"FIELD_COUNT_ERROR_COUNT={field_count_errors}\n")
    f.write(f"EMPTY_FIELD_ERROR_COUNT={empty_field_errors}\n")
    f.write(f"SOURCE_INVALID_COUNT={source_invalid}\n")
    f.write(f"SOURCE_HASH_CHANGED_COUNT={source_hash_changed}\n")
    f.write(f"SOURCE_SIZE_CHANGED_COUNT={source_size_changed}\n")
    f.write(f"DESTINATION_OUTSIDE_SAFE_BUILD_ROOT_COUNT={destination_outside}\n")
    f.write(f"DESTINATION_CONFLICT_COUNT={destination_conflicts}\n")
    f.write(f"DUPLICATE_DESTINATION_COUNT={len(duplicate_destinations)}\n")
    f.write(f"ALREADY_COMPLETE_VALIDATED={already_complete}\n")
    f.write(f"DESTINATIONS_ABSENT={destinations_absent}\n")
    f.write(f"ISSUE_COUNT={len(issues)}\n")
    f.write("FIRST_ISSUE=" + (issues[0] if issues else "NONE") + "\n")
    f.write(f"CHECKPOINT_STATE={checkpoint_state}\n")
    f.write(
        "STATUS_COUNTS="
        + ",".join(f"{key}:{value}" for key, value in sorted(status_counts.items()))
        + "\n"
    )

if issues:
    print(f"HOLD:{issues[0]}|{checkpoint_state}")
else:
    pathlib.Path(contract_out).write_text(
        "CONTRACT_STATUS=PASS\n"
        "PARSER_CONTRACT=ENGINE_NATIVE_OPAQUE_HEADER_PLUS_5_POSITIONAL_TAB_FIELDS\n"
        f"PLAN_SHA256={hashlib.sha256(raw).hexdigest()}\n"
        f"PLAN_DATA_ROWS={data_rows}\n"
        f"ALREADY_COMPLETE_VALIDATED={already_complete}\n"
        f"DESTINATIONS_ABSENT={destinations_absent}\n"
        "DESTINATION_BOUNDARY=SAFE_BUILD_ROOT_ONLY\n"
        "CONCURRENCY=1\n"
        "OVERWRITE=NO\n"
        "DELETE=NO\n"
        "MOVE_ORIGINALS=NO\n"
        "CHECKPOINT_AFTER_EACH_FILE=REQUIRED\n"
        "ENGINE_EXECUTED_IN_THIS_BATCH=NO\n"
        "COPY_EXECUTED_IN_THIS_BATCH=NO\n"
        "NETWORK_ACTION=NONE\n",
        encoding="utf-8",
    )
    print(f"PASS|{checkpoint_state}")
