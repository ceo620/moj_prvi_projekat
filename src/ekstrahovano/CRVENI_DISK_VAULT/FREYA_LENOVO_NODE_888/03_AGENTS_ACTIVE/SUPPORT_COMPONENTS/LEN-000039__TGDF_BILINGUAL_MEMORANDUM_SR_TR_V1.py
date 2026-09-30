import json, time, html, os, re, subprocess
from pathlib import Path

HOME = Path.home()
FACTORY = HOME / "TITAN_GRID_DOCUMENT_FACTORY"

IDENTITY_FILE = FACTORY / "01_IDENTITY_AND_MEMORANDUM" / "TITAN_GRID_OFFICIAL_IDENTITY.json"
LATEST_DEEP = FACTORY / "00_CONTROL" / "LATEST_DEEP_SIGNAL_LAKE.json"
PUBLISH = FACTORY / "06_PUBLISH_HOLD_REVIEW"
TEMPLATES = FACTORY / "04_TEMPLATES"
LOGOS = FACTORY / "08_LOGOS_SEALS_SIGNATURES"

RUN_ID = time.strftime("%Y%m%d_%H%M%S")

for p in [PUBLISH, TEMPLATES, LOGOS]:
    p.mkdir(parents=True, exist_ok=True)

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
    "memo_title_sr": "ZVANIČNI MEMORANDUM DRUŠTVA",
    "memo_title_tr": "ŞİRKET RESMÎ ANTETLİ YAZISI",
    "logo_path": "",
}

def load_identity():
    if IDENTITY_FILE.exists():
        try:
            d = json.loads(IDENTITY_FILE.read_text(encoding="utf-8", errors="ignore"))
            out = dict(DEFAULT_IDENTITY)
            out.update(d)
            return out
        except Exception:
            return DEFAULT_IDENTITY
    return DEFAULT_IDENTITY

def find_logo(identity):
    lp = identity.get("logo_path", "")
    if lp and Path(lp).exists():
        return lp

    candidates = []
    for root in [LOGOS, FACTORY]:
        if root.exists():
            for ext in ["*.png", "*.jpg", "*.jpeg", "*.webp", "*.svg"]:
                for p in root.rglob(ext):
                    low = str(p).lower()
                    if any(x in low for x in ["logo", "ars", "memorandum"]):
                        candidates.append(p)

    if candidates:
        return str(sorted(candidates, key=lambda x: x.stat().st_mtime, reverse=True)[0])
    return ""

def load_deep_data():
    if LATEST_DEEP.exists():
        try:
            return json.loads(LATEST_DEEP.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            return {}
    return {}

identity = load_identity()
logo = find_logo(identity)

deep = load_deep_data()
stats = deep.get("stats", {})
lake_jsonl = deep.get("lake_jsonl", "")
top_records = deep.get("top_records", [])

recipient = stats.get("recipient", "CIVIL ENGINEERING DOO")
topic = stats.get("topic", "Aneks ugovora za projektovanje hale")
instruction = stats.get("instruction", "Koristiti sve signale sa mašine i dokument ostaviti u PUBLISH_HOLD.")
files_seen = stats.get("files_seen", "[NIJE JOŠ ZAVRŠEN DEEP HARVEST]")
files_indexed = stats.get("files_indexed", "[NIJE JOŠ ZAVRŠEN DEEP HARVEST]")
bytes_seen = stats.get("bytes_seen", "[NIJE JOŠ ZAVRŠEN DEEP HARVEST]")

deep_signal_lake = lake_jsonl or "[DEEP_SIGNAL_LAKE — ČEKA SE ZAVRŠETAK]"
top_signal_json = str(FACTORY / "11_DEEP_SIGNAL_LAKE" / "DEEP_SIGNAL_TOP_[RUN_ID].json")
report = str(FACTORY / "11_DEEP_SIGNAL_LAKE" / "REPORTS" / "DEEP_SIGNAL_REPORT_[RUN_ID].txt")
document_txt = str(PUBLISH / "DEEP_ALL_SIGNALS_[DOKUMENT].txt")
document_html = str(PUBLISH / "DEEP_ALL_SIGNALS_[DOKUMENT].html")

rows = [
    (
        "DEEP_SIGNAL_LAKE",
        "Dubinsko jezero signala — glavni indeks svih pronađenih signala sa mašine.",
        "Derin Sinyal Havuzu — bilgisayarda bulunan tüm sinyallerin ana indeksi.",
        deep_signal_lake,
    ),
    (
        "TOP_SIGNAL_JSON",
        "JSON fajl sa najvažnijim signalima koji su korišćeni za pripremu dokumenta.",
        "Belgenin hazırlanmasında kullanılan en önemli sinyalleri içeren JSON dosyası.",
        top_signal_json,
    ),
    (
        "REPORT",
        "Izvještaj o dubinskom harvestu: broj fajlova, izvorne putanje, greške i top signali.",
        "Derin hasat raporu: dosya sayısı, kaynak yolları, hatalar ve en önemli sinyaller.",
        report,
    ),
    (
        "DOCUMENT_TXT",
        "Tekstualna verzija dokumenta za ljudski pregled.",
        "İnsan incelemesi için metin formatındaki belge.",
        document_txt,
    ),
    (
        "DOCUMENT_HTML",
        "HTML verzija dokumenta na memorandumu, pogodna za pregled i štampu u PDF.",
        "Antetli HTML belge; inceleme ve PDF olarak yazdırma için uygundur.",
        document_html,
    ),
    (
        "STATUS=PUBLISH_HOLD_REVIEW_ONLY",
        "Status: dokument je zadržan za ljudski pregled i nije odobren za slanje.",
        "Durum: belge insan incelemesi için bekletilmektedir ve gönderim için onaylanmamıştır.",
        "PUBLISH_HOLD_REVIEW_ONLY",
    ),
    (
        "ORIGINALS_CHANGED=NO",
        "Originalni fajlovi nijesu promijenjeni.",
        "Orijinal dosyalar değiştirilmemiştir.",
        "NO",
    ),
    (
        "AUTO_SEND=NO",
        "Automatsko slanje je isključeno.",
        "Otomatik gönderim kapalıdır.",
        "NO",
    ),
    (
        "READY_FOR_SIGNATURE=NO_UNTIL_HUMAN_REVIEW",
        "Dokument nije spreman za potpisivanje dok ga ne pregleda i odobri ovlašćeno lice.",
        "Belge, yetkili kişi tarafından incelenip onaylanmadan imzaya hazır değildir.",
        "NO_UNTIL_HUMAN_REVIEW",
    ),
]

top_signal_rows = []
for r in top_records[:30]:
    top_signal_rows.append((
        r.get("name", ""),
        f"Signal: {r.get('name','')} | score={r.get('score','')} | fingerprint={r.get('fingerprint','')}",
        f"Sinyal: {r.get('name','')} | puan={r.get('score','')} | parmak izi={r.get('fingerprint','')}",
        r.get("path", ""),
    ))

if not top_signal_rows:
    top_signal_rows.append((
        "Čeka se Deep Signal Lake",
        "Top signali će biti dodati nakon završetka dubinskog harvesta.",
        "Derin hasat tamamlandıktan sonra en önemli sinyaller eklenecektir.",
        "[PENDING]",
    ))

doc_no = f"ARS-TGDF-SR-TR-{RUN_ID}"
date = time.strftime("%d.%m.%Y.")

logo_html = ""
if logo and Path(logo).exists():
    logo_html = f'<img src="{html.escape(logo)}" class="logo">'
else:
    logo_html = '<div class="logo-placeholder">LOGO<br>ARS METAL INDUSTRIES DOO</div>'

def esc(x):
    return html.escape(str(x))

txt = f"""
ARS METAL INDUSTRIES DOO PODGORICA
ZVANIČNI MEMORANDUM DRUŠTVA / ŞİRKET RESMÎ ANTETLİ YAZISI

Broj / Sayı: {doc_no}
Datum / Tarih: {date}
Mjesto / Yer: Podgorica

Za / Alıcı: {recipient}

Predmet / Konu:
Dvojezični srpsko-turski memorandum za Deep Signal Lake dokument:
{topic}

Izvršni direktor / İcra Direktörü:
Danijela Đurović Keskin

SAŽETAK / ÖZET

SRPSKI:
Ovaj memorandum potvrđuje da dokument nastaje iz TITAN GRID Document Factory sistema, na osnovu Deep Signal Lake indeksa, uz PUBLISH_HOLD režim i bez automatskog slanja.

TÜRKÇE:
Bu memorandum, belgenin TITAN GRID Document Factory sistemi tarafından Deep Signal Lake indeksi temel alınarak hazırlandığını, PUBLISH_HOLD modunda tutulduğunu ve otomatik gönderim yapılmadığını teyit eder.

DEEP SIGNAL LAKE STATUS:
files_seen / görülen dosyalar: {files_seen}
files_indexed / indekslenen dosyalar: {files_indexed}
bytes_seen / görülen bayt: {bytes_seen}

POTPIS / İMZA

Za ARS METAL INDUSTRIES DOO PODGORICA

____________________________________
Danijela Đurović Keskin
Izvršni direktor / İcra Direktörü

Pečat društva / Şirket kaşesi: ______________________

Datum potpisivanja / İmza tarihi: __________________
""".strip() + "\n"

txt_path = PUBLISH / f"ARS_BILINGUAL_MEMORANDUM_SR_TR_{RUN_ID}.txt"
html_path = PUBLISH / f"ARS_BILINGUAL_MEMORANDUM_SR_TR_{RUN_ID}.html"

txt_path.write_text(txt, encoding="utf-8")

rows_html = ""
for key, sr, tr, value in rows:
    rows_html += f"""
    <tr>
      <td class="key">{esc(key)}<br><span class="value">{esc(value)}</span></td>
      <td>{esc(sr)}</td>
      <td>{esc(tr)}</td>
    </tr>
    """

signals_html = ""
for name, sr, tr, path in top_signal_rows:
    signals_html += f"""
    <tr>
      <td class="key">{esc(name)}<br><span class="value">{esc(path)}</span></td>
      <td>{esc(sr)}</td>
      <td>{esc(tr)}</td>
    </tr>
    """

html_doc = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>ARS Metal Industries DOO — Srpsko-turski memorandum</title>
<style>
body {{
  font-family: "Times New Roman", serif;
  margin: 18mm;
  color: #111;
  line-height: 1.32;
}}
.header {{
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  border-bottom: 2px solid #111;
  padding-bottom: 12px;
  margin-bottom: 18px;
}}
.company {{
  font-size: 22px;
  font-weight: bold;
  text-transform: uppercase;
}}
.memo {{
  font-size: 13px;
  font-weight: bold;
  margin-top: 4px;
}}
.small {{
  font-size: 12.5px;
  line-height: 1.35;
  margin-top: 8px;
}}
.logo {{
  max-width: 210px;
  max-height: 90px;
}}
.logo-placeholder {{
  width: 190px;
  height: 78px;
  border: 1px solid #555;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  font-size: 12px;
}}
.meta {{
  margin: 16px 0;
  font-size: 14px;
}}
.subject {{
  border: 1px solid #111;
  padding: 10px;
  margin: 14px 0 18px 0;
}}
table {{
  width: 100%;
  border-collapse: collapse;
  margin-top: 12px;
  font-size: 13px;
}}
th, td {{
  border: 1px solid #333;
  vertical-align: top;
  padding: 8px;
}}
th {{
  background: #eee;
  text-align: left;
}}
.key {{
  width: 26%;
  font-weight: bold;
}}
.value {{
  font-weight: normal;
  font-size: 11px;
  word-break: break-all;
}}
.section-title {{
  margin-top: 24px;
  font-size: 16px;
  font-weight: bold;
  border-bottom: 1px solid #111;
  padding-bottom: 5px;
}}
.signature {{
  margin-top: 34px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 28px;
}}
.sig-box {{
  min-height: 150px;
  border-top: 1px solid #111;
  padding-top: 10px;
}}
.notice {{
  font-size: 11px;
  color: #555;
  border-top: 1px solid #ccc;
  margin-top: 28px;
  padding-top: 8px;
}}
@media print {{
  body {{ margin: 16mm; }}
  .notice {{ display: none; }}
}}
</style>
</head>
<body>

<div class="header">
  <div>
    <div class="company">{esc(identity.get("official_name"))}</div>
    <div class="memo">ZVANIČNI MEMORANDUM DRUŠTVA / ŞİRKET RESMÎ ANTETLİ YAZISI</div>
    <div class="small">
      Sjedište/adresa / Merkez-adres: {esc(identity.get("address"))}<br>
      PIB / Vergi kimlik no: {esc(identity.get("pib"))}<br>
      PDV / KDV: {esc(identity.get("pdv"))}<br>
      CRPS / Sicil no: {esc(identity.get("crps"))}<br>
      Telefon / Telefon: {esc(identity.get("phone"))}<br>
      E-mail / E-posta: {esc(identity.get("email"))}<br>
      Web / Web: {esc(identity.get("web"))}<br>
      Žiro račun / IBAN: {esc(identity.get("bank_account"))}
    </div>
  </div>
  <div>{logo_html}</div>
</div>

<div class="meta">
  <b>Broj / Sayı:</b> {esc(doc_no)}<br>
  <b>Datum / Tarih:</b> {esc(date)}<br>
  <b>Mjesto / Yer:</b> Podgorica<br>
  <b>Za / Alıcı:</b> {esc(recipient)}
</div>

<div class="subject">
  <b>Predmet / Konu:</b><br>
  Srpsko-turski dvojezični memorandum za Deep Signal Lake dokument: {esc(topic)}
</div>

<div class="section-title">1. Sažetak / Özet</div>

<table>
  <tr>
    <th>Srpski</th>
    <th>Türkçe</th>
  </tr>
  <tr>
    <td>
      Ovaj memorandum potvrđuje da dokument nastaje iz TITAN GRID Document Factory sistema,
      na osnovu Deep Signal Lake indeksa, uz PUBLISH_HOLD režim i bez automatskog slanja.
      Dokument nije spreman za potpis dok ga ne pregleda i odobri ovlašćeno lice.
    </td>
    <td>
      Bu memorandum, belgenin TITAN GRID Document Factory sistemi tarafından Deep Signal Lake
      indeksi temel alınarak hazırlandığını, PUBLISH_HOLD modunda tutulduğunu ve otomatik
      gönderim yapılmadığını teyit eder. Belge, yetkili kişi tarafından incelenip onaylanmadan
      imzaya hazır değildir.
    </td>
  </tr>
</table>

<div class="section-title">2. Kontrolne linije / Kontrol Satırları</div>

<table>
  <tr>
    <th>Oznaka / Etiket</th>
    <th>Srpski</th>
    <th>Türkçe</th>
  </tr>
  {rows_html}
</table>

<div class="section-title">3. Deep Signal Lake statistika / Derin Sinyal Havuzu İstatistikleri</div>

<table>
  <tr>
    <th>Polje / Alan</th>
    <th>Vrijednost / Değer</th>
  </tr>
  <tr><td>files_seen / görülen dosyalar</td><td>{esc(files_seen)}</td></tr>
  <tr><td>files_indexed / indekslenen dosyalar</td><td>{esc(files_indexed)}</td></tr>
  <tr><td>bytes_seen / görülen bayt</td><td>{esc(bytes_seen)}</td></tr>
  <tr><td>instruction / talimat</td><td>{esc(instruction)}</td></tr>
</table>

<div class="section-title">4. Top signali / En Önemli Sinyaller</div>

<table>
  <tr>
    <th>Fajl / Dosya</th>
    <th>Srpski</th>
    <th>Türkçe</th>
  </tr>
  {signals_html}
</table>

<div class="section-title">5. Potpis / İmza</div>

<div class="signature">
  <div class="sig-box">
    Za ARS METAL INDUSTRIES DOO PODGORICA<br><br><br>
    ____________________________________<br>
    Danijela Đurović Keskin<br>
    Izvršni direktor<br><br>
    Pečat društva: ______________________<br>
    Datum potpisivanja: __________________
  </div>

  <div class="sig-box">
    ARS METAL INDUSTRIES DOO PODGORICA adına<br><br><br>
    ____________________________________<br>
    Danijela Đurović Keskin<br>
    İcra Direktörü<br><br>
    Şirket kaşesi: ______________________<br>
    İmza tarihi: __________________
  </div>
</div>

<div class="notice">
  TITAN GRID DOCUMENT FACTORY — BILINGUAL REVIEW VERSION — PUBLISH_HOLD — NO AUTO SEND.
  Ovo nije ovjereni sudski prevod. / Bu yeminli tercüme değildir.
</div>

</body>
</html>
"""

html_path.write_text(html_doc, encoding="utf-8")

print("=== ARS_BILINGUAL_MEMORANDUM_SR_TR_CREATED ===")
print(f"TXT={txt_path}")
print(f"HTML={html_path}")
print("LANGUAGES=SR_LATIN_TR")
print("STATUS=PUBLISH_HOLD_REVIEW_ONLY")
print("AUTO_SEND=NO")
print("READY_FOR_SIGNATURE=NO_UNTIL_HUMAN_REVIEW")

try:
    subprocess.run(["explorer.exe", str(html_path).replace("/mnt/c/", "C:/")], timeout=3)
except Exception:
    pass
