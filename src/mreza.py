import platform

class CvorMreze:
    def __init__(self, naziv, operater, uloga):
        self.naziv = naziv
        self.operater = operater
        self.uloga = uloga
        self.sistem = platform.system()

    def dobi_info(self):
        return f"Čvor: {self.naziv:<10} | Operater: {self.operater:<23} | Uloga: {self.uloga:<15} | OS: {self.sistem}"

class TitanGrid:
    DOPUSTENI_CVOROVI = [
        ("Asus", "Danijela Đurović Keskin", "Human Gate"),
        ("Lenovo WSL", "Danijela Đurović Keskin", "Human Gate"),
        ("Android Termux", "Danijela Đurović Keskin", "Human Gate"),
        ("iPhone iSH", "Danijela Đurović Keskin", "Human Gate"),
        ("MSI Debian", "Onur Keskin", "Drugi operater"),
        ("MacBook Air", "Onur Keskin", "Drugi operater"),
    ]

    def __init__(self):
        self.cvorovi = [CvorMreze(naziv, op, uloga) for naziv, op, uloga in self.DOPUSTENI_CVOROVI]

    def izlistaj_mrezu(self):
        return [cvor.dobi_info() for cvor in self.cvorovi]

if __name__ == "__main__":
    grid = TitanGrid()
    print("=== TITAN GRID REGISTAR (6 ČVOTOVA) ===")
    for info in grid.izlistaj_mrezu():
        print(info)
