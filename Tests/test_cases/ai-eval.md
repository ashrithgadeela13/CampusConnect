# CampusConnect AI evaluation

| Case | Procedure and expected outcome |
|---|---|
| AI-01 | Run the bundled office and paraphrase queries through the Model2Vec ranking path. Compare the top result and top three to the expected office ID. Record all mismatches. |
| AI-02 | Submit bundled out-of-scope prompts and the supplemental questions. Compare the actual state or ranked office to its fixture. Expected states are none for unsupported or clarify for the ambiguous account prompt. |
| AI-03 | Run with --draft to generate a browser draft for the lost-ID prompt. Save the exact draft and check whether it mentions a relevant topic. This is a keyword check. Review the draft itself for clarity and any invented details when interpreting it. |
| AI-04 | Reuse the live microphone result from UAT-05. Inspect its transcript and office result. Run the UI/UAT kit on your Mac if live voice evidence is still pending. |

The bundled datasets remain in Source_Code/src/ai. Supplemental inputs and the draft rule are in Tests/test_data/ai-eval.json. Copy this kit into the project's matching Tests subfolders. Run from the project root:

```bash
python3 Tests/test_scripts/run_ai_eval.py
```

For the browser draft check, run this using the environment and Chromium already installed for the E2E round:

```bash
source .e2e-venv/bin/activate
python Tests/test_scripts/run_ai_eval.py --draft
```

The report saves each actual result and whether it met the fixture. Search accuracy is measured on these datasets.
