"""ST-LINK/V2 20-pin to Board L 1x5 SWD adapter schematic specification.

Both connectors are deliberately hand-fit/DNP. VAPP is target-voltage sense:
the adapter never connects the ST-LINK/V2 3.3 V output on pin 19.
"""

PROJECT_NAME = 'swd-adapter'
OUT = 'boards/swd-adapter/swd-adapter.kicad_sch'
PAPER = 'A4'

COMPONENTS = {
    'J1': (
        'DS254P-2X10-L0',
        'ST-LINK/V2 20-pin (hand-fit)',
        'C4749199',
        'zudo-led-lamp:IDC-TH_20P-P2.54-V-R2-C10-S2.54',
        True,
        (76.2, 76.2),
    ),
    'J2': (
        'PZ254V-11-05P',
        'Board L SWD 1x5 (hand-fit)',
        'C492404',
        'zudo-led-lamp:HDR-TH_5P-P2.54-V-M',
        True,
        (127.0, 76.2),
    ),
}

NETS = {
    'SWDIO': ['J1.7', 'J2.1'],
    'SWCLK': ['J1.9', 'J2.2'],
    'NRST': ['J1.15', 'J2.3'],
    'VAPP': ['J1.1', 'J1.2', 'J2.4'],
    'GND': [
        'J1.3', 'J1.4', 'J1.5', 'J1.6', 'J1.8', 'J1.10',
        'J1.12', 'J1.14', 'J1.16', 'J1.18', 'J1.20', 'J2.5',
    ],
}

# SWO and the debugger's 3.3 V output are intentionally not forwarded.
NO_CONNECT = ['J1.11', 'J1.13', 'J1.17', 'J1.19']
