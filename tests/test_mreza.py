import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.mreza import TitanGrid

def test_titan_grid():
    grid = TitanGrid()
    assert len(grid.cvorovi) == 6, "Mreža mora imati tačno 6 čvorova!"
    
    human_gate_count = sum(1 for c in grid.cvorovi if c.uloga == "Human Gate")
    assert human_gate_count == 4, "Danijela mora voditi tačno 4 Human Gate čvora!"
    
    print("Svi integracioni testovi za TITAN GRID su uspešno prošli!")

if __name__ == "__main__":
    test_titan_grid()
