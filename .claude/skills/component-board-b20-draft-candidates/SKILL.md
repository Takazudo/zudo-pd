---
name: component-board-b20-draft-candidates
description: Use to audit exact TPS54560DDAR C31966, OPA2187IDGKR C2863562, REF5025AIDR C11341, PE1206FRF470R02L C164156, the RLS12FTCR020 C163047 shunt alternative and the PCSR2512BR010M6 C23067428 10 mOhm shunt as shortlisted parts of the Board B 20 V switcher-direct draft: pins, guaranteed limits, draft lands and placement gaps.
---

# Board B 20 V switcher-direct draft candidates

Read all JSON files in this owner and run the central validator. These records are SHORTLISTED
candidates used only by the unbound draft `scripts/schgen/board_b20_spec.py`
(manufacturing/board-b-20v-switcher-direct-draft.md). That spec is not bound to the central
inventory and is placed only in the unbound `boards/board-b20-draft/board-b20-draft.kicad_pcb`. TI SLVSBN0C,
SBOS807E, SBOS410O and the YAGEO product sheet were retrieved and hashed on 2026-10-31; the PDFs are
not retained. REF5025AIDR is the standard grade (0.1 %, 8 ppm/C), not the high grade. OPA2187
limits differ between its 4.5-8 V and 8-36 V tables; use the table for the actual supply.
RLS12FTCR020 C163047 is a stock alternative to the PE1206 shunt; its TA-I sheet was read only
from a distributor mirror, so its manufacturer facts are UNSOURCED and its primary coverage is OPEN.
PCSR2512BR010M6 C23067428 (RSH1, RSH3) was read from a DigiKey-hosted copy of the RESI sheet, so its
facts are UNSOURCED too.

Phase 19 drew the draft lands: `HSOP-8_TI-DDA0008B`, `VSSOP-8_TI-DGK0008A` and `SOIC-8_TI-D0008A`
from the TI example board layouts; `R1206_TA-I-RLS12` from the RLS12 pad row (a project basis for
the PE1206 part, whose YAGEO sheet has no land); and `R2512_RESI-PCSR2512_Kelvin`, a four-pad Kelvin
land from the PCSR2512 figure. None is fabrication-reviewed, and none has a 3D model.

## Human component reference

[TPS54560DDAR](/docs/components/records/c31966/) [OPA2187IDGKR](/docs/components/records/c2863562/) [REF5025AIDR](/docs/components/records/c11341/) [PE1206FRF470R02L](/docs/components/records/c164156/) [RLS12FTCR020](/docs/components/records/c163047/) [PCSR2512BR010M6](/docs/components/records/c23067428/).
See the [catalog](/docs/components/catalog/) and [integration rules](/docs/components/integration/). The JSON bundle is authoritative.
