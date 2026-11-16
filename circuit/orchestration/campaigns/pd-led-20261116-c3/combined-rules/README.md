# C3g combined integration-rule feasibility

This is a source-bound, in-memory check based on accepted C3f commit
`d360b3954a43e01cad02b735a50161ddd18cde41`. It does not edit or adopt
the PD or LED evidence inventories. `verify.py` regenerates the accepted C3c
translation proposal and C3f calculation audit from their 393 locked JSON
inputs, checks both saved results, then applies the proposed LED ID and
expression changes to copies. It combines those copies with the PD corpus and
calls the installed `validate_rules` function for all 19 generic integration
rules. The PD and LED verdict enums are checked for equality; the schema and
validator file hashes are recorded in `result.json`.

Run from the repository root:

```sh
python3 circuit/orchestration/campaigns/pd-led-20261116-c3/combined-rules/verify.py
python3 -m unittest discover -s circuit/orchestration/campaigns/pd-led-20261116-c3/combined-rules -p 'test_*.py'
```

`result.json` records the deterministic result: 11 PD rules plus 8 translated
LED rules pass the generic rule function against 180 records, 1,868 facts and
464 sources. The nine proposed LED calculation IDs and paired expressions are
included. Tests also prove a missing fact and a stale calculation result fail.

This is a feasibility result for one validator function, not validation of an
active merged corpus. No combined inventory, owner-root, generated route/page,
CAD, publication or deployment validator runs here. The 463 textual reference
locations remain held, as do identity/SMAJ, DNP, private-resource, #307 and
physical decisions. No product decision or canonical adoption follows from
this result.
