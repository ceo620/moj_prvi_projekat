#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "=== TITAN V945-V954 EVIDENCE INTAKE STABILIZATION START ==="

mkdir -p 12_LOGS_HASHES 13_IMPORTED_WORKBOOKS 15_EXTERNAL_RESPONSES

# V945 — VOL09 import correction closure
cat > 12_LOGS_HASHES/V945_VOL09_IMPORT_CORRECTION_CLOSURE.json <<'JSON'
{
  "phase": "V945_VOL09_IMPORT_CORRECTION_CLOSURE",
  "status": "VOL09_WORKBOOK_NOT_FOUND",
  "actual_found_files": [
    "TITAN_vE1_VOL09_GRID_FORENSIC_SSOT_SHA256.txt",
    "TITAN_vE1_VOL09_GRID_FORENSIC_SSOT_SEAL.json"
  ],
  "invalid_placeholder_used": "PASTE_FULL_PATH_HERE",
  "delete": "NO",
  "move": "NO",
  "final_use_allowed": "NO"
}
JSON
sha256sum 12_LOGS_HASHES/V945_VOL09_IMPORT_CORRECTION_CLOSURE.json > 12_LOGS_HASHES/V945_VOL09_IMPORT_CORRECTION_CLOSURE_SHA256.txt

# V946 — source pending register
cat > 13_IMPORTED_WORKBOOKS/V946_SOURCE_PENDING_REGISTER.csv <<'CSV'
VOLUME,EXPECTED_SOURCE,STATUS,NEXT_ACTION,FINAL_USE_ALLOWED
VOL09,GRID_CEDIS_WORKBOOK,NOT_FOUND,CREATE_OR_LOCATE_SOURCE,NO
VOL08,CAPEX_SSOT_WORKBOOK,EXISTS_IN_CHAT_EXPORT,IMPORT_IF_NEEDED,NO
VOL07,EVIDENCE_GAP_REGISTER,PARTIAL,REBUILD_WITH_SAFE_METHOD,NO
CSV
sha256sum 13_IMPORTED_WORKBOOKS/V946_SOURCE_PENDING_REGISTER.csv > 12_LOGS_HASHES/V946_SOURCE_PENDING_REGISTER_SHA256.txt

# V947 — external response intake folders
mkdir -p 15_EXTERNAL_RESPONSES/CEDIS 15_EXTERNAL_RESPONSES/MUNICIPALITY_TUZI 15_EXTERNAL_RESPONSES/ESG 15_EXTERNAL_RESPONSES/EPC 15_EXTERNAL_RESPONSES/BANKS
cat > 15_EXTERNAL_RESPONSES/V947_EXTERNAL_RESPONSE_FOLDER_MAP.csv <<'CSV'
FOLDER,PURPOSE,STATUS
CEDIS,Grid capacity technical conditions reconstruction timeline,WAITING
MUNICIPALITY_TUZI,Local infrastructure and support letters,WAITING
ESG,ESIA DNSH Taxonomy HSE documents,WAITING
EPC,Equipment and civil works quotations,WAITING
BANKS,Debt terms DSCR tenor security package,WAITING
CSV
sha256sum 15_EXTERNAL_RESPONSES/V947_EXTERNAL_RESPONSE_FOLDER_MAP.csv > 12_LOGS_HASHES/V947_EXTERNAL_RESPONSE_FOLDER_MAP_SHA256.txt

# V948 — CEDIS intake checklist
cat > 15_EXTERNAL_RESPONSES/CEDIS/V948_CEDIS_INTAKE_CHECKLIST.md <<'MD'
# V948 — CEDIS Intake Checklist

Required:
- written technical conditions
- available capacity statement
- reconstruction timeline
- connection procedure
- cost allocation
- reservation or prioritization possibility

Status:
PENDING_EXTERNAL_RESPONSE

Control:
NO_GRID_READY_CLAIM
NO_FINAL_USE
MD
sha256sum 15_EXTERNAL_RESPONSES/CEDIS/V948_CEDIS_INTAKE_CHECKLIST.md > 12_LOGS_HASHES/V948_CEDIS_INTAKE_CHECKLIST_SHA256.txt

# V949 — CAPEX evidence intake checklist
cat > 15_EXTERNAL_RESPONSES/EPC/V949_CAPEX_EVIDENCE_INTAKE_CHECKLIST.md <<'MD'
# V949 — CAPEX Evidence Intake Checklist

Required:
- equipment quotations
- civil works BoQ
- solar EPC offer
- grid works estimate
- soft costs evidence
- contingency methodology
- VAT / FX / currency basis
- payment schedule

Status:
CAPEX_UNRESOLVED

Control:
NO_FINAL_CAPEX
NO_FINAL_USE
MD
sha256sum 15_EXTERNAL_RESPONSES/EPC/V949_CAPEX_EVIDENCE_INTAKE_CHECKLIST.md > 12_LOGS_HASHES/V949_CAPEX_EVIDENCE_INTAKE_CHECKLIST_SHA256.txt

# V950 — ESG intake checklist
cat > 15_EXTERNAL_RESPONSES/ESG/V950_ESG_INTAKE_CHECKLIST.md <<'MD'
# V950 — ESG Intake Checklist

Required:
- ESIA screening
- DNSH review
- EU Taxonomy screening
- minimum safeguards review
- HSE plan
- waste/water/noise/air review
- permit dependency map

Status:
ESG_ASSESSMENT_PENDING

Control:
NO_ESG_COMPLIANT_CLAIM
NO_FINAL_USE
MD
sha256sum 15_EXTERNAL_RESPONSES/ESG/V950_ESG_INTAKE_CHECKLIST.md > 12_LOGS_HASHES/V950_ESG_INTAKE_CHECKLIST_SHA256.txt

# V951 — Bank intake checklist
cat > 15_EXTERNAL_RESPONSES/BANKS/V951_BANK_DEBT_INTAKE_CHECKLIST.md <<'MD'
# V951 — Bank / DFI Debt Intake Checklist

Required:
- indicative term sheet
- interest margin
- tenor
- grace period
- DSCR covenant
- security package
- conditions precedent
- equity requirement

Status:
DEBT_CAPACITY_PENDING

Control:
NO_LENDER_READY_CLAIM
NO_FINAL_USE
MD
sha256sum 15_EXTERNAL_RESPONSES/BANKS/V951_BANK_DEBT_INTAKE_CHECKLIST.md > 12_LOGS_HASHES/V951_BANK_DEBT_INTAKE_CHECKLIST_SHA256.txt

# V952 — consolidated blocker tracker
cat > 12_LOGS_HASHES/V952_CONSOLIDATED_BLOCKER_TRACKER.csv <<'CSV'
BLOCKER,STATUS,REQUIRED_NEXT_DOCUMENT,OWNER_CLASS
GRID,PENDING,CEDIS written response,CEDIS
CAPEX,UNRESOLVED,EPC quotations and line-item bridge,Finance/EPC
ESG,PENDING,ESIA screening and DNSH,ESG consultant
PERMITS,PARTIAL,Permit roadmap,Legal/Municipality
OFFTAKE,PENDING,Signed LOI or offtake,Commercial
DEBT,PENDING,Indicative term sheet,Bank/DFI
VOL09_WORKBOOK,NOT_FOUND,Create or locate workbook,Control Tower
CSV
sha256sum 12_LOGS_HASHES/V952_CONSOLIDATED_BLOCKER_TRACKER.csv > 12_LOGS_HASHES/V952_CONSOLIDATED_BLOCKER_TRACKER_SHA256.txt

# V953 — safe operations policy
cat > 12_LOGS_HASHES/V953_SAFE_OPERATIONS_POLICY.md <<'MD'
# V953 — Safe Operations Policy

Allowed:
- copy only
- hash only
- register only
- create pending logs
- create intake checklists

Blocked:
- delete
- move
- overwrite evidence
- claim validation
- claim lender-ready
- claim bankability
- claim final use

Status:
SYSTEM_RED_STEP102_LOCKED
MD
sha256sum 12_LOGS_HASHES/V953_SAFE_OPERATIONS_POLICY.md > 12_LOGS_HASHES/V953_SAFE_OPERATIONS_POLICY_SHA256.txt

# V954 — batch closure seal
cat > 12_LOGS_HASHES/V954_EVIDENCE_INTAKE_STABILIZATION_CLOSURE.json <<'JSON'
{
  "phase": "V954_EVIDENCE_INTAKE_STABILIZATION_CLOSURE",
  "closed_modules": ["V945","V946","V947","V948","V949","V950","V951","V952","V953"],
  "system_status": "SYSTEM RED — STEP102 LOCKED",
  "final_use_allowed": "NO",
  "step103_allowed": "NO",
  "delete": "NO",
  "move": "NO",
  "control_decision": "EVIDENCE_INTAKE_STABILIZED_PENDING_EXTERNAL_DOCUMENTS"
}
JSON
sha256sum 12_LOGS_HASHES/V954_EVIDENCE_INTAKE_STABILIZATION_CLOSURE.json > 12_LOGS_HASHES/V954_EVIDENCE_INTAKE_STABILIZATION_CLOSURE_SHA256.txt

echo "=== TITAN V945-V954 EVIDENCE INTAKE STABILIZATION COMPLETE ==="
