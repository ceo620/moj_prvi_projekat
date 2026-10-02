#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import ast

def validiraj_kod():
    src_dir = os.path.dirname(os.path.abspath(__file__))
    greske = []
    fajlovi_provereni = 0

    for root, dirs, files in os.walk(src_dir):
        # Ignoriši arhivske i fabričke direktorijume u potpunosti
        if "fabrika" in root or "ekstrahovano" in root:
            continue

        for file in files:
            if file.endswith(".py"):
                fajlovi_provereni += 1
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        code = f.read()
                    ast.parse(code)
                except Exception as e:
                    greske.append(f"{os.path.relpath(filepath, src_dir)}: {e}")

    if greske:
        print("[GRESKA] Pronadjene sintaksne greske u operativnim modulima:")
        for g in greske:
            print(f"  - {g}")
    else:
        print(f"[PASS] Svi operativni moduli ({fajlovi_provereni} Python datoteka) su sintaksno ispravni!")

if __name__ == "__main__":
    validiraj_kod()
