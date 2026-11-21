# Remaining CampusConnect proposal checks

Copy the kit files into the corresponding Tests folders. Run each section from the project root containing Source_Code and Tests. The runners use disposable SQLite test data.

## 1. Accessibility and notice placement

Reuse the Playwright environment and Chromium from the E2E tests. Install axe-core using npm on a machine with Node.js.

```bash
source .e2e-venv/bin/activate
npm install --prefix .axe-test --no-save axe-core
python Tests/test_scripts/run_accessibility.py
```

| Case | Expected evidence |
|---|---|
| A11Y-01 to A11Y-04 | Scan Directory, Sign in, Find help, and populated Bookmarks. Each screen passes its scan if there are zero serious or critical findings. Record any findings. |
| A11Y-05 | Tab to labeled sign-in fields, sign in, search the directory, open and close office details, toggle a bookmark, and open Bookmarks with the keyboard. Verify the controls receive keyboard focus. |
| FR-08 | Publish a notice for the Mav Card listing's category. Look for it both on the service details panel and on Notices. Report a scope deviation if the notice appears on the notice board only. |

Results: `Tests/test_results/accessibility-and-notices.json`. Combine this keyboard check with UAT-03 for the Find help screen. Automated scans and basic keyboard checks cover the tested screens and states.

## 2. AI keyword comparison

```bash
python3 Tests/test_scripts/run_keyword_baseline.py
```

Source data: `Source_Code/src/ai/heldout.json` contains category labels; `office-checks.json` and `paraphrase-checks.json` contain office labels. Evaluate the same prompts on both systems. The comparison baseline ranks directory records by distinct query words in common with catalog metadata, skips zero-overlap records, and breaks ties by service ID. For category evaluation it deduplicates category IDs after ranking offices. Report counts separately for each set.

Results: `Tests/test_results/keyword-baseline.json`. The included workspace run has the individual results.

## 3. NFR-06 timed usability

```bash
python3 Tests/test_scripts/run_usability.py
```

Recruit 10 distinct, consenting participants. Give each participant the printed task and a fresh guest session on the displayed local URL. Provide the task goal only. Start the timer when they begin. At the moment they identify an office, give up, or reach three minutes, press Enter. Enter the office they identified and whether they worked without help. Record observations with anonymous codes only.

The script computes success from the observed office, elapsed time, and whether the participant finished without help. It saves after each participant and resumes from the same file. Keep the exact task and settings consistent when resuming. The target is at least 9 of 10 independent successes. Before all 10 participate, the report is Incomplete.

Results: `Tests/test_results/nfr06-usability.json`.
