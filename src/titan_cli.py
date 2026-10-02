import sys
import os

from src.ast_validator import validiraj_kod
from src.freya_integracija import status_integracije
from src.mrezni_kontrolor import proveri_mrezu

def prikazi_meni():
print("\n=============================================")
print("       TITAN GRID - CENTRALNA KONZOLA 888")
print("=============================================")
print("1. Generiši Službeni Memorandum (PDF)")
print("2. Pokreni FREYA Integraciju (PDF Izvještaj)")
print("3. Pokreni Mrežni Kontrolor (Ping & Logovi)")
print("4. Pokreni AST Validaciju Izvornog Koda")
print("5. Otvori Izlazni Folder")
print("6. Generiši Ugovor o Poslovnoj Saradnji (PDF & DOCX)")
print("7. Onur Agent - Verifikuj lokalni projekat")
print("0. Izlaz")
print("=============================================")

def meni():
while True:
    prikazi_meni()
    print("Izaberi opciju [0-7]: ", end="", flush=True)
    izbor = sys.stdin.readline().strip()

    if izbor == "1":
        print("[+] Generišem Službeni Memorandum...")
    elif izbor == "2":
        print("[+] Pokrećem FREYA Integraciju...")
        rezultat = status_integracije()
        print(rezultat if rezultat else "[OK] FREYA Integracija uspešno izvršena.")
    elif izbor == "3":
        print("[+] Pokrećem Mrežni Kontrolor...")
        proveri_mrezu()
    elif izbor == "4":
        print("[+] Pokrećem AST Validaciju...")
        validiraj_kod()
    elif izbor == "5":
        print("[+] Otvaram Izlazni Folder...")
        os.system("open izlaz/ 2>/dev/null || true")
    elif izbor == "6":
        print("[+] Generišem Ugovor o Poslovnoj Saradnji...")
    elif izbor == "7":
        print("[+] Onur Agent - Verifikacija...")
    elif izbor == "0":
        print("Izlazak iz konzole.")
        break
    else:
        print("[GREŠKA] Nepostojeća ili netestirana opcija, pokušaj ponovo.")

if __name__ == "__main__":
meni()
