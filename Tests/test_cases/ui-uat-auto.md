# CampusConnect UI/UAT runner

Copy the kit files into the matching Tests folders. From the project root, activate the Playwright environment and run the suite with Chrome installed:

```bash
source .e2e-venv/bin/activate
python Tests/test_scripts/run_ui_uat.py
```

| Case | Expected outcome |
|---|---|
| UAT-01 | Guest opens Mav Card Office details, closes them, and receives the feedback confirmation. |
| UAT-02 | An unrelated query opens the no-match result and its guided fallback. |
| UAT-03 | Tab reaches the labeled field and submit button with keyboard focus; Enter submits. |
| UAT-04 | At 390 × 844, the result fits horizontally and feedback works. |
| UAT-05 | Click Speak your question and say “I lost my student ID.” The real transcript appears, is edited, and returns the expected office. |
| UAT-06 | A simulated microphone permission denial shows an error; typed search still works. |

The runner records results in Tests/test_results/ui-uat-auto.json and captures screenshots when possible. The keyboard and layout checks are automated indicators; they do not establish full accessibility conformance.
