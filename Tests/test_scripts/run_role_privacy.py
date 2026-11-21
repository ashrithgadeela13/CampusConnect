"""Check local CampusConnect role authorization, password storage and log privacy."""
from contextlib import closing
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

tests = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(tests.parent / "Source_Code" / "src" / "tests"))
from test_website import Website, ROOT, PW
from backend.auth import derive
from backend.db import connect

fixture = json.loads((tests / "test_data" / "role-privacy.json").read_text())
output = {"platform": platform.platform(), "cases": []}


class LocalServer(Website):
    @classmethod
    def launch(cls):
        cls.log = Path(cls.temp.name) / "server.log"
        with cls.log.open("w") as log:
            cls.server = subprocess.Popen(
                [sys.executable, "-u", "start.py", "--no-browser", "--port", "0"],
                cwd=ROOT, env=os.environ.copy(), stdout=subprocess.PIPE, stderr=log, text=True,
            )
        line = cls.server.stdout.readline()
        cls.base = line.split("CampusConnect is ready: ", 1)[1].strip().rstrip("/")

    @classmethod
    def stop(cls):
        if cls.server.stdout.closed:
            return
        cls.server.terminate()
        cls.server.wait(timeout=7)
        cls.captured_stdout = cls.server.stdout.read()
        cls.server.stdout.close()


def record(case, passed, **details):
    output["cases"].append({"case": case, "status": "Pass" if passed else "Fail", **details})


def main():
    LocalServer.setUpClass()
    try:
        web = LocalServer()
        clients = {"guest": web.client(), "student": web.client(), "admin": web.admin()}
        markers = [PW]
        registered = []
        for index, user in enumerate(fixture["synthetic_users"]):
            client = clients["student"] if index == 0 else web.client()
            status, _, headers = web.send(client, "/api/auth/register", {"username": user, "name": user, "password": PW})
            if status != 200:
                raise RuntimeError(f"Test registration returned HTTP {status}")
            cookie = headers["Set-Cookie"].split(";", 1)[0].split("=", 1)[1]
            if not cookie:
                raise RuntimeError("Registration did not issue a session token")
            registered.append(user)
            markers.append(cookie)

        for method, route, body, statuses in fixture["routes"]:
            for role, expected in zip(fixture["roles"], statuses, strict=True):
                actual, _, _ = web.send(clients[role], route, body, method)
                record("NFR-02-ROLES", actual == expected, method=method, route=route,
                       role=role, expected=expected, observed=actual)

        with closing(connect()) as db:
            credentials = [db.execute("SELECT salt, verifier FROM credentials WHERE username=?", (user,)).fetchone()
                           for user in registered]
        salts = [row["salt"] for row in credentials]
        verifiers = [row["verifier"] for row in credentials]
        verified = (
            all(len(salt) == 16 for salt in salts)
            and all(len(verifier) == 32 for verifier in verifiers)
            and len(set(salts)) == len(salts) and len(set(verifiers)) == len(verifiers)
            and all(verifier != PW.encode() and verifier == derive(PW, salt)
                    for salt, verifier in zip(salts, verifiers, strict=True))
        )
        record("NFR-02-PASSWORD", verified, accounts=len(registered))

        question = fixture["question"]
        guide_status, _, _ = web.send(clients["guest"], "/api/guide", {"question": question})
        analytics_status, analytics, _ = web.send(clients["admin"], "/api/analytics")
        record("NFR-03-ANALYTICS", guide_status == analytics_status == 200 and question not in json.dumps(analytics),
               guide_status=guide_status, analytics_status=analytics_status)

        LocalServer.stop()
        logs = LocalServer.captured_stdout + LocalServer.log.read_text(encoding="utf-8")
        record("NFR-03-LOGS", not any(marker in logs for marker in markers),
               scanned_streams=["stdout", "stderr"], password_markers=1, session_token_markers=len(markers) - 1)
    finally:
        LocalServer.tearDownClass()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        output["run_error"] = str(error)
    path = tests / "test_results" / "role-privacy-results.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(output, indent=2) + "\n")
    for result in output["cases"]:
        print(result)
    passed = sum(result["status"] == "Pass" for result in output["cases"])
    print(f"{passed}/{len(output['cases'])} passed. Saved: {path}")
    if "run_error" in output:
        print(output["run_error"], file=sys.stderr)
    sys.exit(0 if "run_error" not in output and passed == len(output["cases"]) else 1)
