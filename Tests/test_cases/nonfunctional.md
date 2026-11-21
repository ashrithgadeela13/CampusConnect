# CampusConnect nonfunctional checks

Run from the folder containing Source_Code and Tests. The runner starts a loopback server and initializes a disposable SQLite database.

| ID | Procedure | Expected outcome |
|---|---|---|
| NF-01 | Warm up health and bootstrap once each, then send 100 requests per endpoint with 10 workers. | All requests return HTTP 200. Each endpoint's p95 is at most 500 ms. |
| NF-02 | Save and view a bookmark as a synthetic student, check another student's account, then restart. | Bookmark and view are private and survive restart. |
| NF-03 | Submit a negative guest vote, then restart the server and sign in as admin. | The original question and feedback reason are still in the admin dashboard. |
| NF-04 | Request the dashboard as a guest, student, and admin. | Responses are HTTP 401, 403, and 200 respectively. |
| NF-05 | Fetch the local homepage and compare its HTTP headers with the fixture. | The tested content type, frame, referrer, and CSP protections are present. |

The 500 ms p95 limit is a chosen local test threshold. Timings describe this test environment and its loopback HTTP routes.

```bash
{ date; python3 --version; python3 Tests/test_scripts/run_nonfunctional.py; } 2>&1 | tee Tests/test_results/nonfunctional-mac.txt
```
