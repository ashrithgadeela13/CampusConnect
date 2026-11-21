# CampusConnect browser test cases

All scenarios use the inputs in `Tests/test_data/e2e.json`. The Playwright runner starts its own local server with a temporary database and provisions the synthetic admin from the existing website test harness. It captures a recording and trace for each browser context and a screenshot when a case reaches its final assertion.

| ID | Steps | Expected result |
|---|---|---|
| E2E-01 | In a guest browser context, submit the lost-ID question, select No and Wrong office, then send feedback. In a separate context, sign in as the synthetic admin. Open Unanswered questions, mark the entry reviewed, then reopen it. | The Mav Card Office is shown. The guest sees a thank-you message. The admin sees the reason, and the review button changes to Reopen and back. |
| E2E-02 | Open Find help in a 390 × 844 mobile viewport and submit the blueberry muffin question. | The page shows No confident match and offers the step-by-step guide. |
| E2E-03 | Click Speak your question with a simulated transcript, edit the transcript, and submit it. | The transcript fills the question box, the search uses the edited text, and the Mav Card Office appears. Live microphone capture is covered separately in manual testing. |

## Run on your Mac

Merge the kit's four directories into the corresponding directories inside your project's existing `Tests/`. In Terminal, go to the folder containing both `Source_Code` and `Tests`. Run with Python 3.11 or newer.

```bash
python3 -m venv .e2e-venv
source .e2e-venv/bin/activate
python -m pip install playwright
python -m playwright install chromium
{ date; python --version; python Tests/test_scripts/run_e2e.py; } 2>&1 | tee Tests/test_results/e2e-mac.txt
```

Look for the individual case outcomes and the final summary. Screenshots, WebM recordings and Playwright trace ZIPs are saved in `Tests/test_results/browser/` when the tests run. The workspace log records a browser launch error before any case executed.
