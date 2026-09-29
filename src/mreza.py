import platform

class CvorMreze:
    def __init__(self, naziv, operater, uloga):
        self.naziv = naziv
        self.operater = operater
        self.uloga = uloga
        self.sistem = platform.system()

    def dobi_info(self):
        return f"Čvor: {self.naziv} | Operater: {self.operater} | Uloga: {self.uloga} | OS: {self.sistem}"

if __name__ == "__main__":
    moj_cvor = CvorMreze("Asus", "Danijela Đurović Keskin", "Human Gate")
    print("Inicijalizovan čvor:")
    print(moj_cvor.dobi_info())
