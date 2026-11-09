---
name: component-tps16630pwpr
description: Use to audit exact TPS16630PWPR C1849461 Board P r3 input eFuse limits, UVLO/OVP/ILIM/dVdT configuration, latch mode, pins 1-21 and the draft HTSSOP-20 land.
---

# TPS16630PWPR input eFuse

Read all JSON files in this owner and run the central validator. Use circuit-spec-integration for the
whole 20 V input chain. TI SLVSET9G was retrieved and hashed on 2026-10-31; the PDF is not retained.
Board P r3 places it as U2 after the LM74700QDBVRQ1 C2941042 ideal-diode stage (U3 driving Q3
CSD18543Q3A), which replaces the TPS26630 B_GATE and Q4. OVP, UVLO and I(OL) rows match the TPS26630
values the dividers were sized for. Fast trip and I(SCP) are TYP only, so no guaranteed let-through bound
exists. The HTSSOP-20 land follows the TI PWP0020T example layout and is not fabrication-reviewed. The
Board P r3 PCB is routed with TPS16630PWPR; layout corrections and native acceptance are tracked
separately. This is not a measured thermal/current rating. Nothing here is measured.

## Human component reference

[TPS16630PWPR](/docs/components/records/c1849461/).
See the [catalog](/docs/components/catalog/) and [integration rules](/docs/components/integration/). The JSON bundle is authoritative.
