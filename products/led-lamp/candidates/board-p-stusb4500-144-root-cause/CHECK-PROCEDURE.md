# #144 Board P check procedure (owner-executable, draft 2026-10-31)

## 日本語サマリー

- 対象: 発注済み STUSB4500 LED Board P（2枚）。15 V を保持できず、RESET が 0.93 V になる不具合（#144）の原因切り分け。
- 目的: 「VBUS 由来のリークが RESET に入る（R13 パッド間・VBUS_VS_DISCH ビア近傍の RESET 配線）」「2.7 V/SCL 側からのリーク」「U1 の損傷」「NVM 内容」のどれかを区別する。
- **ステップ A（無通電の抵抗測定）は許可不要**で、最初に行う。Board L・書き込み治具・USB ケーブルはすべて外す。
- **ステップ B 以降（通電・洗浄・部品変更）はすべてオーナーの明示的な許可が必要。** 各ステップに「要許可」と明記。
- 15 V ソースでの再試験と、R21 の 0 Ω 化・R15/R16 の撤去はいちばん最後。どれも 1 枚のみで行い、もう 1 枚は比較用に現状のまま残す。
- 結果は下の記録表に書き込む。判定は「仮説の絞り込み」であり、修理・検証済みの扱いにはしない。

## Scope and safety

- Desk-derived procedure; nothing in it has been tried. Use **one** Board P (call it P-A); keep P-B untouched as a reference until P-A results are in.
- Board L, the NVM/I2C jig and every USB cable disconnected unless a step says otherwise.
- ESD precautions: J2.4 (RESET) is a bare pad, silk-labelled "NC" by mistake (#143).
- Pads (from `scripts/schgen/board_p_spec.py`):
  - J2: 1 SCL, 2 SDA, 3 GND, 4 RESET.
  - J3: 1 CC1DB, 2 CC2DB, 3 VREG_2V7, 4 VBUS_IN, 5 GND, 6 ATT, 7 PDOK, 8 VBEN.
  - JOUT1: 1,2 VBUS_OUT; 3 ATT; 4 PDOK; 5,6 GND.
- Reference values: R21 10 k (RESET-GND), R13/R14 470 Ohm, R15/R16 4.7 k to VREG_2V7. STUSB4500 RESET: VIL max 0.35 V, VIH min 1.2 V (DS12499 Rev 7).

## A. Unpowered resistance (no permission needed)

Board fully unpowered for > 1 min. Meter on its lowest auto-ranging resistance range. Measure each pair in **both lead polarities** (red on first node, then swapped).

| Step | Pair | Expected if no defect | What it tells |
| --- | --- | --- | --- |
| A1 | J2.4 RESET - J2.3 GND | ~10 k (R21) | Earlier 6.93 k: confirms an extra ~23 k path |
| A2 | J2.4 RESET - J3.4 VBUS_IN | high (chip ESD path, polarity-dependent) | **Finite and the same both ways: resistive PCB leak (rank 1).** Diode-like asymmetry: through U1 (rank 3) |
| A3 | J2.4 RESET - JOUT1.1 VBUS_OUT | high | Same reading as A2 points to the R13 area (RESET runs between R13's pads) |
| A4 | J2.4 RESET - J2.1 SCL | high | Earlier 13 k: path to the 2.7 V/SCL side (rank 2) |
| A5 | J2.4 RESET - J3.3 VREG_2V7 | high | Compare with A4 |
| A6 | J3.4 VBUS_IN - J3.5 GND | high (D5 reverse) | Low value: damaged D5/U1 |
| A7 | J3.3 VREG_2V7 - J3.5 GND | high | Low value: damaged U1 regulator |
| A8 | Repeat A1-A4 on P-B | as above | Same pattern on both boards supports a layout/process cause |

Also: magnifier/microscope photos of the R13 area, the via near U1's RESET corner, and the U1 edge (flux residue, solder balls). No cleaning yet.

## B. Energized at 5 V, Board L off (requires explicit permission)

- **B1 (requires permission).** Supply: bench supply on J3.4 / J3.5, current limit 50 mA, starting at 5.0 V. No USB source, so no PD negotiation. Measure RESET (J2.4), VREG_2V7 (J3.3), SCL (J2.1) and VBEN (J3.8) against GND.
- **B2 (requires permission).** Same set-up: set the supply to 4.6 V, then 5.4 V. Record RESET at each.
  - RESET rises with VBUS: rank 1.
  - RESET stays constant: rank 2.
- **B3 (requires permission).** At 5.0 V, short J2.1 (SCL) to J2.3 (GND) with a jumper and re-read RESET.
  - A fall: SCL-side path contributes.
- **B4 (requires permission).** Read-only NVM dump with the jig at 5.0 V. Save all 40 bytes with board ID and date; do not write.
  - "I2C read error" again: record it; this is itself evidence.
- **B5 (requires permission).** Repeat B1-B2 with the jig unplugged, if it was attached.

## C. Cleaning (requires explicit permission; unpowered, non-destructive)

- **C1.** IPA clean around R13, the via near U1 pin 6 and the U1 edges. Dry fully (>= 30 min). Repeat A1-A4 and B1-B2.
  - Values move toward "expected": contamination (rank 1).

## D. Function retry and rework (requires explicit permission, last)

- **D1 (requires permission).** P-A only, Board L disconnected. 15 V-capable PD source via J1. Record:
  - VBUS (J3.4), RESET (J2.4), VBEN (J3.8), VBUS_OUT (JOUT1.1) over 30 s.
  - RESET crossing ~1.2 V when VBUS steps to 15 V: confirms the reset mechanism.
- **D2 (requires permission; changes the board).** Owner-audit rework: R21 to 0 Ohm strap; remove R15/R16; tie SCL/SDA links to GND. Repeat D1.
  - Holding 15 V: RESET-path cause confirmed.
  - Still failing: U1 damage (rank 3) or NVM (use the B4 dump).
- **D3 (requires permission).** Only after D2 holds 15 V on its own: connect a Board L with SW2 OFF, then switch ON. Record whether VBUS_OUT holds.

## Record sheet

| Step | P-A | P-B | Notes |
| --- | --- | --- | --- |
| A1 RESET-GND | | | |
| A2 RESET-VBUS_IN (+/-) | | | |
| A3 RESET-VBUS_OUT (+/-) | | | |
| A4 RESET-SCL (+/-) | | | |
| A5 RESET-2V7 (+/-) | | | |
| A6 VBUS_IN-GND (+/-) | | | |
| A7 2V7-GND (+/-) | | | |
| B1 RESET / 2V7 / SCL / VBEN @5.0 V | | n/a | |
| B2 RESET @4.6 / 5.4 V | | n/a | |
| B3 RESET with SCL shorted | | n/a | |
| B4 NVM dump file | | n/a | |
| C1 after-clean A1-A4, B2 | | n/a | |
| D1 / D2 / D3 | | n/a | |
