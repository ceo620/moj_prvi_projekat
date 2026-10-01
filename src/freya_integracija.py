#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from memorandum_factory import napravi_memorandum
except ImportError:
    try:
        from src.memorandum_factory import napravi_memorandum
    except ImportError as e:
        napravi_memorandum = None

FREYA_RESOURCES = {
    "node_type": "HUMAN_GATE_MOBILE",
    "integrated_segments": ["FREYA_PORTABLE_FACTORY_888", "output_harmonized_factory"],
    "resources": ["FREYA_PORTABLE_FACTORY_888", "output_harmonized_factory"]
}

def status_integracije():
    return f"[FREYA CORE] ONLINE | Memorandum dostupan: {napravi_memorandum is not None}"

if __name__ == "__main__":
    print(status_integracije())
