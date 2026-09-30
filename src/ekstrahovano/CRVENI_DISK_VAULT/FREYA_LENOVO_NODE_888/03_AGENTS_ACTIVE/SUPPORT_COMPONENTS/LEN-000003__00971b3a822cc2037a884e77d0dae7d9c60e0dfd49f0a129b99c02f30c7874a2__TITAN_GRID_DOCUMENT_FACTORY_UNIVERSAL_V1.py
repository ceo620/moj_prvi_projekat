import os, re, sys, json, time, html, zipfile, hashlib, shutil, subprocess
from pathlib import Path
from xml.etree import ElementTree as ET

RUN_ID = time.strftime("%Y%m%d_%H%M%S")
HOME = Path.home()
FACTORY = HOME / "TITAN_GRID_DOCUMENT_FACTORY"

DIRS = {
    "CONTROL": FACTORY / "00_CONTROL",
    "IDENTITY": FACTORY / "01_IDENTITY_AND_MEMORANDUM",
    "HARVEST": FACTORY / "02_SIGNAL_HARVEST",
    "ORDERS": FACTORY / "03_DOCUMENT_ORDERS",
    "TEMPLATES": FACTORY / "04_TEMPLATES",
    "WORK": FACTORY / "05_WORKROOM",
    "PUBLISH_HOLD": FACTORY / "06_PUBLISH_HOLD_REVIEW",
    "READY": FACTORY / "07_READY_FOR_SIGNATURE_AFTER_APPROVAL",
    "LOGOS": FACTORY / "08_LOGOS_SEALS_SIGNATURES",
    "REPORTS": FACTORY / "09_REPORTS",
    "PACKAGES": FACTORY / "10_PACKAGES",
}
for p in DIRS.values():
    p.mkdir(parents=True, exist_ok=True)

IDENTITY_FILE = DIRS["IDENTITY"] / "TITAN_GRID_OFFICIAL_IDENTITY.json"
LATEST_HARVEST = DIRS["HARVEST"] / "LATEST_HARVEST.json"
LATEST_OUTPUT = DIRS["CONTROL"] / "LATEST_OUTPUT.txt"

TEXT_EXT = {".txt", ".md", ".csv", ".psv", ".json", ".rtf", ".docx", ".xlsx", ".pptx", ".pdf", ".html", ".htm"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".svg", ".gif"}
CAD_EXT = {".dwg", ".dxf", ".dgn", ".ifc", ".rvt", ".rfa", ".skp", ".step", ".stp"}
ALL_EXT = TEXT_EXT | IMAGE_EXT | CAD_EXT

SKIP_DIRS = {
    "AppData", "Windows", "Program Files", "Program Files (x86)", "ProgramData",
    "$Recycle.Bin", "System Volume Information", "node_modules", ".git", ".cache",
    "__pycache__", ".npm", ".local/share/Trash"
}

GENERAL_SIGNAL_TERMS = [
    "ars", "ars metal", "ars metal industries", "titan", "titan grid", "freya",
    "civil engineering", "ugovor", "aneks", "dopis", "opomena", "odluka",
    "ponuda", "račun", "racun", "faktura", "plaćanje", "placanje", "šteta",
    "steta", "gubitak", "rok", "kašnjenje", "kasnjenje", "investicija",
    "projekat", "hala", "tehnička dokumentacija", "tehnicka dokumentacija",
    "pib", "pdv", "crps", "iban", "memorandum", "logo", "pečat", "pecat",
    "izvršni direktor", "izvrsni direktor", "danijela", "keskin"
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

DEFAULT_IDENTITY = {
    "official_name": "ARS METAL INDUSTRIES DOO PODGORICA",
    "short_name": "ARS Metal Industries DOO",
    "group_name": "TITAN GRID",
    "address": "[ADRESA — PROVJERITI U CRPS]",
    "city": "Podgorica",
    "country": "Crna Gora",
    "pib": "[PIB — PROVJERITI]",
    "pdv": "[PDV — AKO POSTOJI]",
    "crps": "[CRPS / REGISTARSKI BROJ — PROVJERITI]",
    "email": "[E-MAIL]",
    "phone": "[TELEFON]",
    "web": "[WEB]",
    "bank_account": "[ŽIRO RAČUN / IBAN]",
    "executive_director": "Danijela Đurović Keskin",
    "signature_title": "Izvršni direktor",
    "memo_title": "ZVANIČNI MEMORANDUM DRUŠTVA",
    "logo_path": "",
    "seal_required": True,
    "publish_policy": "PUBLISH_HOLD_UNTIL_HUMAN_APPROVAL",
}

def now_date():
    return time.strftime("%d.%m.%Y.")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def safe_name(s):
    s = re.sub(r"[^A-Za-z0-9_. -]+", "_", str(s))
    return s.strip()[:170] or "file"

def normalize(text):
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def ensure_identity():
    if not IDENTITY_FILE.exists():
        IDENTITY_FILE.write_text(json.dumps(DEFAULT_IDENTITY, ensure_ascii=False, indent=2), encoding="utf-8")
    return json.loads(IDENTITY_FILE.read_text(encoding="utf-8", errors="ignore"))

def save_identity(identity):
    IDENTITY_FILE.write_text(json.dumps(identity, ensure_ascii=False, indent=2), encoding="utf-8")

def extract_ooxml(path):
    parts, media = [], []
    try:
        with zipfile.ZipFile(path) as z:
            for name in z.namelist():
                if "/media/" in name and Path(name).suffix.lower() in IMAGE_EXT:
                    try:
                        media.append((name, z.read(name)))
                    except Exception:
                        pass
                if name.endswith(".xml") and (name.startswith("word/") or name.startswith("xl/") or name.startswith("ppt/")):
                    try:
                        raw = z.read(name).decode("utf-8", errors="ignore")
                        raw = re.sub(r"<[^>]+>", " ", raw)
                        parts.append(raw)
                    except Exception:
                        pass
    except Exception:
        pass
    return normalize("\n".join(parts)), media

def extract_pdf(path):
    if shutil.which("pdftotext"):
        try:
            r = subprocess.run(
                ["pdftotext", "-layout", str(path), "-"],
                capture_output=True,
                text=True,
                timeout=120,
                errors="ignore"
            )
            return normalize(r.stdout)
        except Exception:
            return ""
    return ""

def extract_binary_strings(path, max_bytes=25 * 1024 * 1024):
    try:
        data = path.read_bytes()[:max_bytes]
        # ASCII-only regex: no Python bytes error.
        chunks = re.findall(rb"[A-Za-z0-9_\- ./\\:;,+(){}\[\]#@]{5,}", data)
        return normalize("\n".join(x.decode("latin-1", errors="ignore") for x in chunks[:10000]))
    except Exception:
        return ""

def extract_text(path):
    ext = path.suffix.lower()
    try:
        if ext in {".docx", ".xlsx", ".pptx"}:
            txt, media = extract_ooxml(path)
            return txt, media, f"OOXML_{ext}"
        if ext == ".pdf":
            return extract_pdf(path), [], "PDF_TEXT"
        if ext in {".txt", ".md", ".csv", ".psv", ".json"}:
            return normalize(path.read_text(encoding="utf-8", errors="ignore")), [], "TEXT"
        if ext == ".rtf":
            raw = path.read_text(encoding="utf-8", errors="ignore")
            raw = re.sub(r"{\\.*?}", " ", raw)
            raw = re.sub(r"\\[a-z]+\d* ?", " ", raw)
            return normalize(raw), [], "RTF"
        if ext in {".html", ".htm"}:
            raw = path.read_text(encoding="utf-8", errors="ignore")
            raw = re.sub(r"<script.*?</script>", " ", raw, flags=re.I | re.S)
            raw = re.sub(r"<style.*?</style>", " ", raw, flags=re.I | re.S)
            raw = re.sub(r"<[^>]+>", " ", raw)
            return normalize(html.unescape(raw)), [], "HTML"
        if ext in CAD_EXT:
            return extract_binary_strings(path), [], "CAD_BINARY_STRINGS"
        if ext in IMAGE_EXT:
            return "", [], "IMAGE"
    except Exception as e:
        return "", [], f"ERROR={repr(e)}"
    return "", [], "UNSUPPORTED"

def scan_roots():
    roots = [
        Path("/mnt/c/Users/titangrid.info/Desktop"),
        Path("/mnt/c/Users/titangrid.info/Documents"),
        Path("/mnt/c/Users/titangrid.info/Downloads"),
        HOME,
    ]
    for letter in "defghijklmnopqrstuvwxyz":
        p = Path(f"/mnt/{letter}")
        if p.exists():
            roots.append(p)
    return roots

def relevant_path(path, extra_terms=None):
    low = str(path).lower().replace("\\", "/")
    terms = GENERAL_SIGNAL_TERMS[:]
    if extra_terms:
        terms += extra_terms
    return any(t.lower() in low for t in terms)

def list_candidate_files(extra_terms=None):
    found = {}
    for root in scan_roots():
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            d = Path(dirpath)
            if str(d).startswith(str(FACTORY)):
                dirnames[:] = []
                continue
            dirnames[:] = [x for x in dirnames if x not in SKIP_DIRS]

            if not relevant_path(d, extra_terms) and len(d.parts) > 7:
                dirnames[:] = []
                continue

            for name in filenames:
                p = d / name
                if p.suffix.lower() not in ALL_EXT:
                    continue
                if relevant_path(p, extra_terms) or len(d.parts) <= 6:
                    found[str(p)] = p
    return sorted(found.values())

def score_record(path, text, topic_terms=None):
    low = (str(path) + "\n" + text[:250000]).lower()
    hits = []
    score = 0

    for t in GENERAL_SIGNAL_TERMS:
        if t.lower() in low:
            hits.append(t)
            score += 2

    if topic_terms:
        for t in topic_terms:
            if t and t.lower() in low:
                hits.append(f"TOPIC:{t}")
                score += 8

    if "ars metal" in low:
        score += 10
    if "titan grid" in low or "titangrid" in low:
        score += 8
    if path.suffix.lower() in CAD_EXT:
        score += 4
    if path.suffix.lower() in IMAGE_EXT:
        score += 2

    return score, sorted(set(hits))

def harvest(topic=""):
    topic_terms = [x.strip() for x in re.split(r"[\s,;:/\\|]+", topic) if len(x.strip()) > 2]
    work = DIRS["HARVEST"] / f"HARVEST_{RUN_ID}"
    text_dir = work / "TEXT"
    media_dir = work / "MEDIA"
    text_dir.mkdir(parents=True, exist_ok=True)
    media_dir.mkdir(parents=True, exist_ok=True)

    records, global_hits, errors = [], {k: [] for k in REGEXES}, []
    files = list_candidate_files(topic_terms)

    for p in files:
        try:
            if p.stat().st_size > 350 * 1024 * 1024:
                continue

            txt, media, status = extract_text(p)
            sc, hits = score_record(p, txt, topic_terms)
            h = sha256_file(p)

            text_path = text_dir / f"{safe_name(p.name)}__{h[:12]}.txt"
            with open(text_path, "w", encoding="utf-8") as f:
                f.write(f"SOURCE={p}\nSHA256={h}\nSTATUS={status}\nSCORE={sc}\nHITS={', '.join(hits)}\n")
                f.write("=" * 100 + "\n")
                for i, line in enumerate(txt.splitlines(), 1):
                    f.write(f"L{i}: {line}\n")

            combined = txt + "\n" + str(p)
            for key, pattern in REGEXES.items():
                for m in re.findall(pattern, combined, re.I):
                    if isinstance(m, tuple):
                        m = " ".join(x for x in m if x)
                    m = str(m).strip()
                    if m and m not in global_hits[key]:
                        global_hits[key].append(m)

            for media_name, data in media:
                ext = Path(media_name).suffix.lower()
                if ext in IMAGE_EXT:
                    mh = hashlib.sha256(data).hexdigest()
                    out = media_dir / f"EMBEDDED_{safe_name(p.stem)}__{safe_name(Path(media_name).name)}__{mh[:12]}{ext}"
                    out.write_bytes(data)

            records.append({
                "path": str(p),
                "name": p.name,
                "ext": p.suffix.lower(),
                "size": p.stat().st_size,
                "sha256": h,
                "status": status,
                "score": sc,
                "hits": hits,
                "text_file": str(text_path),
                "preview": txt[:3000],
            })
        except Exception as e:
            errors.append([str(p), repr(e)])

    records = sorted(records, key=lambda x: x["score"], reverse=True)
    data = {
        "run_id": RUN_ID,
        "date": time.ctime(),
        "topic": topic,
        "factory": str(FACTORY),
        "records": records,
        "global_hits": global_hits,
        "errors": errors,
        "originals_changed": False,
        "policy": "READ_ONLY_HARVEST_NO_DELETE_NO_MOVE_NO_RENAME",
    }

    harvest_path = DIRS["HARVEST"] / f"HARVEST_INDEX_{RUN_ID}.json"
    harvest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    LATEST_HARVEST.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    psv = DIRS["HARVEST"] / f"HARVEST_INDEX_{RUN_ID}.psv"
    with open(psv, "w", encoding="utf-8") as f:
        f.write("PATH|EXT|SIZE|SHA256|SCORE|STATUS|HITS|TEXT_FILE\n")
        for r in records:
            f.write(f"{r['path']}|{r['ext']}|{r['size']}|{r['sha256']}|{r['score']}|{r['status']}|{','.join(r['hits'])}|{r['text_file']}\n")

    return data, harvest_path, psv

def load_harvest_or_make(topic=""):
    if LATEST_HARVEST.exists():
        try:
            return json.loads(LATEST_HARVEST.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            pass
    data, _, _ = harvest(topic)
    return data

def choose_identity_from_harvest(identity, harvest_data):
    hits = harvest_data.get("global_hits", {})
    def first(key, fallback):
        vals = hits.get(key, [])
        return vals[0] if vals else fallback

    identity = dict(identity)
    if identity.get("pib", "").startswith("["):
        identity["pib"] = first("PIB", identity["pib"])
    if identity.get("pdv", "").startswith("["):
        identity["pdv"] = first("PDV", identity["pdv"])
    if identity.get("crps", "").startswith("["):
        identity["crps"] = first("CRPS", identity["crps"])
    if identity.get("email", "").startswith("["):
        identity["email"] = first("EMAIL", identity["email"])
    if identity.get("phone", "").startswith("["):
        identity["phone"] = first("PHONE", identity["phone"])
    if identity.get("bank_account", "").startswith("["):
        identity["bank_account"] = first("IBAN", first("BANK", identity["bank_account"]))
    return identity

def memo_header_text(identity, doc_no, recipient, subject):
    return f"""{identity['official_name']}
{identity['memo_title']}

Sjedište/adresa: {identity['address']}
PIB: {identity['pib']}
PDV: {identity['pdv']}
CRPS / registarski broj: {identity['crps']}
Telefon: {identity['phone']}
E-mail: {identity['email']}
Web: {identity['web']}
Žiro račun / IBAN: {identity['bank_account']}

Broj: {doc_no}
Datum: {now_date()}
Mjesto: {identity['city']}

Za: {recipient}

Predmet: {subject}

{identity['signature_title']}:
{identity['executive_director']}
"""

def human_like_evidence_section(records, limit=60):
    lines = []
    for r in records[:limit]:
        lines.append(f"- {r['name']} | format={r['ext']} | score={r['score']} | SHA256={r['sha256']} | izvor={r['path']}")
    return "\n".join(lines) if lines else "- Nije pronađen dovoljan dokazni signal u trenutnom opsegu."

def build_document_body(doc_type, recipient, topic, instruction, harvest_data):
    records = harvest_data.get("records", [])
    hits = harvest_data.get("global_hits", {})
    dates = hits.get("DATE", [])[:80]
    amounts = hits.get("AMOUNT", [])[:80]
    articles = hits.get("ARTICLE", [])[:80]
    evidence = human_like_evidence_section(records)

    doc_type_low = doc_type.lower()

    common_signal = f"""
DOKAZNI I OPERATIVNI SIGNALI KOJI SU KORIŠĆENI ZA LJUDSKI PREGLED

{evidence}

Automatski pronađeni datumi:
{chr(10).join("- " + x for x in dates) if dates else "- Nema automatski pronađenih datuma."}

Automatski pronađeni iznosi:
{chr(10).join("- " + x for x in amounts) if amounts else "- Nema automatski pronađenih iznosa."}

Automatski pronađeni članovi / pravni signali:
{chr(10).join("- " + x for x in articles) if articles else "- Nema automatski pronađenih članova."}
""".strip()

    if doc_type_low in {"dopis", "letter", "zahtjev", "obavjestenje", "obavještenje"}:
        return f"""
Poštovani,

U ime ARS Metal Industries DOO Podgorica, dostavljamo ovaj dopis povodom sljedeće stvari:

{topic}

Osnov i razlog obraćanja:
{instruction if instruction else "Ovaj dopis se sačinjava radi formalnog evidentiranja stava, zahtjeva, očekivanja i daljih koraka ARS Metal Industries DOO."}

I. ČINJENIČNI OKVIR

Prema dostupnim internim dokumentima, komunikaciji, radnim evidencijama i signalima pronađenim u lokalnoj arhivi, predmet ima poslovni, finansijski i operativni značaj za ARS Metal Industries DOO. Ovaj dopis se zato sačinjava na način koji čuva dokazni trag, jasno formuliše zahtjev i ostavlja prostor za mirno i poslovno rješavanje pitanja.

II. STAV ARS METAL INDUSTRIES DOO

ARS Metal Industries DOO zadržava sva prava koja proizilaze iz ugovora, zakona, poslovne dokumentacije, prethodne komunikacije i pravila dobrog poslovanja. Ništa iz ovog dopisa ne može se tumačiti kao odricanje od prava, priznanje tuđeg potraživanja ili prihvatanje odgovornosti, osim ako je to izričito navedeno u pisanom aktu potpisanom od strane ovlašćenog lica.

III. ZAHTJEV

Molimo / zahtijevamo da druga strana u razumnom roku dostavi pisano izjašnjenje, relevantnu dokumentaciju i prijedlog rješenja, uključujući:
1. potvrdu prijema ovog dopisa;
2. izjašnjenje o predmetu dopisa;
3. dostavljanje dokumentacije koja se odnosi na predmet;
4. prijedlog rokova za zatvaranje otvorenih pitanja;
5. imenovanje kontakt osobe za koordinaciju.

IV. ROK

Predlažemo da se izjašnjenje dostavi u roku od 3 radna dana od dana prijema ovog dopisa, osim ako je u osnovnom odnosu ili prethodnoj komunikaciji već određen kraći rok.

V. REZERVA PRAVA

ARS Metal Industries DOO zadržava pravo da, u zavisnosti od odgovora i dostavljene dokumentacije, preduzme sve dalje pravne, finansijske, operativne i dokazne radnje radi zaštite svojih interesa.

{common_signal}
""".strip()

    if doc_type_low in {"ugovor", "contract"}:
        return f"""
NACRT UGOVORA

I. UGOVORNE STRANE

1. ARS Metal Industries DOO Podgorica, kao jedna ugovorna strana.
2. {recipient}, kao druga ugovorna strana.

II. PREDMET UGOVORA

Predmet ovog ugovora je:
{topic}

Dodatno uputstvo / poslovni cilj:
{instruction if instruction else "Ugovor treba da precizno uredi obaveze, rokove, cijenu, dokumentaciju, odgovornost, način predaje, kontrolu kvaliteta, povjerljivost, zaštitu interesa i raskid."}

III. OBAVEZE STRANA

Svaka ugovorna strana obavezuje se da svoje obaveze izvršava savjesno, profesionalno, u skladu sa zakonom, pravilima struke, ugovorenim rokovima i legitimnim poslovnim interesima druge strane.

IV. ROKOVI

Rokovi izvršenja biće definisani po fazama, uz obavezu pisane potvrde svake predaje, izmjene, prihvatanja ili primjedbe.

V. CIJENA I PLAĆANJE

Cijena, dinamika plaćanja, avans, uslovi fakturisanja, poreski tretman i posljedice kašnjenja u plaćanju biće definisani u posebnom članu ili prilogu ugovora. Nijedna dodatna usluga ne može se fakturisati bez prethodne pisane saglasnosti ARS Metal Industries DOO.

VI. PREDAJA DOKUMENTACIJE I DOKAZI

Svaka predaja mora biti dokumentovana e-mailom, zapisnikom, listom fajlova ili drugim dokazom koji sadrži datum, verziju, opis i odgovorno lice.

VII. ODGOVORNOST

Strana koja neuredno, nepotpuno ili sa zakašnjenjem izvrši obavezu odgovara za štetu koju takvo postupanje prouzrokuje drugoj strani, uključujući direktnu štetu, dodatne troškove, zastoje i druge dokazive posljedice.

VIII. POVJERLJIVOST

Sve informacije, dokumenti, tehnički podaci, finansijski podaci, nacrti, planovi i poslovni podaci predstavljaju povjerljive informacije i ne smiju se koristiti izvan svrhe ovog ugovora.

IX. RASKID

Ugovor se može raskinuti u slučaju bitne povrede obaveza, kašnjenja, neurednog izvršenja, povrede povjerljivosti ili drugog postupanja koje ugrožava interese druge strane.

X. ZAVRŠNE ODREDBE

Sve izmjene i dopune ugovora važe samo ako su sačinjene u pisanoj formi i potpisane od strane ovlašćenih predstavnika obje strane.

{common_signal}
""".strip()

    if doc_type_low in {"aneks", "annex", "addendum"}:
        return f"""
NACRT ANEKSA UGOVORA

I. UGOVORNE STRANE

1. ARS Metal Industries DOO Podgorica.
2. {recipient}.

II. VEZA SA OSNOVNIM UGOVOROM

Ovaj Aneks se odnosi na:
{topic}

III. RAZLOG ZAKLJUČENJA ANEKSA

Aneks se zaključuje radi preciziranja, dopune ili izmjene postojećeg ugovornog odnosa, na osnovu raspoložive dokumentacije, poslovne potrebe i zahtjeva da se jasno urede otvorena pitanja.

Dodatno uputstvo:
{instruction if instruction else "Potrebno je urediti obaveze, rokove, predaju dokumentacije, odgovornost, finansijske posljedice i dokazni režim."}

IV. PRECIZIRANJE OBAVEZA

Strane potvrđuju da će sve obaveze biti tumačene restriktivno prema pisanom ugovoru, pisanim nalozima, pisanim odobrenjima i dokazima o predaji.

V. ROKOVI I PREDAJA

Za svaku obavezu utvrđuju se ugovoreni rok, stvarni datum izvršenja, dokaz predaje, verzija dokumenta i status prihvatanja.

VI. ODGOVORNOST I ŠTETA

Nijedna odredba ovog Aneksa ne predstavlja odricanje ARS Metal Industries DOO od prava na naknadu štete, prigovor neurednog izvršenja, prigovor zakašnjenja ili bilo koje drugo pravo koje proizilazi iz ugovora, zakona ili poslovne dokumentacije.

VII. DODATNO FAKTURISANJE

Dodatne usluge, izmjene obima ili novi radovi mogu se fakturisati samo ako su prethodno pisano odobreni od strane ARS Metal Industries DOO.

VIII. PRILOZI

Sastavni dio ovog Aneksa mogu biti: osnovni ugovor, ponuda, projektni zadatak, fakture, zapisnici, e-mail komunikacija, liste fajlova, tehnička dokumentacija, crteži, obračuni štete i hash manifesti.

{common_signal}
""".strip()

    if doc_type_low in {"opomena", "opomena-pred-tuzbu", "opomena-pred-tuZbu", "opomena_pred_tuzbu"}:
        return f"""
OPOMENA PRED PREDUZIMANJE DALJIH RADNJI

Poštovani,

ARS Metal Industries DOO Podgorica dostavlja ovu opomenu povodom:

{topic}

Dodatno uputstvo:
{instruction if instruction else "Opomena se dostavlja radi zaštite prava, evidentiranja povrede i omogućavanja mirnog rješenja prije daljih pravnih koraka."}

I. POVREDA / OTVORENO PITANJE

Prema dostupnoj dokumentaciji i internim evidencijama, postoji osnovana potreba da druga strana hitno postupi, dostavi izjašnjenje, izvrši obavezu ili otkloni posljedice neurednog postupanja.

II. ZAHTJEV ZA HITNO POSTUPANJE

Zahtijevamo da u roku od 3 dana od prijema ove opomene:
1. dostavite pisano izjašnjenje;
2. dostavite svu relevantnu dokumentaciju;
3. predložite način mirnog rješavanja;
4. izvršite obavezu ili otklonite nedostatke;
5. potvrdite kontakt osobu za dalju komunikaciju.

III. REZERVA PRAVA

Ako izjašnjenje ili postupanje ne bude dostavljeno u ostavljenom roku, ARS Metal Industries DOO zadržava pravo da bez dodatnog upozorenja preduzme sve dalje radnje radi zaštite svojih prava i naknade štete.

{common_signal}
""".strip()

    if doc_type_low in {"odluka", "decision"}:
        return f"""
ODLUKA

Na osnovu ovlašćenja izvršnog direktora i potrebe zaštite interesa ARS Metal Industries DOO Podgorica, donosi se sljedeća:

ODLUKA

I. Predmet odluke:
{topic}

II. Razlog donošenja:
{instruction if instruction else "Odluka se donosi radi organizovanja dokaznog materijala, pripreme dokumentacije, uređenja poslovnog postupanja i zaštite interesa društva."}

III. Nalaže se:
1. da se sva relevantna dokumentacija evidentira i čuva;
2. da se ne brišu, ne preimenuju i ne pomjeraju originali;
3. da se pripremi radna verzija dokumenta;
4. da se dokument zadrži u internom pregledu do posebnog odobrenja;
5. da se za slanje ili potpis obezbijedi posebna odluka izvršnog direktora.

IV. Odgovorno lice:
Danijela Đurović Keskin, izvršni direktor.

V. Stupanje na snagu:
Ova odluka stupa na snagu danom donošenja.

{common_signal}
""".strip()

    if doc_type_low in {"zapisnik", "minutes"}:
        return f"""
ZAPISNIK

Predmet zapisnika:
{topic}

Dodatno uputstvo:
{instruction if instruction else "Zapisnik se sačinjava radi evidentiranja činjenica, dokaza, dogovora, otvorenih pitanja i sljedećih koraka."}

I. UČESNICI

1. ARS Metal Industries DOO Podgorica.
2. {recipient}.
3. Ostali učesnici: [UNIJETI].

II. ČINJENICE

Na osnovu dostupnih dokumenata i signala, evidentiraju se sljedeće činjenice:
1. predmet ima poslovni i operativni značaj za ARS Metal Industries DOO;
2. potrebno je jasno evidentirati šta je traženo, šta je dostavljeno, kada je dostavljeno i šta ostaje otvoreno;
3. svaki zaključak mora biti vezan za dokument ili dokaz.

III. OTVORENA PITANJA

1. dokumentacija koju treba pribaviti;
2. rokovi koje treba potvrditi;
3. finansijski efekti koje treba obračunati;
4. odgovorna lica koja treba imenovati;
5. sljedeći rok za provjeru.

IV. ZAKLJUČCI

Zaključci iz ovog zapisnika važe samo kao radna evidencija dok ih ovlašćena lica ne potvrde.

{common_signal}
""".strip()

    # Default universal document
    return f"""
UNIVERZALNI NACRT DOKUMENTA

Vrsta dokumenta: {doc_type}
Primalac / druga strana: {recipient}
Tema: {topic}

Uputstvo:
{instruction if instruction else "Nema posebnog dodatnog uputstva."}

I. SVRHA DOKUMENTA

Ovaj dokument se sačinjava radi formalnog, dokazno zasnovanog i poslovno upotrebljivog uređenja predmeta navedenog u temi. Dokument je pripremljen na memorandumu ARS Metal Industries DOO Podgorica i namijenjen je ljudskom pregledu prije potpisivanja ili slanja.

II. ČINJENIČNI OKVIR

Na osnovu dostupnih lokalnih signala, predmet zahtijeva pažljivo definisanje činjenica, obaveza, rokova, odgovornosti, finansijskih efekata, dokaza i daljih koraka.

III. STAV I ZAHTJEV

ARS Metal Industries DOO zadržava sva prava i traži jasno pisano izjašnjenje, dostavljanje relevantne dokumentacije i definisanje rokova za zatvaranje otvorenih pitanja.

IV. REZERVA PRAVA

Ništa iz ovog dokumenta ne predstavlja odricanje od prava, priznanje tuđeg potraživanja ili prihvatanje odgovornosti bez posebne pisane odluke ovlašćenog lica.

{common_signal}
""".strip()

def render_html(identity, text, title):
    logo_html = ""
    lp = identity.get("logo_path", "")
    if lp and Path(lp).exists():
        logo_html = f'<img src="{html.escape(lp)}" style="max-height:85px;max-width:220px;">'

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{html.escape(title)}</title>
<style>
body {{
  font-family: "Times New Roman", serif;
  margin: 22mm;
  color: #111;
  line-height: 1.35;
}}
.header {{
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
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
.watermark {{
  color: #777;
  font-size: 11px;
  margin-top: 30px;
  border-top: 1px solid #ccc;
  padding-top: 8px;
}}
@media print {{
  body {{ margin: 20mm; }}
  .watermark {{ display: none; }}
}}
</style>
</head>
<body>
<div class="header">
  <div>
    <div class="company">{html.escape(identity['official_name'])}</div>
    <div class="small">
      {html.escape(identity['address'])}<br>
      PIB: {html.escape(identity['pib'])}<br>
      PDV: {html.escape(identity['pdv'])}<br>
      CRPS / reg. broj: {html.escape(identity['crps'])}<br>
      Tel: {html.escape(identity['phone'])}<br>
      E-mail: {html.escape(identity['email'])}<br>
      Žiro račun / IBAN: {html.escape(identity['bank_account'])}
    </div>
  </div>
  <div>{logo_html}</div>
</div>
<pre>{html.escape(text)}</pre>
<div class="watermark">
TITAN GRID DOCUMENT FACTORY — REVIEW VERSION — NO AUTO SEND — HUMAN APPROVAL REQUIRED
</div>
</body>
</html>"""

def create_document(doc_type, recipient, topic, instruction=""):
    order_id = f"TGDF-{RUN_ID}"
    identity = ensure_identity()

    data, harvest_json, harvest_psv = harvest(topic + " " + recipient)
    identity = choose_identity_from_harvest(identity, data)
    save_identity(identity)

    subject = f"{doc_type.upper()} — {topic}"
    doc_no = f"{doc_type.upper()}-{RUN_ID}"

    header = memo_header_text(identity, doc_no, recipient, subject)
    body = build_document_body(doc_type, recipient, topic, instruction, data)

    full_text = header + "\n\n" + body + f"""

Za {identity['official_name']}

____________________________________
{identity['executive_director']}
{identity['signature_title']}

Pečat društva: ______________________

Datum potpisivanja: __________________
"""

    safe_base = safe_name(f"{doc_type}_{recipient}_{topic}_{RUN_ID}")
    txt_path = DIRS["PUBLISH_HOLD"] / f"{safe_base}.txt"
    html_path = DIRS["PUBLISH_HOLD"] / f"{safe_base}.html"
    order_path = DIRS["ORDERS"] / f"ORDER_{safe_base}.json"

    txt_path.write_text(full_text, encoding="utf-8")
    html_path.write_text(render_html(identity, full_text, subject), encoding="utf-8")

    order = {
        "order_id": order_id,
        "date": time.ctime(),
        "doc_type": doc_type,
        "recipient": recipient,
        "topic": topic,
        "instruction": instruction,
        "txt": str(txt_path),
        "html": str(html_path),
        "harvest_json": str(harvest_json),
        "harvest_psv": str(harvest_psv),
        "status": "PUBLISH_HOLD_REVIEW_ONLY",
        "approval_required": True,
        "originals_changed": False,
    }
    order_path.write_text(json.dumps(order, ensure_ascii=False, indent=2), encoding="utf-8")
    LATEST_OUTPUT.write_text(f"TXT={txt_path}\nHTML={html_path}\nORDER={order_path}\n", encoding="utf-8")

    return txt_path, html_path, order_path, harvest_json

def approve_latest():
    if not LATEST_OUTPUT.exists():
        print("NO_LATEST_OUTPUT")
        return
    lines = LATEST_OUTPUT.read_text(encoding="utf-8", errors="ignore").splitlines()
    items = []
    for line in lines:
        if "=" in line:
            k, v = line.split("=", 1)
            if k in {"TXT", "HTML"} and Path(v).exists():
                items.append(Path(v))
    if not items:
        print("NO_OUTPUT_FILES_FOUND")
        return

    pack_dir = DIRS["READY"] / f"READY_FOR_SIGNATURE_{RUN_ID}"
    pack_dir.mkdir(parents=True, exist_ok=True)

    for item in items:
        shutil.copy2(item, pack_dir / item.name)

    checklist = pack_dir / "SIGNATURE_CHECKLIST.txt"
    checklist.write_text(f"""SIGNATURE_CHECKLIST
DATE={time.ctime()}
STATUS=READY_FOR_SIGNATURE_AFTER_HUMAN_APPROVAL
APPROVAL_ACTOR=Danijela Đurović Keskin
CHECK_BEFORE_SIGNING:
1. Provjeriti naziv i adresu primaoca.
2. Provjeriti PIB/PDV/CRPS podatke.
3. Provjeriti sve datume, iznose i rokove.
4. Provjeriti da dokument ne sadrži interne oznake koje ne treba slati.
5. Provjeriti da su svi prilozi navedeni i spremni.
6. Po potrebi dati advokatu na pregled.
7. Tek nakon toga potpisati i pečatirati.
ORIGINALS_CHANGED=NO
""", encoding="utf-8")

    print(f"READY_FOR_SIGNATURE_FOLDER={pack_dir}")
    print(f"SIGNATURE_CHECKLIST={checklist}")

def package_factory():
    pack = DIRS["PACKAGES"] / f"TITAN_GRID_DOCUMENT_FACTORY_PACKAGE_{RUN_ID}.tar.gz"
    subprocess.run(["tar", "-czf", str(pack), "-C", str(FACTORY), "."], check=False)
    print(f"PACKAGE={pack}")

def status():
    identity = ensure_identity()
    status_file = DIRS["CONTROL"] / "TITAN_GRID_DOCUMENT_FACTORY_STATUS.txt"
    status_file.write_text(f"""TITAN_GRID_DOCUMENT_FACTORY_UNIVERSAL_V1
DATE={time.ctime()}
FACTORY={FACTORY}
STATUS=ACTIVE_MANUAL_OPERATION
MEMORANDUM=ONE_OFFICIAL_MEMORANDUM
EXECUTIVE_DIRECTOR={identity.get('executive_director')}
DELETE_ORIGINALS=NO
MOVE_ORIGINALS=NO
RENAME_ORIGINALS=NO
AUTO_SEND=NO
DAEMON=NO
AUTO_INTERNET=NO
PUBLISH_POLICY=PUBLISH_HOLD_UNTIL_HUMAN_APPROVAL
COMMANDS:
  tgdf status
  tgdf harvest "tema"
  tgdf draft dopis "PRIMALAC" "TEMA" "UPUTSTVO"
  tgdf draft ugovor "PRIMALAC" "TEMA" "UPUTSTVO"
  tgdf draft aneks "PRIMALAC" "TEMA" "UPUTSTVO"
  tgdf draft opomena "PRIMALAC" "TEMA" "UPUTSTVO"
  tgdf draft odluka "PRIMALAC" "TEMA" "UPUTSTVO"
  tgdf draft zapisnik "PRIMALAC" "TEMA" "UPUTSTVO"
  tgdf approve-latest
  tgdf package
""", encoding="utf-8")

    print("=== TITAN_GRID_DOCUMENT_FACTORY_STATUS ===")
    print(f"FACTORY={FACTORY}")
    print(f"STATUS_FILE={status_file}")
    print("STATUS=ACTIVE_MANUAL_OPERATION")
    print("MEMORANDUM=ONE_OFFICIAL_MEMORANDUM")
    print("PUBLISH_POLICY=PUBLISH_HOLD_UNTIL_HUMAN_APPROVAL")
    print("AUTO_SEND=NO")
    print("DAEMON=NO")
    print("ORIGINALS_CHANGED=NO")

def print_help():
    print("""TITAN GRID DOCUMENT FACTORY COMMANDS

tgdf status
tgdf harvest "tema"
tgdf draft dopis "PRIMALAC" "TEMA" "UPUTSTVO"
tgdf draft ugovor "PRIMALAC" "TEMA" "UPUTSTVO"
tgdf draft aneks "PRIMALAC" "TEMA" "UPUTSTVO"
tgdf draft opomena "PRIMALAC" "TEMA" "UPUTSTVO"
tgdf draft odluka "PRIMALAC" "TEMA" "UPUTSTVO"
tgdf draft zapisnik "PRIMALAC" "TEMA" "UPUTSTVO"
tgdf approve-latest
tgdf package
""")

def main():
    args = sys.argv[1:]
    ensure_identity()

    if not args:
        status()
        return

    cmd = args[0].lower()

    if cmd == "status":
        status()
        return

    if cmd == "help":
        print_help()
        return

    if cmd == "harvest":
        topic = args[1] if len(args) > 1 else ""
        data, j, p = harvest(topic)
        print("=== HARVEST_DONE ===")
        print(f"TOPIC={topic}")
        print(f"RECORDS={len(data.get('records', []))}")
        print(f"HARVEST_JSON={j}")
        print(f"HARVEST_PSV={p}")
        print("ORIGINALS_CHANGED=NO")
        return

    if cmd == "draft":
        if len(args) < 4:
            print("USAGE: tgdf draft dopis \"PRIMALAC\" \"TEMA\" \"UPUTSTVO\"")
            return
        doc_type = args[1]
        recipient = args[2]
        topic = args[3]
        instruction = args[4] if len(args) > 4 else ""
        txt, htmlp, order, harvest_json = create_document(doc_type, recipient, topic, instruction)
        print("=== DOCUMENT_CREATED_IN_PUBLISH_HOLD ===")
        print(f"DOC_TYPE={doc_type}")
        print(f"RECIPIENT={recipient}")
        print(f"TOPIC={topic}")
        print(f"TXT={txt}")
        print(f"HTML={htmlp}")
        print(f"ORDER={order}")
        print(f"HARVEST_JSON={harvest_json}")
        print("STATUS=PUBLISH_HOLD_REVIEW_ONLY")
        print("READY_FOR_SIGNATURE=NO_UNTIL_APPROVE_LATEST")
        print("ORIGINALS_CHANGED=NO")
        return

    if cmd == "approve-latest":
        approve_latest()
        return

    if cmd == "package":
        package_factory()
        return

    print_help()

if __name__ == "__main__":
    main()
