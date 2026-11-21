"""Score CampusConnect against labeled questions and save observed answers."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import platform
import re
import sys

tests = Path(__file__).resolve().parents[1]
source = tests.parent / "Source_Code" / "src"
sys.path.insert(0, str(source / "tests"))
from test_semantic_search import SearchQuality

fixture = json.loads((tests / "test_data" / "ai-eval.json").read_text(encoding="utf-8"))


def search():
    groups = {}
    for dataset in ("office-checks", "paraphrase-checks", "unsupported"):
        rows = json.loads((source / "ai" / (dataset + ".json")).read_text(encoding="utf-8"))
        groups[dataset] = ([{"question": q, "state": "none"} for q in rows] if dataset == "unsupported"
                           else [{"question": q, "office": office} for q, office in rows])
    groups["extra"] = fixture["extra"]
    SearchQuality.setUpClass()
    try:
        evaluator = SearchQuality()
        output = {}
        for name, cases in groups.items():
            rows = []
            for case in cases:
                actual = evaluator.ask(case["question"])
                ids = actual["resourceIds"]
                row = {**case, "actual_offices": ids, "actual_state": actual["state"], "method": actual["method"]}
                if "office" in case:
                    row.update(top1=ids[:1] == [case["office"]], top3=case["office"] in ids[:3])
                    row["pass"] = row["top1"] and row["method"] == "model2vec"
                else:
                    row["pass"] = actual["state"] == case["state"] and row["method"] == "model2vec"
                rows.append(row)
            ranking = [row for row in rows if "top1" in row]
            labels = [row for row in rows if "state" in row]
            print(f"{name}: top-1 {sum(r['top1'] for r in ranking)}/{len(ranking)}, "
                  f"top-3 {sum(r['top3'] for r in ranking)}/{len(ranking)}, "
                  f"expected state {sum(r['actual_state'] == r['state'] for r in labels)}/{len(labels)}")
            output[name] = rows
        return output
    finally:
        SearchQuality.tearDownClass()


def draft():
    from playwright.sync_api import expect, sync_playwright
    from test_website import Website

    Website.setUpClass()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page()
            page.goto(Website.base + "/#/guide")
            page.locator("#guide-question").fill(fixture["draft"]["question"])
            page.get_by_role("button", name="Find resources").click()
            page.get_by_role("button", name="Draft a question").click()
            textarea = page.locator("#office-draft-text")
            expect(textarea).to_be_visible()
            text = textarea.input_value()
            related = bool(re.search(fixture["draft"]["term_pattern"], text, re.I))
            return {"status": "Pass" if related else "Fail", "text": text, "mentions_relevant_topic": related}
    finally:
        Website.tearDownClass()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--draft", action="store_true", help="also exercise Draft a question in Playwright")
    parser.add_argument("--output", default="ai-eval-mac.json")
    args = parser.parse_args()
    output = {"time": datetime.now().astimezone().isoformat(), "platform": platform.platform(), "search": search()}
    output["draft"] = {"status": "Not run", "reason": "Run with --draft to exercise the browser."}
    if args.draft:
        try:
            output["draft"] = draft()
        except Exception as error:
            output["draft"] = {"status": "Error", "reason": str(error)}
    path = tests / "test_results" / args.output
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print("Draft check:", output["draft"]["status"])
    print("Saved:", path)
