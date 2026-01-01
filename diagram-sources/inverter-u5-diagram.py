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

    # LM2586SX-ADJ IC (TO-263-7 package)
    # U5 - Flyback converter
    # Centered in the drawing
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
    ).label('U5\nLM2586SX-ADJ', loc='center', fontsize=14)
    )

    # Save to doc/static/circuits/
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, '../doc/static/circuits/inverter-u5-diagram.svg')
    d.save(output_path)

print("✓ LM2586 IC diagram (pin configuration only) generated")
