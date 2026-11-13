---
name: component-csd18543q3a
description: Use to audit exact CSD18543Q3A C840100 as the Board P reverse-blocking FET driven by LM74700 U3 and the B20 draft Q1-Q6 back-to-back pass pairs: VDS/VGS ratings, RDS(on), VGS(th), capacitance and gate-charge rows, pins 1-9 and the draft SON footprint.
---

# CSD18543Q3A reverse-blocking and pass FET

Read all JSON files in this owner and run the central validator. TI SLPS633 was retrieved and hashed on
2026-10-31 and re-retrieved on 2026-11-12 with an identical SHA-256; the PDF is not retained. Board P r3 uses it
as the LM74700 ideal-diode FET (source on VBUS_IN = ANODE, drain on EF_IN). The B20 draft uses Q1-Q6 as three
back-to-back common-source output pass pairs after the rail shunts; its simulation vendor macro is not committed.
VGS(th), Ciss/Coss/Crss, RG and Qg have guaranteed 25 C rows; gfs, Qgd, Qgs and Qg(th) are typical only, and
no guaranteed bound across temperature exists for VGS(th). No curve value has been read.
The footprint is a project-authored draft from the TI land-pattern text because the EasyEDA import was refused;
redraw it from the drawing before layout. Nothing here is measured.

## Human component reference

[CSD18543Q3A](/docs/components/records/c840100/). See the [catalog](/docs/components/catalog/) and
[integration rules](/docs/components/integration/). The JSON bundle is authoritative.
