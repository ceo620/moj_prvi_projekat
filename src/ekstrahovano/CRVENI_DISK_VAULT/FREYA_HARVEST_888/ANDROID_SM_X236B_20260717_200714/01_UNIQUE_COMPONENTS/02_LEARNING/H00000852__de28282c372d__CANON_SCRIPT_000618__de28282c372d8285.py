# FREYA_DIRECT_REPAIR_RUNTIME_GATE
import os as _freya_os, sys as _freya_sys
if _freya_os.environ.get("HUMAN_GATE_RUNTIME_APPROVED") != "YES":
    print("BLOCKED_BY_FREYA_HUMAN_GATE: runtime not approved")
    _freya_sys.exit(0)
# END_FREYA_DIRECT_REPAIR_RUNTIME_GATE

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
