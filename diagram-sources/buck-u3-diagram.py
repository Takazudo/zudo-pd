#!/usr/bin/env python3
"""
LM2596S-ADJ Buck Converter: +15V → +7.5V
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
    ).label('U3\nLM2596S', loc='center', fontsize=10)

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

    # Connect junction3 to VIN
    elm.Line().at(junction3).to(ic.VIN)

    # Connect ON pin to GND (enable regulator)
    elm.Line().at(ic.ON).left(1.0)
    elm.Line().down(1.0)
    elm.Ground()

    # C8 from junction2 (closer to IC - high-freq decoupling)
    d.pop()
    elm.Capacitor().down(2.0).label('C8\n100nF', loc='bot')
    elm.Ground()

    # C7 from junction1 (farther from IC - bulk filtering, electrolytic)
    d.pop()
    elm.Capacitor(polar=True).down(2.0).label('C7\n100µF', loc='bot')
    elm.Ground()

    # Output stage from VOUT pin
    elm.Line().at(ic.VOUT).right(0.5)
    elm.Dot()
    d.push()

    elm.Inductor().right(2.5).label('L2\n100µH\n4.5A', loc='top',ofst=0.2)
    elm.Dot()
    output_junction = d.here
    d.push()

    elm.Line().right(1.0)  # Half distance to center
    elm.Dot()  # Junction for feedback network
    feedback_junction = d.here
    d.push()

    elm.Line().right(1.0)  # Remaining half to +7.5V
    elm.Dot(open=True).label('+7.5V', loc='right')

    # Return from feedback_junction to add voltage divider
    d.pop()

    # Feedback voltage divider network (R3 || C32 in parallel, then R4)
    elm.Line().up(4)
    elm.Dot()
    d.push()  # Save position before R3 for parallel C32 capacitor

    elm.Resistor(scale=0.7).left().label('R3\n5.1kΩ', loc='bot', ofst=0.5)
    r3_end = d.here
    d.push()  # Save position after R3 (this is the Tap)

    elm.Dot()  # Tap junction for FB connection
    d.push()  # Save tap position for FB connection

    elm.Resistor(scale=0.7).left().label('R4\n1kΩ', loc='bot', ofst=0.5)
    elm.Line().left(0.2)
    elm.Line().down(0.2)
    elm.Ground()

    # Connect tap junction to FB pin
    d.pop()
    elm.Line().to(ic.FB)

    # C32 capacitor in parallel with R3 (feedback compensation)
    d.pop()  # Return to r3_end (after R3)
    d.pop()  # Return to r3_start (the dot junction)
    elm.Line().up(2)
    elm.Capacitor().left().label('C32\n22nF', loc='top', ofst=0.3)
    elm.Line().to(r3_end)

    # Output capacitor C4 (from output junction - right side, facing up, electrolytic)
    d.pop()
    elm.Capacitor(polar=True).down(2.0).label('C4\n470µF\n16V', loc='bot', ofst=0.5)
    elm.Ground()

    # Flyback diode D2 (from switching node - left side, facing up)
    d.pop()
    elm.Diode().down(2.0).reverse().label('D2\nSS34', loc='top')
    elm.Ground()

    # Save to doc/static/circuits/ (one level up from diagram-sources)
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, '../doc/static/circuits/buck-u3-diagram.svg')
    d.save(output_path)

print("✓ Buck converter diagram generated with transparent background")
