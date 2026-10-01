import sys
import os
from pathlib import Path

# Uvozimo naše razvijene module
try:
    from memorandum_factory import napravi_memorandum
    from freya_integracija import generisi_freya_izvjestaj, status_integracije
    from mrezni_kontrolor import proveri_mrezu
    from ast_validator import validiraj_python_fajlove
except ImportError as e:
    print(f"[GRESKA] Problem pri uvozu modula: {e}")

def prikazi_meni():
    print("\n" + "="*45)
    print("       TITAN GRID - CENTRALNA KONZOLA 888    ")
    print("="*45)
    print("1. Generiši Službeni Memorandum (PDF)")
    print("2. Pokreni FREYA Integraciju (PDF Izvještaj)")
    print("3. Pokreni Mrežni Kontrolor (Ping & Logovi)")
    print("4. Pokreni AST Validaciju Izvornog Koda")
    print("5. Otvori Izlazni Folder na Windows Desktopu")
    print("0. Izlaz")
    print("="*45)

def pokreni_cli():
    while True:
        prikazi_meni()
        izbor = input("Izaberi opciju [0-5]: ").strip()
        
        if izbor == "1":
            klijent = input("Unesi ime klijenta/sektora: ").strip() or "INTERNA KOMANDA"
            predmet = input("Unesi predmet: ").strip() or "Službeni Dopis"
            tekst = input("Unesi tekst dopisa: ").strip() or "Testna poruka iz Titan CLI-ja."
            pdf = napravi_memorandum(klijent=klijent, predmet=predmet, tekst=tekst)
            print(f"\n[OK] Memorandum kreiran: {pdf}")
            
        elif izbor == "2":
            print(f"\n{status_integracije()}")
            pdf = generisi_freya_izvjestaj()
            print(f"[OK] FREYA PDF izvještaj kreiran: {pdf}")
            
        elif izbor == "3":
            print("\nPokrećem mrežnu dijagnostiku...")
            proveri_mrezu()
            
        elif izbor == "4":
            print("\nPokrećem AST validaciju sintakse...")
            validiraj_python_fajlove()
            
        elif izbor == "5":
            out_dir = Path.home() / "projekti" / "moj_prvi_projekat" / "izlaz" / "dokumenti"
            os.system(f"explorer.exe $(wslpath -w '{out_dir}') 2>/dev/null &")
            print("\n[OK] Otvoren izlazni folder u Windows Exploreru.")
            
        elif izbor == "0":
            print("\nGašenje Titan CLI konzole. Doviđenja!")
            break
        else:
            print("\n[!] Neispravna opcija, pokušaj ponovo.")

if __name__ == "__main__":
    pokreni_cli()
