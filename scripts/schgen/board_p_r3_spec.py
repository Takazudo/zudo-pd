"""Board P r3 DRAFT: 20 V / 5 A revision with the TPS16630 + LM74700 front end and the
common controller block (unvalidated paper draft; separate from board_p_spec).

This is a sibling of board_p_spec.py on purpose. board_p_spec.py (r2, TPS26630) is bound
to the central inventory, and its TPS26630 facts feed integration rules whose
independent observed runs are hash-locked. Folding r3 into it needs those rules and
runs refreshed. Until then r3 is not bound to the inventory: TPS16630PWPR C1849461 and
LM74700QDBVRQ1 C2941042 are SHORTLISTED candidates, the HTSSOP-20 land is a TI-derived
draft, and no PCB exists. Interface spec: manager common-controller-block.md.

Everything not listed under "r3" below is unchanged from board_p_spec.py r2.

Shared exact parts use this project's existing pin-mapped library symbols.
The outline, mounting and interface placement reuse the routed module; the PCB
has NOT been updated to this revision (PCB layout is a later step).

20 V revision (user decision card 2026-10-31, D3-A + D5-1; see
scripts/schgen/decisions.json dec-p-20v-revision and dec-p-20v-front-end-r2):
- D5 TVS2200DRVR (22 V standoff) clamps the connector node VBUS_IN.
- r3 front end (user decision 2026-10-31, dec-p-20v-front-end-r3; replaces TPS26630
  and its B_GATE driver Q4): U3 LM74700QDBVRQ1 ideal-diode controller drives Q3
  CSD18543Q3A (source on VBUS_IN = ANODE, drain on EF_IN = CATHODE, gate on EF_GATE).
  EN is tied to ANODE (always on, SNOSD17G Table 5-1); C37 1 uF is the VCAP-to-ANODE
  charge-pump capacitor (0.1 uF minimum).
- U2 TPS16630PWPR (HTSSOP-20, TI-derived draft land) feeds the protected node VBUS_P
  ahead of every other Board P part. IN 1-3 and P_IN 6 on EF_IN; OUT 18-20 on VBUS_P.
  OVP R24/R25 174k/10k 0.1 %: 21.60-22.56 V rising (V(OVPR) 1.176-1.224 V, SLVSET9G).
  UVLO R22/R23 11.5k/4.02k 0.1 %: 4.53-4.73 V rising. R26 4.02k: I(OL) 4.185-4.815 A.
  C5 100 nF dVdT. MODE open = latch; SHDN, IMON, FLT and PGOOD open. Both dividers
  sense VBUS_IN, ahead of the ideal diode.
- r3 common controller block (manager common-controller-block.md, LED requirements
  R1.1-R1.3): RESET is strapped to GND by R21 0R at the pin and is no longer on a pogo
  pad (J2.4 is NC). The I2C pull-ups R15/R16 are removed; the programming jig supplies
  them from its own rail. SCL/SDA float between programming sessions (OPEN).
- C3 is the single 100 uF protected-node bulk (80-120 uF initial tolerance),
  sized so the 5->20 V transition inrush at the 30 V/ms PD slew ceiling stays
  below the I(OL) minimum.
- Q1 is PROPOSED as DMP3036SFG-7 C461081 (PowerDI3333-8, -30 V, +/-25 V VGS,
  -5.8 A at 70 C / -7.2 A at 25 C with VGS -5 V on 1 in2 of 2 oz copper) in place of
  AO3401A (-4.2 A), per decisions.json dec-p-20v-q1-5a. Pins 1-3 S on VBUS_P, 4 G on
  Q1_G, 5-8 and exposed pad 9 D on VBUS_OUT. The draft footprint and the copper
  needed for the rating are not laid out.
- Q1 gate drive DRAFT (dec-p-20v-q1-gate-clamp, phase 6): R11 (source-gate) 100k ->
  150k C22807 and R12 (gate-VBEN) 150k -> 4.7k C23162, so the asserted VGS is
  -4.60 / -4.85 / -5.09 V at 4.75 / 5.00 / 5.25 V VBUS (was -2.0 V at 5 V, inside the
  threshold range), and D8 BZT52C11-7-F C92321 (cathode
  VBUS_P, anode Q1_G, the Board A dec-e-q1-20v-gate-guard topology) clamps VGS to
  10.4-11.6 V at 20 V so the +/-25 V VGSS limit keeps >= 13.3 V margin. With D8 open
  the divider alone gives -24.44 V at the 25.21 V overshoot case (inside 25 V).
  C35 is unchanged; the turn-on gate time constant falls from 6.0 ms to 0.46 ms and
  the VBEN-release turn-off constant (R11 x C35) rises from 10 ms to 15 ms.
- Q1 soft turn-on DRAFT (dec-p-20v-q1-soft-start, phase 7, independent review
  finding 3): C36 1 uF C15849 is a Miller capacitor from VBUS_OUT to node Q1_MX, and
  Q5 BSS138-7-F (gate and source on Q1_MX, drain on Q1_G) acts as a body diode from
  Q1_MX to Q1_G. The diode lets the drain's rise feed back into the gate during
  turn-on, so the drain slews at the R12 gate current divided by C36. It blocks the
  reverse path, so a VBUS_P rise with Q1 off cannot pull the gate below the source.
  R27 150k C22807 recharges Q1_MX from VBUS_P between cycles. The 20 V closure slews
  at about 3.1-10 V/ms (PA plateau and DC-bias range). Into a 250 uF Board B bank
  that is at most 2.5 A, below the I(OL) 4.185 A minimum. Q1 SOA is OPEN.
- VBUS_VS_DISCH series resistance is R14 + R28, 2 x 470R C23179 (independent review
  finding 10): 26.7 mA at 25.1 V, against the 50 mA maximum. The STUSB discharge time
  constant doubles (OPEN interaction).
- Q1 discharge path R13 is unchanged; its value is a PLACEHOLDER (OSC interface
  discharge values are Board B items).
"""

PROJECT_NAME = 'board-p-r3-draft'
OUT = 'boards/board-p-r3-draft/board-p-r3-draft.kicad_sch'
PAPER = 'A3'

COMPONENTS = {
    'J1': ('TYPE-C-31-M-17', 'TYPE-C-31-M-17', 'C283540', 'zudo-pd:USB-C-SMD_10P-P1.00-L6.8-W8.9', False, (63.5, 88.9)),
    'U1': ('STUSB4500QTR', 'STUSB4500QTR', 'C2678061', 'zudo-pd:QFN-24_L4.0-W4.0-P0.50-BL-EP2.8', False, (152.4, 88.9)),
    'Q1': ('DMP3036SFG-7', 'DMP3036SFG-7', 'C461081', 'zudo-pd:PowerDI3333-8_DMP3036SFG', False, (241.3, 50.8)),
    'D5': ('TVS2200DRVR', 'TVS2200DRVR', 'C523793', 'zudo-pd:WSON-6_L2.0-W2.0-P0.65-BL-EP', False, (203.2, 38.1)),
    'U2': ('TPS16630PWPR', 'TPS16630PWPR', 'C1849461', 'zudo-pd:HTSSOP-20_PWP0020T_P0.65_EP2.96_TI-DRAFT', False, (114.3, 38.1)),
    'U3': ('LM74700QDBVRQ1', 'LM74700QDBVRQ1', 'C2941042', 'zudo-pd:SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BL', False, (241.3, 266.7)),
    'C37': ('CL10A105KB8NNNC', '1uF/50V', 'C15849', 'zudo-pd:C0603', False, (190.5, 266.7)),
    'C3': ('RVT1H101M0810', '100uF 50V', 'C970687', 'zudo-pd:CAP-SMD_BD8.0-L8.3-W8.3-LS9.0-FD', False, (266.7, 241.3)),
    'Q3': ('CSD18543Q3A', 'CSD18543Q3A', 'C840100', 'zudo-pd:VSON-8_L3.3-W3.3-P0.65_CSD18543Q3A', False, (63.5, 38.1)),
    'C5': ('CC0603KRX7R9BB104', '100nF/50V', 'C14663', 'zudo-pd:C0603', False, (228.6, 241.3)),
    'R22': ('RT0603BRD0711K5L', '11.5k 0.1%', 'C705719', 'zudo-pd:R0603', False, (38.1, 241.3)),
    'R23': ('RT0603BRD074K02L', '4.02k 0.1%', 'C705781', 'zudo-pd:R0603', False, (76.2, 241.3)),
    'R24': ('RT0603BRD07174KL', '174k 0.1%', 'C861163', 'zudo-pd:R0603', False, (114.3, 241.3)),
    'R25': ('RT0603BRD0710KL', '10k 0.1%', 'C95204', 'zudo-pd:R0603', False, (152.4, 241.3)),
    'R26': ('RT0603BRD074K02L', '4.02k 0.1%', 'C705781', 'zudo-pd:R0603', False, (190.5, 241.3)),
    'D6': ('PESD24VS1UB_C85382', 'PESD24VS1UB', 'C85382', 'zudo-pd:SOD-523_L1.2-W0.8-LS1.6-RD', True, (228.6, 165.1)),
    'D7': ('PESD24VS1UB_C85382', 'PESD24VS1UB', 'C85382', 'zudo-pd:SOD-523_L1.2-W0.8-LS1.6-RD', True, (190.5, 215.9)),
    'C1': ('CL31A106KBHNNNE', '10uF/50V', 'C13585', 'zudo-pd:C1206', False, (38.1, 165.1)),
    'C2': ('CC0603KRX7R9BB104', '100nF/50V', 'C14663', 'zudo-pd:C0603', False, (76.2, 165.1)),
    'C30': ('CL10A105KB8NNNC', '1uF/50V', 'C15849', 'zudo-pd:C0603', False, (114.3, 165.1)),
    'C34': ('CL10A105KB8NNNC', '1uF/50V', 'C15849', 'zudo-pd:C0603', False, (152.4, 165.1)),
    'C35': ('CC0603KRX7R9BB104', '100nF/50V', 'C14663', 'zudo-pd:C0603', False, (190.5, 165.1)),
    'R11': ('0603WAF1503T5E', '150k', 'C22807', 'zudo-pd:R0603', False, (38.1, 190.5)),
    'R12': ('0603WAF4701T5E', '4.7k', 'C23162', 'zudo-pd:R0603', False, (76.2, 190.5)),
    'D8': ('BZT52C11-7-F_C92321', 'BZT52C11-7-F', 'C92321', 'zudo-pd:SOD-123_L2.8-W1.8-LS3.7-RD', False, (279.4, 76.2)),
    'R13': ('0603WAF4700T5E', '470R', 'C23179', 'zudo-pd:R0603', False, (114.3, 190.5)),
    'R14': ('0603WAF4700T5E', '470R', 'C23179', 'zudo-pd:R0603', False, (152.4, 190.5)),
    'R28': ('0603WAF4700T5E', '470R', 'C23179', 'zudo-pd:R0603', False, (152.4, 266.7)),
    'C36': ('CL10A105KB8NNNC', '1uF/50V', 'C15849', 'zudo-pd:C0603', False, (38.1, 266.7)),
    'Q5': ('BSS138-7-F', 'BSS138-7-F', 'C40912', 'zudo-pd:SOT-23_L2.9-W1.3-P1.90-LS2.4-BR', False, (76.2, 266.7)),
    'R27': ('0603WAF1503T5E', '150k', 'C22807', 'zudo-pd:R0603', False, (114.3, 266.7)),
    'R17': ('0603WAF5101T5E', '5.1k', 'C23186', 'zudo-pd:R0603', True, (38.1, 215.9)),
    'R18': ('0603WAF5101T5E', '5.1k', 'C23186', 'zudo-pd:R0603', True, (76.2, 215.9)),
    'R19': ('0603WAF0000T5E', '0R', 'C21189', 'zudo-pd:R0603', False, (114.3, 215.9)),
    'R20': ('0603WAF0000T5E', '0R', 'C21189', 'zudo-pd:R0603', False, (152.4, 215.9)),
    'R21': ('0603WAF0000T5E', '0R', 'C21189', 'zudo-pd:R0603', False, (266.7, 190.5)),
    'JOUT1': ('PZ254V-11-06P', '2.54mm 1x6 male', 'C492405', 'zudo-pd:HDR-TH_6P-P2.54-V-M', False, (317.5, 88.9)),
    'J2': ('Conn_1x04', 'PogoPad_1x4_NVM_I2C', '', 'zudo-pd:PogoPad_1x04_P2.54mm', False, (317.5, 139.7)),
    'J3': ('Conn_1x08', 'PogoPad_1x8_Debug', '', 'zudo-pd:PogoPad_1x08_P2.54mm', False, (317.5, 190.5)),
}

NETS = {
    'VBUS_IN': ['J1.2', 'J1.5', 'C1.2', 'C2.2', 'J3.4', 'D5.4', 'D5.5', 'D5.6', 'Q3.1', 'Q3.2', 'Q3.3', 'U3.6', 'U3.3', 'C37.2', 'R22.1', 'R24.1'],
    'EF_IN': ['Q3.5', 'Q3.6', 'Q3.7', 'Q3.8', 'Q3.9', 'U3.4', 'U2.1', 'U2.2', 'U2.3', 'U2.6'],
    'EF_GATE': ['Q3.4', 'U3.5'],
    'EF_VCAP': ['U3.1', 'C37.1'],
    'VBUS_P': ['U2.18', 'U2.19', 'U2.20', 'U1.24', 'R14.1', 'R11.2', 'R27.1', 'Q1.1', 'Q1.2', 'Q1.3', 'C35.2', 'C3.1', 'D8.1'],
    'EF_UVLO': ['U2.7', 'R22.2', 'R23.1'],
    'EF_OVP': ['U2.8', 'R24.2', 'R25.1'],
    'EF_DVDT': ['U2.10', 'C5.1'],
    'EF_ILIM': ['U2.11', 'R26.1'],
    'CC1': ['J1.3', 'U1.2', 'R17.1', 'R19.2', 'D6.1'],
    'CC2': ['J1.4', 'U1.4', 'R18.1', 'R20.2', 'D7.1'],
    'CC1DB': ['U1.1', 'R19.1', 'J3.1'],
    'CC2DB': ['U1.5', 'R20.1', 'J3.2'],
    'VBUS_VS_DISCH': ['U1.18', 'R28.2'],
    'VBUS_DISCH_R': ['R14.2', 'R28.1'],
    'VBEN': ['U1.16', 'R12.1', 'J3.8'],
    'Q1_G': ['Q1.4', 'R11.1', 'R12.2', 'C35.1', 'D8.2', 'Q5.3'],
    'Q1_MX': ['C36.1', 'Q5.1', 'Q5.2', 'R27.2'],
    'VBUS_OUT': ['Q1.5', 'Q1.6', 'Q1.7', 'Q1.8', 'Q1.9', 'R13.1', 'C36.2', 'JOUT1.1', 'JOUT1.2'],
    'DISCH': ['U1.9', 'R13.2'],
    'VREG_2V7': ['U1.23', 'C30.2', 'J3.3'],
    'VREG_1V2': ['U1.21', 'C34.1'],
    'SCL': ['U1.7', 'J2.1'],
    'SDA': ['U1.8', 'J2.2'],
    'RESET': ['U1.6', 'R21.1'],
    'ATT': ['U1.11', 'J3.6', 'JOUT1.3'],
    'PDOK': ['U1.20', 'J3.7', 'JOUT1.4'],
    'GND': ['U1.10', 'U1.12', 'U1.13', 'U1.22', 'U1.25', 'J1.1', 'J1.6', 'J1.0', 'C1.1', 'C2.1', 'C30.1', 'C34.2', 'R21.2', 'R17.2', 'R18.2', 'J2.3', 'J3.5', 'D5.1', 'D5.2', 'D5.3', 'D5.7', 'U2.9', 'U2.21', 'U3.2', 'R23.2', 'R25.2', 'R26.2', 'C5.2', 'C3.2', 'D6.2', 'D7.2', 'JOUT1.5', 'JOUT1.6'],
}

NO_CONNECT = ['U1.3', 'U1.14', 'U1.15', 'U1.17', 'U1.19',
              'U2.4', 'U2.5', 'U2.12', 'U2.13', 'U2.14', 'U2.15', 'U2.16', 'U2.17',
              'J2.4']

LABEL_OVERRIDES = {'Q1': {'Reference': (256.54, 43.18), 'Value': (256.54, 58.419999999999995)}}
