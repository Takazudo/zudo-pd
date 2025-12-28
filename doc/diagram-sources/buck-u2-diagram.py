#!/usr/bin/env python3
"""
LM2596S-ADJ Buck Converter: +15V → +13.5V
Complete circuit with dark theme (black background, white foreground, Arial font)
"""

import schemdraw
from schemdraw import elements as elm

with schemdraw.Drawing(
    font='Arial',         # Sans-serif font
    fontsize=11,
    color='white',        # Foreground: white
    bgcolor='black'       # Background: black
) as d:
    d.config(unit=3)

    # Just the IC (positions unchanged, only pin numbers corrected)
    ic = elm.Ic(
        pins=[
            elm.IcPin(name='GND', pin='3', side='left', slot='1/3'),
            elm.IcPin(name='ON', pin='5', side='left', slot='2/3'),
            elm.IcPin(name='VIN', pin='1', side='left', slot='3/3'),
            elm.IcPin(name='FB', pin='4', side='right', slot='1/2'),
            elm.IcPin(name='VOUT', pin='2', side='right', slot='2/2'),
        ],
        edgepadW=2.5,
        edgepadH=0.8,
        pinspacing=1.0,
        leadlen=1.0
    ).label('U2\nLM2596S', loc='center', fontsize=10)

    # GND connection
    elm.Line().at(ic.GND).down(2.5)
    elm.Ground()

    # Calculate Y position (midpoint between VIN and ON)
    junction_y = (ic.VIN[1] + ic.ON[1]) / 2

    # Input rail: straight horizontal line at junction_y
    # +15V -> dot -> dot -> junction3
    elm.Dot(open=True).at((ic.VIN[0] - 7.0, junction_y)).label('+15V', loc='left')

    elm.Line().right(2.0)
    elm.Dot()
    junction1 = d.here
    d.push()

    elm.Line().right(2.0)
    elm.Dot()
    junction2 = d.here
    d.push()

    elm.Line().right(2.0)
    elm.Dot()
    junction3 = d.here

    # Connect junction3 to VIN and ON pins
    elm.Line().at(junction3).to(ic.VIN)
    elm.Line().at(junction3).to(ic.ON)

    # C5 from junction1
    d.pop()
    elm.Capacitor().down(2.0).label('C5\n100µF', loc='bot')
    elm.Ground()

    # C6 from junction2
    d.pop()
    elm.Capacitor().down(2.0).label('C6\n100nF', loc='bot')
    elm.Ground()

    # Output stage from VOUT pin (halved spacing)
    elm.Line().at(ic.VOUT).right(1.0)  # Halved spacing before L1
    elm.Dot()
    vout_junction = d.here
    d.push()

    elm.Inductor().right(2.5).label('L1\n100µH\n4.5A', loc='top')
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

    # Feedback voltage divider network (straight down, spacing = 0.5)
    elm.Line().down(0.5)
    elm.Resistor().down().label('R1\n10kΩ', loc='bot', ofst=0.5)
    elm.Line().down(0.5)
    elm.Dot()  # Tap junction for FB connection
    tap_junction = d.here
    d.push()  # Save tap position for FB connection

    elm.Line().down(0.5)
    elm.Resistor().down().label('R2\n1kΩ', loc='bot', ofst=0.5)
    elm.Line().down(0.5)
    elm.Ground()

    # Connect tap junction to FB pin
    d.pop()
    elm.Line().to(ic.FB)

    # Output capacitor C3 (from output junction - right side, facing up)
    d.pop()
    elm.Capacitor().up(2.0).label('C3\n470µF\n25V', loc='bot', ofst=0.5)
    elm.Ground().flip()

    # Flyback diode D1 (from switching node - left side, facing up)
    d.pop()
    elm.Diode().up(2.0).reverse().label('D1\nSS34', loc='top')
    elm.Ground().flip()

    # Save to docs/_fragments (one level up from diagram-sources)
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, '../docs/_fragments/buck-u2-diagram.svg')
    d.save(output_path)

print("✓ Buck converter diagram generated with dark theme")
