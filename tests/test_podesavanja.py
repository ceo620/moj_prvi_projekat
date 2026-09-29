import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config.podesavanja import DEBIAN_URL, SISTEM_STATUS

def test_podesavanja():
    assert DEBIAN_URL == "https://deb.debian.org"
    assert SISTEM_STATUS == "aktivan"
    print("Svi konfiguracioni testovi su uspesno prosli!")

if __name__ == "__main__":
    test_podesavanja()
