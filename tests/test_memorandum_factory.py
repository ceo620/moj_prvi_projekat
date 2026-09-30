import unittest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

class TestMemorandumFactory(unittest.TestCase):
    def test_factory_file_exists(self):
        factory_path = os.path.expanduser('~/projekti/moj_prvi_projekat/src/memorandum_factory.py')
        self.assertTrue(os.path.exists(factory_path))

    def test_factory_importable(self):
        try:
            import src.memorandum_factory as mf
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Uvoz memorandum_factory modula nije uspeo: {e}")

if __name__ == "__main__":
    unittest.main()
