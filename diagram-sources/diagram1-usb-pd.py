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

    # J1 USB-C Connector (6-pin power-only) - Flipped order with spacing (top to bottom)
    # Height matched to U1: 12 units, using /14 slots for maximum spacing between CC2 and GND
    j1 = elm.Ic(
        pins=[
            elm.IcPin(name='GND2', pin='6', side='right', slot='1/15'),
            elm.IcPin(name='GND1', pin='5', side='right', slot='2/15'),
            elm.IcPin(name='CC2', pin='4', side='right', slot='8/15'),  # Increased gap: 2->7 (5 slots)
            elm.IcPin(name='CC1', pin='3', side='right', slot='9/15'),
            elm.IcPin(name='VBUS2', pin='2', side='right', slot='14/15'),
            elm.IcPin(name='VBUS1', pin='1', side='right', slot='15/15'),
        ],
        size=(3, 12),  # Explicit size: width=2, height=12
        leadlen=1.0
    ).label('J1\nUSB-C', loc='center', fontsize=14, ofst=(-0.5, 1))

    # U1 CH224D IC (QFN-20) - USB PD Sink Controller
    # Left side pins aligned with J1 matching pins
    u1 = elm.Ic(
        pins=[
            # Left side pins - aligned by function with J1 (using /14 slots to match J1)
            elm.IcPin(name='GND', pin='0', side='left', slot='2/15'),    # Aligned with J1 GND1
            elm.IcPin(name='CC2', pin='10', side='left', slot='8/15'),   # Aligned with J1 CC2
            elm.IcPin(name='CC1', pin='11', side='left', slot='9/15'),   # Aligned with J1 CC1
            elm.IcPin(name='VBUS', pin='2', side='left', slot='15/15'),  # Aligned with J1 VBUS1
            # Right side pins (top to bottom) - PG moved below DM
            elm.IcPin(name='GATE', pin='5', side='right', slot='12/12'),
            elm.IcPin(name='NMOS#', pin='6', side='right', slot='11/12'),
            elm.IcPin(name='ISP', pin='14', side='right', slot='10/12'),
            elm.IcPin(name='ISN', pin='15', side='right', slot='9/12'),
            elm.IcPin(name='DRV', pin='1', side='right', slot='8/12'),
            elm.IcPin(name='CFG1', pin='19', side='right', slot='7/12'),
            elm.IcPin(name='CFG2', pin='13', side='right', slot='6/12'),
            elm.IcPin(name='CFG3', pin='12', side='right', slot='5/12'),
            elm.IcPin(name='DP', pin='8', side='right', slot='4/12'),
            elm.IcPin(name='DM', pin='9', side='right', slot='3/12'),
            elm.IcPin(name='PG', pin='3', side='right', slot='2/12'),   # Moved below DM
            elm.IcPin(name='VDD', pin='7', side='right', slot='1/12'),  # Internal regulator output
        ],
        size=(4, 12),  # Explicit size to match J1 height
        leadlen=1.0
    ).anchor('center').at((j1.VBUS1[0] + 10.0, j1.center[1])).label('U1\nCH224D', loc='center', fontsize=14, ofst=(-0.5, 1))

    # VBUS connection: J1 VBUS1 - dot - dot - dot - dot - U1 VBUS
    elm.Dot().at(j1.VBUS1)  # First dot at J1 VBUS1
    elm.Line().right(2.0)
    elm.Dot()  # Second dot
    d.push()
    elm.Line().down(0.1)
    elm.Capacitor().label('C1\n10µF\n50V', loc='bot', ofst=-1.7)
    elm.Ground()
    d.pop()

    elm.Line().right(2.0)
    elm.Dot()  # Third dot
    d.push()
    elm.Line().down(0.1)
    elm.Capacitor().label('C2\n100nF\n50V', loc='bot', ofst=0.2)
    elm.Ground()

    d.pop()
    elm.Line().right(2.0)
    elm.Dot()  # Fourth dot
    d.push()
    elm.Line().up(2.5)
    elm.Dot(open=True).label('OUT\n+5V first\n+15V\nafter init', loc='right', ofst=(0.2, -1.0))

    d.pop()
    elm.Line().to(u1.VBUS)  # Connect to U1 VBUS

    # Connect J1 VBUS2 to the first dot
    elm.Line().at(j1.VBUS2).to(j1.VBUS1)

    # GND connection: J1 GND1 - dot - - - dot - U1 GND
    elm.Dot().at(j1.GND1)  # First dot at J1 GND1
    elm.Line().right(6.0)
    elm.Dot()  # Final dot
    d.push()  # Save position for GND symbol
    elm.Line().to(u1.GND)  # Connect to U1 GND

    # GND symbol from final dot
    d.pop()
    elm.Line().down(1.0)
    elm.Ground()

    # Connect J1 GND2 to the first dot
    elm.Line().at(j1.GND2).to(j1.GND1)

    ## CC1 to CC1
    elm.Line().at(j1.CC1).right(4.0)
    elm.Dot() # to R12
    d.push()  # Save position for U1 CC1 connection
    elm.Line().down(0.4)
    elm.Resistor(scale=0.7).down().label('R12\n5.1kΩ', loc='bot', ofst=0.5)
    elm.Line().down(0.1)
    elm.Ground()

    # Connect dot to U1 CC1
    d.pop()
    elm.Line().to(u1.CC1)

    ## CC2 to CC2
    elm.Line().at(j1.CC2).right(2.0)
    elm.Dot()
    d.push()  # Save position for U1 CC2 connection
    elm.Line().down(0.1)
    elm.Resistor(scale=0.7).down().label('R13\n5.1kΩ', loc='bot', ofst=-2.2)
    elm.Line().down(0.1)
    elm.Ground()  # Removed flip()

    # Connect dot to U1 CC2
    d.pop()
    elm.Line().to(u1.CC2)

    # Connect U1 DM to DP
    elm.Dot().at(u1.DP)
    elm.Line().to(u1.DM)

    # NMOS# pin (pin 6) to GND
    elm.Line().at(getattr(u1, 'NMOS#')).right(1)
    elm.Line().down(0.5)
    elm.Ground()

    elm.Dot().at(u1.ISN)
    d.push()
    elm.Line().to(u1.ISP)

    d.pop()
    elm.Line().right(2)
    elm.Line().down(0.5)
    elm.Ground()

    elm.Dot().at(u1.CFG1)
    d.push()
    elm.Line().to(u1.DRV)

    d.pop()
    elm.Line().right(3.5)
    elm.Resistor(scale=0.7).down().label('R11\n56kΩ', loc='bot', ofst=-2.1)
    elm.Ground()

    # PG pin with LED and R10 to +5V
    elm.Line().at(u1.PG).right(0.1)
    elm.LED().right().reverse().label('D1', loc='bot', ofst=(0, -0.5))
    elm.Resistor(scale=0.7).right().label('R10\n330Ω', loc='top', ofst=0.5)
    elm.Dot(open=True).label('+5V IN', loc='top', ofst=(0, 0.2))

    # VDD pin (pin 7) with 1µF decoupling capacitor
    elm.Line().at(u1.VDD).right(1.0)
    elm.Capacitor().down(2.0).label('C3\n1µF', loc='bot', ofst=0.5)
    elm.Ground()

    # Save to doc/static/circuits/
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, '../doc/static/circuits/diagram1-usb-pd.svg')
    d.save(output_path)

print("✓ USB-PD power section diagram generated with transparent background")
