# CampusConnect

**Team 10 · CSE 6324 Advanced Topics in Software Engineering**

CampusConnect helps UT Arlington students find the campus office or service that can help with a question. Guests can browse the directory, filter resources, use Find help, and give optional feedback. Students with an account can bookmark offices and see recent visits. Administrators can maintain the directory, publish notices, view aggregate analytics, and review unanswered questions.

## Run the app

Extract the ZIP and open the `Team10_CampusConnect_Final` folder.

**macOS or Linux** requires Python 3.11 or newer. From the extracted project root:

```bash
python3 Source_Code/src/start.py
```

On macOS you can also double-click `Source_Code/Start-CampusConnect.command`. On 64-bit Windows 10 or 11, double-click `Source_Code/Start-CampusConnect.cmd` to use the included Python runtime.

Open the local address printed by the launcher. The server normally starts at `http://127.0.0.1:8000/`. Leave the Terminal window open while using the site, and press **Ctrl+C** to stop the server. The frontend is already built and the database initializes on the first launch.

### Student and administrator access

The directory and Find help are available as a guest. Use **Sign in → Create a student account** to enable bookmarks and recent views.

To create a local administrator, double-click `Source_Code/Create-Admin.cmd` on Windows or run this from the project root on macOS or Linux:

```bash
python3 Source_Code/src/manage.py create-admin
```

Enter a username, display name, and password of at least 12 characters. Use that account to sign in and open **Administration → Unanswered questions**. Local changes persist in `Source_Code/src/instance/campusconnect.sqlite3`. Optional environment settings are described in `Source_Code/config.example`.

## AI features

- **Model2Vec** ranks relevant offices using the local MinishLab `potion-base-8M` model.
- **TensorFlow.js** generates an editable follow-up draft in the browser.
- **Browser speech recognition** can turn spoken input into an editable question on supported browsers. It may require permission and an internet connection.
- **Figma Make** was used for the original interface prototype.

See [AI evidence](Documentation/ai_evidence/README.md) for model references, evaluation outputs, and engineering evidence.

## Run the tests

Run commands from the project root. Automated suites use temporary test databases where applicable.

| Test | Command |
|---|---|
| Packaged regressions | `python3 -m unittest discover -s Source_Code/src/tests -v` |
| Unit and API | `python3 Tests/test_scripts/run_unit.py` and `python3 Tests/test_scripts/run_api.py` |
| Performance and reliability | `python3 Tests/test_scripts/run_nonfunctional.py`, `python3 Tests/test_scripts/run_search_performance.py`, and `python3 Tests/test_scripts/run_restart_check.py` |
| Roles and privacy | `python3 Tests/test_scripts/run_role_privacy.py` |
| AI search and baseline | `python3 Tests/test_scripts/run_ai_eval.py` and `python3 Tests/test_scripts/run_keyword_baseline.py` |
| Timed usability study | `python3 Tests/test_scripts/run_usability.py` with actual participants |

For browser tests, install Playwright and Chromium in a dedicated Python environment. The following commands use macOS or Linux shell syntax:

```bash
python3 -m venv .e2e-venv
source .e2e-venv/bin/activate
python -m pip install playwright
python -m playwright install chromium
python Tests/test_scripts/run_e2e.py
```

The automated UI/UAT runner uses Google Chrome, and the live speech check needs microphone input. Run `python Tests/test_scripts/run_ui_uat.py` to run the UI/UAT suite. To check the draft, run `python Tests/test_scripts/run_ai_eval.py --draft`. For accessibility, run `npm install --prefix .axe-test --no-save axe-core` and then `python Tests/test_scripts/run_accessibility.py`. Test cases, fixtures, and recorded outputs are under `Tests/`.

## Project files

| Location | Contents |
|---|---|
| `Final_Report/Team10_Final_Report.pdf` | Final report, design figures, requirements traceability, and test evidence |
| `Source_Code/` | Launch scripts, configuration example, bundled runtime, and app source in `src/` |
| `Tests/` | Test cases, data, scripts, and recorded results |
| `Documentation/design/` | Updated architecture, use-case, data, and sequence diagrams in the original visual style |
| `Documentation/planning/` | Master Gantt and sprint burndown from the original report |
| `Documentation/ai_evidence/` | AI tool documentation and evaluation evidence |
| `Documentation/screenshots/` | App screenshots from the earlier CampusConnect build |
