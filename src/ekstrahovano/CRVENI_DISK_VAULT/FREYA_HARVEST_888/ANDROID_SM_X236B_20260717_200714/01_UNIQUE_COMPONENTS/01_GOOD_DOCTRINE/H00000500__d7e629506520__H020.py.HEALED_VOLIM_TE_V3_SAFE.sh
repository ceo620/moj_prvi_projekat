#!/data/data/com.termux/files/usr/bin/sh
# ANDROID_SCRIPT_HEALING_DOCTRINE_V3
# KEYWORD=VOLIM_TE
# ORIGINAL_IS_SACRED=YES
# REPAIR_ON_COPY_ONLY=YES
# SAFE_WRAPPER_ONLY=YES
# ID=H020
# ORIGINAL_NAME=token_harvest_all_documents.py
# ORIGINAL_PATH=/data/data/com.termux/files/home/ANDROID_ARCHIVE_KNOWLEDGE_20260702_200007/02_REVIEW_ONLY_EXTRACTED/53a21c08c3c46142b0167d055300ef128f16274d35ed932599302421e4784f09_53a21c08c3c46142b0167d055300ef128f16274d35ed932599302421e4784f09_VDR__99_Index_and_Control__Android__uredjaj-20260513T002438Z-3-001.zip/Android uredjaj/TITAN_SCRIPT_MODULE_INTAKE/01_RAW_SCRIPTS/token_harvest_all_documents.py
# ORIGINAL_SHA256=b4e13935efa214579594e8b236e45c6553463bd8d4263fd0db4de997a7997a68
# HUMAN_GATE=ACTIVE

HUMAN_GATE="${HUMAN_GATE:-BLOCKED}"
if [ "$HUMAN_GATE" != "ALLOW_RUNTIME" ]; then
  echo "HUMAN_GATE_BLOCKED: Android V3 healed wrapper is static-only."
  exit 88
fi

echo "RUNTIME_NOT_IMPLEMENTED_YET: original payload preserved below for review."
exit 88

: <<'__ANDROID_VOLIM_TE_V3_PAYLOAD_H020_20260703_015331__'
import os
from pathlib import Path
import json
from datetime import datetime

root = Path("/storage/emulated/0/Download/TITAN_ECOSYSTEM/TITAN1_SYSTEM")
output = root / "99_MASTER_CONTROL" / "TITAN1_TOKEN_HARVEST.json"
signals = {
    "timestamp": datetime.now().isoformat(),
    "project": "TITAN 1",
    "files_processed": 0,
    "key_signals": {
        "CAPEX": [],
        "Power": [],
        "Location": [],
        "Company": [],
        "Legal": [],
        "Infrastructure": [],
        "Partners": [],
        "Risks": []
    },
    "raw_extracted": {}
}

for file_path in root.rglob("*"):
    if file_path.is_file() and file_path.suffix.lower() in [".docx", ".pdf", ".txt", ".md", ".xlsx"]:
        try:
            signals["files_processed"] += 1
            content = ""
            if file_path.suffix.lower() == ".docx":
                from docx import Document
                doc = Document(file_path)
                content = "\n".join([para.text for para in doc.paragraphs])
            elif file_path.suffix.lower() == ".pdf":
                content = f"[PDF content not extracted - {file_path.name}]"
            else:
                content = file_path.read_text(encoding="utf-8", errors="ignore")

            signals["raw_extracted"][str(file_path)] = content[:2000]  # first 2000 chars for safety

            # Token harvest
            text = content.lower()
            if "18,2" in text or "18.2" in text or "18200000" in text:
                signals["key_signals"]["CAPEX"].append(str(file_path))
            if "12,5" in text or "12.5" in text or "12500" in text or "12.5 mw" in text:
                signals["key_signals"]["Power"].append(str(file_path))
            if "tuzi" in text and "kap" in text:
                signals["key_signals"]["Location"].append(str(file_path))
            if "ars metal" in text or "dasmetal" in text:
                signals["key_signals"]["Company"].append(str(file_path))
            if "zakon" in text or "cedis" in text or "ipard" in text or "just transition" in text:
                signals["key_signals"]["Legal"].append(str(file_path))

        except Exception as e:
            pass

with open(output, "w", encoding="utf-8") as f:
    json.dump(signals, f, ensure_ascii=False, indent=2)

print("✅ TOKEN HARVEST ZAVRŠEN")
print(f"   Procesirano fajlova: {signals['files_processed']}")
print(f"   Rezultat: {output}")
__ANDROID_VOLIM_TE_V3_PAYLOAD_H020_20260703_015331__
