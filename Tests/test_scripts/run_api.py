"""Run selected existing HTTP integration tests with stable case IDs."""
import json
from pathlib import Path
import sys
import unittest

tests = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(tests.parent / "Source_Code" / "src" / "tests"))

from test_website import Website


class CampusConnectAPI(Website):
    pass


if __name__ == "__main__":
    cases = json.loads((tests / "test_data" / "api-cases.json").read_text(encoding="utf-8"))
    suite = unittest.TestSuite()
    for case in cases:
        name = "test_" + case["id"].replace("-", "_")
        setattr(CampusConnectAPI, name, getattr(Website, case["method"]))
        suite.addTest(CampusConnectAPI(name))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
