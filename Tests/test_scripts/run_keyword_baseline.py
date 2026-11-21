"""Compare the delivered classifier with deterministic lexical overlap."""
import json
from pathlib import Path
import re
import sys

tests = Path(__file__).resolve().parents[1]
source = tests.parent / "Source_Code" / "src"
sys.path.insert(0, str(source / "tests"))
from test_semantic_search import SearchQuality

STOP = set("a an and are at be can do for from have how i in is it me my of on the to want what when where who will with you your need".split())


def tokens(text):
    return set(re.findall(r"[a-z0-9]+", text.lower())) - STOP


def main():
    SearchQuality.setUpClass()
    try:
        evaluator = SearchQuality()
        catalog = {office["id"]: office for office in evaluator.offices}
        profiles = {key: tokens(" ".join(str(office.get(field) or "") for field in
                              ("name", "category_name", "tags", "summary", "description")))
                    for key, office in catalog.items()}
        report = {}
        for dataset in ("heldout", "office-checks", "paraphrase-checks"):
            inputs = json.loads((source / "ai" / (dataset + ".json")).read_text(encoding="utf-8"))
            rows = []
            category_eval = dataset == "heldout"
            for question, expected in inputs:
                words = tokens(question)
                scored = sorted(((-len(words & profile), key) for key, profile in profiles.items()))
                baseline = [key for score, key in scored if score < 0][:3]
                actual = evaluator.ask(question)
                delivered = actual["resourceIds"][:3]
                if category_eval:
                    baseline = list(dict.fromkeys(catalog[key]["category_id"] for key in baseline))
                    delivered = [category["id"] for category in actual["categories"]][:3]
                rows.append({"question": question, "expected": expected, "keyword": baseline,
                             "delivered": delivered, "delivered_method": actual["method"]})
            report[dataset] = {"rows": rows, "total": len(rows)}
            for name in ("keyword", "delivered"):
                top1 = sum(row[name][:1] == [row["expected"]] for row in rows)
                top3 = sum(row["expected"] in row[name] for row in rows)
                report[dataset][name] = {"top1": top1, "top3": top3}
                print(f"{dataset} {name}: top-1 {top1}/{len(rows)}, top-3 {top3}/{len(rows)}")
        path = tests / "test_results" / "keyword-baseline.json"
        path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print("Saved:", path)
    finally:
        SearchQuality.tearDownClass()


if __name__ == "__main__":
    main()
