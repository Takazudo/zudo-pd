#!/usr/bin/env python3
"""
LM7812 Linear Regulator: +13.5V → +12V
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

    # LM7812 linear regulator IC (3-pin TO-263-2)
    ic = elm.Ic(
        pins=[
            elm.IcPin(name='GND', pin='2', side='left', slot='1/2'),
            elm.IcPin(name='IN', pin='1', side='left', slot='2/2'),
            elm.IcPin(name='OUT', pin='3', side='right', slot='1/1'),
        ],
        edgepadW=2.0,
        edgepadH=0.8,
        pinspacing=1.0,
        leadlen=1.0
    ).label('U6\nLM7812', loc='center', fontsize=14)

    # GND connection
    elm.Line().at(ic.GND).down(1.0)
    elm.Ground()

    # Y position at IN pin level
    junction_y = ic.IN[1]

    # Input rail: straight horizontal line at IN level
    # +13.5V -> dot -> dot -> junction3
    elm.Dot(open=True).at((ic.IN[0] - 5, junction_y)).label('+13.5V', loc='left')

    elm.Line().right(1)
    elm.Dot()
    junction1 = d.here
    d.push()

    elm.Line().right(2.0)
    elm.Dot()
    junction2 = d.here
    d.push()

    elm.Line().right(2.0)
    junction3 = d.here

    # Connect junction3 to IN
    elm.Line().at(junction3).to(ic.IN)

    # C14 from junction2 (closer to IC - high-freq filtering)
    d.pop()
    elm.Capacitor().down(2.0).label('C14\n470nF', loc='bot')
    elm.Ground()

    # C20 from junction1 (farther from IC - bulk storage)
    d.pop()
    elm.Capacitor().down(2.0).label('C20\n470µF', loc='bot')
    elm.Ground()

    # Output rail from ic.OUT
    elm.Line().at(ic.OUT).right(0.2)
    elm.Dot()
    output_junction1 = d.here
    d.push()

    elm.Line().right(2.0)
    elm.Dot()
    output_junction2 = d.here

    # C21 from output_junction2 (farther from IC - bulk storage)
    elm.Capacitor().down(2.0).label('C21\n470µF', loc='bot')
    elm.Ground()

    # C17 from output_junction1 (closer to IC - high-freq filtering)
    d.pop()
    elm.Capacitor().down(2.0).label('C17\n100nF', loc='bot')
    elm.Ground()

    elm.Line().at(output_junction2).right(1.0)
    elm.Dot()
    to_led_junction = d.here

    elm.Line().right(1)
    elm.Fuse().right(1.5).label('PTC1', loc='top')

    elm.Line().right(1)
    elm.Dot()
    d.push()

    # TVS1 diode (cathode up to +12V, anode down to GND)
    elm.Zener().down(2.0).reverse().label('TVS1', loc='right', ofst=(1,-1))
    elm.Ground()

    d.pop()
    elm.Line().right(1.0)
    elm.Dot(open=True).label('+12V\nOUT', loc='top', ofst=(0,0.3))

    elm.Line().at(to_led_junction).up(4.0)
    elm.Line().left(1)
    elm.Resistor(scale=0.7).left(1.0).label('R7\n1kΩ', loc='top', ofst=0.3)
    elm.Line().left(1)
    elm.LED().left(1.0).label('LED2\nGreen', loc='top', ofst=0.3)
    elm.Line().left(1)
    elm.Line().down(0.5)
    elm.Ground()

    # Save to doc/static/circuits/ (one level up from diagram-sources)
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, '../doc/static/circuits/ldo-u6-diagram.svg')
    d.save(output_path)

print("✓ Linear regulator diagram generated with transparent background")
