"""LED Board P r-next DRAFT (UNADOPTED): common STUSB4500 block + LED voltage window.

Not validated. Schematic only: no PCB, no footprint review, no NVM written.

Sources
- Common block: zudo-pd scripts/schgen/board_p_r3_spec.py @3ac13d46 (read-only copy in
  inputs/board_p_r3_spec-3ac13d4.py.txt) and manager common-controller-block.md. Every
  r3 ref, value and net below is copied unchanged, except that JOUT1.1/.2 move from
  VBUS_OUT to LED_OUT behind the window.
- Window: ../board-p-stusb-window-subcircuit (V196 TPS3701 + TPS259474L window,
  RMH2 187 k / option O3) with refs renumbered (U4, U5, C40-C42, R30-R39).

Integration changes against the standalone window sub-circuit
- QINH, RG, RB and RBE are dropped. VBUS_EN_SNK already drives Q1 through R12, and
  the window senses VBUS_OUT after Q1, so the contract gate is Q1 itself. Keeping RG
  from the VBEN node to the window input (VBUS_OUT) would be harmful: with VBEN released
  and VBUS_OUT near 0 V, VBUS_P-R11-R12-RG carries about 49 uA and pulls Q1's VGS to
  about -7 V, turning Q1 on. RG to VBUS_P would be harmless but only duplicate Q1.
- The SMAJ20A input TVS is dropped. Input surge is handled by the common block's
  TVS2200 + LM74700 + TPS16630 front end (PD gate L7). U4 IN (28 V abs max) and U5 VDD
  sit on VBUS_OUT, which follows the protected node VBUS_P through Q1, so they share
  the STUSB4500 VDD L7 status (OPEN in the PD worker's analysis).
- Footprints of U3 (LM74700), D5 (TVS2200) and D8 (BZT52C11) use drafted manufacturer
  example lands (footprints/rnext-mfr.pretty, tools/draft_lands.py) because the zudo-pd lands
  differ from the TI/Diodes drawings (checks/land-check.json). Values, LCSC codes and nets
  stay identical to r3; this is fed back to the PD worker as a common-block land finding.
- LED per-product population: J3 (debug access, no orderable part) uses a 2 x 4 bare test-pad
  array at 1.5 mm pitch (rnext-mfr:TestPadArray_2x4_P1.5_D1.0_J3) instead of the 1 x 8 2.54 mm
  edge-clip pogo row. Same eight nets and pin numbers; J2 (NVM I2C edge-clip row) is unchanged
  so the programming jig contact pattern stays the same.

Per-product parameter pair (PDO2 current and U4 current limit move together)
- OPTION 'I1A5' (default, pending user): NVM I_SNK_PDO2 = 0101b (1.50 A); RILM 3.32 k,
  TI SLVSFC9C tabulated point 0.850-1.150 A at exactly 3.32 k.
- OPTION 'I3A' (alternative): NVM I_SNK_PDO2 = 1011b (3.00 A); RILM 1.27 k (V196 value,
  between TI tabulated points; nominal about 2.6 A, so U4 trips before 3 A).
"""

PROJECT_NAME = 'board-p-rnext'
OUT = 'candidates/board-p-rnext-stusb-unadopted/board-p-rnext.kicad_sch'
LIB_PATH = 'candidates/board-p-rnext-stusb-unadopted/libraries/rnext.kicad_sym'
PAPER = 'A2'

OPTION = 'I1A5'
OPTIONS = {
    'I1A5': {'nvm_i_snk_pdo2': '0101b (1.50 A)',
             'RILM': ('R_CANDIDATE', '3.32k 1% / 0603WAF3321T5E (LCSC unverified)', '',
                      'zudo-led-lamp:R0603')},
    'I3A': {'nvm_i_snk_pdo2': '1011b (3.00 A)',
            'RILM': ('R_CANDIDATE', '1.27k 1% / RC0603FR-071K27L', 'C245930', 'zudo-led-lamp:R0603')},
}

# Common NVM image for this product (text only; nothing programmed). Common block 6.2.
NVM_IMAGE = {
    'SNK_PDO_NUMB': '10b (2 PDOs)',
    'V_SNK_PDO2': '300 (15.00 V)',
    'I_SNK_PDO2': OPTIONS[OPTION]['nvm_i_snk_pdo2'],
    'POWER_ONLY_ABOVE_5V': '1b',
    'POWER_OK_CFG': '10b (unchanged)',
}

_rilm = OPTIONS[OPTION]['RILM']

COMPONENTS = {
    # ---- common block, copied from board_p_r3_spec.py @3ac13d46 (footprints keep the zudo-pd names) ----
    'J1': ('TYPE-C-31-M-17', 'TYPE-C-31-M-17', 'C283540', 'zudo-pd:USB-C-SMD_10P-P1.00-L6.8-W8.9', False, (63.5, 88.9)),
    'U1': ('STUSB4500QTR', 'STUSB4500QTR', 'C2678061', 'zudo-pd:QFN-24_L4.0-W4.0-P0.50-BL-EP2.8', False, (152.4, 88.9)),
    'Q1': ('DMP3036SFG-7', 'DMP3036SFG-7', 'C461081', 'zudo-pd:PowerDI3333-8_DMP3036SFG', False, (241.3, 50.8)),
    'D5': ('TVS2200DRVR', 'TVS2200DRVR', 'C523793', 'rnext-mfr:WSON-6_DRV0006A_TI-EXAMPLE', False, (203.2, 38.1)),
    'U2': ('TPS16630PWPR', 'TPS16630PWPR', 'C1849461', 'zudo-pd:HTSSOP-20_PWP0020T_P0.65_EP2.96_TI-DRAFT', False, (114.3, 38.1)),
    'U3': ('LM74700QDBVRQ1', 'LM74700QDBVRQ1', 'C2941042', 'rnext-mfr:SOT-23-6_DBV0006A_TI-EXAMPLE', False, (241.3, 266.7)),
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
    'D8': ('BZT52C11-7-F_C92321', 'BZT52C11-7-F', 'C92321', 'rnext-mfr:SOD-123_DIODES-SUGGESTED', False, (279.4, 76.2)),
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
    'JOUT1': ('PZ254V-11-06P', '2.54mm 1x6 male', 'C492405', 'zudo-led-lamp:HDR-TH_6P-P2.54-V-M', False, (317.5, 88.9)),
    'J2': ('Conn_1x04', 'PogoPad_1x4_NVM_I2C', '', 'zudo-pd:PogoPad_1x04_P2.54mm', False, (317.5, 139.7)),
    'J3': ('Conn_1x08', 'TestPad_2x4_Debug', '', 'rnext-mfr:TestPadArray_2x4_P1.5_D1.0_J3', False, (317.5, 190.5)),
    # ---- LED voltage window (../board-p-stusb-window-subcircuit, renumbered) ----
    'U4': ('TPS259474LRPWR', 'TPS259474LRPWR', 'C2864845', 'husb-candidate:TPS259474_RPW0010A_TI_EXAMPLE', False, (419.1, 63.5)),
    'U5': ('TPS3701DDCT', 'TPS3701DDCT', 'C132027', 'monitor-candidate:TPS3701_DDC0006A_DRAFT', False, (419.1, 139.7)),
    'C40': ('CL31B475KBHNNNE', '4.7uF/50V 1206', 'C51205', 'cout-candidate:COUT_CL31B475KBHNNNE_1206_TRIAL', False, (508.0, 50.8)),
    'C41': ('C_CANDIDATE', '22nF C0G / GRM21B5C1H223JA01L', 'C77069', 'husb-candidate:GRM21B5C1H223JA01L_MURATA_REFLOW', False, (533.4, 76.2)),
    'C42': ('CC0603KRX7R9BB104', '100nF/50V', 'C14663', 'zudo-led-lamp:C0603', False, (508.0, 101.6)),
    'R30': ('0603WAF1000T5E', '100R', 'C22775', 'zudo-led-lamp:R0603', False, (508.0, 127.0)),
    'R31': ('R_CANDIDATE', '97.6k 0.1% / RT0603BRD0797K6L', 'C861608', 'zudo-led-lamp:R0603', False, (533.4, 127.0)),
    'R32': ('RT0603BRD0710KL', '10k 0.1%', 'C95204', 'zudo-led-lamp:R0603', False, (508.0, 152.4)),
    'R33': ('R_CANDIDATE', '133k 0.1% / RT0603BRD07133KL', 'C861111', 'zudo-led-lamp:R0603', False, (533.4, 177.8)),
    'R34': ('RT0603BRD0710KL', '10k 0.1%', 'C95204', 'zudo-led-lamp:R0603', False, (508.0, 177.8)),
    'R35': ('R_CANDIDATE', '133k 0.1% / RT0603BRD07133KL', 'C861111', 'zudo-led-lamp:R0603', False, (533.4, 228.6)),
    'R36': ('R_CANDIDATE', '187k 0.1% / RT0603BRD07187KL (LCSC unverified)', '', 'zudo-led-lamp:R0603', False, (533.4, 254.0)),
    'R37': ('RT0603BRD0710KL', '10k 0.1%', 'C95204', 'zudo-led-lamp:R0603', False, (508.0, 203.2)),
    'R38': (_rilm[0], _rilm[1], _rilm[2], _rilm[3], False, (533.4, 203.2)),
    # ---- ERC power flags (KiCad stock PWR_FLAG; virtual, not exported): Q1 drain drives VBUS_OUT,
    # the ground plane drives GND. Without them ERC reports U4 IN/GND power_pin_not_driven.
    '#FLG01': ('PWR_FLAG', 'PWR_FLAG', '', '', False, (469.9, 30.48)),
    '#FLG02': ('PWR_FLAG', 'PWR_FLAG', '', '', False, (495.3, 30.48)),
    'R39': ('R_CANDIDATE', '2.2k 1210 / 1210W2F2201T5E', 'C422361', 'husb-candidate:RBLEED_1210W2F2201T5E', False, (533.4, 279.4)),
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
    'VBUS_OUT': ['Q1.5', 'Q1.6', 'Q1.7', 'Q1.8', 'Q1.9', 'R13.1', 'C36.2',
                 'U4.5', 'U5.5', 'C42.1', 'R31.1', 'R33.1', 'R35.1', '#FLG02.1'],
    'DISCH': ['U1.9', 'R13.2'],
    'VREG_2V7': ['U1.23', 'C30.2', 'J3.3'],
    'VREG_1V2': ['U1.21', 'C34.1'],
    'SCL': ['U1.7', 'J2.1'],
    'SDA': ['U1.8', 'J2.2'],
    'RESET': ['U1.6', 'R21.1'],
    'ATT': ['U1.11', 'J3.6', 'JOUT1.3'],
    'PDOK': ['U1.20', 'J3.7', 'JOUT1.4'],
    'WIN_EN_UVLO': ['U4.1', 'R31.2', 'R32.1', 'U5.1'],
    'WIN_OVLO': ['U4.2', 'R33.2', 'R34.1'],
    'WIN_MON_SERIES': ['R35.2', 'R36.1'],
    'WIN_MON_SENSE': ['R36.2', 'R37.1', 'U5.3'],
    'WIN_DVDT': ['U4.7', 'R30.1'],
    'WIN_DVDT_CAP': ['R30.2', 'C41.1'],
    'WIN_ILM': ['U4.9', 'R38.1'],
    'LED_OUT': ['U4.6', 'C40.1', 'R39.1', 'JOUT1.1', 'JOUT1.2'],
    'GND': ['U1.10', 'U1.12', 'U1.13', 'U1.22', 'U1.25', 'J1.1', 'J1.6', 'J1.0', 'C1.1', 'C2.1', 'C30.1', 'C34.2', 'R21.2', 'R17.2', 'R18.2', 'J2.3', 'J3.5', 'D5.1', 'D5.2', 'D5.3', 'D5.7', 'U2.9', 'U2.21', 'U3.2', 'R23.2', 'R25.2', 'R26.2', 'C5.2', 'C3.2', 'D6.2', 'D7.2', 'JOUT1.5', 'JOUT1.6',
            'U4.8', 'U4.4', 'U5.2', 'U5.4', 'R32.2', 'R34.2', 'R37.2', 'R38.2', 'C42.2', 'C40.2', 'C41.2', 'R39.2', '#FLG01.1'],
}

NO_CONNECT = ['U1.3', 'U1.14', 'U1.15', 'U1.17', 'U1.19',
              'U2.4', 'U2.5', 'U2.12', 'U2.13', 'U2.14', 'U2.15', 'U2.16', 'U2.17',
              'J2.4',
              'U4.3', 'U4.10', 'U5.6']

LABEL_OVERRIDES = {'Q1': {'Reference': (256.54, 43.18), 'Value': (256.54, 58.419999999999995)}}
