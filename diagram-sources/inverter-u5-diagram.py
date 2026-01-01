#!/usr/bin/env python3
"""
LM2586SX-ADJ Flyback Converter Circuit Diagram (U5)

Generates circuit diagram showing:
- LM2586SX-ADJ IC (U5) with pin configuration
- Input filtering: C13 (100µF bulk), C16 (100nF ceramic)
- Flyback transformer: T1 (MSD1514-473MED, 47µH:47µH, 1:1 ratio)
- Compensation network: R9 (3kΩ), C15 (47nF)

Circuit flow: +15V IN → T1 primary → LM2586 SW pin → -15V output (not shown)
"""

import os
import schemdraw
from schemdraw import elements as elm

# ============================================================================
# Drawing Configuration and Main Circuit
# ============================================================================

with schemdraw.Drawing(
    font='Arial',
    fontsize=11,
    color='black',
    transparent=True
) as d:
    d.config(unit=3)

    # ========================================================================
    # IC Definition: LM2586SX-ADJ (U5)
    # ========================================================================
    # IC is positioned first so other components can reference its pins

    ic_x = 6  # IC X position
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
        edgepadW=3.0,
        edgepadH=1.2,
        pinspacing=0.8,
        leadlen=1.0,
        pinlblsize=12
    ).at((ic_x, ic_y))
     .anchor('VIN')
     .label('U5\nLM2586SX-ADJ', loc='top', fontsize=14, ofst=0.2)
    )

    # ========================================================================
    # Input Section: +15V with filtering capacitors
    # ========================================================================

    # +15V input terminal
    vin_start = (0, ic.VIN[1])
    elm.Dot(open=True).at(vin_start).label('+15V IN', loc='top', fontsize=14, ofst=0.5)

    # Input rail with tap points for capacitors and transformer
    elm.Line().right(1)
    elm.Dot()
    vin_tap1 = d.here  # First tap: connects to T1 primary
    d.push()
    elm.Line().right(0.5)
    elm.Dot()

    # C13: 100µF bulk capacitor for low-frequency filtering
    elm.Capacitor().down(2.5).label('C13\n100µF', loc='bottom', fontsize=11)
    elm.Ground()

    # Continue input rail to second capacitor
    d.pop()
    elm.Line().right(2.5)
    elm.Dot()
    d.push()

    # C16: 100nF ceramic capacitor for high-frequency decoupling
    elm.Capacitor().down(2.5).label('C16\n100nF', loc='bottom', fontsize=11)
    elm.Ground()

    # Continue input rail to IC VIN pin
    d.pop()
    elm.Line().to(ic.VIN)

    # ========================================================================
    # Ground Connection
    # ========================================================================

    elm.Line().at(ic.GND).down(0.8)
    elm.Ground()

    # ========================================================================
    # Compensation Network: R9 and C15
    # ========================================================================
    # Type II compensation network for control loop stability

    # Route from COMP pin
    elm.Line().at(ic.COMP).left(1)
    elm.Line().down(4)
    elm.Resistor(scale=0.7).left().label('R9\n3kΩ', loc='bottom', fontsize=11, ofst=0.8)
    elm.Dot()
    comp_junction = d.here
    d.push()

    # C15: 47nF compensation capacitor (first path to GND)
    elm.Capacitor().down(2).label('C15\n47nF', loc='left', fontsize=11, ofst=(-1,-0.8))
    elm.Ground()

    # Second GND path from compensation junction
    d.pop()
    elm.Line().left(2)
    elm.Line().down(1)
    elm.Ground()

    # ========================================================================
    # Flyback Transformer (T1): Primary winding connection
    # ========================================================================
    # Circuit path: +15V (vin_tap1) → T1 primary (p1-p2) → SW pin
    # T1 is a coupled transformer: MSD1514-473MED (47µH:47µH, 1:1 ratio)

    # Route from first tap point up and across to above SW pin
    elm.Line().at(vin_tap1).up(4.0)
    point_to_switch = d.here

    # Horizontal line across, then down to transformer position
    elm.Line().right(ic.SW[0] - point_to_switch[0])
    elm.Line().down(1)
    t1_top = d.here

    # T1: Flyback transformer
    # Oriented horizontally (.right()) with primary on left, secondary on right
    # Primary (p1-p2): connects between +15V rail and SW pin
    # Secondary (s1-s2): will connect to output rectifier (not shown in this diagram)
    t1 = elm.Transformer(t1=3, t2=3).right().anchor('p1').label('T1\n1:1', loc='left', fontsize=11, ofst=(-0.5, 0))

    # Connect transformer p2 to IC SW pin
    elm.Line().at(t1.p2).to(ic.SW)

    # ========================================================================
    # Save Output
    # ========================================================================

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, '../doc/static/circuits/inverter-u5-diagram.svg')
    d.save(output_path)

print("✓ LM2586 flyback converter diagram generated successfully")
