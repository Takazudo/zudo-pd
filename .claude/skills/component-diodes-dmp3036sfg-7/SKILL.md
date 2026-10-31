---
name: component-diodes-dmp3036sfg-7
description: Use to audit exact DMP3036SFG-7 C461081 as the proposed Board P Q1 output load switch: VDS/VGS, copper-dependent current and thermal rows, RDS(on), threshold, pins 1-9 and the draft PowerDI3333-8 footprint.
---

# DMP3036SFG-7 output load switch (proposal)

Read all JSON files in this owner and run the central validator. Diodes DS37038 Rev. 6-2 was retrieved
and hashed on 2026-10-31; the PDF is not retained. The Board P draft spec proposes it as Q1, the VBEN-driven
output P-channel switch, replacing AO3401A (-4.2 A) for the 5 A target. Its -5.8 A to -7.2 A ratings assume 1 in2
of 2 oz copper; the routed Board P has not been laid out for it. The footprint is a project-authored draft from the
Diodes suggested pad layout text; redraw it before layout. Nothing here is measured.

## Human component reference

[DMP3036SFG-7](/docs/components/records/c461081/). See the [catalog](/docs/components/catalog/) and
[integration rules](/docs/components/integration/). The JSON bundle is authoritative.
