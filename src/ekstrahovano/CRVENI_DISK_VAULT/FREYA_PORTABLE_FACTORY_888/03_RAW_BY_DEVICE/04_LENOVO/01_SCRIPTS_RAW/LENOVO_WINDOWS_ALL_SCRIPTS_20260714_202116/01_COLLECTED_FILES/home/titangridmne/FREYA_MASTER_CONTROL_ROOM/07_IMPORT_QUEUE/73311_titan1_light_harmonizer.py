import os, re, json, hashlib, glob
from datetime import datetime

# === TITAN 1 ACTIVE TOKEN BASELINE (kanonski) ===
BASELINE = {
    "project_id": "TITAN_1",
    "active_capex_eur": 18200000,
    "active_capex_label": "18,2 miliona EUR",
    "blocked_tokens": [
        r"43\.5M", r"51\.4M", r"3 factories", r"TITAN 2", r"TITAN 3",
        r"38%", r"25% grant", r"lender ready", r"bankable",
        r"state obligation", r"approved financing", r"power transformers",
        r"do 5 MVA", r"preko 5 MVA"
    ]
}

REPORT_DIR = f"/root/Documents/TITAN1_HARMONIZED_REPORT_{datetime.now().strftime('%Y%m%d_%H%M')}"
os.makedirs(REPORT_DIR, exist_ok=True)

print("🔒 TITAN 1 LIGHT HARMONIZER — ACTIVE SCOPE ONLY")
print("   Status: ACTIVE_TITAN1_SCOPE_CANONICAL_WORKING_BASELINE\n")

titan_folder = "/root/Documents/TITAN FINAL"
bleedthrough = []

for file_path in glob.glob(f"{titan_folder}/**/*.*", recursive=True):
    if file_path.endswith(('.xlsx', '.pptx', '.pdf')):
        continue
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            for pattern in BASELINE["blocked_tokens"]:
                if re.search(pattern, content, re.IGNORECASE):
                    bleedthrough.append({
                        "file": file_path,
                        "blocked_token": pattern,
                        "status": "BLEEDTHROUGH_DETECTED"
                    })
                    print(f"   ⚠️  BLEEDTHROUGH → {os.path.basename(file_path)} : {pattern}")
    except:
        pass

# Sačuvaj izvještaj
report = {
    "timestamp": datetime.now().isoformat(),
    "baseline_capex": BASELINE["active_capex_label"],
    "bleedthrough_found": len(bleedthrough),
    "bleedthrough_details": bleedthrough,
    "status": "CLEAN" if not bleedthrough else "HARMONIZATION_REQUIRED"
}

with open(f"{REPORT_DIR}/TITAN1_HARMONIZATION_REPORT.json", "w") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(f"\n✅ Harmonizacija završena!")
print(f"   Report folder: {REPORT_DIR}")
print(f"   Bleedthrough pronađen: {len(bleedthrough)}")
print("\nSljedeći korak: reci mi da li želiš automatsko čišćenje bleedthrough-a ili kreiranje čistog TITAN1_ONLY generatora.")
