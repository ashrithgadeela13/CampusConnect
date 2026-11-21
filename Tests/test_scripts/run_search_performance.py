"""Benchmark the directory search route with the proposal's catalog and load."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
import math
from pathlib import Path
import platform
import sys
from threading import Barrier
from time import perf_counter
from urllib.request import urlopen

tests = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(tests.parent / "Source_Code" / "src" / "tests"))
from test_website import Website

fixture = json.loads((tests / "test_data" / "nfr01-search.json").read_text(encoding="utf-8"))


def main():
    Website.setUpClass()
    try:
        session = Website()
        admin = session.admin()
        status, catalog, _ = session.send(admin, "/api/resources?status=all")
        assert status == 200
        original = [row for row in catalog["resources"] if row["status"] == "published"]
        assert 0 < len(original) <= fixture["catalog_size"]
        for index in range(fixture["catalog_size"] - len(original)):
            prototype = original[index % len(original)]
            status, _, _ = session.send(admin, "/api/resources", {
                **prototype, "name": f"Synthetic service {index + 1:02d}",
                "summary": f"Synthetic directory entry {index + 1} for local load testing.",
                "description": f"Temporary campus service record {index + 1} for performance measurement.",
                "tags": "synthetic,performance fixture",
            })
            assert status == 201, f"Seeding returned HTTP {status}"
        with urlopen(Website.base + "/api/bootstrap", timeout=7) as response:
            count = len(json.load(response)["resources"])
        assert count == fixture["catalog_size"], f"Expected 40 public services, found {count}"

        queries = fixture["queries"]
        ready = Barrier(fixture["clients"], timeout=30)

        def client(client_id):
            opener = session.client()
            results = []
            for index in range(fixture["requests_per_client"]):
                query = queries[(client_id + index) % len(queries)]
                ready.wait()
                start = perf_counter()
                error = None
                try:
                    status, body, _ = session.send(opener, "/api/search", {"query": query, "category": ""})
                    valid = status == 200 and isinstance(body.get("resourceIds"), list)
                except Exception as exc:
                    status, valid, error = None, False, str(exc)
                elapsed = (perf_counter() - start) * 1000
                results.append({"client": client_id + 1, "request": index + 1, "query": query,
                                "http_status": status, "valid_response": valid, "ms": elapsed, "error": error})
            return results

        with ThreadPoolExecutor(max_workers=fixture["clients"]) as pool:
            samples = [sample for group in pool.map(client, range(fixture["clients"])) for sample in group]
        delays = sorted(row["ms"] for row in samples)
        successful = sum(row["valid_response"] for row in samples)
        on_time = sum(row["valid_response"] and row["ms"] <= fixture["limit_ms"] for row in samples)
        report = {
            "case": "NFR-01", "time": datetime.now().astimezone().isoformat(), "platform": platform.platform(),
            "path": "/api/search", "clients": fixture["clients"], "catalog_size": count,
            "original_services": len(original), "synthetic_services": count - len(original),
            "total": len(samples), "successful": successful, "within_target": on_time,
            "target_ms": fixture["limit_ms"], "required_fraction": fixture["required_fraction"],
            "p95_ms": round(delays[math.ceil(len(delays) * .95) - 1], 2),
            "max_ms": round(delays[-1], 2),
            "status": "Pass" if on_time / len(samples) >= fixture["required_fraction"] else "Fail",
        }
        path = tests / "test_results" / "nfr01-search-performance.json"
        path.parent.mkdir(exist_ok=True)
        print(json.dumps(report, indent=2))
        path.write_text(json.dumps({**report, "requests": samples}, indent=2) + "\n", encoding="utf-8")
        print("Saved:", path)
        return 0 if report["status"] == "Pass" else 1
    finally:
        Website.tearDownClass()


if __name__ == "__main__":
    sys.exit(main())
