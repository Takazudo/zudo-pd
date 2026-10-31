"""Board P: reusable USB-PD sink core, 20 V / 5 A revision (unvalidated draft).

Shared exact parts use this project's existing pin-mapped library symbols.
The outline, mounting and interface placement reuse the routed module; the PCB
has NOT been updated to this revision (PCB layout is a later step).

20 V revision (user decision card 2026-10-31, D3-A + D5-1; see
scripts/schgen/decisions.json dec-p-20v-revision):
- D5 TVS2200DRVR (22 V standoff) replaces the 16 V SMAJ16A at the connector.
- U2 TPS26630RGER eFuse sits between connector VBUS_IN and the protected node
  VBUS_P, ahead of every other Board P part. OVP divider R24/R25 (174k/10k,
  0.1 %) sets 21.60-22.56 V rising; UVLO divider R22/R23 (10.5k/4.3k) sets
  4.02-4.25 V rising; R26 4.02k sets I(OL) 4.185-4.815 A (SLVSE94G table point);
  C5 100 nF sets the dVdT ramp. MODE open selects latch-off. PGTH to GND
  disables fast recovery turn-on (SLVSE94G 8.3.2.1). No external blocking FET:
  B_GATE/DRV float and IN_SYS ties to IN, so there is no reverse blocking.
- C3/C4 (2x 100 uF 50 V) are the protected-node bulk, >=160 uF after the
  -20 % initial tolerance only.
- Q1 discharge path R13 is unchanged; its value is a PLACEHOLDER until the OSC
  interface file fixes the discharge requirement.
"""

PROJECT_NAME = 'board-p'
OUT = 'boards/board-p/board-p.kicad_sch'
PAPER = 'A3'

COMPONENTS = {
    'J1': ('TYPE-C-31-M-17', 'TYPE-C-31-M-17', 'C283540', 'zudo-pd:USB-C-SMD_10P-P1.00-L6.8-W8.9', False, (63.5, 88.9)),
    'U1': ('STUSB4500QTR', 'STUSB4500QTR', 'C2678061', 'zudo-pd:QFN-24_L4.0-W4.0-P0.50-BL-EP2.8', False, (152.4, 88.9)),
    'Q1': ('AO3401A_C347476', 'AO3401A', 'C347476', 'zudo-pd:SOT-23_L2.9-W1.3-P1.90-LS2.4-BR', False, (241.3, 50.8)),
    'D5': ('TVS2200DRVR', 'TVS2200DRVR', 'C523793', 'zudo-pd:WSON-6_L2.0-W2.0-P0.65-BL-EP', False, (203.2, 38.1)),
    'U2': ('TPS26630RGER', 'TPS26630RGER', 'C1850276', 'zudo-pd:VQFN-24_L4.0-W4.0-P0.50-TL-EP2.7', False, (114.3, 38.1)),
    'C3': ('RVT1H101M0810', '100uF 50V', 'C970687', 'zudo-pd:CAP-SMD_BD8.0-L8.3-W8.3-LS9.0-FD', False, (266.7, 241.3)),
    'C4': ('RVT1H101M0810', '100uF 50V', 'C970687', 'zudo-pd:CAP-SMD_BD8.0-L8.3-W8.3-LS9.0-FD', False, (304.8, 241.3)),
    'C5': ('CC0603KRX7R9BB104', '100nF/50V', 'C14663', 'zudo-pd:C0603', False, (228.6, 241.3)),
    'R22': ('RT0603BRD0710K5L', '10.5k 0.1%', 'C861077', 'zudo-pd:R0603', False, (38.1, 241.3)),
    'R23': ('0603WAF4301T5E', '4.3k', 'C23159', 'zudo-pd:R0603', False, (76.2, 241.3)),
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
    'R11': ('0603WAF1003T5E', '100k', 'C25803', 'zudo-pd:R0603', False, (38.1, 190.5)),
    'R12': ('0603WAF1503T5E', '150k', 'C22807', 'zudo-pd:R0603', False, (76.2, 190.5)),
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
    'VBUS_IN': ['J1.2', 'J1.5', 'C1.2', 'C2.2', 'J3.4', 'D5.4', 'D5.5', 'D5.6', 'U2.1', 'U2.2', 'U2.5', 'R22.1', 'R24.1'],
    'VBUS_P': ['U2.17', 'U2.18', 'U1.24', 'R14.1', 'R11.2', 'Q1.2', 'C35.2', 'C3.1', 'C4.1'],
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
    'Q1_G': ['Q1.1', 'R11.1', 'R12.2', 'C35.1'],
    'VBUS_OUT': ['Q1.3', 'R13.1', 'JOUT1.1', 'JOUT1.2'],
    'DISCH': ['U1.9', 'R13.2'],
    'VREG_2V7': ['U1.23', 'C30.2', 'R15.2', 'R16.2', 'J3.3'],
    'VREG_1V2': ['U1.21', 'C34.1'],
    'SCL': ['U1.7', 'R15.1', 'J2.1'],
    'SDA': ['U1.8', 'R16.1', 'J2.2'],
    'RESET': ['U1.6', 'R21.1', 'J2.4'],
    'ATT': ['U1.11', 'J3.6', 'JOUT1.3'],
    'PDOK': ['U1.20', 'J3.7', 'JOUT1.4'],
    'GND': ['U1.10', 'U1.12', 'U1.13', 'U1.22', 'U1.25', 'J1.1', 'J1.6', 'J1.0', 'C1.1', 'C2.1', 'C30.1', 'C34.2', 'R21.2', 'R17.2', 'R18.2', 'J2.3', 'J3.5', 'D5.1', 'D5.2', 'D5.3', 'D5.7', 'U2.8', 'U2.15', 'U2.25', 'R23.2', 'R25.2', 'R26.2', 'C5.2', 'C3.2', 'C4.2', 'D6.2', 'D7.2', 'JOUT1.5', 'JOUT1.6'],
}

NO_CONNECT = ['U1.3', 'U1.14', 'U1.15', 'U1.17', 'U1.19',
              'U2.3', 'U2.4', 'U2.11', 'U2.12', 'U2.13', 'U2.14', 'U2.16',
              'U2.19', 'U2.20', 'U2.21', 'U2.22', 'U2.23', 'U2.24']

LABEL_OVERRIDES = {'Q1': {'Reference': (256.54, 43.18), 'Value': (256.54, 58.419999999999995)}}
