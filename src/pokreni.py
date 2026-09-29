import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import requests
from config.podesavanja import DEBIAN_URL

print("Sistem je spreman! Provera internet konekcije...")
odgovor = requests.get(DEBIAN_URL)
print(f"Status odgovora Debian servera: {odgovor.status_code}")
