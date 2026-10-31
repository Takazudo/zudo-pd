---
name: component-board-p-r3-candidates
description: Use to audit exact TPS16630PWPR C1849461 as the shortlisted Board P r3 20 V input eFuse (TPS26630 replacement with an LM74700 ideal-diode front end): pins, guaranteed limits, draft land and placement gaps.
---

# Board P r3 draft candidates

Read all JSON files in this owner and run the central validator. TPS16630PWPR is a SHORTLISTED
candidate used only by the unbound draft `scripts/schgen/board_p_r3_spec.py`. That spec is not
bound to the central inventory and has no PCB. TI SLVSET9G was retrieved and hashed on 2026-10-31;
the PDF is not retained. TPS16630 keeps the TPS26630 OVP, UVLO and I(OL) rows but has no B_GATE
or IN_SYS pin: reverse blocking is the LM74700QDBVRQ1 C2941042 record in
`component-ti-board-b-limiter-candidates`, driving Q3 CSD18543Q3A. The HTSSOP-20 land
`HTSSOP-20_PWP0020T_P0.65_EP2.96_TI-DRAFT` follows the TI PWP0020T example board layout and is
not fabrication-reviewed.

## Human component reference

[TPS16630PWPR](/docs/components/records/c1849461/).
See the [catalog](/docs/components/catalog/) and [integration rules](/docs/components/integration/). The JSON bundle is authoritative.
