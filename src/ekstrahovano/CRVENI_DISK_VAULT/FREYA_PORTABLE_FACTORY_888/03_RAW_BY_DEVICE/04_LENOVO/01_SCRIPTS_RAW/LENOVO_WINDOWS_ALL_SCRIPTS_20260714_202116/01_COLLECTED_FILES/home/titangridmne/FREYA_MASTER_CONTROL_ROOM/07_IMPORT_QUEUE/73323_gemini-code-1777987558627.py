import os
from weasyprint import HTML

output_pdf_path = "C:/Users/Korisnik/Desktop/TITAN_VALID_ESG_TAXONOMY_COMPLIANCE.pdf"

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
            content: "TITAN — Klasa [888] — ESG & Zeleni Stub";
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
        border-bottom: 3px solid #319795;
        padding-bottom: 10px;
        margin-bottom: 25px;
    }
    .section {
        margin-top: 22px;
        margin-bottom: 12px;
    }
    .section-title {
        font-weight: bold;
        color: #2c7a7b;
        text-transform: uppercase;
        font-size: 11pt;
    }
    .input-box {
        color: #dd6b20;
        font-weight: bold;
    }
    .dns-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 15px;
    }
    .dns-table th {
        background-color: #2c7a7b;
        color: white;
        font-size: 9pt;
        padding: 8px;
        border: 1px solid #cbd5e0;
    }
    .dns-table td {
        padding: 8px;
        border: 1px solid #cbd5e0;
        font-size: 9pt;
    }
</style>
</head>
<body>

    <div class="header">
        <h1 style="margin: 0; font-size: 15pt; color: #2c7a7b; text-transform: uppercase;">ESG IZVJEŠTAJ I USKLAĐENOST SA EU TAKSONOMIJOM</h1>
        <h2 style="font-size: 11pt; color: #4a5568; margin-top: 5px; margin-bottom: 0;">Standard: European Green Deal & DNSH (Do No Significant Harm) Framework</h2>
    </div>

    <p>Ovaj verifikacioni manifest služi kao formalni dokazni okvir za procjenu ekoloških i energetskih performansi projekta <strong>ARS Metal Industries (TITAN)</strong> pred evropskim finansijskim institucijama.</p>

    <div class="section">
        <div class="section-title">1. Energetski miks i solarni kapaciteti (MDR / RW_005)</div>
        <p>U cilju postizanja niske karbonske intenzivnosti, projekat predviđa integraciju obnovljivih izvora energije:</p>
        <ul>
            <li><strong>Planirani solarni fotonaponski sistem:</strong> <span class="input-box">[UNETI INSTALIRANU SNAGU U kWp/MWp]</span></li>
            <li><strong>Projektovani procenat energetske nezavisnosti:</strong> Do 70% pokrivenosti iz sopstvenih izvora tokom vršnog opterećenja.</li>
            <li><strong>STATUS DOKAZA:</strong> <span class="input-box">[EG_004 / ZAKLJUČAN RIZIK]</span> — Tvrdnja o 70% energetske nezavisnosti smatra se <em>namjerom implementacije</em> dok se ne priloži zvanični energetski audit i tehničko rješenje potpisano od strane licenciranog elektro-inženjera.</li>
        </ul>
    </div>

    <div class="section">
        <div class="section-title">2. DNSH Matrica (Do No Significant Harm — Bez nanošenja značajne štete)</div>
        <p>Evaluacija 6 ključnih ekoloških ciljeva EU:</p>
        <table class="dns-table">
            <thead>
                <tr>
                    <th style="width: 40%;">Ekološki cilj EU</th>
                    <th style="width: 20%;">Status Usklađenosti</th>
                    <th style="width: 40%;">Zahtijevani Dokaz / Akcija</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>1. Ublažavanje klimatskih promjena</td>
                    <td><strong>U TOKU</strong></td>
                    <td>Proračun smanjenja CO2 emisija u odnosu na tradicionalnu preradu.</td>
                </tr>
                <tr>
                    <td>2. Prilagođavanje klimatskim promjenama</td>
                    <td><strong>U TOKU</strong></td>
                    <td>Procjena rizika od ekstremnih vremenskih nepogoda na lokaciji.</td>
                </tr>
                <tr>
                    <td>3. Održivo korišćenje i zaštita voda</td>
                    <td><span class="input-box">[PROVJERITI]</span></td>
                    <td>Plan upravljanja industrijskim otpadnim vodama.</td>
                </tr>
                <tr>
                    <td>4. Prelazak na cirkularnu ekonomiju</td>
                    <td><strong>U TOKU</strong></td>
                    <td>Ugovor o reciklaži i zbrinjavanju metalnog ostatka i šljake.</td>
                </tr>
            </tbody>
        </table>
    </div>

    <div style="background-color: #e6fffa; border-left: 4px solid #319795; padding: 12px; margin-top: 30px; font-size: 9pt;">
        <strong>SMJERNICA ZA REVIZIJU (Nakon tvog odmora):</strong><br>
        U člana 1. unijeti tačne podatke iz idejnog projekta solarne elektrane. Popunjavanjem ove matrice, privremeni karantin nad parametrom <strong>RW_005</strong> se trajno ukida, a projekat dobija "zeleni" revizorski sertifikat neophodan za EU fondove.
    </div>

</body>
</html>
"""

HTML(string=html_content).write_pdf(output_pdf_path)
print("ESG PDF je uspešno generisan.")