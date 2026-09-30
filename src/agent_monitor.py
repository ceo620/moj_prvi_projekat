# Autonomni AI Monitor Agent za TITAN GRID mrežu
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.mreza import TitanGrid
from src.freya_integracija import status_integracije

class TitanMonitor:
    def __init__(self):
        self.grid = TitanGrid()
        self.doc_path = os.path.expanduser('/mnt/c/Users/ceo/OneDrive/Desktop/FIRMA_DOKUMENTACIJA')

    def skeniraj_mrezu(self):
        statusi = []
        for cvor in self.grid.cvorovi:
            is_hg = " [HUMAN GATE]" if getattr(cvor, 'human_gate', False) else ""
            statusi.append(f"Čvor: {cvor.naziv} ({cvor.OS}){is_hg} - OK")
        return statusi

    def proveri_fabriku_dokumenata(self):
        if os.path.exists(self.doc_path):
            kompanije = [d for d in os.listdir(self.doc_path) if os.path.isdir(os.path.join(self.doc_path, d))]
            return f"[FACTORY OK] Pronađeno {len(kompanije)} kompanijskih foldera."
        return "[FACTORY STANDBY] Dokumentacija još nije generisana."

    def generisi_izvestaj(self):
        cvorovi_status = self.skeniraj_mrezu()
        freya_status = status_integracije()
        factory_status = self.proveri_fabriku_dokumenata()

        izvestaj = [
            "=== TITAN GRID AGENT MONITOR REPORT ===",
            f"Aktivnih čvorova: {len(cvorovi_status)}",
            f"Integracija: {freya_status}",
            f"Fabrika Dokumenta: {factory_status}",
            "--- STATUS ČVORIŠTA ---"
        ] + cvorovi_status
        return "\n".join(izvestaj)

if __name__ == "__main__":
    agent = TitanMonitor()
    print(agent.generisi_izvestaj())
