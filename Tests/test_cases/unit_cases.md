# CampusConnect unit test cases

Each case uses the matching ID in `test_data/unit.json`. The script `test_scripts/run_unit.py` calls the named backend function directly and checks its return value or the status carried by its exception. Python 3.11 or newer and the extracted CampusConnect source are required.

| ID | Case | Expected result |
|---|---|---|
| UNIT-01 | Trim surrounding spaces from a guide question | Returns `Mav Card` |
| UNIT-02 | Check a question shorter than three characters after trimming | Validation status 422 |
| UNIT-03 | Check a numeric question | Validation status 422 |
| UNIT-04 | Check the minimum question length of three characters | Returns `ID?` |
| UNIT-05 | Check the maximum question length of 500 characters | Returns all 500 characters |
| UNIT-06 | Check a 501-character question | Validation status 422 |
| UNIT-07 | Validate a feedback payload containing only allowed fields | Accepted |
| UNIT-08 | Validate a feedback payload containing an unexpected field | Validation status 422 |
| UNIT-09 | Validate a leap-year date | Returns `2024-02-29` |
| UNIT-10 | Validate a date that does not exist | Validation status 422 |
| UNIT-11 | Check a synthetic 12-character password | Accepted |
| UNIT-12 | Check a synthetic password below 12 characters | Validation status 422 |
| UNIT-13 | Require admin access with no signed-in account | Access status 401 |
| UNIT-14 | Require admin access with a student role | Access status 403 |
| UNIT-15 | Require admin access with an admin role | Returns the admin account |

Merge the four folders in this kit into the project's existing `Tests/` folder. From the project root, run:

```bash
python3 Tests/test_scripts/run_unit.py 2>&1 | tee Tests/test_results/unit-mac.txt
```
