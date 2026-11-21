"""Facilitator runs a timed study with distinct, consenting participants."""
import json
from datetime import datetime
from pathlib import Path
import sys
from time import perf_counter

tests = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(tests.parent / "Source_Code" / "src" / "tests"))
from test_website import Website

fixture = json.loads((tests / "test_data" / "usability-tasks.json").read_text())
path = tests / "test_results" / "nfr06-usability.json"


def normalize(value):
    return "".join(character for character in value.casefold() if character.isalnum())


def save(rows):
    successes = sum(row["success"] for row in rows)
    complete = len(rows) == fixture["participants"]
    report = {"recorded_at": datetime.now().astimezone().isoformat(), "results": rows, "successes": successes,
              "target": fixture["target"], "required_participants": fixture["participants"],
              "status": ("Pass" if successes >= fixture["target"] else "Fail") if complete else "Incomplete"}
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{successes}/{len(rows)} successful. Status: {report['status']}. Saved: {path}")


def study():
    rows = json.loads(path.read_text())["results"] if path.exists() else []
    Website.setUpClass()
    try:
        for index in range(len(rows), fixture["participants"]):
            task = fixture["tasks"][index % len(fixture["tasks"])]
            code = f"P{index + 1:02d}"
            print(f"Open a fresh guest window for {code}: {Website.base}/")
            if input("Press Enter when ready or type stop to pause: ").strip().lower() == "stop":
                break
            start = perf_counter()
            print(f"Read aloud: {task['prompt']}", flush=True)
            input("Press Enter as soon as they identify an office, give up, or reach three minutes: ")
            elapsed = perf_counter() - start
            office = input("Office identified (blank if none): ").strip()
            unassisted = input("Did they complete without help? [y/N] ").strip().lower() == "y"
            passed = normalize(office) == normalize(task["office"]) and unassisted and elapsed <= fixture["seconds"]
            rows.append({"participant": code, "task": task["prompt"], "expected_office": task["office"],
                         "observed_office": office, "seconds": round(elapsed, 2), "unassisted": unassisted,
                         "success": passed})
            save(rows)
    finally:
        Website.tearDownClass()
        save(rows)


if __name__ == "__main__":
    study()
