# MAGNUS DEBIAN DOCUMENT FACTORY 888
import sys
import os

DOCX_AVAILABLE = False
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    pass

class MemorandumFactory:
    def __init__(self):
        self.docx_enabled = DOCX_AVAILABLE

    def status(self):
        if self.docx_enabled:
            return "[FACTORY READY] Puna podrška za DOCX i PDF generisanje."
        return "[FACTORY LIMITED] Generisanje onemogućeno — nedostaje 'python-docx'."

if __name__ == "__main__":
    factory = MemorandumFactory()
    print(factory.status())
