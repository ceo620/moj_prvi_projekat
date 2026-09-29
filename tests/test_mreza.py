import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.mreza import CvorMreze

def test_kreiranje_cvora():
    cvor = CvorMreze("TestNode", "Danijela", "Human Gate")
    assert cvor.naziv == "TestNode"
    assert cvor.operater == "Danijela"
    assert cvor.uloga == "Human Gate"
    print("Test kreiranja čvora je uspešno prošao!")

if __name__ == "__main__":
    test_kreiranje_cvora()
