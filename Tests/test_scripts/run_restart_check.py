"""Verify committed CampusConnect data after restarting its local process."""
import json
from pathlib import Path
import platform
import sys

tests = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(tests.parent / "Source_Code" / "src" / "tests"))
from test_website import Website, PW

data = json.loads((tests / "test_data" / "restart.json").read_text(encoding="utf-8"))


def run(report):
    Website.setUpClass()
    try:
        web = Website()
        admin = web.admin()
        guest = web.client()
        student = web.student(data["student"])
        resource_id = data["resource"]

        def request(client, route, payload=None, method=None, expected=200):
            status, body, _ = web.send(client, route, payload, method)
            if status != expected:
                raise RuntimeError(f"{route}: expected HTTP {expected}, got {status}")
            return body

        rows = request(admin, "/api/resources?status=all")["resources"]
        original = next(row for row in rows if row["id"] == resource_id)
        updated = request(admin, f"/api/resources/{resource_id}",
                          {**original, "name": data["updated_name"]}, "PATCH")["resource"]
        notices = request(admin, "/api/notices", {
            "title": data["notice_title"], "body": data["notice_body"],
            "category_id": original["category_id"], "status": "published", "expires_on": "",
        }, expected=201)["notices"]
        notice = next(row for row in notices if row["title"] == data["notice_title"])
        request(student, "/api/personal", {"action":"save","id":resource_id,"saved":True})
        request(student, "/api/activity", {"kind":"view","id":resource_id})
        guide = request(guest, "/api/guide", {"question": data["question"]})
        before = request(admin, "/api/analytics?days=7")
        report["before_pid"] = Website.server.pid

        Website.stop()
        Website.launch()
        report["after_pid"] = Website.server.pid
        admin = web.admin()
        login = request(student, "/api/auth/login", {"username":data["student"],"password":PW})
        personal = request(student, "/api/personal")
        public_rows = request(guest, "/api/resources")["resources"]
        public_notices = request(guest, "/api/notices")["notices"]
        after = request(admin, "/api/analytics?days=7")
        checks = [
            ("NFR05-01", "Edited listing and version", any(row["id"] == resource_id and row["name"] == updated["name"]
                    and row["version"] == updated["version"] for row in public_rows)),
            ("NFR05-02", "Published notice visible to guests", any(row["id"] == notice["id"]
                    and row["title"] == notice["title"] and row["body"] == notice["body"] for row in public_notices)),
            ("NFR05-03", "Student bookmark", resource_id in personal["saved"]),
            ("FR10-01", "Student login after restart", isinstance(login, dict)),
            ("FR10-02", "Student recent view", resource_id in personal["recent"]),
            ("FR10-03", "Guide category aggregate", bool(guide["categories"] and before["needs"]
                and before["needs"] == after["needs"] and before["metrics"]["guides"] == after["metrics"]["guides"] == 1)),
        ]
        report["cases"] = [{"id": case, "check": label, "status": "Pass" if passed else "Fail"}
                           for case, label, passed in checks]
    finally:
        if Website.server.poll() is None:
            Website.tearDownClass()


if __name__ == "__main__":
    report = {"environment": platform.platform(), "cases": []}
    try:
        run(report)
    except Exception as exc:
        report["run_error"] = str(exc)
    path = tests / "test_results" / "restart-results.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("Saved:", path)
    sys.exit(not (len(report["cases"]) == 6 and all(row["status"] == "Pass" for row in report["cases"])))
