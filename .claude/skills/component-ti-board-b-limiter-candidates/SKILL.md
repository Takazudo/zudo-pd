---
name: component-ti-board-b-limiter-candidates
description: Use to audit exact INA301A3QDGKTQ1 C179864 (B20 U11/U12 since the 2026-11-22 JST sourcing adoption) and the superseded INA301A3IDGKR C2861552 Board B 20 V limiter comparators: pins, guaranteed limits and placement gaps.
---

# TI Board B limiter candidates

Read all JSON files in this owner and run the central validator. This record is a
SHORTLISTED candidates for the switcher-direct 20 V Board B (manufacturing/board-b-protection-20v.md). No
generator spec places them and no KiCad asset exists. TI SBOS713A was retrieved and hashed on
2026-10-31; the PDF is not retained. The INA301A3 comparator offset is a 25 C limit only. LM74700QDBVRQ1 C2941042 is now
the fitted Board P U3 (component-lm74700qdbvrq1); its Board B use still needs an external NFET that is not chosen. LTC4354, ST TCPP03-M20 and the Nexperia parts remain without obtainable
primaries and have no records here.

Sourcing adoption 2026-11-22 JST (#326): B20 U11 and U12 now use INA301A3QDGKTQ1 C179864 (TI
SBOS786B, AEC-Q100 grade 1, retained in Takazudo/circuit-dev-resources). It keeps the INA301A3 gain
100 V/V, gain error 0.2 %, VOS 35 uV, ILIMIT 79.2-80.8 uA, the 1 us / 1.5 us delay rows with their
different conditions and the DGK pin map, with RESET=GND, OUT=NC and ALERT on FAULT_N unchanged.
INA301A3IDGKR C2861552 (zero JLC stock on 2026-11-21 UTC) is a superseded SHORTLISTED fallback. The
observed C179864 stock of 13 is a dated read, not a reservation; INA301A3QDGKRQ1 C2155855 is a
recorded spare in the sourcing ledger only. Do not substitute A1/A2 gain, INA381 or INA300.

## Human component reference

[INA301A3QDGKTQ1](/docs/components/records/c179864/) and INA301A3IDGKR (superseded at its B20/Board P placements; record not published).
See the [catalog](/docs/components/catalog/) and [integration rules](/docs/components/integration/). The JSON bundle is authoritative.
