# NFR-01 directory search benchmark

1. Start a loopback test server with a disposable SQLite catalog.
2. Add synthetic published service entries until the catalog contains 40 services. Check the public count.
3. Run 20 simulated clients in parallel. Each client submits 10 requests to POST /api/search. Synchronize clients at the beginning of each round. Each observer times its request through reading and parsing the response. The first round is included.
4. Pass if at least 95% of the 200 requests return a valid HTTP 200 search response within 2,000 ms. Report p95 and maximum across all completed requests, including errors or timeouts. A valid response has a list of resource IDs. This is a latency check; ranking correctness is measured by the AI evaluation.
5. Save the verdict and per-request data. The test harness discards the database.

Copy these files into the corresponding project Tests folders and run from the folder containing Source_Code and Tests:

```bash
python3 Tests/test_scripts/run_search_performance.py
```

The report is saved as Tests/test_results/nfr01-search-performance.json. The workspace report records the Linux loopback run. The synthetic rows apply only to this test catalog.
