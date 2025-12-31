#!/usr/bin/env python3
"""
LM2596S-ADJ Buck Converter: +15V → +13.5V
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

    # Just the IC (VOUT and FB positions swapped)
    ic = elm.Ic(
        pins=[
            elm.IcPin(name='GND', pin='3', side='left', slot='1/3'),
            elm.IcPin(name='ON', pin='5', side='left', slot='2/3'),
            elm.IcPin(name='VIN', pin='1', side='left', slot='3/3'),
            elm.IcPin(name='VOUT', pin='2', side='right', slot='1/2'),  # Swapped: was 2/2
            elm.IcPin(name='FB', pin='4', side='right', slot='2/2'),    # Swapped: was 1/2
        ],
        edgepadW=2.5,
        edgepadH=0.8,
        pinspacing=1.0,
        leadlen=1.0
    ).label('U2\nLM2596S', loc='center', fontsize=10)

    # GND connection
    elm.Line().at(ic.GND).down(1.0)
    elm.Ground()

    # Y position at VIN pin level (not connected to ON)
    junction_y = ic.VIN[1]

    # Input rail: straight horizontal line at VIN level
    # +15V -> dot -> dot -> junction3
    elm.Dot(open=True).at((ic.VIN[0] - 5.5, junction_y)).label('+15V', loc='left')

    elm.Line().right(0.5)
    elm.Dot()
    junction1 = d.here
    d.push()

    elm.Line().right(2.0)
    elm.Dot()
    junction2 = d.here
    d.push()

    elm.Line().right(2.0)
    junction3 = d.here

    # Connect junction3 to VIN only (ON pin left floating)
    elm.Line().at(junction3).to(ic.VIN)

    # Connect ON pin to GND (enable regulator)
    elm.Line().at(ic.ON).left(1.0)
    elm.Line().down(1.0)
    elm.Ground()

    # C6 from junction2 (closer to IC - high-freq decoupling)
    d.pop()
    elm.Capacitor().down(2.0).label('C6\n100nF', loc='bot')
    elm.Ground()

    # C5 from junction1 (farther from IC - bulk filtering)
    d.pop()
    elm.Capacitor().down(2.0).label('C5\n100µF', loc='bot')
    elm.Ground()

    # Output stage from VOUT pin (halved spacing)
    elm.Line().at(ic.VOUT).right(0.5)  # Halved spacing before L1
    elm.Dot()
    vout_junction = d.here
    d.push()

    elm.Inductor().right(2.5).label('L1\n100µH\n4.5A', loc='top',ofst=0.2)
    elm.Dot()
    output_junction = d.here
    d.push()

    elm.Line().right(1.0)  # Half distance to center
    elm.Dot()  # Junction for feedback network
    feedback_junction = d.here
    d.push()

    elm.Line().right(1.0)  # Remaining half to +13.5V
    elm.Dot(open=True).label('+13.5V', loc='right')

    # Return from feedback_junction to add voltage divider
    d.pop()

    # Feedback voltage divider network (R1 || C4 in parallel, then R2)
    elm.Line().up(4)
    elm.Dot()
    d.push()  # Save position before R1 for parallel C4 capacitor

    elm.Resistor(scale=0.7).left().label('R1\n10kΩ', loc='bot', ofst=0.5)
    r1_end = d.here
    d.push()  # Save position after R1 (this is the Tap)

    elm.Dot()  # Tap junction for FB connection
    d.push()  # Save tap position for FB connection

    elm.Resistor(scale=0.7).left().label('R2\n1kΩ', loc='bot', ofst=0.5)
    elm.Line().left(0.2)
    elm.Line().down(0.2)
    elm.Ground()

    # Connect tap junction to FB pin
    d.pop()
    elm.Line().to(ic.FB)

    # C4 capacitor in parallel with R1 (feedback compensation)
    d.pop()  # Return to r1_end (after R1)
    d.pop()  # Return to r1_start (the dot junction)
    elm.Line().up(2)
    elm.Capacitor().left().label('C4\n22nF', loc='top', ofst=0.3)
    elm.Line().to(r1_end)

    # Output capacitor C3 (from output junction - right side, facing up)
    d.pop()
    elm.Capacitor().down(2.0).label('C3\n470µF\n25V', loc='bot', ofst=0.5)
    elm.Ground()

    # Flyback diode D1 (from switching node - left side, facing up)
    d.pop()
    elm.Diode().down(2.0).reverse().label('D1\nSS34', loc='top')
    elm.Ground()

    # Save to doc/static/circuits/ (one level up from diagram-sources)
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, '../doc/static/circuits/buck-u2-diagram.svg')
    d.save(output_path)

print("✓ Buck converter diagram generated with transparent background")
