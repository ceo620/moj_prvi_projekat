import unittest
from src.agent_monitor import TitanMonitor

class TestTitanMonitor(unittest.TestCase):
    def setUp(self):
        self.agent = TitanMonitor()

    def test_skeniraj_mrezu(self):
        statusi = self.agent.skeniraj_mrezu()
        self.assertEqual(len(statusi), 6)

    def test_generisi_izvestaj(self):
        izvestaj = self.agent.generisi_izvestaj()
        self.assertIn("TITAN GRID AGENT MONITOR REPORT", izvestaj)
        self.assertIn("Aktivnih čvorova: 6", izvestaj)

if __name__ == "__main__":
    unittest.main()
