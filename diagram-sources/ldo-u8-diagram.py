#!/usr/bin/env python3
"""
LM7912 Linear Regulator: -13.5V → -12V (Negative Voltage)
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

    # LM7912 linear regulator IC (3-pin TO-252-3)
    # Note: LM7912 has different pinout: pin 1=IN, pin 2=OUT, pin 3=GND
    ic = elm.Ic(
        pins=[
            elm.IcPin(name='GND', pin='3', side='left', slot='1/2'),
            elm.IcPin(name='IN', pin='1', side='left', slot='2/2'),
            elm.IcPin(name='OUT', pin='2', side='right', slot='1/1'),
        ],
        edgepadW=2.5,
        edgepadH=0.8,
        pinspacing=1.0,
        leadlen=1.0
    ).label('U8\nLM7912', loc='center', fontsize=10)

    # GND connection
    elm.Line().at(ic.GND).down(1.0)
    elm.Ground()

    # Y position at IN pin level
    junction_y = ic.IN[1]

    # Input rail: straight horizontal line at IN level
    # -13.5V -> dot -> dot -> junction3
    elm.Dot(open=True).at((ic.IN[0] - 5.5, junction_y)).label('-13.5V', loc='left')

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

    # Connect junction3 to IN
    elm.Line().at(junction3).to(ic.IN)

    # C16 from junction2 (closer to IC - high-freq filtering)
    # Non-polarized ceramic capacitor
    d.pop()
    elm.Capacitor().down(2.0).label('C16\n470nF', loc='bot')
    elm.Ground()

    # C24 from junction1 (farther from IC - bulk storage)
    # NEGATIVE VOLTAGE: Electrolytic with reversed polarity
    # Negative terminal (top) to -13.5V, positive terminal (bottom) to GND
    d.pop()
    elm.Capacitor().down(2.0).reverse().label('C24\n470µF', loc='bot')
    elm.Ground()

    # Output stage from OUT pin
    elm.Line().at(ic.OUT).right(0.5)
    elm.Dot()
    output_junction1 = d.here
    d.push()

    elm.Line().right(1.0)
    elm.Dot()
    output_junction2 = d.here
    d.push()

    elm.Line().right(1.0)
    elm.Dot()
    output_junction3 = d.here
    d.push()

    elm.Line().right(1.0)
    elm.Dot(open=True).label('-12V', loc='right')

    # C19 from output_junction1 (closest to IC - high-freq filtering)
    # Non-polarized ceramic capacitor
    d.pop()
    d.pop()
    d.pop()
    elm.Capacitor().down(2.0).label('C19\n100nF', loc='bot')
    elm.Ground()

    # C25 from output_junction2 (farther - bulk storage)
    # NEGATIVE VOLTAGE: Electrolytic with reversed polarity
    # Negative terminal (top) to -12V, positive terminal (bottom) to GND
    d.pop()
    elm.Capacitor().down(2.0).reverse().label('C25\n470µF', loc='bot')
    elm.Ground()

    # LED indicator from output_junction3
    # NEGATIVE VOLTAGE: LED reversed - anode UP (to GND), cathode down (to -12V through resistor)
    d.pop()
    elm.LED().down(1.0).reverse().label('LED4', loc='top', ofst=0.3)
    elm.Resistor().down(1.0).label('R9\n1kΩ', loc='bot', ofst=0.3)
    elm.Line().down(0.5)
    elm.Line().left(0.2)
    elm.Line().down(0.2)
    elm.Ground()

    # Save to doc/static/circuits/ (one level up from diagram-sources)
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, '../doc/static/circuits/ldo-u8-diagram.svg')
    d.save(output_path)

print("✓ Linear regulator diagram generated with transparent background")
