#!/usr/bin/env python3
"""
LM2586SX-ADJ Flyback Converter: +15V → -15V
Complete circuit with transparent background, black foreground, Arial font
"""

import os
import schemdraw
from schemdraw import elements as elm

with schemdraw.Drawing(
    font='Arial',
    fontsize=11,
    color='black',
    transparent=True
) as d:
    d.config(unit=3)

    # Starting position for +15V input
    vin_start = (0, 0)

    # +15V Input label (open dot on left)
    elm.Dot(open=True).at(vin_start).label('+15V IN', loc='left', fontsize=14, ofst=0.3)

    # Main +15V rail going right
    elm.Line().right(2.0)
    vin_rail = d.here
    d.push()

    # C13 bulk capacitor (100µF) from +15V to GND
    elm.Line().down(0.5)
    elm.Dot()
    d.push()
    elm.Capacitor().down(1.5).label('C13\n100µF', loc='right', ofst=0.2)
    elm.Ground()

    # C16 ceramic decoupling (100nF) next to C13
    d.pop()
    elm.Line().right(1.0)
    elm.Dot()
    elm.Capacitor().down(1.5).label('C16\n100nF', loc='right', ofst=0.2)
    elm.Ground()

    # Continue +15V rail to VIN pin and to transformer primary
    d.pop()
    elm.Line().at(vin_rail).right(2.5)
    vin_to_ic = d.here
    d.push()

    # LM2586SX-ADJ IC (TO-263-7 package)
    # U5 - Flyback converter
    ic = (elm.Ic(
        pins=[
            # Left side (top to bottom)
            elm.IcPin(name='VIN', pin='7', side='left', slot='1/4'),
            elm.IcPin(name='COMP', pin='2', side='left', slot='2/4'),
            elm.IcPin(name='Freq.Sync.', pin='6', side='left', slot='3/4'),
            elm.IcPin(name='GND', pin='4', side='left', slot='4/4'),
            # Right side (top to bottom)
            elm.IcPin(name='SW', pin='5', side='right', slot='1/4'),
            elm.IcPin(name='Freq.Adj.', pin='1', side='right', slot='2/4'),
            elm.IcPin(name='FB', pin='3', side='right', slot='3/4'),
        ],
        edgepadW=5.0,
        edgepadH=1.2,
        pinspacing=0.8,
        leadlen=1.0,
        pinlblsize=12
    ).at((vin_to_ic[0] + 2.0, vin_to_ic[1] - 3.5))
     .label('U5\nLM2586SX-ADJ', loc='center', fontsize=14)
    )

    # VIN connection from +15V rail to IC (VIN now on left side)
    elm.Line().at(vin_to_ic).to(ic.VIN)

    # GND connection (GND now on left side bottom)
    elm.Line().at(ic.GND).left(0.5)
    elm.Line().down(0.8)
    elm.Ground()

    # Compensation network (COMP pin): R9 + C15 to GND
    elm.Line().at(ic.COMP).left(0.8)
    elm.Dot()
    comp_junction = d.here
    d.push()

    elm.Resistor().down(1.5).label('R9\n3kΩ', loc='bot', ofst=0.2)
    elm.Dot()
    r9_bottom = d.here
    d.push()
    elm.Ground()

    # C15 parallel to R9
    d.pop()
    elm.Line().right(1.2)
    elm.Dot()
    elm.Capacitor().up(1.5).label('C15\n47nF', loc='bot', ofst=0.2)
    elm.Line().to(comp_junction)

    # Freq.Sync pin - not connected (show as open)
    # (No connection drawn)

    # Freq.Adj pin - floating (always ON)
    # (No connection drawn)

    # SW pin connection to transformer primary
    elm.Line().at(ic.SW).right(1.5)
    sw_junction = d.here
    d.push()

    # Continue +15V rail to top for transformer primary
    d.pop()
    elm.Line().at(vin_to_ic).up(4.0)
    vin_top_rail = d.here
    elm.Line().right(5.5)
    primary_top = d.here

    # T1 Flyback Transformer (coupled inductor)
    # Primary winding (left coil)
    elm.Line().at(primary_top).down(0.3)
    primary_start = d.here
    elm.Inductor2(loops=3).down(1.8).label('T1', loc='top', fontsize=13, ofst=(1.0, 0))
    primary_end = d.here
    elm.Line().down(0.3)
    elm.Dot()

    # Connect primary bottom to SW pin
    elm.Line().left(primary_end[0] - sw_junction[0])

    # Secondary winding (right coil, next to primary)
    # Start from top (GND connection)
    elm.Line().at((primary_top[0] + 1.2, primary_top[1])).down(0.3)
    secondary_start = d.here
    elm.Inductor2(loops=3).down(1.8)
    secondary_end = d.here
    elm.Line().down(0.3)
    elm.Dot()
    secondary_junction = d.here

    # GND connection for secondary top
    elm.Line().at((primary_top[0] + 1.2, primary_top[1])).up(0.5)
    elm.Ground(lead=False)

    # D4 Schottky diode from secondary to output
    elm.Line().at(secondary_junction).right(1.5)
    elm.Diode(fill='white').right().label('D4\nSS34', loc='top', ofst=0.2)
    elm.Dot()
    output_rail = d.here
    d.push()

    # C14 output filter capacitor
    elm.Capacitor().down(2.5).label('C14\n100µF', loc='right', ofst=0.2)
    elm.Ground()

    # -15V output
    d.pop()
    elm.Line().right(1.5)
    elm.Dot(open=True).label('-15V OUT', loc='right', fontsize=14, ofst=0.3)

    # Feedback network: R7 and R8 voltage divider
    # Connect from output to FB pin
    fb_tap = d.here
    elm.Line().at(output_rail).down(0.8)
    elm.Dot()
    fb_top = d.here

    elm.Resistor().down(1.5).label('R7\n10kΩ', loc='right', ofst=0.2)
    elm.Dot()
    fb_middle = d.here
    d.push()

    # Connect FB tap to IC FB pin (FB now on right side)
    elm.Line().left(fb_middle[0] - ic.FB[0] + 0.5)
    elm.Dot()
    elm.Line().up(fb_middle[1] - ic.FB[1])
    elm.Line().to(ic.FB)

    # R8 to GND
    d.pop()
    elm.Resistor().down(1.5).label('R8\n910Ω', loc='right', ofst=0.2)
    elm.Ground()

    # Save to doc/static/circuits/
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, '../doc/static/circuits/inverter-u5-diagram.svg')
    d.save(output_path)

print("✓ LM2586 flyback converter diagram generated with transparent background")
