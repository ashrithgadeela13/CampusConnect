"""Run local performance, persistence and defensive HTTP checks."""
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import json
import math
from pathlib import Path
import sys
import time
import unittest
from urllib.request import urlopen

tests = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(tests.parent / "Source_Code" / "src" / "tests"))
from test_website import Website

data = json.loads((tests / "test_data" / "nonfunctional.json").read_text(encoding="utf-8"))


def request_sample(base, path):
    start = time.perf_counter()
    try:
        with urlopen(base + path, timeout=7) as response:
            response.read()
            status = response.status
    except OSError as error:
        status = str(error)
    return status, (time.perf_counter() - start) * 1000


class LocalChecks(Website):
    def test_NF_01_latency_and_success(self):
        for path in data["paths"]:
            with self.subTest(path=path):
                with urlopen(self.base + path, timeout=7) as response:
                    response.read()
                with ThreadPoolExecutor(max_workers=data["concurrency"]) as pool:
                    samples = list(pool.map(partial(request_sample, self.base), [path] * data["requests"]))
                delays = sorted(ms for _, ms in samples)
                p50 = delays[math.ceil(len(delays) * .5) - 1]
                p95 = delays[math.ceil(len(delays) * .95) - 1]
                successes = sum(status == 200 for status, _ in samples)
                print(f"\n{path}: {successes}/{len(samples)} HTTP 200, p50={p50:.2f} ms, p95={p95:.2f} ms, max={max(delays):.2f} ms", flush=True)
                self.assertEqual(successes, len(samples), [status for status, _ in samples if status != 200])
                self.assertLessEqual(p95, data["max_p95_ms"])

    def test_NF_03_feedback_persists(self):
        guest = self.client()
        status, guide, _ = self.send(guest, "/api/guide", {"question": data["question"]})
        self.assertEqual(status, 200)
        status, _, _ = self.send(guest, "/api/guide/feedback", {
            "receipt": guide["feedbackReceipt"], "solved": False, "reason": data["reason"],
        })
        self.assertEqual(status, 200)
        type(self).stop()
        type(self).launch()
        status, report, _ = self.send(self.admin(), data["dashboard"])
        self.assertEqual(status, 200)
        self.assertTrue(any(row["question"] == data["question"] and row["reason"] == data["reason"]
                            for row in report["items"]))

    def test_NF_04_admin_dashboard_access(self):
        clients = {"guest": self.client(), "student": self.student("nf-student"), "admin": self.admin()}
        for role, expected in data["expected_dashboard_status"].items():
            with self.subTest(role=role):
                actual, _, _ = self.send(clients[role], data["dashboard"])
                print(f"\nDashboard {role}: HTTP {actual} (expected {expected})", flush=True)
                self.assertEqual(actual, expected)

    def test_NF_05_response_headers(self):
        status, _, headers = self.send(self.client(), "/")
        self.assertEqual(status, 200)
        for name, expected in data["security_headers"].items():
            with self.subTest(header=name):
                print(f"\n{name}: {headers.get(name)}", flush=True)
                self.assertEqual(headers.get(name), expected)
        csp = headers.get("Content-Security-Policy", "")
        print(f"\nContent-Security-Policy: {csp}", flush=True)
        self.assertIn("default-src 'self'", csp)
        self.assertIn("frame-ancestors 'none'", csp)


LocalChecks.test_NF_02_bookmarks_persist = Website.test_bookmarks_are_private_and_persist_after_server_restart

if __name__ == "__main__":
    cases = sorted(name for name in vars(LocalChecks) if name.startswith("test_NF_"))
    suite = unittest.TestSuite(LocalChecks(name) for name in cases)
    sys.exit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
