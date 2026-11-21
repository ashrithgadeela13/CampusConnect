# CampusConnect restart persistence

The script starts a local server with disposable SQLite data. It performs the actions below, stops the server, starts a new process using the same database, and verifies the saved state through HTTP.

| ID | Action | Expected after restart |
|---|---|---|
| NFR05-01 | Edit the Mav Card listing | Public listing has the updated name and version |
| NFR05-02 | Publish the fixture notice | Guest can read the same notice, title, and body via the notices endpoint |
| NFR05-03 | Bookmark the listing | The student sees the bookmark |
| FR10-01 | Register the fixture student | The student can sign in again |
| FR10-02 | Record a listing view | The listing appears in student recent views |
| FR10-03 | Submit the fixture question | The guide count and category aggregate are preserved |

Copy the kit's files into the corresponding Tests folders. From the folder containing Source_Code and Tests, run:

```bash
python3 Tests/test_scripts/run_restart_check.py
```

The runner saves Tests/test_results/restart-results.json. The kit includes the Linux workspace run separately.
