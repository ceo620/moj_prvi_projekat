#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import glob

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

FREYA_RESOURCES = {
    "node_type": "HUMAN_GATE_MOBILE",
    "integrated_segments": ["FREYA_PORTABLE_FACTORY_888", "output_harmonized_factory"],
    "resources": ["FREYA_PORTABLE_FACTORY_888", "output_harmonized_factory"]
}

def status_integracije():
    # Provera postojanja kreiranih PDF memoranduma/ugovora u izlaznom folderu
    pdf_fajlovi = glob.glob("izlaz/dokumenti/*.pdf")
    memorandum_dostupan = len(pdf_fajlovi) > 0
    return f"[FREYA CORE] ONLINE | Memorandum dostupan: {memorandum_dostupan}"

if __name__ == "__main__":
    print(status_integracije())
