# CampusConnect role authorization and log privacy

| Case | Procedure and expected result |
|---|---|
| NFR-02-ROLES | Call the 12 protected route/method combinations as a guest, student and admin. Guests receive 401. Students receive 403 on administrator operations and 200 on their personal routes. Admin reads and valid actions return 200. Empty admin write requests reach input validation and return 422. |
| NFR-02-PASSWORD | Register two synthetic accounts using the same test password. Verify both records have unique salts and distinct stored verifiers that match the application's password derivation. |
| NFR-03-ANALYTICS | Submit the sample question, then read analytics as admin. The question text is absent from analytics. Admin-only unresolved question text is allowed by the delivered Unanswered questions workflow and is a deviation from the proposal. |
| NFR-03-LOGS | Capture local server stdout and stderr for the run. Verify the synthetic password and issued student session tokens do not appear. The evidence contains only counts and verdicts. |

Copy the kit files into the corresponding Tests folders. From the folder containing Source_Code and Tests, run:

```bash
python3 Tests/test_scripts/run_role_privacy.py
```

The runner saves Tests/test_results/role-privacy-results.json and uses a disposable SQLite database. The workspace results are included separately.
