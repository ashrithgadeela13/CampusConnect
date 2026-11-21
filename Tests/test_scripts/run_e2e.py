"""Exercise CampusConnect in Chromium against an isolated local server."""
import json
import os
from pathlib import Path
import sys
import unittest

from playwright.sync_api import expect, sync_playwright

tests = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(tests.parent / "Source_Code" / "src" / "tests"))
import test_website as harness

data = json.loads((tests / "test_data" / "e2e.json").read_text(encoding="utf-8"))
artifacts = tests / "test_results" / "browser"


class BrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        harness.Website.setUpClass()
        cls.addClassCleanup(harness.Website.tearDownClass)
        runtime = sync_playwright().start()
        cls.addClassCleanup(runtime.stop)
        cls.browser = runtime.chromium.launch(executable_path=os.getenv("CAMPUSCONNECT_CHROMIUM"))
        cls.addClassCleanup(cls.browser.close)
        artifacts.mkdir(parents=True, exist_ok=True)

    def page(self, label, **options):
        context = self.browser.new_context(record_video_dir=artifacts, **options)
        self.addCleanup(context.close)
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        self.addCleanup(context.tracing.stop, path=artifacts / (label + ".zip"))
        return context.new_page()

    def ask(self, page, question):
        page.goto(harness.Website.base + "/#/guide")
        page.locator("#guide-question").fill(question)
        page.get_by_role("button", name="Find resources").click()

    def test_E2E_01_guest_feedback_and_admin_review(self):
        guest = self.page("E2E-01-guest")
        self.ask(guest, data["question"])
        expect(guest.get_by_role("button", name=data["office"], exact=False).first).to_be_visible()
        guest.get_by_role("button", name="No", exact=True).click()
        guest.get_by_label("What went wrong? (Optional)").select_option(label=data["reason"])
        guest.get_by_role("button", name="Send feedback").click()
        expect(guest.get_by_text("Thanks for your feedback.")).to_be_visible()

        admin = self.page("E2E-01-admin")
        admin.goto(harness.Website.base + "/login#/unanswered")
        admin.get_by_label("Username", exact=True).fill("demo-admin")
        admin.get_by_label("Password", exact=True).fill(harness.PW)
        admin.get_by_role("button", name="Sign in").click()
        expect(admin.get_by_role("heading", name="Unanswered questions")).to_be_visible()
        entry = admin.locator("article").filter(has_text=data["question"])
        expect(entry.get_by_text("Student feedback: No · " + data["reason"])).to_be_visible()
        entry.get_by_role("button", name="Mark reviewed").click()
        expect(entry.get_by_role("button", name="Reopen")).to_be_visible()
        entry.get_by_role("button", name="Reopen").click()
        expect(entry.get_by_role("button", name="Mark reviewed")).to_be_visible()
        admin.screenshot(path=artifacts / "E2E-01.png")

    def test_E2E_02_mobile_unmatched_question(self):
        page = self.page("E2E-02", viewport=data["mobile_viewport"], is_mobile=True, has_touch=True)
        self.ask(page, data["unmatched"])
        expect(page.get_by_role("heading", name="No confident match")).to_be_visible()
        expect(page.get_by_role("button", name="Try the step-by-step guide")).to_be_visible()
        page.screenshot(path=artifacts / "E2E-02.png")

    def test_E2E_03_simulated_voice_transcript(self):
        page = self.page("E2E-03")
        transcript = json.dumps(data["question"])
        page.add_init_script(f"""window.SpeechRecognition = class {{
            start() {{ setTimeout(() => {{
                this.onresult?.({{results: [[{{transcript: {transcript}}}]]}});
                this.onend?.();
            }}, 100); }}
            stop() {{ this.onend?.(); }}
            abort() {{ this.onend?.(); }}
        }};""")
        page.goto(harness.Website.base + "/#/guide")
        page.get_by_role("button", name="Speak your question").click()
        question = page.locator("#guide-question")
        expect(question).to_have_value(data["question"])
        edited = data["question"] + " Where can I get a new one?"
        question.fill(edited)
        page.get_by_role("button", name="Find resources").click()
        expect(page.get_by_text(edited, exact=True)).to_be_visible()
        expect(page.get_by_role("button", name=data["office"], exact=False).first).to_be_visible()
        page.screenshot(path=artifacts / "E2E-03.png")


if __name__ == "__main__":
    unittest.main(verbosity=2)
