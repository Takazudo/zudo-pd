---
name: component-diodes-dmp3036sfg-7
description: Use to audit exact DMP3036SFG-7 C461081 as the adopted Board P r3 Q1 output load switch: VDS/VGS, copper-dependent current and thermal rows, RDS(on), threshold, pins 1-9 and the draft PowerDI3333-8 footprint.
---

# DMP3036SFG-7 output load switch

Read all JSON files in this owner and run the central validator. Diodes DS37038 Rev. 6-2 was retrieved
and hashed on 2026-10-31; the PDF is not retained. Board P r3 places it as Q1, the VBEN-driven
output P-channel switch replacing historical AO3401A for the 5 A contract. The r3 PCB is routed;
layout corrections and native acceptance are tracked separately. Its -5.8 A to -7.2 A ratings assume
1 in2 of 2 oz copper and do not establish an r3 rating. R11/R12 are 150k/4.7k with parallel D8/D13
BZT52C11 clamps; the obsolete -2.0 V at 5 V divider description is superseded. Keep the project
land, conditional thermal/SOA screen and physical verification limitations explicit. Nothing is measured.

## Human component reference

[DMP3036SFG-7](/docs/components/records/c461081/). See the [catalog](/docs/components/catalog/) and
[integration rules](/docs/components/integration/). The JSON bundle is authoritative.
