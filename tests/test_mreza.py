import unittest
from src.mreza import TitanGrid

class TestTitanGrid(unittest.TestCase):
    def setUp(self):
        self.mreza = TitanGrid()
        self.iphone = self.mreza.iphone_cvor

    def test_ukupno_cvorova(self):
        self.assertEqual(len(self.mreza.cvorovi), 6)

    def test_human_gate_broj(self):
        self.assertEqual(len(self.mreza.dobij_human_gate_cvorove()), 4)

    def test_iphone_funkcionalnosti(self):
        self.iphone.aktiviraj_ai_okruzenje()
        self.assertTrue(self.iphone.venv_aktivan)
        self.iphone.izvrsi_git_sinhronizaciju("dev")
        self.assertEqual(self.iphone.git_grana, "dev")
        self.assertIn("[HUMAN GATE APPROVAL]", self.iphone.autorizuj_promenu("v1.1"))

if __name__ == "__main__":
    unittest.main()
