# CampusConnect Integration / API test cases

The Python runner starts the packaged website on a free loopback port and creates a temporary SQLite database. Each case uses the fixture description in `test_data/api-cases.json`; executable payloads and assertions come from its mapped method in `Source_Code/src/tests/test_website.py`.

| ID | Procedure | Expected result |
|---|---|---|
| API-01 | Request bootstrap, filter the directory, and load the site and its assets as a guest. | Catalog and filtered FabLab entry load; no guest account is attached. |
| API-02 | Register two students. Save and view a resource as one student. Read both accounts' lists around a restart. Clear the first student's lists. | Lists remain private and persist across restart. Clearing updates the saved state. |
| API-03 | Submit the same course question to search and guide. Search for a printer with a category filter and submit a blank query. | Search and guide agree on Academic Advising. Scoped search includes FabLab. Blank input is rejected. |
| API-04 | Submit negative feedback twice. Read the dashboard as a guest, student and admin. Mark the entry reviewed as admin. Submit an unmatched question and mark it solved. | Access is restricted to admins. The repeated vote creates one entry, review status persists in the API response and the solved question leaves the dashboard queue. |
| API-05 | Record a guide match, a nonmatch and directory activity. Retrieve the 7-day and 30-day analytics. | Dates and counter changes match the recorded activity. Matched question text is absent from analytics. |
| API-06 | Send valid, irrelevant, and malformed topic hints to Guide. | Relevant results remain correct, irrelevant requests remain unmatched and malformed hints are rejected. |

Copy the four folders into the corresponding folders under the project's existing `Tests/`. Use Python 3.11 or newer. From the folder containing both `Tests` and `Source_Code`, run:

```bash
{ date; python3 --version; python3 Tests/test_scripts/run_api.py; } 2>&1 | tee Tests/test_results/api-mac.txt
```

Use the final unittest summary and individual case lines as evidence. No browser or already-running server is needed.
