---
name: component-board-b20-draft-candidates
description: Use to audit exact TPS54560DDAR C31966, OPA2187IDGKR C2863562, REF5025AIDR C11341, PE1206FRF470R02L C164156 and the RLS12FTCR020 C163047 shunt alternative as shortlisted parts of the Board B 20 V switcher-direct draft: pins, guaranteed limits and placement gaps.
---

# Board B 20 V switcher-direct draft candidates

Read all JSON files in this owner and run the central validator. These records are SHORTLISTED
candidates used only by the unbound draft `scripts/schgen/board_b20_spec.py`
(manufacturing/board-b-20v-switcher-direct-draft.md). That spec is not bound to the central
inventory, has no PCB, and the draft symbols reference footprints that do not exist. TI SLVSBN0C,
SBOS807E, SBOS410O and the YAGEO product sheet were retrieved and hashed on 2026-10-31; the PDFs are
not retained. REF5025AIDR is the standard grade (0.1 %, 8 ppm/C), not the high grade. OPA2187
limits differ between its 4.5-8 V and 8-36 V tables; use the table for the actual supply.
RLS12FTCR020 C163047 is a stock alternative to the PE1206 shunt; its TA-I sheet was read only
from a distributor mirror, so its manufacturer facts are UNSOURCED and its primary coverage is OPEN.

## Human component reference

[TPS54560DDAR](/docs/components/records/c31966/) [OPA2187IDGKR](/docs/components/records/c2863562/) [REF5025AIDR](/docs/components/records/c11341/) [PE1206FRF470R02L](/docs/components/records/c164156/) [RLS12FTCR020](/docs/components/records/c163047/).
See the [catalog](/docs/components/catalog/) and [integration rules](/docs/components/integration/). The JSON bundle is authoritative.
