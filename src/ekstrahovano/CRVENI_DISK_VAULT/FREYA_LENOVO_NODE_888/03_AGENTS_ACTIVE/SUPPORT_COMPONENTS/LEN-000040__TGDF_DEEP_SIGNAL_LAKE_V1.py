import os, re, sys, json, time, html, zipfile, hashlib, shutil, subprocess, heapq
from pathlib import Path

HOME = Path.home()
RUN_ID = time.strftime("%Y%m%d_%H%M%S")
FACTORY = HOME / "TITAN_GRID_DOCUMENT_FACTORY"

DIRS = {
    "CONTROL": FACTORY / "00_CONTROL",
    "IDENTITY": FACTORY / "01_IDENTITY_AND_MEMORANDUM",
    "LAKE": FACTORY / "11_DEEP_SIGNAL_LAKE",
    "TEXT": FACTORY / "11_DEEP_SIGNAL_LAKE" / "TEXT_EXTRACT",
    "REPORTS": FACTORY / "11_DEEP_SIGNAL_LAKE" / "REPORTS",
    "PUBLISH": FACTORY / "06_PUBLISH_HOLD_REVIEW",
}
for p in DIRS.values():
    p.mkdir(parents=True, exist_ok=True)

PROGRESS = DIRS["CONTROL"] / "LATEST_DEEP_SIGNAL_PROGRESS.txt"
LATEST_LAKE = DIRS["CONTROL"] / "LATEST_DEEP_SIGNAL_LAKE.json"

TEXT_EXT = {".txt", ".md", ".csv", ".psv", ".json", ".rtf", ".html", ".htm", ".xml", ".log", ".py", ".sh", ".ps1"}
OOXML_EXT = {".docx", ".xlsx", ".pptx"}
PDF_EXT = {".pdf"}
CAD_EXT = {".dwg", ".dxf", ".dgn", ".ifc", ".rvt", ".rfa", ".skp", ".step", ".stp"}
IMG_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".svg", ".gif"}
ARCHIVE_EXT = {".zip", ".tar", ".gz", ".tgz", ".7z", ".rar"}

SKIP_DIRS = {
    "AppData", "Windows", "Program Files", "Program Files (x86)", "ProgramData",
    "$Recycle.Bin", "System Volume Information", "node_modules", ".git", ".cache",
    "__pycache__", ".npm", ".local/share/Trash", "Temp", "tmp"
}

CORE_TERMS = [
    "ars", "ars metal", "ars metal industries", "titan", "titan grid", "titangrid",
    "freya", "civil engineering", "civil engineering doo", "ugovor", "aneks",
    "dopis", "opomena", "odluka", "zapisnik", "ponuda", "faktura", "račun",
    "racun", "plaćanje", "placanje", "šteta", "steta", "gubitak", "rok",
    "kašnjenje", "kasnjenje", "docnja", "investicija", "projekat", "hala",
    "tehnička dokumentacija", "tehnicka dokumentacija", "glavni projekat",
    "idejni projekat", "odgovorni projektant", "vodeći projektant",
    "vodeci projektant", "zakon", "član", "clan", "pib", "pdv", "crps",
    "iban", "memorandum", "logo", "pečat", "pecat", "danijela", "keskin"
]

REGEXES = {
    "EMAIL": r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
    "PHONE": r"(?:\+382|00382|0)\s?[267]\d(?:[\s./-]?\d{2,3}){2,4}",
    "PIB": r"(?i)\b(?:PIB|P\.I\.B\.|poreski identifikacioni broj)\s*[:#\-]?\s*([0-9]{6,10})\b",
    "PDV": r"(?i)\b(?:PDV|P\.D\.V\.|VAT)\s*[:#\-]?\s*([A-Z]{0,2}\s*[0-9]{6,14})\b",
    "CRPS": r"(?i)\b(?:CRPS|registarski broj|registracioni broj|matični broj|maticni broj|MB)\s*[:#\-]?\s*([A-Z0-9\-/.]{5,30})\b",
    "IBAN": r"\bME\d{2}(?:\s?\d{4}){4}\s?\d{2}\b",
    "BANK": r"\b\d{3}[\s\-]?\d{6,13}[\s\-]?\d{2}\b",
    "DATE": r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b|\b\d{4}-\d{1,2}-\d{1,2}\b",
    "AMOUNT": r"\b\d{1,3}(?:[.\s]\d{3})*(?:,\d{2})?\s*(?:€|eur|eura|euro)\b",
    "ARTICLE": r"\b(?:član|clan)\s+\d+[a-zA-Z]?(?:\s+stav\s+\d+)?\b",
}

IDENTITY = {
    "official_name": "ARS METAL INDUSTRIES DOO PODGORICA",
    "address": "[ADRESA — PROVJERITI U CRPS]",
    "pib": "[PIB — PROVJERITI]",
    "pdv": "[PDV — AKO POSTOJI]",
    "crps": "[CRPS / REGISTARSKI BROJ — PROVJERITI]",
    "phone": "[TELEFON]",
    "email": "[E-MAIL]",
    "bank": "[ŽIRO RAČUN / IBAN]",
    "city": "Podgorica",
    "director": "Danijela Đurović Keskin",
    "title": "Izvršni direktor",
}

def write_progress(msg):
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {msg}"
    print(line, flush=True)
    with open(PROGRESS, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def normalize(text):
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def safe_name(s):
    return re.sub(r"[^A-Za-z0-9_. -]+", "_", str(s)).strip()[:160] or "file"

def roots():
    out = [
        HOME,
        Path("/mnt/c/Users/titangrid.info"),
    ]
    for letter in "defghijklmnopqrstuvwxyz":
        p = Path(f"/mnt/{letter}")
        if p.exists():
            out.append(p)
    # unique
    seen = []
    for r in out:
        if r.exists() and str(r) not in [str(x) for x in seen]:
            seen.append(r)
    return seen

def fingerprint(path, size):
    h = hashlib.sha256()
    mode = "FULL_SHA256"
    try:
        with open(path, "rb") as f:
            if size <= 120 * 1024 * 1024:
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    h.update(chunk)
            else:
                mode = "PARTIAL_SHA256_FIRST_LAST_SIZE"
                first = f.read(2 * 1024 * 1024)
                h.update(first)
                h.update(str(size).encode())
                try:
                    f.seek(max(0, size - 2 * 1024 * 1024))
                    h.update(f.read(2 * 1024 * 1024))
                except Exception:
                    pass
        return h.hexdigest(), mode
    except Exception as e:
        return f"ERROR={repr(e)}", "HASH_ERROR"

def extract_ooxml(path):
    parts = []
    media_count = 0
    try:
        with zipfile.ZipFile(path) as z:
            for name in z.namelist():
                if "/media/" in name:
                    media_count += 1
                if name.endswith(".xml") and (name.startswith("word/") or name.startswith("xl/") or name.startswith("ppt/")):
                    try:
                        raw = z.read(name).decode("utf-8", errors="ignore")
                        raw = re.sub(r"<[^>]+>", " ", raw)
                        parts.append(raw)
                    except Exception:
                        pass
    except Exception:
        pass
    return normalize("\n".join(parts))[:500000], media_count

def extract_pdf(path):
    if shutil.which("pdftotext"):
        try:
            r = subprocess.run(
                ["pdftotext", "-layout", str(path), "-"],
                capture_output=True, text=True, timeout=90, errors="ignore"
            )
            return normalize(r.stdout)[:500000]
        except Exception:
            return ""
    return ""

def extract_ascii_binary(path, max_bytes=8 * 1024 * 1024):
    try:
        data = path.read_bytes()[:max_bytes]
        chunks = re.findall(rb"[A-Za-z0-9_\- ./\\:;,+(){}\[\]#@]{5,}", data)
        return normalize("\n".join(x.decode("latin-1", errors="ignore") for x in chunks[:6000]))[:300000]
    except Exception:
        return ""

def extract_text(path, ext, size):
    try:
        if ext in TEXT_EXT:
            if size > 40 * 1024 * 1024:
                return extract_ascii_binary(path), "BIG_TEXT_ASCII_EXTRACT", 0
            return normalize(path.read_text(encoding="utf-8", errors="ignore"))[:500000], "TEXT", 0
        if ext in OOXML_EXT:
            txt, media_count = extract_ooxml(path)
            return txt, f"OOXML_MEDIA={media_count}", media_count
        if ext in PDF_EXT:
            return extract_pdf(path), "PDF_TEXT", 0
        if ext in CAD_EXT:
            return extract_ascii_binary(path), "CAD_BINARY_STRINGS", 0
        if ext in IMG_EXT:
            return "", "IMAGE_METADATA_ONLY", 0
        if ext in ARCHIVE_EXT:
            return extract_ascii_binary(path), "ARCHIVE_METADATA_STRINGS", 0
        return extract_ascii_binary(path), "UNKNOWN_BINARY_STRINGS", 0
    except Exception as e:
        return "", f"EXTRACT_ERROR={repr(e)}", 0

def score(path, text, topic_terms):
    low = (str(path) + "\n" + text[:250000]).lower()
    hits = []
    sc = 0
    for t in CORE_TERMS:
        if t.lower() in low:
            hits.append(t)
            sc += 2
    for t in topic_terms:
        if t and t.lower() in low:
            hits.append(f"TOPIC:{t}")
            sc += 10
    if "ars metal" in low:
        sc += 20
    if "civil" in low and "engineering" in low:
        sc += 20
    if "titan grid" in low or "titangrid" in low:
        sc += 15
    if "hala" in low:
        sc += 15
    if path.suffix.lower() in CAD_EXT:
        sc += 8
    return sc, sorted(set(hits))

def harvest_all(recipient, topic, instruction):
    topic_terms = [x for x in re.split(r"[\s,;:/\\|]+", f"{recipient} {topic} {instruction}") if len(x) > 2]
    lake_jsonl = DIRS["LAKE"] / f"DEEP_SIGNAL_LAKE_{RUN_ID}.jsonl"
    top_json = DIRS["LAKE"] / f"DEEP_SIGNAL_TOP_{RUN_ID}.json"
    report = DIRS["REPORTS"] / f"DEEP_SIGNAL_REPORT_{RUN_ID}.txt"

    stats = {
        "files_seen": 0,
        "files_indexed": 0,
        "extract_errors": 0,
        "bytes_seen": 0,
        "roots": [str(r) for r in roots()],
        "start": time.ctime(),
        "run_id": RUN_ID,
        "recipient": recipient,
        "topic": topic,
        "instruction": instruction,
    }
    global_hits = {k: [] for k in REGEXES}
    top_heap = []

    PROGRESS.write_text("", encoding="utf-8")
    write_progress("DEEP_SIGNAL_LAKE_START")
    write_progress(f"ROOTS={stats['roots']}")

    with open(lake_jsonl, "w", encoding="utf-8") as out:
        for root in roots():
            write_progress(f"SCAN_ROOT_START={root}")
            for dirpath, dirnames, filenames in os.walk(root):
                d = Path(dirpath)

                if str(d).startswith(str(FACTORY)):
                    dirnames[:] = []
                    continue

                dirnames[:] = [x for x in dirnames if x not in SKIP_DIRS]

                for name in filenames:
                    p = d / name
                    stats["files_seen"] += 1

                    try:
                        st = p.stat()
                        size = st.st_size
                        ext = p.suffix.lower()
                        stats["bytes_seen"] += size

                        # every file contributes path/name/metadata
                        txt, ex_status, media_count = extract_text(p, ext, size)
                        fp, fp_mode = fingerprint(p, size)
                        sc, hits = score(p, txt, topic_terms)

                        combined = txt + "\n" + str(p)
                        local_regex_hits = {}
                        for key, pat in REGEXES.items():
                            vals = []
                            for m in re.findall(pat, combined, re.I):
                                if isinstance(m, tuple):
                                    m = " ".join(x for x in m if x)
                                m = str(m).strip()
                                if m and m not in vals:
                                    vals.append(m)
                                if m and m not in global_hits[key]:
                                    global_hits[key].append(m)
                            if vals:
                                local_regex_hits[key] = vals[:30]

                        text_file = ""
                        if txt and sc > 0:
                            text_file_path = DIRS["TEXT"] / f"{safe_name(name)}__{fp[:12]}.txt"
                            with open(text_file_path, "w", encoding="utf-8") as tf:
                                tf.write(f"SOURCE={p}\nFINGERPRINT={fp}\nFINGERPRINT_MODE={fp_mode}\nEXTRACT_STATUS={ex_status}\nSCORE={sc}\nHITS={', '.join(hits)}\n")
                                tf.write("=" * 100 + "\n")
                                for i, line in enumerate(txt.splitlines(), 1):
                                    tf.write(f"L{i}: {line}\n")
                            text_file = str(text_file_path)

                        rec = {
                            "path": str(p),
                            "name": name,
                            "ext": ext,
                            "size": size,
                            "mtime": st.st_mtime,
                            "fingerprint": fp,
                            "fingerprint_mode": fp_mode,
                            "extract_status": ex_status,
                            "media_count": media_count,
                            "score": sc,
                            "hits": hits[:80],
                            "regex_hits": local_regex_hits,
                            "text_file": text_file,
                            "preview": txt[:1200] if sc > 0 else "",
                        }

                        out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        stats["files_indexed"] += 1

                        if sc > 0:
                            heapq.heappush(top_heap, (sc, stats["files_indexed"], rec))
                            if len(top_heap) > 700:
                                heapq.heappop(top_heap)

                    except Exception as e:
                        stats["extract_errors"] += 1

                    if stats["files_seen"] % 500 == 0:
                        write_progress(
                            f"FILES_SEEN={stats['files_seen']} FILES_INDEXED={stats['files_indexed']} TOP_SIGNALS={len(top_heap)} ERRORS={stats['extract_errors']}"
                        )

            write_progress(f"SCAN_ROOT_DONE={root}")

    top_records = [x[2] for x in sorted(top_heap, key=lambda x: x[0], reverse=True)]
    data = {
        "run_id": RUN_ID,
        "date": time.ctime(),
        "lake_jsonl": str(lake_jsonl),
        "stats": stats,
        "global_hits": global_hits,
        "top_records": top_records,
        "originals_changed": False,
        "policy": "READ_ONLY_FULL_MACHINE_SIGNAL_LAKE",
    }

    top_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    LATEST_LAKE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    with open(report, "w", encoding="utf-8") as f:
        f.write("TITAN_GRID_DEEP_SIGNAL_LAKE_REPORT\n")
        f.write(f"RUN_ID={RUN_ID}\n")
        f.write(f"DATE={time.ctime()}\n")
        f.write(f"RECIPIENT={recipient}\n")
        f.write(f"TOPIC={topic}\n")
        f.write(f"FILES_SEEN={stats['files_seen']}\n")
        f.write(f"FILES_INDEXED={stats['files_indexed']}\n")
        f.write(f"BYTES_SEEN={stats['bytes_seen']}\n")
        f.write(f"ERRORS={stats['extract_errors']}\n")
        f.write(f"LAKE_JSONL={lake_jsonl}\n")
        f.write(f"TOP_JSON={top_json}\n")
        f.write("ORIGINALS_CHANGED=NO\n")
        f.write("DELETE_MOVE_RENAME=NO\n\n")
        f.write("TOP SIGNALS:\n")
        for r in top_records[:200]:
            f.write("=" * 100 + "\n")
            f.write(f"PATH={r['path']}\n")
            f.write(f"SCORE={r['score']}\n")
            f.write(f"FINGERPRINT={r['fingerprint']}\n")
            f.write(f"HITS={', '.join(r['hits'])}\n")

    write_progress("DEEP_SIGNAL_LAKE_DONE")
    return data, lake_jsonl, top_json, report

def pick(global_hits, key, fallback):
    vals = global_hits.get(key, [])
    return vals[0] if vals else fallback

def make_document(data):
    recipient = data["stats"]["recipient"]
    topic = data["stats"]["topic"]
    instruction = data["stats"]["instruction"]
    hits = data.get("global_hits", {})
    top = data.get("top_records", [])

    IDENTITY["pib"] = pick(hits, "PIB", IDENTITY["pib"])
    IDENTITY["pdv"] = pick(hits, "PDV", IDENTITY["pdv"])
    IDENTITY["crps"] = pick(hits, "CRPS", IDENTITY["crps"])
    IDENTITY["email"] = pick(hits, "EMAIL", IDENTITY["email"])
    IDENTITY["phone"] = pick(hits, "PHONE", IDENTITY["phone"])
    IDENTITY["bank"] = pick(hits, "IBAN", pick(hits, "BANK", IDENTITY["bank"]))

    evidence = []
    for r in top[:250]:
        evidence.append(f"- {r['name']} | score={r['score']} | format={r['ext']} | fingerprint={r['fingerprint']} | izvor={r['path']}")

    dates = hits.get("DATE", [])[:120]
    amounts = hits.get("AMOUNT", [])[:120]
    articles = hits.get("ARTICLE", [])[:120]

    doc_no = f"TGDF-DEEP-{RUN_ID}"

    text = f"""
{IDENTITY['official_name']}
ZVANIČNI MEMORANDUM DRUŠTVA

Sjedište/adresa: {IDENTITY['address']}
PIB: {IDENTITY['pib']}
PDV: {IDENTITY['pdv']}
CRPS / registarski broj: {IDENTITY['crps']}
Telefon: {IDENTITY['phone']}
E-mail: {IDENTITY['email']}
Žiro račun / IBAN: {IDENTITY['bank']}

Broj: {doc_no}
Datum: {time.strftime("%d.%m.%Y.")}
Mjesto: {IDENTITY['city']}

Za: {recipient}

Predmet: Dopis / Aneks / uređenje obaveza — {topic}

{IDENTITY['title']}:
{IDENTITY['director']}


NACRT DOKUMENTA KOJI JE NAPISAN NA OSNOVU DEEP SIGNAL LAKE INDEKSA CIJELE MAŠINE


I. UVOD

Poštovani,

U ime ARS Metal Industries DOO Podgorica, dostavljamo ovaj radni nacrt dokumenta povodom predmeta:

{topic}

Ovaj dokument je pripremljen nakon dubinskog indeksiranja signala dostupnih na ovoj mašini. U indeks su uključeni nazivi fajlova, putanje, metapodaci, dostupni tekstualni sadržaj, tehnička dokumentacija, ugovorni i finansijski signali, CAD/crtežni signali, zakonski signali, identifikacioni podaci, datumi, iznosi i drugi operativni tragovi.

Dodatno uputstvo izvršnog direktora / Human Gate:
{instruction}


II. ČINJENIČNI OKVIR

Na osnovu dostupnih signala, predmet ima poslovni, finansijski, tehnički i dokazni značaj za ARS Metal Industries DOO. Dokument se sačinjava sa ciljem da bude obuhvatan, ljudski čitljiv, spreman za pregled, i spreman za potpisivanje tek nakon provjere svih podataka, priloga i pravnih tvrdnji.

Svi zaključci u ovom nacrtu moraju biti provjereni kroz izvorne dokumente prije slanja ili potpisivanja. Nijedan interni signal ne predstavlja konačnu pravnu tvrdnju bez ljudske i pravne provjere.


III. STAV ARS METAL INDUSTRIES DOO

ARS Metal Industries DOO zadržava sva prava koja proizilaze iz ugovora, zakona, poslovne dokumentacije, tehničke dokumentacije, prethodne komunikacije, finansijskih evidencija i pravila dobrog poslovanja.

Ništa iz ovog dokumenta ne predstavlja odricanje od prava, priznanje tuđeg potraživanja, prihvatanje odgovornosti ili odobrenje dodatnog troška, osim ako je to izričito navedeno u posebnom aktu koji je potpisalo ovlašćeno lice ARS Metal Industries DOO.


IV. ZAHTJEV PREMA DRUGOJ STRANI

ARS Metal Industries DOO traži da druga strana dostavi pisano izjašnjenje, kompletnu dokumentaciju i prijedlog rješenja, uključujući:

1. potvrdu prijema ovog dopisa;
2. izjašnjenje o svim otvorenim pitanjima;
3. dostavljanje kompletne tehničke, ugovorne i finansijske dokumentacije;
4. potvrdu svih rokova, datuma predaje i verzija dokumenata;
5. potvrdu odgovorne osobe za dalju komunikaciju;
6. prijedlog rješenja bez dodatnog odlaganja;
7. izjašnjenje o eventualnoj odgovornosti za kašnjenje, neuredno izvršenje, nepotpunu dokumentaciju ili štetu.


V. DOKUMENTACIJA, CRTEŽI I TEHNIČKI SIGNALI

Ako se predmet odnosi na tehničku dokumentaciju, projektovanje, halu, konstrukciju, CAD/DWG/DXF/IFC fajlove ili druge tehničke priloge, druga strana je dužna da dostavi kompletnu, čitljivu i upotrebljivu dokumentaciju u izvornim i preglednim formatima.

Dokumentacija mora sadržati najmanje: listu fajlova, verzije, datume predaje, odgovorna lica, PDF verzije, izvorne CAD/BIM fajlove, tehničke opise, crteže, revizione komentare, odgovore na komentare i potvrdu da su svi djelovi dokumentacije međusobno usaglašeni.


VI. ROKOVI, KAŠNJENJE I ODGOVORNOST

Za svaku obavezu potrebno je utvrditi ugovoreni rok, stvarni datum izvršenja, dokaz predaje, status prihvatanja i posljedice eventualnog kašnjenja.

Ako se utvrdi da je obaveza izvršena neuredno, nepotpuno ili sa zakašnjenjem, ARS Metal Industries DOO zadržava pravo da zahtijeva otklanjanje nedostataka, naknadu štete, kompenzaciju, umanjenje cijene, raskid ili drugo pravno i poslovno sredstvo zaštite.


VII. FINANSIJSKE POSLJEDICE I ŠTETA

ARS Metal Industries DOO zadržava pravo da traži naknadu svake dokazive štete, uključujući direktne troškove, troškove čekanja, troškove angažovanja trećih lica, povećanje cijena, odlaganje proizvodnje, izgubljenu dobit, izgubljene ugovore, finansijske troškove, reputacionu štetu i druge posljedice koje se mogu dokazati dokumentima.


VIII. DOKAZNI SIGNALI KORIŠĆENI ZA LJUDSKI PREGLED

Deep Signal Lake statistika:

- files_seen: {data['stats']['files_seen']}
- files_indexed: {data['stats']['files_indexed']}
- bytes_seen: {data['stats']['bytes_seen']}
- roots: {', '.join(data['stats']['roots'])}
- lake_jsonl: {data['lake_jsonl']}

Najvažniji signali koji su ušli u nacrt:

{chr(10).join(evidence) if evidence else "- Nema relevantnih signala."}


IX. AUTOMATSKI PRONAĐENI DATUMI, IZNOSI I ČLANOVI

Datumi:
{chr(10).join("- " + x for x in dates) if dates else "- Nije pronađeno."}

Iznosi:
{chr(10).join("- " + x for x in amounts) if amounts else "- Nije pronađeno."}

Članovi / pravni signali:
{chr(10).join("- " + x for x in articles) if articles else "- Nije pronađeno."}


X. REZERVA PRAVA

Ovaj dokument ne predstavlja konačno pravno mišljenje. Dokument je radna verzija za ljudski pregled i potpisivanje nakon provjere. ARS Metal Industries DOO zadržava sva prava, uključujući pravo na izmjenu, dopunu, povlačenje, dostavljanje advokatu, slanje drugoj strani ili korišćenje u dokaznom paketu.


XI. POTPIS

Za ARS METAL INDUSTRIES DOO PODGORICA

____________________________________
{IDENTITY['director']}
{IDENTITY['title']}

Pečat društva: ______________________

Datum potpisivanja: __________________
""".strip() + "\n"

    safe_base = safe_name(f"DEEP_ALL_SIGNALS_{recipient}_{topic}_{RUN_ID}")
    txt = DIRS["PUBLISH"] / f"{safe_base}.txt"
    htmlp = DIRS["PUBLISH"] / f"{safe_base}.html"

    txt.write_text(text, encoding="utf-8")

    htmlp.write_text(f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{html.escape(topic)}</title>
<style>
body {{
  font-family: "Times New Roman", serif;
  margin: 22mm;
  color: #111;
  line-height: 1.35;
}}
.header {{
  border-bottom: 2px solid #111;
  padding-bottom: 12px;
  margin-bottom: 24px;
}}
.company {{
  font-size: 22px;
  font-weight: bold;
  text-transform: uppercase;
}}
.small {{
  font-size: 12.5px;
  line-height: 1.35;
}}
pre {{
  white-space: pre-wrap;
  font-family: "Times New Roman", serif;
  font-size: 15px;
}}
@media print {{
  body {{ margin: 20mm; }}
}}
</style>
</head>
<body>
<div class="header">
  <div class="company">{html.escape(IDENTITY['official_name'])}</div>
  <div class="small">
    PIB: {html.escape(IDENTITY['pib'])}<br>
    PDV: {html.escape(IDENTITY['pdv'])}<br>
    CRPS / reg. broj: {html.escape(IDENTITY['crps'])}<br>
    Tel: {html.escape(IDENTITY['phone'])}<br>
    E-mail: {html.escape(IDENTITY['email'])}<br>
    Žiro račun / IBAN: {html.escape(IDENTITY['bank'])}
  </div>
</div>
<pre>{html.escape(text)}</pre>
</body>
</html>
""", encoding="utf-8")

    return txt, htmlp

def main():
    if len(sys.argv) < 4:
        print('USAGE: tgdf-deep-all "PRIMALAC" "TEMA" "UPUTSTVO"')
        return

    recipient = sys.argv[1]
    topic = sys.argv[2]
    instruction = sys.argv[3]

    data, lake, top, report = harvest_all(recipient, topic, instruction)
    txt, htmlp = make_document(data)

    print("=== TGDF_DEEP_ALL_SIGNALS_DONE ===")
    print(f"DEEP_SIGNAL_LAKE={lake}")
    print(f"TOP_SIGNAL_JSON={top}")
    print(f"REPORT={report}")
    print(f"DOCUMENT_TXT={txt}")
    print(f"DOCUMENT_HTML={htmlp}")
    print("STATUS=PUBLISH_HOLD_REVIEW_ONLY")
    print("ORIGINALS_CHANGED=NO")
    print("AUTO_SEND=NO")
    print("READY_FOR_SIGNATURE=NO_UNTIL_HUMAN_REVIEW")

if __name__ == "__main__":
    main()
