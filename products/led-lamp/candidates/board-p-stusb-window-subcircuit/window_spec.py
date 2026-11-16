"""LED Board P r-next voltage window: standalone sub-circuit source (UNADOPTED).

Connectivity is the V196 window (candidates/board-p-v196-unadopted, schematic netlist
evidence/rerun-20261031/V196-schematic-netlist.net) with three deliberate changes:
the HUSB238 GATE is replaced by the STUSB4500 VBUS_EN_SNK open drain, RMH2 is 187 k
(V196 option O3), and an input TVS (SMAJ20A) is added on RAW_VBUS.
"""

# ref: (MPN, value, LCSC, role). LCSC codes are the V196 BOM-TRIAL values unless noted.
COMPONENTS = {
    'U2':    ('TPS259474LRPWR', 'eFuse, latch-off', 'C2864845', 'sink switch with UVLO/OVLO/ILM'),
    'UMON':  ('TPS3701DDCT', 'window monitor', 'C132027', 'INA undervoltage reject (INB unused)'),
    'QINH':  ('SMMBT3904LT1G', 'NPN', 'C84555', 'holds EN low while VBUS_EN_SNK is released'),
    'DIN':   ('SMAJ20A', 'TVS 20 V', 'C571370', 'input TVS on RAW_VBUS (V196 open item)'),
    'CMON':  ('CC0603KRX7R9BB104', '100nF/50V', 'C14663', 'UMON VDD decoupling'),
    'COUT':  ('CL31B475KBHNNNE', '4.7uF/50V 1206', 'C51205', 'output bulk'),
    'CSLEW': ('GRM21B5C1H223JA01L', '22nF C0G', 'C77069', 'DVDT slew'),
    'RSLEW': ('0603WAF1000T5E', '100R', 'C22775', 'DVDT series'),
    'RG':    ('RT0603BRD07100KL', '100k 0.1%', 'C122538', 'VBUS_EN_SNK pull-up to RAW_VBUS'),
    'RB':    ('RT0603BRD07100KL', '100k 0.1%', 'C122538', 'QINH base series'),
    'RBE':   ('RC0603FR-071ML', '1M', 'C105578', 'QINH base-emitter'),
    'RUVH':  ('RT0603BRD0797K6L', '97.6k 0.1%', 'C861608', 'EN/UVLO divider top'),
    'RUVL':  ('RT0603BRD0710KL', '10k 0.1%', 'C95204', 'EN/UVLO divider bottom'),
    'ROVH':  ('RT0603BRD07133KL', '133k 0.1%', 'C861111', 'OVLO divider top'),
    'ROVL':  ('RT0603BRD0710KL', '10k 0.1%', 'C95204', 'OVLO divider bottom'),
    'RMH1':  ('RT0603BRD07133KL', '133k 0.1%', 'C861111', 'monitor divider top 1'),
    'RMH2':  ('RT0603BRD07187KL', '187k 0.1%', None, 'monitor divider top 2 (O3; LCSC code not verified)'),
    'RML':   ('RT0603BRD0710KL', '10k 0.1%', 'C95204', 'monitor divider bottom'),
    'RILM':  ('0603WAF3321T5E', '3.32k 1%', None, 'ILM: TI tabulated point 0.850-1.150 A (LED option; LCSC code not verified)'),
    'RBLEED': ('1210W2F2201T5E', '2.2k 1210', 'C422361', 'output bleed'),
}

# Pin numbers for the ICs were checked against the hashed primary documents (see README).
PINS = {
    'U2':   {1: 'EN/UVLO', 2: 'OVLO', 3: 'PG', 4: 'PGTH', 5: 'IN', 6: 'OUT', 7: 'DVDT', 8: 'GND', 9: 'ILM', 10: 'ITIMER'},
    'UMON': {1: 'OUTA', 2: 'GND', 3: 'INA', 4: 'INB', 5: 'VDD', 6: 'OUTB'},
    'QINH': {1: 'B', 2: 'E', 3: 'C'},
    'DIN':  {1: 'K', 2: 'A'},
}

# Off-sheet interface nets (provided by the common STUSB4500 block / JOUT1).
INTERFACE = {
    'RAW_VBUS':        'VBUS after the common block input protection; STUSB4500 VDD side',
    'VBUS_EN_SNK_N':   'STUSB4500 pin 16, active-low HV open drain (released = OFF)',
    'SWITCHED_OUTPUT': 'to JOUT1.1/.2 and, via the STUSB4500 discharge resistor, DISCH (pin 9)',
    'GND':             'common ground; JOUT1.5/.6',
}

NETS = {
    'RAW_VBUS':        ['U2.5', 'UMON.5', 'CMON.1', 'RG.1', 'RUVH.1', 'ROVH.1', 'RMH1.1', 'DIN.1'],
    'VBUS_EN_SNK_N':   ['RG.2', 'RB.1'],
    'INHIBIT_BASE':    ['RB.2', 'RBE.1', 'QINH.1'],
    'EN_UVLO':         ['U2.1', 'RUVH.2', 'RUVL.1', 'QINH.3', 'UMON.1'],
    'OVLO':            ['U2.2', 'ROVH.2', 'ROVL.1'],
    'MON_SERIES':      ['RMH1.2', 'RMH2.1'],
    'MON_SENSE':       ['RMH2.2', 'RML.1', 'UMON.3'],
    'DVDT':            ['U2.7', 'RSLEW.1'],
    'DVDT_CAP':        ['RSLEW.2', 'CSLEW.1'],
    'ILM':             ['U2.9', 'RILM.1'],
    'SWITCHED_OUTPUT': ['U2.6', 'COUT.1', 'RBLEED.1'],
    'GND':             ['U2.8', 'U2.4', 'UMON.2', 'UMON.4', 'QINH.2', 'RBE.2', 'RUVL.2', 'ROVL.2',
                        'RML.2', 'RILM.2', 'CMON.2', 'COUT.2', 'CSLEW.2', 'RBLEED.2', 'DIN.2'],
}

NO_CONNECT = ['U2.3', 'U2.10', 'UMON.6']
