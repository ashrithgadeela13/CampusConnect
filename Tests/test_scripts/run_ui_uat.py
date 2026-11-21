"""Run six CampusConnect UI checks, including an interactive microphone test."""
import json
import platform
import re
import sys
from datetime import datetime
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

tests = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(tests.parent / "Source_Code" / "src" / "tests"))
from test_website import Website

data = json.loads((tests / "test_data" / "ui-uat-auto.json").read_text(encoding="utf-8"))
results = tests / "test_results"
results.mkdir(exist_ok=True)
summary = {"date": datetime.now().astimezone().isoformat(),
           "platform": platform.platform(), "cases": []}
unmatched = data["unmatched"]


class Blocked(Exception):
    pass


def question(page):
    return page.locator("#guide-question")


def submit(page, text=None):
    if text is not None:
        question(page).fill(text)
    page.get_by_role("button", name="Find resources").click()


def office(page):
    return page.locator(".lead-match").filter(has_text=data["office"])


def details_feedback(page, row):
    submit(page, data["prompt"])
    office(page).click()
    dialog = page.get_by_role("dialog")
    expect(dialog.get_by_role("heading", name=data["office"], exact=True)).to_be_visible()
    dialog.get_by_role("button", name="Close").click()
    expect(dialog).to_be_hidden()
    if question(page).is_visible():
        submit(page, data["prompt"])
    page.get_by_role("button", name="Yes", exact=True).click()
    expect(page.get_by_text("Thanks for your feedback.")).to_be_visible()
    return "Office details opened and guest feedback was acknowledged."


def fallback(page, row):
    submit(page, unmatched)
    expect(page.get_by_role("heading", name="No confident match")).to_be_visible()
    page.get_by_role("button", name="Try the step-by-step guide").click()
    expect(page.get_by_role("heading", name="What area is this about?")).to_be_visible()
    return "No-match result opened the guided topic choices."


def keyboard(page, row):
    expect(page.get_by_text("What do you need help with?", exact=True)).to_be_visible()
    target = page.get_by_role("button", name="Find resources")
    for control in (question(page), target):
        for _ in range(80):
            page.keyboard.press("Tab")
            if control.evaluate("(node) => node === document.activeElement"):
                break
        else:
            raise AssertionError("Tab navigation did not reach the expected control.")
        assert control.evaluate("(node) => node.matches(':focus-visible')")
        if control == target:
            page.keyboard.press("Enter")
        else:
            page.keyboard.type(data["prompt"])
    expect(office(page)).to_be_visible()
    return "Tab reached the labeled field and submit button; Enter returned Mav Card Office."


def mobile(page, row):
    submit(page, data["prompt"])
    expect(office(page)).to_be_visible()
    feedback = page.get_by_role("button", name="Yes", exact=True)
    expect(feedback).to_be_enabled()
    widths = page.evaluate("() => [document.documentElement.clientWidth, document.documentElement.scrollWidth]")
    row["viewport_and_content_width"] = widths
    assert widths[1] <= widths[0], "Page overflows horizontally."
    feedback.click()
    expect(page.get_by_text("Thanks for your feedback.")).to_be_visible()
    return "Mobile result fit the viewport and the feedback button worked."


def live_voice(page, row):
    unavailable = page.get_by_text("Voice input is unavailable", exact=False)
    if unavailable.is_visible():
        raise Blocked(unavailable.inner_text())
    print(f'In Chrome, click Speak your question, allow access, then say "{data["prompt"]}"', flush=True)
    try:
        page.wait_for_function("() => document.querySelector('#guide-question')?.value.trim().length > 0", timeout=90000)
    except Exception:
        status = page.get_by_text(re.compile("Microphone access was denied|Voice input could not|No speech detected"))
        raise Blocked(status.first.inner_text() if status.count() else "No transcript within 90 seconds.") from None
    transcript = question(page).input_value()
    row["transcript"] = transcript
    row["submitted_question"] = transcript + " " + data["edit"]
    submit(page, row["submitted_question"])
    expect(page.locator("#match-heading")).to_be_visible()
    row["recommended_offices"] = page.locator(".lead-match strong").all_text_contents()
    assert {"lost", "student", "id"} <= set(re.findall(r"[a-z]+", transcript.lower())), "Transcript did not preserve the expected wording."
    expect(office(page)).to_be_visible()
    return "Live transcript was captured, edited, and returned Mav Card Office."


def denied(page, row):
    page.get_by_role("button", name="Speak your question").click()
    expect(page.get_by_text("Microphone access was denied.", exact=False)).to_be_visible()
    submit(page, data["prompt"])
    expect(office(page)).to_be_visible()
    return "Simulated microphone denial showed an error and typed search worked."


cases = [details_feedback, fallback, keyboard, mobile, live_voice, denied]


def run():
    Website.setUpClass()
    try:
        with sync_playwright() as runtime:
            browser = runtime.chromium.launch(channel="chrome", headless=False)
            summary["chrome_version"] = browser.version
            for index, check in enumerate(cases, 1):
                row = {"id": f"UAT-{index:02}", "status": "Blocked"}
                summary["cases"].append(row)
                context = browser.new_context(**({"viewport": {"width": 390, "height": 844}, "is_mobile": True, "has_touch": True} if index == 4 else {}))
                page = context.new_page()
                try:
                    if index == 6:
                        page.add_init_script("""window.SpeechRecognition = class {
                            start() { setTimeout(() => {
                                this.onerror?.({error: 'not-allowed'});
                                this.onend?.();
                            }, 100); }
                            abort() {}
                        };""")
                    page.goto(Website.base + "/#/guide")
                    expect(question(page)).to_be_visible()
                    row["status"] = "Fail"
                    row["observation"] = check(page, row)
                    row["status"] = "Pass"
                except Blocked as error:
                    row.update(status="Blocked", observation=str(error))
                except Exception as error:
                    row["observation"] = str(error)
                finally:
                    try:
                        screenshot = row["id"] + ".png"
                        page.screenshot(path=results / screenshot, timeout=3000)
                        row["screenshot"] = screenshot
                    except Exception:
                        pass
                    context.close()
                print(row["id"], row["status"], row["observation"], flush=True)
    finally:
        Website.tearDownClass()


if __name__ == "__main__":
    try:
        run()
    except Exception as error:
        summary["run_error"] = str(error)
        print(error, file=sys.stderr)
    finally:
        completed = {row["id"] for row in summary["cases"]}
        for index in range(1, 7):
            case_id = f"UAT-{index:02}"
            if case_id not in completed:
                summary["cases"].append({"id": case_id, "status": "Blocked",
                                         "observation": "Runner stopped before reaching this case."})
        path = results / "ui-uat-auto.json"
        path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(f"Saved: {path}")
    sys.exit(0 if all(row["status"] == "Pass" for row in summary["cases"]) else 1)
