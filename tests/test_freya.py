import unittest
from src.freya_integracija import status_integracije, FREYA_RESOURCES

class TestFreyaIntegracija(unittest.TestCase):
    def test_status_integracije(self):
        msg = status_integracije()
        self.assertIn("[FREYA CORE]", msg)

    def test_freya_resources_structure(self):
        self.assertEqual(FREYA_RESOURCES["node_type"], "HUMAN_GATE_MOBILE")
        self.assertTrue(len(FREYA_RESOURCES["integrated_segments"]) > 0)

if __name__ == "__main__":
    unittest.main()
