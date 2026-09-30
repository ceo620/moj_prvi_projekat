#!/data/data/com.termux/files/usr/bin/sh
# ANDROID_SCRIPT_HEALING_DOCTRINE_V3
# KEYWORD=VOLIM_TE
# ORIGINAL_IS_SACRED=YES
# REPAIR_ON_COPY_ONLY=YES
# SAFE_WRAPPER_ONLY=YES
# ID=H021
# ORIGINAL_NAME=token_harvest_full_titan1.py
# ORIGINAL_PATH=/data/data/com.termux/files/home/ANDROID_ARCHIVE_KNOWLEDGE_20260702_200007/02_REVIEW_ONLY_EXTRACTED/53a21c08c3c46142b0167d055300ef128f16274d35ed932599302421e4784f09_53a21c08c3c46142b0167d055300ef128f16274d35ed932599302421e4784f09_VDR__99_Index_and_Control__Android__uredjaj-20260513T002438Z-3-001.zip/Android uredjaj/TITAN_SCRIPT_MODULE_INTAKE/01_RAW_SCRIPTS/token_harvest_full_titan1.py
# ORIGINAL_SHA256=b5d2a60cd5e1f0d2ed835ce07c3cc7c255d2953e1fbb78d0fdea6ab32a06e135
# HUMAN_GATE=ACTIVE

HUMAN_GATE="${HUMAN_GATE:-BLOCKED}"
if [ "$HUMAN_GATE" != "ALLOW_RUNTIME" ]; then
  echo "HUMAN_GATE_BLOCKED: Android V3 healed wrapper is static-only."
  exit 88
fi

echo "RUNTIME_NOT_IMPLEMENTED_YET: original payload preserved below for review."
exit 88

: <<'__ANDROID_VOLIM_TE_V3_PAYLOAD_H021_20260703_015331__'
from pathlib import Path
import json
from datetime import datetime

root = Path("/storage/emulated/0/Download/TITAN_ECOSYSTEM/TITAN1_SYSTEM")
output = root / "99_MASTER_CONTROL" / "TITAN1_FULL_TOKEN_HARVEST.json"

signals = {
    "timestamp": datetime.now().isoformat(),
    "project": "TITAN 1",
    "files_processed": 0,
    "key_signals": {
        "CAPEX": [],
        "Power_MW": [],
        "Location_Tuzi_KAP": [],
        "Company_ArsMetal": [],
        "Legal_CEDIS_Opstina": [],
        "Partners_dasmetal": [],
        "Infrastructure_Grid": [],
        "Vertical_Chain_TITAN123": []
    },
    "raw_extracted": {}
}

for file_path in root.rglob("*"):
    if not file_path.is_file():
        continue
    if file_path.suffix.lower() not in [".docx", ".pdf", ".txt", ".md", ".json"]:
        continue

    try:
        signals["files_processed"] += 1
        content = ""

        if file_path.suffix.lower() == ".docx":
            from docx import Document
            doc = Document(file_path)
            content = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        else:
            content = file_path.read_text(encoding="utf-8", errors="ignore")

        signals["raw_extracted"][str(file_path.relative_to(root))] = content[:3000]

        text_lower = content.lower()

        # Token harvest za TITAN 1
        if any(x in text_lower for x in ["18,2", "18.2", "18200000", "18.2 milion"]):
            signals["key_signals"]["CAPEX"].append(str(file_path.relative_to(root)))
        if any(x in text_lower for x in ["12,5", "12.5", "12500", "12.5 mw"]):
            signals["key_signals"]["Power_MW"].append(str(file_path.relative_to(root)))
        if "tuzi" in text_lower and "kap" in text_lower:
            signals["key_signals"]["Location_Tuzi_KAP"].append(str(file_path.relative_to(root)))
        if "ars metal" in text_lower or "arsmetal" in text_lower:
            signals["key_signals"]["Company_ArsMetal"].append(str(file_path.relative_to(root)))
        if "dasmetal" in text_lower or "ads metal" in text_lower:
            signals["key_signals"]["Partners_dasmetal"].append(str(file_path.relative_to(root)))
        if any(x in text_lower for x in ["cedis", "opština tuzi", "zakon o energetici", "urbanističko-tehnički"]):
            signals["key_signals"]["Legal_CEDIS_Opstina"].append(str(file_path.relative_to(root)))
        if any(x in text_lower for x in ["infrastruktura", "rekonstrukcija", "priključak", "mreža"]):
            signals["key_signals"]["Infrastructure_Grid"].append(str(file_path.relative_to(root)))
        if any(x in text_lower for x in ["titan 1", "titan1", "vertikalna", "titan 2", "titan 3"]):
            signals["key_signals"]["Vertical_Chain_TITAN123"].append(str(file_path.relative_to(root)))

    except Exception:
        pass

with open(output, "w", encoding="utf-8") as f:
    json.dump(signals, f, ensure_ascii=False, indent=2)

print("✅ FULL TOKEN HARVEST ZA TITAN 1 ZAVRŠEN")
print(f"   Procesirano fajlova: {signals['files_processed']}")
print(f"   Rezultat: {output.name}")
print("\nKljučni signali pronađeni:")
for category, files in signals["key_signals"].items():
    if files:
        print(f"   • {category}: {len(files)} fajlova")
__ANDROID_VOLIM_TE_V3_PAYLOAD_H021_20260703_015331__
