#!/usr/bin/env python3
"""
USB-PD Power Section: J1 USB-C Connector
Complete circuit with transparent background, black foreground, Arial font
"""

import schemdraw
from schemdraw import elements as elm

with schemdraw.Drawing(
    font='Arial',         # Sans-serif font
    fontsize=11,
    color='black',        # Foreground: black
    transparent=True      # Transparent background
) as d:
    d.config(unit=3)

    # J1 USB-C Connector (6-pin power-only) - Flipped order (top to bottom)
    # Height matched to U1: (6-1)*1.0 + 2*3.5 = 12 units (same as U1's 11 pins)
    j1 = elm.Ic(
        pins=[
            elm.IcPin(name='GND2', pin='6', side='right', slot='1/6'),
            elm.IcPin(name='GND1', pin='5', side='right', slot='2/6'),
            elm.IcPin(name='CC2', pin='4', side='right', slot='3/6'),
            elm.IcPin(name='CC1', pin='3', side='right', slot='4/6'),
            elm.IcPin(name='VBUS2', pin='2', side='right', slot='5/6'),
            elm.IcPin(name='VBUS1', pin='1', side='right', slot='6/6'),
        ],
        size=(3, 12),  # Explicit size: width=2, height=12
        leadlen=1.0
    ).label('J1\nUSB-C', loc='center', fontsize=10, ofst=(-0.5, 0.5))

    # U1 CH224D IC (QFN-20) - USB PD Sink Controller
    # Left side pins aligned with J1 matching pins
    u1 = elm.Ic(
        pins=[
            # Left side pins - aligned by function with J1
            elm.IcPin(name='GND', pin='0', side='left', slot='1/6'),    # Aligned with J1 GND2
            elm.IcPin(name='CC2', pin='10', side='left', slot='3/6'),   # Aligned with J1 CC2
            elm.IcPin(name='CC1', pin='11', side='left', slot='4/6'),   # Aligned with J1 CC1
            elm.IcPin(name='VBUS', pin='2', side='left', slot='6/6'),   # Aligned with J1 VBUS1
            # Right side pins (top to bottom)
            elm.IcPin(name='GATE', pin='5', side='right', slot='1/11'),
            elm.IcPin(name='NMOS#', pin='6', side='right', slot='2/11'),
            elm.IcPin(name='ISP', pin='14', side='right', slot='3/11'),
            elm.IcPin(name='ISN', pin='15', side='right', slot='4/11'),
            elm.IcPin(name='DRV', pin='1', side='right', slot='5/11'),
            elm.IcPin(name='CFG1', pin='19', side='right', slot='6/11'),
            elm.IcPin(name='CFG2', pin='13', side='right', slot='7/11'),
            elm.IcPin(name='CFG3', pin='12', side='right', slot='8/11'),
            elm.IcPin(name='PG', pin='3', side='right', slot='9/11'),
            elm.IcPin(name='DP', pin='8', side='right', slot='10/11'),
            elm.IcPin(name='DM', pin='9', side='right', slot='11/11'),
        ],
        size=(8, 12),  # Explicit size to match J1 height
        leadlen=1.0
    ).anchor('center').at((j1.VBUS1[0] + 13.0, j1.center[1])).label('U1\nCH224D', loc='center', fontsize=10)

    # VBUS connection: J1 VBUS1 - dot - dot - dot - dot - U1 VBUS
    elm.Dot().at(j1.VBUS1)  # First dot at J1 VBUS1
    elm.Line().right(2.0)
    elm.Dot()  # Second dot
    elm.Line().right(2.0)
    elm.Dot()  # Third dot
    elm.Line().right(2.0)
    elm.Dot()  # Fourth dot
    elm.Line().to(u1.VBUS)  # Connect to U1 VBUS

    # Connect J1 VBUS2 to the first dot
    elm.Line().at(j1.VBUS2).to(j1.VBUS1)

    # Save to doc/static/circuits/
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, '../doc/static/circuits/diagram1-usb-pd.svg')
    d.save(output_path)

print("✓ USB-PD power section diagram generated with transparent background")
