---
name: component-lm74700qdbvrq1
description: Use to audit exact LM74700QDBVRQ1 C2941042 as the Board P r3 ideal-diode controller driving Q3: GATE/VCAP limits, reverse threshold, pins 1-6 and the SOT-23-6 land.
---

# LM74700QDBVRQ1 ideal-diode controller

Read all JSON files in this owner and run the central validator. TI SNOSD17G was retrieved and hashed on
2026-10-31; the PDF is not retained. Board P r3 places it as U3 ahead of the TPS16630 eFuse U2: ANODE and
EN on VBUS_IN, CATHODE on EF_IN, GATE to Q3 CSD18543Q3A and C37 1 uF from VCAP to ANODE. GATE-ANODE is
15 V absolute maximum and the charge pump turns off at 13.9 V maximum, inside the Q3 20 V VGS rating. The
Board B 20 V reverse-blocking use is still unplaced. The Board P PCB still carries r2. Nothing here is measured.

## Human component reference

[LM74700QDBVRQ1](/docs/components/records/c2941042/).
See the [catalog](/docs/components/catalog/) and [integration rules](/docs/components/integration/). The JSON bundle is authoritative.
