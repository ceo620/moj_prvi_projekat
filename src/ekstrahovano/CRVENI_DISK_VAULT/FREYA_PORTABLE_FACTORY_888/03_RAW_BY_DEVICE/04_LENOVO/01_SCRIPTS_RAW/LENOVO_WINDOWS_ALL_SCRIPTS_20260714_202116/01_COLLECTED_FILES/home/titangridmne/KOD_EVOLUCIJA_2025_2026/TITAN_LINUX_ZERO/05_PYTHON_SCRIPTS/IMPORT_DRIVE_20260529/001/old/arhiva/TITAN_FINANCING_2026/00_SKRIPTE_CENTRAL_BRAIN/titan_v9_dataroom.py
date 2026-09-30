import os

BASE = r"C:\Users\Lenovo\Desktop\TITAN_DATA_ROOM"

folders = [
    "01_PROJECT_OVERVIEW",
    "02_FINANCIALS",
    "03_TECHNICAL",
    "04_REGULATORY",
    "05_MARKET",
    "06_ESG",
    "07_RISK",
    "08_LEGAL",
    "09_CONSTRUCTION",
    "10_OPERATIONS",
    "99_ADMIN"
]

subfolders = {
    "02_FINANCIALS": ["MODEL", "CAPEX", "OPEX", "DSCR"],
    "04_REGULATORY": ["LICENSES", "TAX", "COMPLIANCE"],
    "07_RISK": ["SCENARIOS", "SENSITIVITY"],
    "08_LEGAL": ["CONTRACTS", "OWNERSHIP"],
}

# CREATE MAIN STRUCTURE
for folder in folders:
    path = os.path.join(BASE, folder)
    os.makedirs(path, exist_ok=True)

    if folder in subfolders:
        for sub in subfolders[folder]:
            os.makedirs(os.path.join(path, sub), exist_ok=True)

# CREATE INDEX FILE
index_path = os.path.join(BASE, "99_ADMIN", "DATA_ROOM_INDEX.txt")

with open(index_path, "w") as f:
    f.write("TITAN DATA ROOM STRUCTURE\n\n")
    for folder in folders:
        f.write(folder + "\n")

print("✅ DATA ROOM CREATED:", BASE)