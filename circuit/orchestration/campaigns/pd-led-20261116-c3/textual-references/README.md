# C3h textual reference disposition

This bounded, non-adopting proposal follows independently accepted C3g head
`b0b08d6ab4b3bf5054919286e2c1c41bfcef0779`. C3c held 463 LED prose and
locator locations that mention evidence IDs. `audit.py` first regenerates and
checks the saved C3c proposal against its 393 source-locked JSON files. It then
classifies every held location and proposes exact-token ID substitutions in
memory. Original LED files are never edited. The result records each source
path, JSON pointer, original/proposed text hash, old IDs and replacement count;
it does not erase the original text or treat a historical source extract as an
active cross-reference.

The deterministic [result](result.json) proposes 584 exact-token substitutions
across 459 locations: 340 source-prefixed fact locators, 49 other fact locators,
and 70 reason/condition strings. Four `sources.json` evidence extracts remain
verbatim historical text. The translated in-memory corpus has exactly those
four locations still matching old IDs. Token boundaries prevent replacement
inside longer IDs. All 463 locations retain an explicit disposition, but every
proposed prose edit still needs independent contextual review before adoption.

From the repository root:

```sh
python3 circuit/orchestration/campaigns/pd-led-20261116-c3/textual-references/audit.py
python3 -m unittest discover -s circuit/orchestration/campaigns/pd-led-20261116-c3/textual-references -p 'test_*.py'
```

This is not canonical corpus validation, a citation-authority decision or a
decision to publish source extracts. Identity/SMAJ, DNP, CAD, publication,
private-resource, #307 and physical holds remain. No generated site, native
CAD, CI, PR, merge or deployment check runs in this step.
