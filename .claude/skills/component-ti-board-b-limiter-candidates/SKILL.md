---
name: component-ti-board-b-limiter-candidates
description: Use to audit exact INA301A3IDGKR C2861552 and LM74700QDBVRQ1 C2941042 as shortlisted Board B 20 V limiter and reverse-blocking candidates: pins, guaranteed limits and placement gaps.
---

# TI Board B limiter and reverse-blocking candidates

Read all JSON files in this owner and run the central validator. These records are
SHORTLISTED candidates for the switcher-direct 20 V Board B (manufacturing/board-b-protection-20v.md). No
generator spec places them and no KiCad asset exists. TI SBOS713A and SNOSD17G were retrieved and hashed on
2026-10-31; the PDFs are not retained. The INA301A3 comparator offset is a 25 C limit only. LM74700-Q1 needs
an external NFET that is not chosen. LTC4354, ST TCPP03-M20 and the Nexperia parts remain without obtainable
primaries and have no records here.

## Human component reference

[INA301A3IDGKR](/docs/components/records/c2861552/) and [LM74700QDBVRQ1](/docs/components/records/c2941042/).
See the [catalog](/docs/components/catalog/) and [integration rules](/docs/components/integration/). The JSON bundle is authoritative.
