from __future__ import annotations

import csv
import json
from pathlib import Path
from datetime import datetime, timezone

SYSTEM_STATUS = "SYSTEM RED — STEP102 LOCKED — NO FINAL USE"

ROOT = Path.home() / "TITAN_FULL_RAG"
V897_OUTPUT = ROOT / "V897_OUTPUT"

CANDIDATES = V897_OUTPUT / "TITAN_EVIDENCE_CANDIDATE_MATCHES.csv"
REVIEW_QUEUE = V897_OUTPUT / "TITAN_HUMAN_REVIEW_QUEUE.csv"

OUTPUT_DIR = ROOT / "V898_OUTPUT"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SCORING_REGISTER = OUTPUT_DIR / "TITAN_EVIDENCE_SCORING_L0_L5.csv"
SUMMARY_JSON = OUTPUT_DIR / "TITAN_EVIDENCE_SCORING_SUMMARY.json"

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def load_csv(path: Path):
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return list(csv.DictReader(f))

def score_candidate(row):
    path = row.get("candidate_path", "").lower()
    duplicate_status = row.get("duplicate_status", "")
    evidence_status = row.get("evidence_status", "")

    if not path:
        return "L0", "NO_DOCUMENT"

    if duplicate_status == "DUPLICATE_CONTENT":
        return "L1", "DUPLICATE_COPY_ONLY"

    if evidence_status == "CANDIDATE_ONLY_NOT_APPROVED":
        if path.endswith(".docx"):
            return "L2", "INTERNAL_DOCUMENT_CANDIDATE"
        if path.endswith(".pdf"):
            return "L2", "PDF_CANDIDATE_REQUIRES_REVIEW"
        return "L1", "LOW_STRENGTH_CANDIDATE"

    return "L0", "UNBOUND"

def build_scoring(candidates):
    with open(SCORING_REGISTER, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow([
            "claim_id",
            "subject",
            "candidate_path",
            "candidate_sha256",
            "duplicate_status",
            "preliminary_score",
            "score_reason",
            "evidence_approved",
            "final_use_allowed"
        ])

        for row in candidates:
            score, reason = score_candidate(row)

            writer.writerow([
                row.get("claim_id", ""),
                row.get("subject", ""),
                row.get("candidate_path", ""),
                row.get("candidate_sha256", ""),
                row.get("duplicate_status", ""),
                score,
                reason,
                "NO",
                "NO"
            ])

def write_summary(candidates, review_queue):
    scores = {"L0": 0, "L1": 0, "L2": 0, "L3": 0, "L4": 0, "L5": 0}

    for row in candidates:
        score, _ = score_candidate(row)
        scores[score] += 1

    data = {
        "created_utc": utc_now(),
        "system_status": SYSTEM_STATUS,
        "phase": "V898_EVIDENCE_SCORING_L0_L5",
        "candidate_records": len(candidates),
        "review_queue_records": len(review_queue),
        "score_counts": scores,
        "highest_score": max([k for k, v in scores.items() if v > 0], default="L0"),
        "evidence_approved_count": 0,
        "l4_l5_count": scores["L4"] + scores["L5"],
        "binding_status": "PRELIMINARY_SCORING_ONLY",
        "safe_to_execute_now": "NO",
        "final_use_allowed": "NO"
    }

    with open(SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def main():
    print(SYSTEM_STATUS)
    print("V898 Evidence Scoring L0-L5")

    candidates = load_csv(CANDIDATES)
    review_queue = load_csv(REVIEW_QUEUE)

    build_scoring(candidates)
    write_summary(candidates, review_queue)

    print(f"Candidate records: {len(candidates)}")
    print(f"Review queue records: {len(review_queue)}")
    print(f"Output: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
