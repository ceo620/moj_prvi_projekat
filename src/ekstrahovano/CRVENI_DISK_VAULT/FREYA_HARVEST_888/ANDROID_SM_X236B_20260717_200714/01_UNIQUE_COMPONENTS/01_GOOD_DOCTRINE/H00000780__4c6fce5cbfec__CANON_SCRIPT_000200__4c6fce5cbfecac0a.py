# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

from pathlib import Path
import hashlib
import csv
import re
from datetime import datetime

ROOT = Path("/storage/emulated/0/Download/TITAN_ECOSYSTEM/TITAN1_SYSTEM")
OUT = ROOT / "99_MASTER_CONTROL"
OUT.mkdir(parents=True, exist_ok=True)

CROSSWALK = OUT / "TITAN1_TOKEN_TO_DOCUMENT_CROSSWALK.md"
EXPECTED_CROSSWALK_SHA256 = "350ed9163790f33e4fdeea6e1bc9d1385357f3fcb8d567e76acf789e25f1d5c0"

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def safe_text(path):
    try:
        return path.read_text(errors="ignore")
    except Exception:
        return ""

crosswalk_status = "PASS" if CROSSWALK.exists() and sha256(CROSSWALK) == EXPECTED_CROSSWALK_SHA256 else "FAIL"

patterns = {
    "CAPEX_18_2": re.compile(r"18[,.]2|18\s*200\s*000|18\.200\.000", re.I),
    "CAPEX_43_5_RISK": re.compile(r"43[,.]5|43\s*500\s*000|43\.500\.000", re.I),
    "POWER_12_5": re.compile(r"12[,.]5\s*MW|12[,.]5", re.I),
    "TITAN1": re.compile(r"TITAN\s*1|kazana|tankova|transformatorskih kazana", re.I),
    "TITAN2_3_RISK": re.compile(r"TITAN\s*2|TITAN\s*3|do\s*5\s*MVA|preko\s*5\s*MVA|power transform", re.I),
    "ARS": re.compile(r"Ars Metal Industries|ARS METAL", re.I),
    "ADS": re.compile(r"ADS Metal|adsmetal", re.I),
    "TUZI_KAP": re.compile(r"Tuzi|KAP", re.I),
    "CEDIS": re.compile(r"CEDIS|elektrodistribut", re.I),
}

rows = []
for path in sorted(ROOT.rglob("*")):
    if not path.is_file():
        continue

    rel = str(path.relative_to(ROOT))
    ext = path.suffix.lower()
    digest = sha256(path)
    text = safe_text(path) if ext in [".txt", ".md", ".csv", ".py", ".json"] else ""

    hits = {k: bool(v.search(text)) for k, v in patterns.items()} if text else {k: False for k in patterns}

    if "99_MASTER_CONTROL" in rel:
        status = "CONTROL_REGISTER"
    elif "01_ACTIVE" in rel:
        status = "ACTIVE_OUTPUT_REVIEW_REQUIRED"
    elif "02_ATTACHMENTS" in rel or "ATTACHMENTS" in rel:
        status = "ATTACHMENT_REVIEW_REQUIRED"
    elif hits["TITAN2_3_RISK"]:
        status = "RISK_TITAN2_3_BLEEDTHROUGH"
    elif hits["CAPEX_43_5_RISK"]:
        status = "RISK_CAPEX_43_5_PRESENT"
    elif hits["CAPEX_18_2"] or hits["TITAN1"] or hits["CEDIS"] or hits["TUZI_KAP"]:
        status = "POTENTIALLY_ALIGNED_TITAN1"
    else:
        status = "NO_TEXT_OR_PENDING_MANUAL_REVIEW"

    rows.append({
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "crosswalk_sha256_status": crosswalk_status,
        "file": rel,
        "sha256": digest,
        "status": status,
        **{k: "YES" if v else "NO" for k, v in hits.items()}
    })

csv_path = OUT / "TITAN1_CROSSWALK_HARMONIZATION_AUDIT.csv"
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["timestamp"])
    writer.writeheader()
    writer.writerows(rows)

summary_path = OUT / "TITAN1_CROSSWALK_HARMONIZATION_SUMMARY.md"
total = len(rows)
risk_43 = sum(r["status"] == "RISK_CAPEX_43_5_PRESENT" for r in rows)
risk_23 = sum(r["status"] == "RISK_TITAN2_3_BLEEDTHROUGH" for r in rows)
pending = sum(r["status"] == "NO_TEXT_OR_PENDING_MANUAL_REVIEW" for r in rows)

summary_path.write_text(f"""# TITAN1_CROSSWALK_HARMONIZATION_SUMMARY

CROSSWALK_SHA256_STATUS:
{crosswalk_status}

EXPECTED_CROSSWALK_SHA256:
{EXPECTED_CROSSWALK_SHA256}

TOTAL_FILES_SCANNED:
{total}

RISK_CAPEX_43_5_PRESENT:
{risk_43}

RISK_TITAN2_3_BLEEDTHROUGH:
{risk_23}

NO_TEXT_OR_PENDING_MANUAL_REVIEW:
{pending}

FINAL RULE:
This audit does not prove every PDF/DOCX/XLSX was fully interpreted. It proves inventory, hashing, text-scan risk flags, and crosswalk alignment status. Binary Office/PDF files require manual or extractor-based validation.

FINAL STATUS:
HARMONIZATION AUDIT CREATED.
""", encoding="utf-8")

print("CROSSWALK_STATUS:", crosswalk_status)
print("AUDIT_CSV:", csv_path)
print("SUMMARY:", summary_path)
print("TOTAL_FILES:", total)
print("RISK_CAPEX_43_5_PRESENT:", risk_43)
print("RISK_TITAN2_3_BLEEDTHROUGH:", risk_23)
print("PENDING_MANUAL_REVIEW:", pending)
