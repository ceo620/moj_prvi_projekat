import os, re, csv, hashlib, zipfile, datetime

roots = [
    "/mnt/c/Users/titangrid.info/Desktop",
    "/mnt/c/Users/titangrid.info/Documents",
    "/mnt/c/Users/titangrid.info/Downloads",
    "/mnt/c/Users/titangrid.info/OneDrive",
]

exclude_parts = [
    "TITAN_GRID_CEO_OUTREACH_20260702",
    "FREYA_1150_ENTITY_BUSINESS_STRATEGIES",
    "FREYA_160_SIGNAL_PAPER_FACTORY",
    "FREYA_150_FROM_MAC_REVIEW_ONLY",
    "FREYA_LENOVO_RECEIVER_DROPZONES",
    "99_DAEMON_RUN_GATE",
    "node_modules",
    ".git",
    "__pycache__",
    "AppData",
    "Cache",
]

allowed_ext = {
    ".csv", ".tsv", ".txt", ".md", ".json", ".vcf", ".html", ".htm",
    ".eml", ".docx", ".xlsx", ".xlsm", ".pdf"
}

email_re = re.compile(rb"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")

reg_path = os.environ["REG"]
emails_path = os.environ["EMAILS"]
top_path = os.environ["TOP"]

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def read_bytes_for_scan(path, ext):
    try:
        if ext in {".docx", ".xlsx", ".xlsm"}:
            out = []
            with zipfile.ZipFile(path) as z:
                for name in z.namelist():
                    low = name.lower()
                    if low.endswith((".xml", ".rels", ".txt")):
                        try:
                            out.append(z.read(name)[:2_000_000])
                        except Exception:
                            pass
            return b"\n".join(out)
        with open(path, "rb") as f:
            return f.read(5_000_000)
    except Exception:
        return b""

def business_hint(path, email):
    low = (path + " " + email).lower()
    if any(x in low for x in ["eib", "ebrd", "ifc", "kfw", "worldbank", "world-bank", "bank", "lender", "invest", "fund"]):
        return "LENDER_INVESTOR"
    if any(x in low for x in ["supplier", "vendor", "procurement", "purchase", "dobavljac", "manufacturer"]):
        return "SUPPLIER_PROCUREMENT"
    if any(x in low for x in ["buyer", "customer", "client", "sales", "kupac", "distributor"]):
        return "CUSTOMER_BUYER_SALES"
    if any(x in low for x in ["ceo", "director", "board", "management", "executive"]):
        return "EXECUTIVE_CONTACT"
    if any(x in low for x in ["ars", "metal", "turkey", "ankara", "podgorica", "montenegro"]):
        return "ARS_METAL_RELEVANT"
    if any(x in low for x in ["audit", "due", "diligence", "data room", "dataroom", "review"]):
        return "DATA_ROOM_DD_REVIEW"
    return "GENERAL_CONTACT"

def score_row(hint, ext, email):
    score = 10
    score += {
        "LENDER_INVESTOR": 100,
        "DATA_ROOM_DD_REVIEW": 95,
        "EXECUTIVE_CONTACT": 90,
        "ARS_METAL_RELEVANT": 85,
        "SUPPLIER_PROCUREMENT": 70,
        "CUSTOMER_BUYER_SALES": 65,
        "GENERAL_CONTACT": 40,
    }.get(hint, 20)
    if ext in [".csv", ".tsv", ".xlsx", ".xlsm", ".vcf"]:
        score += 30
    if not any(bad in email.lower() for bad in ["noreply", "no-reply", "donotreply", "example.com"]):
        score += 20
    return score

file_rows = []
email_rows = []
seen_emails = set()
file_id = 0

for root in roots:
    if not os.path.isdir(root):
        continue
    for dirpath, dirnames, filenames in os.walk(root):
        if any(part in dirpath for part in exclude_parts):
            dirnames[:] = []
            continue
        for fn in filenames:
            path = os.path.join(dirpath, fn)
            ext = os.path.splitext(fn)[1].lower()
            if ext not in allowed_ext:
                continue
            try:
                size = os.path.getsize(path)
                if size > 50_000_000:
                    continue
                mtime = datetime.datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M:%S")
                sha = sha256_file(path)
                data = read_bytes_for_scan(path, ext)
                found = sorted({m.decode("utf-8", "ignore") for m in email_re.findall(data)})
                if not found:
                    continue
                file_id += 1
                item_id = f"EMAIL_SOURCE_{file_id:05d}"
                file_rows.append([item_id, path, ext, str(size), mtime, sha, str(len(found)), "HAS_EMAILS_REVIEW_ONLY_NO_SEND"])
                for email in found:
                    key = email.lower()
                    if key in seen_emails:
                        continue
                    seen_emails.add(key)
                    hint = business_hint(path, email)
                    score = score_row(hint, ext, email)
                    email_rows.append([email, hint, str(score), item_id, path, "RECIPIENT_NOT_CONFIRMED_NO_SEND"])
            except Exception:
                continue

email_rows.sort(key=lambda r: int(r[2]), reverse=True)

with open(reg_path, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(["ITEM_ID","PATH","EXT","SIZE_BYTES","MTIME","SHA256","EMAIL_COUNT","SAFE_STATUS"])
    w.writerows(file_rows)

with open(emails_path, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(["EMAIL","BUSINESS_HINT","SCORE","SOURCE_ITEM_ID","SOURCE_PATH","SAFE_STATUS"])
    w.writerows(email_rows)

with open(top_path, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(["RANK","EMAIL","BUSINESS_HINT","SCORE","SOURCE_ITEM_ID","SOURCE_PATH","SAFE_STATUS"])
    for i, row in enumerate(email_rows[:50], 1):
        w.writerow([i] + row)
