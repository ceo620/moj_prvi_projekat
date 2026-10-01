#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from mrezni_kontrolor import proveri_mrezu

def meni():
    while True:
        print("\n=============================================")
        print("       TITAN GRID - CENTRALNA KONZOLA 888")
        print("=============================================")
        print("1. Generiši Službeni Memorandum (PDF)")
        print("2. Pokreni FREYA Integraciju (PDF Izvještaj)")
        print("3. Pokreni Mrežni Kontrolor (Ping & Logovi + PDF)")
        print("4. Pokreni AST Validaciju Izvornog Koda")
        print("5. Otvori Izlazni Folder na Windows Desktopu")
        print("6. Generiši Ugovor o Poslovnoj Saradnji (PDF & DOCX)")
        print("0. Izlaz")
        print("=============================================")
        
        izbor = input("Izaberi opciju [0-6]: ").strip()
        
        if izbor == "3":
            print("\n[+] Pokrećem Mrežni Kontrolor...")
            proveri_mrezu(generisi_pdf=True)
            input("\n[Pritisni ENTER za povratak u meni...]")
        elif izbor == "0":
            print("\nExiting TITAN CLI...")
            break
        else:
            print("\n[GREŠKA] Nepostojeća ili netestirana opcija, pokušaj ponovo.")

if __name__ == "__main__":
    meni()
