class CvorMreze:
    def __init__(self, naziv, operater, uloga, OS, verifikovan=True):
        self.naziv = naziv
        self.operater = operater
        self.uloga = uloga
        self.OS = OS
        self.verifikovan = verifikovan

class iPhoneConsoleNode(CvorMreze):
    def __init__(self):
        super().__init__(
            naziv="danijela@IPHONE_ISH",
            operater="Danijela Đurović Keskin",
            uloga="Human Gate Ultra-Mobile Console",
            OS="Alpine Linux (iSH)",
            verifikovan=True
        )
        self.ssh_kljuc_aktivan = True
        self.venv_aktivan = False
        self.git_grana = "dev"

    def aktiviraj_ai_okruzenje(self):
        self.venv_aktivan = True
        return "Virtuelno okruzenje uspešno aktivirano."

    def izvrsi_git_sinhronizaciju(self, grana="dev"):
        if not self.ssh_kljuc_aktivan:
            raise PermissionError("SSH neautorizovan!")
        self.git_grana = grana
        return f"Sinhronizovana grana {grana}."

    def autorizuj_promenu(self, opis):
        return f"[HUMAN GATE APPROVAL] Danijela Đurović Keskin: {opis}"

class TitanGrid:
    def __init__(self):
        self.iphone_cvor = iPhoneConsoleNode()
        self.cvorovi = [
            CvorMreze("Asus Laptop", "Danijela Đurović Keskin", "Human Gate Primary Node", "Windows"),
            CvorMreze("Lenovo Laptop", "Danijela Đurović Keskin", "Human Gate Node", "Ubuntu WSL"),
            CvorMreze("Android Telefon", "Danijela Đurović Keskin", "Human Gate Mobile", "Android Termux"),
            self.iphone_cvor,
            CvorMreze("MSI Laptop", "Onur Keskin", "Secondary Operator Node", "Debian"),
            CvorMreze("MacBook Air", "Onur Keskin", "Secondary Operator Node", "macOS")
        ]

    def dobij_human_gate_cvorove(self):
        return [c for c in self.cvorovi if "Human Gate" in c.uloga]
