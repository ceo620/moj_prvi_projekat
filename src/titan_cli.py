import sys
import os
import subprocess

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memorandum_factory import napravi_memorandum
from freya_integracija import generisi_freya_izvjestaj, status_integracije
from mrezni_kontrolor import proveri_mrezu
from ast_validator import validiraj_python_fajlove
from ugovor_factory import generisi_ugovor_pdf, generisi_ugovor_docx

def prikazi_meni():
    print("\n=============================================")
    print("       TITAN GRID - CENTRALNA KONZOLA 888    ")
    print("=============================================")
    print("1. Generiši Službeni Memorandum (PDF)")
    print("2. Pokreni FREYA Integraciju (PDF Izvještaj)")
    print("3. Pokreni Mrežni Kontrolor (Ping & Logovi)")
    print("4. Pokreni AST Validaciju Izvornog Koda")
    print("5. Otvori Izlazni Folder na Windows Desktopu")
    print("6. Generiši Ugovor o Poslovnoj Saradnji (PDF & DOCX)")
    print("0. Izlaz")
    print("=============================================")

def main():
    while True:
        prikazi_meni()
        izbor = input("Izaberi opciju [0-6]: ").strip()
        
        if izbor == "1":
            klijent = input("Unesi ime klijenta/sektora: ")
            predmet = input("Unesi naslov/predmet: ")
            tekst = input("Unesi tekst memoranduma: ")
            pdf = napravi_memorandum(klijent, predmet, tekst)
            print(f"\n[USPJEH] Memorandum uspješno kreiran: {pdf}")
            
        elif izbor == "2":
            print(f"\n{status_integracije()}")
            pdf = generisi_freya_izvjestaj()
            print(f"[USPJEH] FREYA izvještaj kreiran: {pdf}")
            
        elif izbor == "3":
            proveri_mrezu()
            print("[USPJEH] Mrežna dijagnostika kompletirana.")
            
        elif izbor == "4":
            validiraj_python_fajlove("src")
            
        elif izbor == "5":
            izlaz_dir = os.path.join(os.getcwd(), "izlaz", "dokumenti")
            os.makedirs(izlaz_dir, exist_ok=True)
            win_path = subprocess.check_output(["wslpath", "-w", izlaz_dir]).decode().strip()
            subprocess.run(["explorer.exe", win_path])
            print(f"[USPJEH] Izlazni folder otvoren u Windows Exploreru: {win_path}")
            
        elif izbor == "6":
            broj = input("Unesi broj ugovora (npr. 888/2026): ")
            narucilac = input("Unesi naziv Naručioca: ")
            izvrsilac = input("Unesi naziv Izvršioca: ")
            predmet = input("Unesi predmet ugovora: ")
            iznos = input("Unesi iznos u EUR: ")
            
            pdf_p = generisi_ugovor_pdf(broj, narucilac, izvrsilac, predmet, iznos)
            docx_p = generisi_ugovor_docx(broj, narucilac, izvrsilac, predmet, iznos)
            print(f"\n[USPJEH] PDF ugovor: {pdf_p}")
            print(f"[USPJEH] DOCX ugovor: {docx_p}")

        elif izbor == "0":
            print("\nZatvaranje TITAN GRID konzole...")
            break
        else:
            print("\n[GREŠKA] Nepostojeća opcija, pokušaj ponovo.")

if __name__ == "__main__":
    main()
