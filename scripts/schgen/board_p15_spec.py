"""Board P 15 V: the separate 15 V zudo-pd product's USB-PD sink module (dec-separate-products).

Unvalidated draft. Stage 1 reproduced the as-built routed module (boards/board-p/board-p.kicad_pcb and
scripts/schgen/baselines/board-p.json) exactly. Stage 2 applies the common-controller-block RESET subset
(dec-p15-reset-subset, LED requirements R1.1-R1.3): R21 becomes a 0 Ohm C21189 strap from RESET to GND
at U1.6, J2.4 is no longer connected, and the R15/R16 I2C pull-ups to VREG_2V7 move to the programming
jig. Phase 17 adds dec-p15-i2c-pulldowns (R22/R23 100k from SCL/SDA to GND, so the pins are defined in
normal use while the jig pull-ups override them) and dec-p15-vdd-local-clamp (the r3 VDD feed: VDD on VDD_LOC
behind R29 1k + R30 470R from VBUS_IN, clamped by D9 BZT52C18-7-F; the as-built C2 100 nF moves from VBUS_IN
to VDD_LOC as the local decoupler, and r3's C38 is not fitted). Everything else (SMAJ16A D5, AO3401A Q1,
470 Ohm R13/R14, 15 V NVM image) is the as-built 15 V design. scripts/schgen/baselines/board-p15-allow.json
lists the deltas.
"""
PROJECT_NAME = 'board-p15'
OUT = 'boards/board-p15/board-p15.kicad_sch'
PAPER = 'A3'

COMPONENTS = {
    'J1': ('TYPE-C-31-M-17', 'TYPE-C-31-M-17', 'C283540', 'zudo-pd:USB-C-SMD_10P-P1.00-L6.8-W8.9', False, (63.5, 88.9)),
    'U1': ('STUSB4500QTR', 'STUSB4500QTR', 'C2678061', 'zudo-pd:QFN-24_L4.0-W4.0-P0.50-BL-EP2.8', False, (152.4, 88.9)),
    'Q1': ('AO3401A_C347476', 'AO3401A', 'C347476', 'zudo-pd:SOT-23_L2.9-W1.3-P1.90-LS2.4-BR', False, (241.3, 50.8)),
    'D5': ('SMAJ16A', 'SMAJ16A', 'C74561', 'zudo-pd:SMA_Littelfuse_SMAJ16A_C74561', False, (203.2, 38.1)),
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
    'R17': ('0603WAF5101T5E', '5.1k', 'C23186', 'zudo-pd:R0603', True, (38.1, 215.9)),
    'R18': ('0603WAF5101T5E', '5.1k', 'C23186', 'zudo-pd:R0603', True, (76.2, 215.9)),
    'R19': ('0603WAF0000T5E', '0R', 'C21189', 'zudo-pd:R0603', False, (114.3, 215.9)),
    'R20': ('0603WAF0000T5E', '0R', 'C21189', 'zudo-pd:R0603', False, (152.4, 215.9)),
    'R21': ('0603WAF0000T5E', '0R', 'C21189', 'zudo-pd:R0603', False, (266.7, 190.5)),
    'R22': ('0603WAF1003T5E', '100k', 'C25803', 'zudo-pd:R0603', False, (228.6, 215.9)),
    'R23': ('0603WAF1003T5E', '100k', 'C25803', 'zudo-pd:R0603', False, (266.7, 215.9)),
    'R29': ('0603WAF1001T5E', '1k', 'C21190', 'zudo-pd:R0603', False, (190.5, 190.5)),
    'R30': ('0603WAF4700T5E', '470R', 'C23179', 'zudo-pd:R0603', False, (228.6, 190.5)),
    'D9': ('BZT52C18-7-F_C192739', 'BZT52C18-7-F', 'C192739', 'zudo-pd:SOD-123_L2.8-W1.8-LS3.7-RD', False, (266.7, 165.1)),
    'JOUT1': ('PZ254V-11-06P', '2.54mm 1x6 male', 'C492405', 'zudo-pd:HDR-TH_6P-P2.54-V-M', False, (317.5, 88.9)),
    'J2': ('Conn_1x04', 'PogoPad_1x4_NVM_I2C', '', 'zudo-pd:PogoPad_1x04_P2.54mm', False, (317.5, 139.7)),
    'J3': ('Conn_1x08', 'PogoPad_1x8_Debug', '', 'zudo-pd:PogoPad_1x08_P2.54mm', False, (317.5, 190.5)),
}

NETS = {
    'VBUS_IN': ['J1.2', 'J1.5', 'C1.2', 'R29.1', 'R14.1', 'R11.2', 'Q1.2', 'J3.4', 'D5.1', 'C35.2'],
    'CC1': ['J1.3', 'U1.2', 'R17.1', 'R19.2', 'D6.1'],
    'CC2': ['J1.4', 'U1.4', 'R18.1', 'R20.2', 'D7.1'],
    'CC1DB': ['U1.1', 'R19.1', 'J3.1'],
    'CC2DB': ['U1.5', 'R20.1', 'J3.2'],
    'VBUS_VS_DISCH': ['U1.18', 'R14.2'],
    'VBEN': ['U1.16', 'R12.1', 'J3.8'],
    'Q1_G': ['Q1.1', 'R11.1', 'R12.2', 'C35.1'],
    'VBUS_OUT': ['Q1.3', 'R13.1', 'JOUT1.1', 'JOUT1.2'],
    'DISCH': ['U1.9', 'R13.2'],
    'VREG_2V7': ['U1.23', 'C30.2', 'J3.3'],
    'VREG_1V2': ['U1.21', 'C34.1'],
    'VDD_MID': ['R29.2', 'R30.1'],
    'VDD_LOC': ['U1.24', 'C2.2', 'R30.2', 'D9.1'],
    'SCL': ['U1.7', 'J2.1', 'R22.1'],
    'SDA': ['U1.8', 'J2.2', 'R23.1'],
    'RESET': ['U1.6', 'R21.1'],
    'ATT': ['U1.11', 'J3.6', 'JOUT1.3'],
    'PDOK': ['U1.20', 'J3.7', 'JOUT1.4'],
    'GND': ['U1.10', 'U1.12', 'U1.13', 'U1.22', 'U1.25', 'J1.1', 'J1.6', 'J1.0', 'C1.1', 'C2.1', 'C30.1', 'C34.2', 'R21.2', 'R17.2', 'R18.2', 'J2.3', 'J3.5', 'D5.2', 'D6.2', 'D7.2', 'JOUT1.5', 'JOUT1.6', 'R22.2', 'R23.2', 'D9.2'],
}

NO_CONNECT = ['U1.3', 'U1.14', 'U1.15', 'U1.17', 'U1.19', 'J2.4']

LABEL_OVERRIDES = {'Q1': {'Reference': (256.54, 43.18), 'Value': (256.54, 58.419999999999995)}}
