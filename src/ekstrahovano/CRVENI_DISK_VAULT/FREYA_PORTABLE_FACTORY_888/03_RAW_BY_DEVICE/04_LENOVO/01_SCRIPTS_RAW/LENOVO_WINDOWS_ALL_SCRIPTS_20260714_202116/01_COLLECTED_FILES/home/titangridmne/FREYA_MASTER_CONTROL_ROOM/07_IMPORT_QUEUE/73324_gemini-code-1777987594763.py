import os
from weasyprint import HTML

output_pdf_path = "C:/Users/Korisnik/Desktop/TITAN_VALID_OPERATIONAL_LOGISTICS_PLAN.pdf"

# Kreiranje foldera ukoliko ne postoji u sandboxu
if not os.path.exists("C:/Users/Korisnik/Desktop"):
    os.makedirs("C:/Users/Korisnik/Desktop", exist_ok=True)

html_content = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page {
        size: A4;
        margin: 20mm 15mm;
        @bottom-right {
            content: "TITAN — Klasa [888] — Operativni Stub";
            font-family: Arial, sans-serif;
            font-size: 8pt;
            color: #718096;
        }
        @bottom-left {
            content: "STATUS: SYSTEM RED — SAMO ZA INTERNU REVIZIJU";
            font-family: Arial, sans-serif;
            font-size: 8pt;
            font-weight: bold;
            color: #e53e3e;
        }
    }
    body {
        font-family: Arial, sans-serif;
        color: #2d3748;
        line-height: 1.5;
        font-size: 10pt;
    }
    .header {
        border-bottom: 3px solid #7b341e;
        padding-bottom: 10px;
        margin-bottom: 25px;
    }
    .section {
        margin-top: 22px;
        margin-bottom: 12px;
    }
    .section-title {
        font-weight: bold;
        color: #7b341e;
        text-transform: uppercase;
        font-size: 11pt;
    }
    .input-box {
        color: #dd6b20;
        font-weight: bold;
    }
    .kpi-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 15px;
    }
    .kpi-table th {
        background-color: #7b341e;
        color: white;
        font-size: 9pt;
        padding: 8px;
        border: 1px solid #cbd5e0;
    }
    .kpi-table td {
        padding: 8px;
        border: 1px solid #cbd5e0;
        font-size: 9pt;
    }
</style>
</head>
<body>

    <div class="header">
        <h1 style="margin: 0; font-size: 14pt; color: #7b341e; text-transform: uppercase;">OPERATIVNI I LOGISTIČKI MASTER PLAN (RAMP-UP STRATEGIJA)</h1>
        <h2 style="font-size: 11pt; color: #4a5568; margin-top: 5px; margin-bottom: 0;">Standard: Industry 4.0 Operational Excellence & Supply Chain Security Matrix</h2>
    </div>

    <p>Ovaj verifikacioni plan definiše proizvodnu dinamiku, ciljane KPI indikatore i logističke rute za industrijski kompleks <strong>ARS Metal Industries (TITAN)</strong>.</p>

    <div class="section">
        <div class="section-title">1. Proračun i Validacija OEE Stope (RW_004)</div>
        <p>Ukupna efikasnost opreme (OEE) pratiće se kroz tri standardne metričke komponente:</p>
        <table class="kpi-table">
            <thead>
                <tr>
                    <th style="width: 25%;">OEE Komponenta</th>
                    <th style="width: 25%;">Ciljani Parametar</th>
                    <th style="width: 50%;">Metoda Validacije / Izvor Dokaza</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>1. Dostupnost (Availability)</strong></td>
                    <td><span class="input-box">[UNETI %]</span></td>
                    <td>Planirani zastoji, smjene i preventivno održavanje mašina.</td>
                </tr>
                <tr>
                    <td><strong>2. Performanse (Performance)</strong></td>
                    <td><span class="input-box">[UNETI %]</span></td>
                    <td>Brzina rada linije u odnosu na fabrički projektovani maksimum.</td>
                </tr>
                <tr>
                    <td><strong>3. Kvalitet (Quality)</strong></td>
                    <td><span class="input-box">[UNETI %]</span></td>
                    <td>Procenat ispravnih komada bez škarta (First Time Through).</td>
                </tr>
                <tr style="background-color: #f7fafc; font-weight: bold;">
                    <td>KUMULATIVNI OEE TARGET</td>
                    <td>&gt;85%</td>
                    <td><span class="input-box">[ZAKLJUČAN RIZIK EG_007]</span> - Zahtijeva testni run nakon instalacije.</td>
                </tr>
            </tbody>
        </table>
    </div>

    <div class="section">
        <div class="section-title">2. Lanac Snabdijevanja i Logistički Okvir (RW_001)</div>
        <p>Upravljanje ulaznim sirovinama i izlaznim isporukama:</p>
        <ul>
            <li><strong>Primarni dobavljači sirovina:</strong> <span class="input-box">[UNETI NAZIVE I SHA256 KONTRACTA]</span></li>
            <li><strong>Logistički koridori:</strong> Drumska i željeznička mreža sa ključnim čvorištima.</li>
            <li><strong>Dinamika isporuke:</strong> Ciljani rok od 3–7 dana postavlja se kao *okvirni operativni prozor* u prvoj ramp-up fazi, zavisno od stabilizacije carinskih i transportnih protokola.</li>
        </ul>
    </div>

    <div style="background-color: #fffaf0; border-left: 4px solid #dd6b20; padding: 12px; margin-top: 30px; font-size: 9pt;">
        <strong>KONAČNA SMJERNICA ZA AUDIT (Nakon povratka sa odmora):</strong><br>
        Ovim je generisan i poslednji, peti konstitutivni dokument cjelokupne projektne arhitekture. Popunjavanjem parametara tabele i ugradnjom ramp-up plana, uklanja se rizik <strong>EG_002</strong> i projekat se prevodi u potpuno operativno i auditabilno stanje.
    </div>

</body>
</html>
"""

HTML(string=html_content).write_pdf(output_pdf_path)
print("Operativni PDF je uspešno generisan.")