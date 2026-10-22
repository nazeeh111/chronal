from pathlib import Path
import tempfile
import unittest

from chronal.artifacts import dump, read, seal, verify_bundle
from chronal.study import run_study


class StudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name) / "study"
        run_study(cls.root, replications=2, first_seed=100)

    def test_study_uses_the_same_integrity_and_replay_entrypoint(self):
        result = verify_bundle(self.root, replay=True)
        self.assertTrue(result["valid"])
        self.assertTrue(result["replayed"])
        self.assertEqual(result["replications"], 2)
        self.assertEqual(result["kind"], "synthetic_selection_study")

    def test_resealed_study_cannot_silently_omit_a_registered_seed(self):
        import shutil

        with tempfile.TemporaryDirectory() as temporary:
            copy = Path(temporary) / "copy"
            shutil.copytree(self.root, copy)
            results = read(copy / "results.json")
            results["observations"].pop()
            dump(copy / "results.json", results)
            seal(copy)
            with self.assertRaisesRegex(ValueError, "registered seeds"):
                verify_bundle(copy, replay=True)


if __name__ == "__main__":
    unittest.main()
