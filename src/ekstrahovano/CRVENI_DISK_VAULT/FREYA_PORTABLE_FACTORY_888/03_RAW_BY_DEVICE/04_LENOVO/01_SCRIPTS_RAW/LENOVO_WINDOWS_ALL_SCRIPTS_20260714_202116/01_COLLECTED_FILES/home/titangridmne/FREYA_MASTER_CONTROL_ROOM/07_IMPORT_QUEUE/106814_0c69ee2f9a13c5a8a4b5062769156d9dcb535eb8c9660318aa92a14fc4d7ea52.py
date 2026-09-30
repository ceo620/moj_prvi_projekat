from __future__ import annotations

import csv
import json
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

SYSTEM_STATUS = "SYSTEM RED — STEP102 LOCKED — NO FINAL USE"

ROOT = Path.home() / "TITAN_FULL_RAG"

V893 = ROOT / "V893_EVIDENCE_GAP_REGISTER.csv"
HASH_REGISTER = ROOT / "PACKAGE_SHA256_REGISTER_FINAL_CLEAN.txt"

OUTPUT_DIR = ROOT / "V897_OUTPUT"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CLAIM_MATRIX = OUTPUT_DIR / "TITAN_CLAIM_EVIDENCE_MATRIX.csv"
CANDIDATE_MATRIX = OUTPUT_DIR / "TITAN_EVIDENCE_CANDIDATE_MATCHES.csv"
DUPLICATE_REGISTER = OUTPUT_DIR / "TITAN_DUPLICATE_AWARE_CANDIDATE_REGISTER.csv"
REVIEW_QUEUE = OUTPUT_DIR / "TITAN_HUMAN_REVIEW_QUEUE.csv"
SUMMARY_JSON = OUTPUT_DIR / "TITAN_EVIDENCE_BINDING_SUMMARY.json"

KEYWORDS = {
    "EG_001": ["financial", "model", "assumption", "stress", "cash", "revenue"],
    "EG_002": ["loi", "mou", "pipeline", "offtake", "cedis", "epcg", "memorandum"],
    "EG_003": ["technology", "transfer", "implementation", "training", "ads"],
    "EG_004": ["esg", "taxonomy", "dnsh", "esia", "environment", "elaborat"],
    "EG_005": ["land", "cadastre", "katastar", "nepokretnosti", "parcel"],
    "EG_006": ["permit", "utu", "building", "municipal", "dozvola"],
    "EG_007": ["capex", "boq", "quote", "supplier", "cost"],
    "EG_008": ["dscr", "debt", "covenant", "repayment", "amortization"]
}

HIGH_PRIORITY = {
    "EG_001",
    "EG_002",
    "EG_007",
    "EG_008"
}

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def load_v893():
    if not V893.exists():
        return []

    with open(V893, "r", encoding="utf-8", errors="ignore") as f:
        return list(csv.DictReader(f))

def load_hashes():
    rows = []

    if not HASH_REGISTER.exists():
        return rows

    with open(HASH_REGISTER, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            parts = line.split(maxsplit=1)

            if len(parts) != 2:
                continue

            rows.append({
                "sha256": parts[0],
                "path": parts[1].strip()
            })

    return rows

def match_candidates(gap_id, hash_rows):

    keys = KEYWORDS.get(gap_id, [])
    matches = []

    for h in hash_rows:

        p = h["path"].lower()

        score = sum(1 for k in keys if k.lower() in p)

        if score > 0:
            matches.append({
                "sha256": h["sha256"],
                "path": h["path"],
                "keyword_score": score
            })

    return sorted(matches, key=lambda x: (-x["keyword_score"], x["path"]))

def choose_primary(paths):

    def rank(path):
        p = path.lower()

        archive_penalty = 10 if "/archive/" in p or "\\archive\\" in p else 0
        duplicate_penalty = 10 if "duplicate" in p else 0
        docx_bonus = -1 if p.endswith(".docx") else 0

        return archive_penalty + duplicate_penalty + docx_bonus, p

    return sorted(paths, key=rank)[0]

def duplicate_status_for_matches(matches):

    grouped = defaultdict(list)

    for m in matches:
        grouped[m["sha256"]].append(m["path"])

    status = {}

    for sha, paths in grouped.items():

        if len(paths) == 1:
            status[(sha, paths[0])] = ("UNIQUE_CANDIDATE", paths[0])

        else:
            primary = choose_primary(paths)

            for p in paths:

                if p == primary:
                    status[(sha, p)] = (
                        "PRIMARY_CANDIDATE_DUPLICATE_SET",
                        primary
                    )

                else:
                    status[(sha, p)] = (
                        "DUPLICATE_CONTENT",
                        primary
                    )

    return status

def priority_for_gap(gap_id):

    if gap_id in HIGH_PRIORITY:
        return "HIGH"

    return "NORMAL"

def build_outputs(v893_rows, hash_rows):

    total_matches = 0
    duplicate_records = 0
    primary_records = 0
    missing_count = 0
    review_queue_count = 0

    with open(CLAIM_MATRIX, "w", newline="", encoding="utf-8") as f1, \
         open(CANDIDATE_MATRIX, "w", newline="", encoding="utf-8") as f2, \
         open(DUPLICATE_REGISTER, "w", newline="", encoding="utf-8") as f3, \
         open(REVIEW_QUEUE, "w", newline="", encoding="utf-8") as f4:

        claim_writer = csv.writer(f1)
        cand_writer = csv.writer(f2)
        dup_writer = csv.writer(f3)
        queue_writer = csv.writer(f4)

        claim_writer.writerow([
            "claim_id",
            "subject",
            "gap_type",
            "candidate_document_count",
            "unique_sha256_count",
            "binding_status",
            "final_use_allowed"
        ])

        cand_writer.writerow([
            "claim_id",
            "subject",
            "candidate_path",
            "candidate_sha256",
            "keyword_score",
            "duplicate_status",
            "primary_candidate_path",
            "evidence_status",
            "final_use_allowed"
        ])

        dup_writer.writerow([
            "claim_id",
            "subject",
            "sha256",
            "candidate_path",
            "duplicate_status",
            "primary_candidate_path",
            "final_use_allowed"
        ])

        queue_writer.writerow([
            "review_id",
            "priority",
            "claim_id",
            "subject",
            "review_type",
            "status",
            "candidate_path",
            "sha256",
            "required_action",
            "final_use_allowed"
        ])

        counter = 1

        for row in v893_rows:

            claim_id = row.get("ID", "UNKNOWN")
            subject = row.get("SUBJECT", "UNKNOWN")
            gap = row.get("GAP_TYPE", "UNKNOWN")

            priority = priority_for_gap(claim_id)

            candidates = match_candidates(claim_id, hash_rows)
            dup_status = duplicate_status_for_matches(candidates)

            unique_sha = len(set(c["sha256"] for c in candidates))
            total_matches += len(candidates)

            if not candidates:

                status = "MISSING_EVIDENCE"
                missing_count += 1

                queue_writer.writerow([
                    f"RVW_{counter:04d}",
                    priority,
                    claim_id,
                    subject,
                    "MISSING_EVIDENCE",
                    "HUMAN_REVIEW_REQUIRED",
                    "",
                    "",
                    "Locate external supporting evidence",
                    "NO"
                ])

                review_queue_count += 1
                counter += 1

            else:

                status = "CANDIDATE_MATCHES_REQUIRE_HUMAN_REVIEW"

            claim_writer.writerow([
                claim_id,
                subject,
                gap,
                len(candidates),
                unique_sha,
                status,
                "NO"
            ])

            for c in candidates:

                dstatus, primary = dup_status[(c["sha256"], c["path"])]

                if dstatus == "DUPLICATE_CONTENT":
                    duplicate_records += 1

                elif dstatus == "PRIMARY_CANDIDATE_DUPLICATE_SET":
                    primary_records += 1

                cand_writer.writerow([
                    claim_id,
                    subject,
                    c["path"],
                    c["sha256"],
                    c["keyword_score"],
                    dstatus,
                    primary,
                    "CANDIDATE_ONLY_NOT_APPROVED",
                    "NO"
                ])

                dup_writer.writerow([
                    claim_id,
                    subject,
                    c["sha256"],
                    c["path"],
                    dstatus,
                    primary,
                    "NO"
                ])

                queue_writer.writerow([
                    f"RVW_{counter:04d}",
                    priority,
                    claim_id,
                    subject,
                    "CANDIDATE_DOCUMENT",
                    "HUMAN_REVIEW_REQUIRED",
                    c["path"],
                    c["sha256"],
                    "Validate authenticity and evidence strength",
                    "NO"
                ])

                review_queue_count += 1
                counter += 1

    return {
        "total_matches": total_matches,
        "duplicate_records": duplicate_records,
        "primary_records": primary_records,
        "missing_count": missing_count,
        "review_queue_count": review_queue_count
    }

def write_summary(v893_rows, hash_rows, stats):

    data = {
        "created_utc": utc_now(),
        "system_status": SYSTEM_STATUS,
        "phase": "V897_PHASE_5_HUMAN_REVIEW_QUEUE",
        "v893_rows": len(v893_rows),
        "hash_records": len(hash_rows),
        "candidate_matches": stats["total_matches"],
        "duplicate_records": stats["duplicate_records"],
        "primary_duplicate_set_records": stats["primary_records"],
        "missing_evidence_count": stats["missing_count"],
        "review_queue_count": stats["review_queue_count"],
        "binding_status": "HUMAN_REVIEW_REQUIRED",
        "evidence_approved_count": 0,
        "safe_to_execute_now": "NO",
        "final_use_allowed": "NO"
    }

    with open(SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def main():

    print(SYSTEM_STATUS)
    print("V897 Phase 5 — Human Review Queue")

    v893_rows = load_v893()
    hash_rows = load_hashes()

    stats = build_outputs(v893_rows, hash_rows)

    write_summary(v893_rows, hash_rows, stats)

    print(f"Review queue count: {stats['review_queue_count']}")
    print(f"Missing evidence gaps: {stats['missing_count']}")
    print(f"Candidate matches: {stats['total_matches']}")
    print(f"Output: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
