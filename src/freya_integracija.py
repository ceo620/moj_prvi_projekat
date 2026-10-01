# Modul za integraciju vrednih FREYA i IPHONE segmenata u TITAN GRID
import os
import sys

# Uvozimo nasu gotovu fabriku memoranduma
try:
    from memorandum_factory import napravi_memorandum
except ImportError:
    print("GRESKA: memorandum_factory.py nije pronadjen!")
    sys.exit(1)

FREYA_RESOURCES = {
    "node_type": "HUMAN_GATE_MOBILE",
    "version": "1.1",
    "integrated_segments": [
        "FREYA_IPHONE_ISH_NODE_888",
        "FREYA_RAD_888",
        "IPHONE_888_LOKALNI"
    ]
}

def status_integracije():
    return f"[FREYA CORE] Integrisano {len(FREYA_RESOURCES['integrated_segments'])} kljucna segmenta u TITAN GRID."

def generisi_freya_izvjestaj():
    status_tekst = status_integracije()
    # ReportLab koristi <br/> za novi red u paragrafima
    detalji = "<br/>".join([f"• {seg}" for seg in FREYA_RESOURCES["integrated_segments"]])
    puni_tekst = f"{status_tekst}<br/><br/><b>Aktivni segmenti:</b><br/>{detalji}"

    # Saljemo Freya podatke u nasu fabriku
    pdf_putanja = napravi_memorandum(
        klijent="FREYA MOBILNI KLASTER",
        predmet=f"Status Integracije v{FREYA_RESOURCES['version']}",
        tekst=puni_tekst
    )
    return pdf_putanja

if __name__ == "__main__":
    print("Pokrecem FREYA integraciju...")
    print(status_integracije())
    out_pdf = generisi_freya_izvjestaj()
    print(f"FREYA_IZVJESTAJ_KREIRAN={out_pdf}")
