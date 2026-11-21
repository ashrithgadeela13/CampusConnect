"""Run case-ID-based CampusConnect unit tests from the project root."""
import json
from pathlib import Path
import sys
import unittest

tests = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(tests.parent / "Source_Code" / "src"))

from backend import auth, common

operations = {
    "text": common.text,
    "only": common.only,
    "day_string": common.day_string,
    "validate_password": auth.validate_password,
    "require": auth.require,
}


def build_test(case):
    def test(self):
        args = case["input"]
        if "repeat" in case:
            args[0]["question"] *= case["repeat"]
        operation = operations[case["operation"]]
        if "status" in case:
            with self.assertRaises(common.Problem) as error:
                operation(*args)
            self.assertEqual(error.exception.status, case["status"])
        elif "expected_length" in case:
            self.assertEqual(len(operation(*args)), case["expected_length"])
        else:
            self.assertEqual(operation(*args), case["expected"])
    return test


class CampusConnectUnitTests(unittest.TestCase):
    pass


for case in json.loads((tests / "test_data" / "unit.json").read_text(encoding="utf-8")):
    name = "test_" + case["id"].replace("-", "_") + "_" + case["operation"]
    setattr(CampusConnectUnitTests, name, build_test(case))


if __name__ == "__main__":
    unittest.main(verbosity=2)
