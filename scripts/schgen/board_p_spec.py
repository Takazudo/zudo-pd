"""Board P: reusable USB-PD sink core, 20 V / 5 A revision (unvalidated draft).

Shared exact parts use this project's existing pin-mapped library symbols.
The outline, mounting and interface placement reuse the routed module; the PCB
has NOT been updated to this revision (PCB layout is a later step).

20 V revision (user decision card 2026-10-31, D3-A + D5-1; see
scripts/schgen/decisions.json dec-p-20v-revision and dec-p-20v-front-end-r2):
- D5 TVS2200DRVR (22 V standoff) clamps the connector node VBUS_IN.
- Q3 CSD18543Q3A is U2's external reverse-blocking NFET (source on VBUS_IN =
  IN_SYS, drain on U2 IN, gate on B_GATE); Q4 BSS138-7-F is the B_GATE fast
  pulldown driven by DRV (SLVSE94G 8.3.5).
- U2 TPS26630RGER feeds the protected node VBUS_P ahead of every other part.
  OVP R24/R25 174k/10k 0.1 %: 21.60-22.56 V rising. UVLO R22/R23 11.5k/4.02k
  0.1 %: 4.53-4.73 V rising (falling 4.20-4.45 V). R26 4.02k: I(OL)
  4.185-4.815 A. C5 100 nF dVdT. MODE open = latch; PGTH to GND.
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
- Q1 discharge path R13 is unchanged; its value is a PLACEHOLDER (OSC interface
  discharge values are Board B items).
"""

PROJECT_NAME = 'board-p'
OUT = 'boards/board-p/board-p.kicad_sch'
PAPER = 'A3'

COMPONENTS = {
    'J1': ('TYPE-C-31-M-17', 'TYPE-C-31-M-17', 'C283540', 'zudo-pd:USB-C-SMD_10P-P1.00-L6.8-W8.9', False, (63.5, 88.9)),
    'U1': ('STUSB4500QTR', 'STUSB4500QTR', 'C2678061', 'zudo-pd:QFN-24_L4.0-W4.0-P0.50-BL-EP2.8', False, (152.4, 88.9)),
    'Q1': ('DMP3036SFG-7', 'DMP3036SFG-7', 'C461081', 'zudo-pd:PowerDI3333-8_DMP3036SFG', False, (241.3, 50.8)),
    'D5': ('TVS2200DRVR', 'TVS2200DRVR', 'C523793', 'zudo-pd:WSON-6_L2.0-W2.0-P0.65-BL-EP', False, (203.2, 38.1)),
    'U2': ('TPS26630RGER', 'TPS26630RGER', 'C1850276', 'zudo-pd:VQFN-24_L4.0-W4.0-P0.50-TL-EP2.7', False, (114.3, 38.1)),
    'C3': ('RVT1H101M0810', '100uF 50V', 'C970687', 'zudo-pd:CAP-SMD_BD8.0-L8.3-W8.3-LS9.0-FD', False, (266.7, 241.3)),
    'Q3': ('CSD18543Q3A', 'CSD18543Q3A', 'C840100', 'zudo-pd:VSON-8_L3.3-W3.3-P0.65_CSD18543Q3A', False, (63.5, 38.1)),
    'Q4': ('BSS138-7-F', 'BSS138-7-F', 'C40912', 'zudo-pd:SOT-23_L2.9-W1.3-P1.90-LS2.4-BR', False, (304.8, 241.3)),
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
    'R15': ('0603WAF4701T5E', '4.7k', 'C23162', 'zudo-pd:R0603', False, (190.5, 190.5)),
    'R16': ('0603WAF4701T5E', '4.7k', 'C23162', 'zudo-pd:R0603', False, (228.6, 190.5)),
    'R17': ('0603WAF5101T5E', '5.1k', 'C23186', 'zudo-pd:R0603', True, (38.1, 215.9)),
    'R18': ('0603WAF5101T5E', '5.1k', 'C23186', 'zudo-pd:R0603', True, (76.2, 215.9)),
    'R19': ('0603WAF0000T5E', '0R', 'C21189', 'zudo-pd:R0603', False, (114.3, 215.9)),
    'R20': ('0603WAF0000T5E', '0R', 'C21189', 'zudo-pd:R0603', False, (152.4, 215.9)),
    'R21': ('0805W8F1002T5E', '10k', 'C17414', 'zudo-pd:R0805', False, (266.7, 190.5)),
    'JOUT1': ('PZ254V-11-06P', '2.54mm 1x6 male', 'C492405', 'zudo-pd:HDR-TH_6P-P2.54-V-M', False, (317.5, 88.9)),
    'J2': ('Conn_1x04', 'PogoPad_1x4_NVM_I2C', '', 'zudo-pd:PogoPad_1x04_P2.54mm', False, (317.5, 139.7)),
    'J3': ('Conn_1x08', 'PogoPad_1x8_Debug', '', 'zudo-pd:PogoPad_1x08_P2.54mm', False, (317.5, 190.5)),
}

NETS = {
    'VBUS_IN': ['J1.2', 'J1.5', 'C1.2', 'C2.2', 'J3.4', 'D5.4', 'D5.5', 'D5.6', 'Q3.1', 'Q3.2', 'Q3.3', 'Q4.2', 'U2.5', 'R22.1', 'R24.1'],
    'EF_IN': ['Q3.5', 'Q3.6', 'Q3.7', 'Q3.8', 'Q3.9', 'U2.1', 'U2.2'],
    'EF_BGATE': ['Q3.4', 'Q4.3', 'U2.3'],
    'EF_DRV': ['Q4.1', 'U2.4'],
    'VBUS_P': ['U2.17', 'U2.18', 'U1.24', 'R14.1', 'R11.2', 'Q1.1', 'Q1.2', 'Q1.3', 'C35.2', 'C3.1', 'D8.1'],
    'EF_UVLO': ['U2.6', 'R22.2', 'R23.1'],
    'EF_OVP': ['U2.7', 'R24.2', 'R25.1'],
    'EF_DVDT': ['U2.9', 'C5.1'],
    'EF_ILIM': ['U2.10', 'R26.1'],
    'CC1': ['J1.3', 'U1.2', 'R17.1', 'R19.2', 'D6.1'],
    'CC2': ['J1.4', 'U1.4', 'R18.1', 'R20.2', 'D7.1'],
    'CC1DB': ['U1.1', 'R19.1', 'J3.1'],
    'CC2DB': ['U1.5', 'R20.1', 'J3.2'],
    'VBUS_VS_DISCH': ['U1.18', 'R14.2'],
    'VBEN': ['U1.16', 'R12.1', 'J3.8'],
    'Q1_G': ['Q1.4', 'R11.1', 'R12.2', 'C35.1', 'D8.2'],
    'VBUS_OUT': ['Q1.5', 'Q1.6', 'Q1.7', 'Q1.8', 'Q1.9', 'R13.1', 'JOUT1.1', 'JOUT1.2'],
    'DISCH': ['U1.9', 'R13.2'],
    'VREG_2V7': ['U1.23', 'C30.2', 'R15.2', 'R16.2', 'J3.3'],
    'VREG_1V2': ['U1.21', 'C34.1'],
    'SCL': ['U1.7', 'R15.1', 'J2.1'],
    'SDA': ['U1.8', 'R16.1', 'J2.2'],
    'RESET': ['U1.6', 'R21.1', 'J2.4'],
    'ATT': ['U1.11', 'J3.6', 'JOUT1.3'],
    'PDOK': ['U1.20', 'J3.7', 'JOUT1.4'],
    'GND': ['U1.10', 'U1.12', 'U1.13', 'U1.22', 'U1.25', 'J1.1', 'J1.6', 'J1.0', 'C1.1', 'C2.1', 'C30.1', 'C34.2', 'R21.2', 'R17.2', 'R18.2', 'J2.3', 'J3.5', 'D5.1', 'D5.2', 'D5.3', 'D5.7', 'U2.8', 'U2.15', 'U2.25', 'R23.2', 'R25.2', 'R26.2', 'C5.2', 'C3.2', 'D6.2', 'D7.2', 'JOUT1.5', 'JOUT1.6'],
}

NO_CONNECT = ['U1.3', 'U1.14', 'U1.15', 'U1.17', 'U1.19',
              'U2.11', 'U2.12', 'U2.13', 'U2.14', 'U2.16',
              'U2.19', 'U2.20', 'U2.21', 'U2.22', 'U2.23', 'U2.24']

LABEL_OVERRIDES = {'Q1': {'Reference': (256.54, 43.18), 'Value': (256.54, 58.419999999999995)}}
