#!/usr/bin/env python3
"""
LM7912 Linear Regulator: -13.5V → -12V (Negative Voltage)
Complete circuit with transparent background, black foreground, Arial font
"""

import os
import schemdraw
from schemdraw import elements as elm

with schemdraw.Drawing(
    font='Arial',         # Sans-serif font
    fontsize=11,
    color='black',        # Foreground: black
    transparent=True      # Transparent background
) as d:
    d.config(unit=3)

    # LM7912 linear regulator IC (3-pin TO-252-3)
    ic = elm.Ic(
        pins=[
            elm.IcPin(name='GND', pin='3', side='left', slot='1/2'),
            elm.IcPin(name='IN', pin='1', side='left', slot='2/2'),
            elm.IcPin(name='OUT', pin='2', side='right', slot='1/1'),
        ],
        edgepadW=2.0,
        edgepadH=0.8,
        pinspacing=1.0,
        leadlen=1.0
    ).label('U8\nLM7912', loc='center', fontsize=14)

    # GND connection
    elm.Line().at(ic.GND).down(1.0)
    elm.Ground()

    # Input rail with capacitors (C24 farther, C16 closer to IC)
    junction_y = ic.IN[1]
    elm.Dot(open=True).at((ic.IN[0] - 5, junction_y)).label('-13.5V', loc='left')

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

    # C16 from junction2 (closer to IC - high-freq filtering)
    d.pop()
    elm.Capacitor().down(2.0).label('C16\n470nF', loc='bot')
    elm.Ground()

    # C24 from junction1 (farther from IC - bulk storage, REVERSED for negative voltage)
    d.pop()
    elm.Capacitor().down(2.0).reverse().label('C24\n470µF', loc='bot')
    elm.Ground()

    # Output rail with capacitors (C19 closer, C25 farther from IC)
    elm.Line().at(ic.OUT).right(0.2)
    elm.Dot()
    output_junction1 = d.here
    d.push()

    elm.Line().right(2.0)
    elm.Dot()
    output_junction2 = d.here

    # C25 from output_junction2 (farther from IC - bulk storage, REVERSED for negative voltage)
    elm.Capacitor().down(2.0).reverse().label('C25\n470µF', loc='bot')
    elm.Ground()

    # C19 from output_junction1 (closer to IC - high-freq filtering)
    d.pop()
    elm.Capacitor().down(2.0).label('C19\n100nF', loc='bot')
    elm.Ground()

    # Protection circuit: PTC3 fuse + TVS3 diode
    elm.Line().at(output_junction2).right(1.0)
    elm.Dot()
    to_led_junction = d.here

    elm.Line().right(1)
    elm.Fuse().right(1.5).label('PTC3', loc='top')

    elm.Line().right(1)
    elm.Dot()
    d.push()

    # TVS3 diode (anode up to -12V, cathode down to GND - reversed for negative rail)
    elm.Zener().down(2.0).label('TVS3', loc='right', ofst=(1,-1))
    elm.Ground()

    # -12V output label
    d.pop()
    elm.Line().right(1.0)
    elm.Dot(open=True).label('-12V\nOUT', loc='top', ofst=(0,0.3))

    # Status LED indicator: R9 + LED4 (REVERSED for negative voltage)
    elm.Line().at(to_led_junction).up(4.0)
    elm.Line().left(1)
    elm.Resistor(scale=0.7).left(1.0).label('R9\n1kΩ', loc='top', ofst=0.3)
    elm.Line().left(1)
    elm.LED().left(1.0).reverse().label('LED4\nRed', loc='top', ofst=0.3)
    elm.Line().left(1)
    elm.Line().down(0.5)
    elm.Ground()

    # Save to doc/static/circuits/
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, '../doc/static/circuits/ldo-u8-diagram.svg')
    d.save(output_path)

print("✓ Linear regulator diagram generated with transparent background")
