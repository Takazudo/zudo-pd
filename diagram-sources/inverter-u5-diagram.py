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

    # +15V input from left with capacitors
    vin_start = (0, 0)
    elm.Dot(open=True).at(vin_start).label('+15V IN', loc='left', fontsize=12)
    d.push()

    elm.Line().right(1.0)
    elm.Dot()
    junction_in_to_switch = d.here
    elm.Line().up(4)

    d.pop()

    # Input rail
    elm.Line().right(2)
    elm.Dot()
    vin_tap1 = d.here
    d.push()

    # C13 bulk capacitor (100µF)
    elm.Capacitor().down(2.5).label('C13\n100µF', loc='bottom', fontsize=11)
    elm.Ground()

    # Continue input rail
    d.pop()
    elm.Line().right(2)
    elm.Dot()
    vin_tap2 = d.here
    d.push()

    # C16 ceramic capacitor (100nF)
    elm.Capacitor().down(2.5).label('C16\n100nF', loc='bottom', fontsize=11)
    elm.Ground()

    # Continue to IC VIN pin
    d.pop()
    elm.Line().right(4)
    vin_to_ic = d.here

    # LM2586SX-ADJ IC (TO-263-7 package)
    # U5 - Flyback converter
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
    ).at(vin_to_ic)
     .anchor('VIN')
     .label('U5\nLM2586SX-ADJ', loc='center', fontsize=14)
    )

    # GND connection from IC GND pin
    elm.Line().at(ic.GND).left(0.8)
    elm.Line().down(0.8)
    elm.Ground()

    # T1 flyback transformer primary: +15V -> T1 -> SW
    # Take tap from input line before VIN
    elm.Line().at(vin_tap1).up(4.0)
    t1_top = d.here

    # T1 primary inductor
    elm.Inductor2(loops=3).down(2.0).label('T1', loc='left', fontsize=12, ofst=0.3)
    t1_bottom = d.here

    # Connect to SW pin
    elm.Line().to((ic.SW[0], t1_bottom[1]))
    elm.Line().to(ic.SW)

    # Save to doc/static/circuits/
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, '../doc/static/circuits/inverter-u5-diagram.svg')
    d.save(output_path)

print("✓ LM2586 IC diagram (pin configuration only) generated")
