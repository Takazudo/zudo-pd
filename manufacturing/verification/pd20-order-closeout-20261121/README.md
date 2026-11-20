# PD20 pre-order closeout evidence (#322)

Desk evidence for the [PD20 order sheet](../../releases/pd20-prototype-review/ORDER-SHEET.md). Nothing here is a
quote, cart, upload, pre-order or order. The frozen package (`manufacturing/releases/pd20-prototype-review/`) is read,
never written.

## The six upload files pass UPLOAD FILE INTEGRITY on a fresh checkout

`python3 scripts/pcb/pd20-order/verify-upload-files.py`, run 2026-11-20 UTC on `e974d710` (no package diff from
#307's final head `cc3f5904`): PASS, 6/6. Scope: the Board P r3 and B20 Gerber ZIP, BOM and CPL equal their
`SHA256SUMS` entries, and the checksum-verified `manifest.json` locks the same six hashes. It is **not** a complete
engineering replay, native KiCad validation or electrical qualification. Refusal tests:
`scripts/pcb/pd20-order/test_verify_upload_files.py`.

## Complete historical replay is NOT RUN in a fresh checkout

`sha256sum -c SHA256SUMS`: 158 of 159 OK. `mechanical/assembly/populated-stack.step` (SHA-256 `59b0e220…`,
367,630,999 bytes) is local-only and absent. Against `e974d710`, the manifest's source locks differ in
`.claude/skills/component-pesd24vs1ub-c85382/routing.json` (both boards; later identity-alias adoption) and the two
ignored B20 inputs `boards/board-b20-draft/assembly-preview/{populated-stack,board-p-stacked}.step` are absent.
`verify-jlcpcb.py` therefore stops at its first gate. The prerequisites are in the order sheet.

## Polarity evidence comes from the package PCBs, not from `cpl.csv`

`cpl.csv` has only designator, centre, side and rotation. `scripts/pcb/pd20-order/polarity-reference.py` reads the
checksum-locked package source PCBs (`board-p/source/board-p.kicad_pcb` `3fa6db3b…`,
`board-b20-draft/source/board-b20-draft.kicad_pcb` `c5df71c5…`) and lists pad 1 of every fitted D / DZ / Q / U / J
part and every electrolytic C on a `CAP-SMD_BD` footprint (25SVPF47M, RVT1H101M0810). What pad 1 is (cathode, pin 1, gate) comes from each part's owner pin map, routed through
`.claude/skills/component-spec-audit/references/inventory.json`; for example the BZT52 owners record K = pin 1
(band end) on these SOD-123 lands, and the 25SVPF47M owner records positive pin 1 to system ground on the
negative output (CCF1). Geometry check: the script reproduces the independent P15 checklist values
(D5 pad 1 x = 20.45 on VBUS_IN, D9 x = 17.325 on VDD_LOC, U1 pad 1 at x = 12.978, CPL y = −21.288), and on both PD20 boards
every same-layer track end that lands inside a computed pad carries that pad's net (independent review: Board P 110/110,
B20 364/364, including all bottom-side footprints). JLC places with its own
library footprints, so this listing does not prove placed orientation. Bottom-side previews are mirrored.

Coordinates use the CPL frame: X right and Y up from the manifest origin (Board P (0, 0) with negative Y,
B20 (0, 85)).

### Board P r3 (`board-p`)

| Ref | Part | LCSC | Footprint | Side | Rot | Pad-1 net | Pad-1 centre X, Y (mm, CPL frame) |
| --- | --- | --- | --- | --- | ---: | --- | --- |
| C3 | 100uF 50V | C970687 | CAP-SMD_BD8.0-L8.3-W8.3-LS9.0-FD | Top | 0 | `VBUS_P` | 14.860, -13.000 |
| D5 | TVS2200DRVR | C523793 | WSON-6_L2.0-W2.0-P0.65-BL-EP | Top | 0 | `GND` | 10.650, -11.575 |
| D9 | BZT52C18-7-F | C192739 | SOD-123_L2.8-W1.8-LS3.7-RD | Top | 0 | `VDD_LOC` | 18.175, -22.000 |
| D10 | BZT52C20-7-F | C260890 | SOD-123_L2.8-W1.8-LS3.7-RD | Top | 0 | `VBUS_VS_DISCH` | 15.675, -27.250 |
| D11 | BZT52C18-7-F | C192739 | SOD-123_L2.8-W1.8-LS3.7-RD | Top | 180 | `VBEN_PIN` | 13.575, -27.500 |
| J1 | TYPE-C-31-M-17 | C283540 | USB-C-SMD_10P-P1.00-L6.8-W8.9 | Top | 180 | `GND` | 16.256, -7.050 |
| JOUT1 | 2.54mm 1x6 male | C492405 | HDR-TH_6P-P2.54-V-M | Top | 0 | `VBUS_OUT` | 6.550, -37.700 |
| Q1 | DMP3036SFG-7 | C461081 | PowerDI3333-8_DMP3036SFG | Top | 270 | `VBUS_P` | 7.275, -26.000 |
| Q3 | CSD18543Q3A | C840100 | VSON-8_L3.3-W3.3-P0.65_CSD18543Q3A | Top | 270 | `VBUS_IN` | 8.875, -10.025 |
| Q5 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 0 | `Q1_MX` | 3.500, -38.450 |
| Q6 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 0 | `VG_LOC` | 19.500, -31.450 |
| U1 | STUSB4500QTR | C2678061 | QFN-24_L4.0-W4.0-P0.50-BL-EP2.8 | Top | 180 | `CC1DB` | 15.650, -21.290 |
| U2 | TPS16630PWPR | C1849461 | HTSSOP-20_PWP0020T_P0.65_EP2.96_TI-DRAFT | Top | 270 | `EF_IN` | 8.925, -15.100 |
| U3 | LM74700QDBVRQ1 | C2941042 | SOT-23-6_TI-DBV0006A | Top | 0 | `EF_VCAP` | 3.050, -12.500 |
| D8 | BZT52C11-7-F | C92321 | SOD-123_L2.8-W1.8-LS3.7-RD | Bottom | 0 | `VBUS_P` | 5.925, -24.250 |
| D12 | BZT52C18-7-F | C192739 | SOD-123_L2.8-W1.8-LS3.7-RD | Bottom | 0 | `DISCH` | 12.425, -23.000 |
| D13 | BZT52C11-7-F | C92321 | SOD-123_L2.8-W1.8-LS3.7-RD | Bottom | 0 | `VBUS_P` | 5.925, -21.750 |

### B20 (`board-b20-draft`)

| Ref | Part | LCSC | Footprint | Side | Rot | Pad-1 net | Pad-1 centre X, Y (mm, CPL frame) |
| --- | --- | --- | --- | --- | ---: | --- | --- |
| C1 | 100uF 50V | C970687 | CAP-SMD_BD8.0-L8.3-W8.3-LS9.0-FD | Top | 90 | `VIN` | 16.480, 75.370 |
| CAF1 | 47uF 25V polymer | C136280 | CAP-SMD_BD6.3-L6.6-W6.6-FD | Top | 0 | `P12_PRE` | 60.530, 61.000 |
| CBF1 | 47uF 25V polymer | C136280 | CAP-SMD_BD6.3-L6.6-W6.6-FD | Top | 0 | `P5_PRE` | 88.530, 61.000 |
| CCF1 | 47uF 25V polymer | C136280 | CAP-SMD_BD6.3-L6.6-W6.6-FD | Top | 0 | `GND` | 69.330, 32.350 |
| CSO3 | 47uF 25V polymer | C136280 | CAP-SMD_BD6.3-L6.6-W6.6-FD | Top | 0 | `P5_SUP` | 3.430, 12.250 |
| D1 | SDT5A60SA-13 | C3024223 | SMA_Diodes_SDT5A60SA_C3024223 | Top | 180 | `A_SW` | 55.050, 79.020 |
| D2 | SDT5A60SA-13 | C3024223 | SMA_Diodes_SDT5A60SA_C3024223 | Top | 180 | `B_SW` | 83.050, 79.020 |
| D3 | B560C-13-F | C85100 | SMC_Diodes_B560C_C85100 | Top | 180 | `C_SW` | 38.050, 43.750 |
| DZ1 | BZT52C11-7-F | C92321 | SOD-123_L2.8-W1.8-LS3.7-RD | Top | 90 | `P12_G` | 67.800, 46.575 |
| DZ2 | BZT52C11-7-F | C92321 | SOD-123_L2.8-W1.8-LS3.7-RD | Top | 90 | `P5_G` | 93.150, 52.475 |
| DZ3 | BZT52C11-7-F | C92321 | SOD-123_L2.8-W1.8-LS3.7-RD | Top | 90 | `M12_G` | 54.350, 30.775 |
| J5 | PM254V-11-06-H85 | C2832269 | HDR-TH_6P-P2.54-V-F | Top | 270 | `VIN` | 37.200, 66.450 |
| J6 | WJ500V-5.08-2P | C8465 | WJ500V-5.08-2P_C8465 | Top | 90 | `GND` | 7.000, 34.460 |
| J7 | WJ500V-5.08-2P | C8465 | WJ500V-5.08-2P_C8465 | Top | 90 | `P5_OUT` | 7.000, 21.460 |
| J10 | DW254P-2X8-L0 | C4749189 | IDC-TH_16P-P2.54_321016RG0ABK00A01 | Top | 0 | `M12_OUT` | 50.290, 13.500 |
| J11 | DW254P-2X8-L0 | C4749189 | IDC-TH_16P-P2.54_321016RG0ABK00A01 | Top | 0 | `M12_OUT` | 90.390, 13.500 |
| Q1 | CSD18543Q3A | C840100 | VSON-8_L3.3-W3.3-P0.65_CSD18543Q3A | Top | 90 | `P12_CS` | 61.325, 52.525 |
| Q2 | CSD18543Q3A | C840100 | VSON-8_L3.3-W3.3-P0.65_CSD18543Q3A | Top | 90 | `P12_CS` | 66.325, 52.525 |
| Q3 | CSD18543Q3A | C840100 | VSON-8_L3.3-W3.3-P0.65_CSD18543Q3A | Top | 90 | `P5_CS` | 88.175, 52.575 |
| Q4 | CSD18543Q3A | C840100 | VSON-8_L3.3-W3.3-P0.65_CSD18543Q3A | Top | 0 | `P5_CS` | 88.775, 49.625 |
| Q5 | CSD18543Q3A | C840100 | VSON-8_L3.3-W3.3-P0.65_CSD18543Q3A | Top | 0 | `M12_CS` | 57.625, 34.825 |
| Q6 | CSD18543Q3A | C840100 | VSON-8_L3.3-W3.3-P0.65_CSD18543Q3A | Top | 0 | `M12_CS` | 56.375, 39.675 |
| Q10 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 0 | `EN_N` | 64.900, 47.800 |
| Q11 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 270 | `EN_N` | 94.150, 45.300 |
| Q12 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 0 | `RAMP_RST` | 87.700, 18.250 |
| Q24 | DMP3036SFG-7 | C461081 | PowerDI3333-8_DMP3036SFG | Top | 90 | `P5_SUP` | 94.725, 31.550 |
| Q25 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 270 | `M12_OFF` | 63.350, 32.900 |
| Q30 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 0 | `FLT_L` | 5.650, 59.700 |
| Q31 | DMP3036SFG-7 | C461081 | PowerDI3333-8_DMP3036SFG | Top | 0 | `P5_SUP` | 21.650, 51.225 |
| Q32 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 180 | `POR_H` | 13.750, 41.200 |
| Q33 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 0 | `EN_E` | 64.950, 43.200 |
| Q34 | DMP3036SFG-7 | C461081 | PowerDI3333-8_DMP3036SFG | Top | 90 | `P5_SUP` | 69.825, 58.650 |
| Q35 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 90 | `POR_N` | 17.050, 64.150 |
| Q36 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 0 | `PDOK` | 23.550, 16.550 |
| Q37 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 0 | `RDY` | 21.700, 10.700 |
| Q38 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 0 | `FAULT_N` | 19.150, 15.550 |
| Q39 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 0 | `FLT_L` | 22.350, 54.300 |
| Q40 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 180 | `VINUV_CMP` | 106.100, 13.800 |
| Q41 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 90 | `ILIM12N_CMP` | 52.200, 19.850 |
| Q42 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 0 | `OV12_CMP` | 61.600, 2.950 |
| Q43 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 0 | `UV12_CMP` | 16.700, 24.650 |
| Q44 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 0 | `OV5_CMP` | 98.000, 80.000 |
| Q45 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 90 | `UV5_CMP` | 33.600, 70.250 |
| Q46 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 0 | `OVN_CMP` | 14.450, 13.300 |
| Q47 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 0 | `UVN_CMP` | 57.400, 42.550 |
| Q48 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 0 | `EN_N` | 29.050, 48.950 |
| Q49 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 0 | `ARM` | 26.500, 24.050 |
| Q50 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 0 | `PDOK` | 33.550, 50.500 |
| Q54 | DMP3036SFG-7 | C461081 | PowerDI3333-8_DMP3036SFG | Top | 0 | `DIS_C` | 102.100, 34.975 |
| Q56 | DMP3036SFG-7 | C461081 | PowerDI3333-8_DMP3036SFG | Top | 90 | `DIS_C` | 62.675, 12.550 |
| Q57 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 90 | `EN_E` | 92.350, 19.350 |
| Q59 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 0 | `TRK12_PX` | 80.850, 35.500 |
| Q60 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 0 | `TRK5_PX` | 80.750, 30.800 |
| Q61 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 0 | `TRK12N_PX` | 47.600, 17.200 |
| Q62 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 180 | `RAMP_P12` | 83.800, 39.100 |
| Q63 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 0 | `RAMP_M12` | 105.650, 16.500 |
| Q64 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 180 | `RAMP_P5` | 83.400, 34.550 |
| Q65 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 90 | `EN_E` | 17.750, 35.750 |
| Q66 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Top | 0 | `EN_HO` | 18.650, 20.050 |
| U1 | TPS54560DDAR | C31966 | HSOP-8_TI-DDA0008B | Top | 0 | `A_BOOT` | 47.300, 75.905 |
| U2 | TPS54560DDAR | C31966 | HSOP-8_TI-DDA0008B | Top | 0 | `B_BOOT` | 75.300, 75.905 |
| U3 | TPS54560DDAR | C31966 | HSOP-8_TI-DDA0008B | Top | 0 | `C_BOOT` | 27.300, 38.905 |
| U4 | OPA2187IDGKR | C2863562 | VSSOP-8_TI-DGK0008A | Top | 0 | `SV12` | 98.150, 52.025 |
| U5 | OPA2187IDGKR | C2863562 | VSSOP-8_TI-DGK0008A | Top | 0 | `SV12N` | 101.450, 29.925 |
| U6 | OPA2187IDGKR | C2863562 | VSSOP-8_TI-DGK0008A | Top | 0 | `OV12_CMP` | 69.800, 25.975 |
| U7 | OPA2187IDGKR | C2863562 | VSSOP-8_TI-DGK0008A | Top | 0 | `OV5_CMP` | 81.800, 27.975 |
| U8 | OPA2187IDGKR | C2863562 | VSSOP-8_TI-DGK0008A | Top | 0 | `OVN_CMP` | 93.800, 23.975 |
| U9 | OPA2187IDGKR | C2863562 | VSSOP-8_TI-DGK0008A | Top | 180 | `ILIM12N_CMP` | 53.200, 25.375 |
| U10 | REF5025AIDR | C11341 | SOIC-8_TI-D0008A | Top | 90 | `unconnected-(U10-DNC-Pad1)` | 98.095, 58.300 |
| U11 | INA301A3IDGKR | C2861552 | VSSOP-8_TI-DGK0008A | Top | 0 | `P5_SUP` | 46.800, 53.325 |
| U12 | INA301A3IDGKR | C2861552 | VSSOP-8_TI-DGK0008A | Top | 0 | `P5_SUP` | 74.800, 53.325 |
| U13 | OPA2187IDGKR | C2863562 | VSSOP-8_TI-DGK0008A | Top | 0 | `P12_DRV` | 71.800, 39.975 |
| U14 | AP63201WU-7 | C2071044 | TSOT-23-6_L2.9-W1.6-P0.95-LS2.8-BR | Top | 90 | `SUP_FB` | 32.150, 79.100 |
| U15 | OPA2187IDGKR | C2863562 | VSSOP-8_TI-DGK0008A | Top | 0 | `MABS` | 81.800, 43.975 |
| U16 | OPA2187IDGKR | C2863562 | VSSOP-8_TI-DGK0008A | Top | 180 | `CLPM12_O` | 97.650, 40.675 |
| D4 | BZT52C11-7-F | C92321 | SOD-123_L2.8-W1.8-LS3.7-RD | Bottom | 0 | `M12_DG` | 47.425, 64.500 |
| D5 | BZT52C3V9-7-F | C154917 | SOD-123_L2.8-W1.8-LS3.7-RD | Bottom | 0 | `GND` | 36.925, 71.500 |
| Q7 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Bottom | 0 | `SEQ_RG` | 40.500, 80.450 |
| Q8 | DMP3036SFG-7 | C461081 | PowerDI3333-8_DMP3036SFG | Bottom | 0 | `DIS_P` | 34.500, 74.025 |
| Q9 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Bottom | 270 | `SEQ_G` | 52.450, 66.500 |
| Q13 | BSS138-7-F | C40912 | SOT-23_DIODES-DS30144-SUGGESTED | Bottom | 90 | `SEQ_Z` | 44.050, 71.500 |
| Q51 | CSD18543Q3A | C840100 | VSON-8_L3.3-W3.3-P0.65_CSD18543Q3A | Bottom | 180 | `GND` | 4.155, 10.375 |
| Q52 | CSD18543Q3A | C840100 | VSON-8_L3.3-W3.3-P0.65_CSD18543Q3A | Bottom | 180 | `GND` | 8.905, 10.375 |
| Q55 | CSD18543Q3A | C840100 | VSON-8_L3.3-W3.3-P0.65_CSD18543Q3A | Bottom | 90 | `M12_OUT` | 50.975, 58.525 |

## JLC stock re-read 2026-11-20 18:16:23–18:18:30 UTC: the same six lines to resolve

`pd20-order-package-20261120/scripts/fetch-parts.py`, unedited, read JLC's public parts endpoint for all 99 exact
LCSC codes of both package BOMs (`parts-availability-20261120T1816Z.json`, raw responses in `evidence/jlc/`). Every
row's model equals its BOM comment (C970687 adds the suffix "100UF 50V"). The 12:14–12:15 UTC snapshot in
`../pd20-order-package-20261120/` is retained unchanged. Stock moved on other lines, but both snapshots give identical values for the six lines below.

`scripts/stock-review.py` (no network) flags lines for two pairs (`stock-review-20261120T1816Z.json`):

| LCSC | Part | Placements | Stock | 2 pairs + `lossNumber` | `minPurchaseNum` | `leastPatchNumber` | Flag |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| C2861552 | INA301A3IDGKR | B20 U11, U12 | 0 | 4 | 4 | 0 | zero stock |
| C861332 | RT0603BRD0733RL | B20 R35 | 0 | 10 | 200 | 20 | zero stock |
| C705764 | RT0603BRD0730K1L | B20 RVX1 | 2 | 10 | 255 | 20 | below need, minimum and least-patch |
| C523793 | TVS2200DRVR | Board P D5 | 2 | 2 | 21 | 5 | below minimum and least-patch |
| C861371 | RT0603BRD073K09L | B20 R22, R31 | 195 | 12 | 389 | 20 | below minimum |
| C861076 | RT0603BRD0710K4L | B20 R66 | 11 | 8 | 1 | 20 | below least-patch |

JLC does not document `lossNumber` or `leastPatchNumber`, and whether `minPurchaseNum` binds a Standard PCBA order
is not established. Only the supplier's BOM matching and quote decide. The earlier statement that every other line
was "in stock" was true only as stock > 0. These lines are prompts to resolve exact-part supply. No substitution is
proposed; a substitute needs its own component, design and package review.

LCSC retail stock was not re-read. Cost was not re-estimated; the 2026-11-20 two-pair estimate
(USD 527.34 parts and assembly) remains an estimate, not a quote.
