#!/usr/bin/env python3
"""
LM2586SX-ADJ IC - Pin Configuration
Simple IC diagram showing only the component with pin labels
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

    # Define IC first at a fixed position so we can reference it
    ic_x = 8  # IC X position
    ic_y = 0.0   # IC Y position

    ic = (elm.Ic(
        pins=[
            # Left side (top to bottom)
            elm.IcPin(name='VIN', pin='7', side='left', slot='4/4'),
            elm.IcPin(name='COMP', pin='2', side='left', slot='3/4'),
            elm.IcPin(name='Freq.Sync.', pin='6', side='left', slot='2/4'),
            elm.IcPin(name='GND', pin='4', side='left', slot='1/4'),
            # Right side (top to bottom)
            elm.IcPin(name='SW', pin='5', side='right', slot='4/4'),
            elm.IcPin(name='Freq.Adj.', pin='1', side='right', slot='3/4'),
            elm.IcPin(name='FB', pin='3', side='right', slot='2/4'),
        ],
        edgepadW=5.0,
        edgepadH=1.2,
        pinspacing=0.8,
        leadlen=1.0,
        pinlblsize=12
    ).at((ic_x, ic_y))
     .anchor('VIN')
     .label('U5\nLM2586SX-ADJ', loc='center', fontsize=14)
    )

    # Now draw input section to the left of IC
    # +15V input from left with capacitors
    vin_start = (0, ic.VIN[1])
    elm.Dot(open=True).at(vin_start).label('+15V IN', loc='top', fontsize=14, ofst=0.5)

    # Input rail
    elm.Line().right(1)
    elm.Dot()
    vin_tap1 = d.here
    d.push()
    elm.Line().right(0.5)
    elm.Dot()

    # C13 bulk capacitor (100µF)
    elm.Capacitor().down(2.5).label('C13\n100µF', loc='bottom', fontsize=11)
    elm.Ground()

    # Continue input rail
    d.pop()
    elm.Line().right(2.5)
    elm.Dot()
    vin_tap2 = d.here
    d.push()

    # C16 ceramic capacitor (100nF)
    elm.Capacitor().down(2.5).label('C16\n100nF', loc='bottom', fontsize=11)
    elm.Ground()

    # Continue to IC VIN pin
    d.pop()
    elm.Line().to(ic.VIN)

    # GND connection from IC GND pin
    elm.Line().at(ic.GND).left(0.8)
    elm.Line().down(0.8)
    elm.Ground()

    # Compensation network from COMP pin
    elm.Line().at(ic.COMP).left(3)
    elm.Line().down(5)
    elm.Line().left(1)
    elm.Resistor().left().label('R9\n3kΩ', loc='bottom', fontsize=11)
    elm.Line().left(1)
    elm.Dot()
    comp_junction = d.here
    d.push()

    # C15 capacitor to GND
    elm.Capacitor().down(2).label('C15\n47nF', loc='right', fontsize=11)
    elm.Ground()

    # Return to junction, second path to GND
    d.pop()
    elm.Line().left(1)
    elm.Line().down(1)
    elm.Ground()

    # T1 flyback transformer primary: +15V -> T1 -> SW
    # Vertical line up from first tap point
    elm.Line().at(vin_tap1).up(3.0)
    point_to_switch = d.here

    # Horizontal line across the top to above SW pin
    elm.Line().right(ic.SW[0] - point_to_switch[0])
    t1_top = d.here

    # T1 primary inductor (positioned above SW pin)
    elm.Inductor2(loops=3).down(2.0).label('T1', loc='left', fontsize=12, ofst=(-0.75,-0.8))

    # Connect down to SW pin
    elm.Line().down(t1_top[1] - ic.SW[1] - 2.0)
    elm.Line().to(ic.SW)

    # Save to doc/static/circuits/
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, '../doc/static/circuits/inverter-u5-diagram.svg')
    d.save(output_path)

print("✓ LM2586 IC diagram (pin configuration only) generated")
