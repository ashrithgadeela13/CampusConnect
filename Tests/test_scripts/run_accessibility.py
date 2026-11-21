"""Scan representative screens, exercise keyboard workflows, and check FR-08."""
import json
from pathlib import Path
import sys

from playwright.sync_api import expect, sync_playwright

tests = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(tests.parent / "Source_Code" / "src" / "tests"))
from test_website import Website, PW

data = json.loads((tests / "test_data" / "accessibility.json").read_text())
axe = tests.parent / ".axe-test" / "node_modules" / "axe-core" / "axe.min.js"
results = []


def tab_to(page, target, key="Tab"):
    if target.evaluate("(node) => node === document.activeElement && !node.matches(':focus-visible')"):
        page.keyboard.press("Shift+Tab")
    for _ in range(100):
        if target.evaluate("(node) => node === document.activeElement && node.matches(':focus-visible')"):
            return
        page.keyboard.press(key)
    active = page.evaluate("() => document.activeElement?.outerHTML.slice(0, 200)")
    raise AssertionError(f"Keyboard could not reach {target} with focus-visible state. Active element: {active}")


def checked(case, name, run):
    try:
        result = {"case": case, "name": name, **run()}
    except Exception as exc:
        result = {"case": case, "name": name, "status": "Error", "observation": str(exc)}
    results.append(result)
    print(case, name, result["status"], flush=True)
    if result.get("observation") and result["status"] == "Error":
        print(result["observation"], flush=True)


def run():
    if not axe.is_file():
        raise RuntimeError("Install axe-core in .axe-test using the test case instructions.")
    Website.setUpClass()
    try:
        web = Website()
        web.student(data["student"])
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            scan_context = browser.new_context(bypass_csp=True)
            page = scan_context.new_page()
            base = Website.base
            office = data["office"]

            def scan(name, route):
                page.goto(base + route)
                heading = page.get_by_role("heading", name={"Directory":"Directory", "Sign in":"Welcome back",
                                          "Find help":"Find help", "Bookmarks":"Bookmarks"}[name], exact=False).first
                if name == "Directory":
                    expect(page.get_by_role("textbox", name="Search campus resources")).to_be_visible()
                else:
                    expect(heading).to_be_visible()
                page.add_script_tag(path=str(axe))
                payload = page.evaluate("""async () => {
                    const scan = await axe.run();
                    return {version: scan.testEngine.version, violations: scan.violations.map(v => ({
                        id: v.id, impact: v.impact, help: v.help, targets: v.nodes.map(n => n.target)
                    }))};
                }""")
                high = [item for item in payload["violations"] if item["impact"] in {"critical", "serious"}]
                return {"status": "Fail" if high else "Pass", "critical_or_serious": len(high), **payload}

            for index, (name, route) in enumerate(data["axe_pages"], 1):
                if name == "Bookmarks":
                    login = page.request.post(base + "/api/auth/login", headers={"Origin": base},
                                              data={"username": data["student"], "password": PW})
                    if login.ok:
                        page.request.post(base + "/api/personal", headers={"Origin": base},
                                          data={"action": "save", "id": "mav-card", "saved": True})
                    if not login.ok:
                        results.append({"case": f"A11Y-0{index}", "name": name, "status": "Error"})
                        continue
                checked(f"A11Y-0{index}", name, lambda: scan(name, route))

            scan_context.close()
            page = browser.new_page()

            def keyboard():
                page.goto(base + "/login")
                for label, value in (("Username", data["student"]), ("Password", PW)):
                    field = page.get_by_label(label, exact=True)
                    tab_to(page, field)
                    page.keyboard.type(value)
                tab_to(page, page.get_by_role("button", name="Sign in"))
                page.keyboard.press("Enter")
                search = page.get_by_role("textbox", name="Search campus resources")
                expect(search).to_be_visible()
                tab_to(page, search)
                page.keyboard.type(data["search"])
                result = page.get_by_role("button", name="Office details: " + office, exact=True)
                expect(result).to_be_visible()
                tab_to(page, result)
                page.keyboard.press("Enter")
                panel = page.get_by_role("dialog")
                expect(panel.get_by_role("heading", name=office, exact=True)).to_be_visible()
                bookmark = panel.locator("button[aria-pressed].detail-bookmark")
                expect(bookmark).to_be_enabled()
                if bookmark.get_attribute("aria-pressed") == "true":
                    tab_to(page, bookmark)
                    page.keyboard.press("Enter")
                    expect(bookmark).to_have_attribute("aria-pressed", "false")
                tab_to(page, bookmark)
                page.keyboard.press("Enter")
                expect(bookmark).to_have_attribute("aria-pressed", "true")
                page.keyboard.press("Escape")
                expect(panel).to_be_hidden()
                expect(page.locator("[data-sonner-toast]:visible").first).to_be_hidden(timeout=15000)
                bookmarks = page.get_by_role("button", name="Bookmarks", exact=True)
                expect(bookmarks).to_be_visible()
                tab_to(page, bookmarks, key="Shift+Tab")
                page.keyboard.press("Enter")
                expect(page.get_by_role("button", name=office, exact=False).filter(has_text=office).first).to_be_visible()
                return {"status": "Pass", "observation": "Keyboard login, directory search, details and bookmark update worked."}

            checked("A11Y-05", "Primary keyboard workflow", keyboard)

            def notice():
                admin = web.admin()
                status, catalog, _ = web.send(admin, "/api/resources?status=all")
                assert status == 200
                office_row = next(row for row in catalog["resources"] if row["id"] == "mav-card")
                status, _, _ = web.send(admin, "/api/notices", {
                    "title": data["notice_title"], "body": "Synthetic notice for the FR-08 check.",
                    "category_id": office_row["category_id"], "status": "published", "expires_on": "",
                })
                assert status == 201
                page.goto(base + "/#/directory?office=mav-card")
                panel = page.get_by_role("dialog")
                expect(panel.get_by_role("heading", name=office, exact=True)).to_be_visible()
                on_listing = panel.get_by_text(data["notice_title"], exact=True).is_visible()
                page.goto(base + "/#/notices")
                expect(page.get_by_text(data["notice_title"], exact=True)).to_be_visible()
                return {"status": "Pass" if on_listing else "Scope deviation",
                        "notice_board_visible": True, "listing_visible": on_listing}

            checked("FR-08", "Published notice location", notice)
    finally:
        Website.tearDownClass()


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        results.append({"status": "Blocked", "reason": str(exc)})
    path = tests / "test_results" / "accessibility-and-notices.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print("Saved:", path)
    sys.exit(0 if results and all(row["status"] == "Pass" for row in results) else 1)
