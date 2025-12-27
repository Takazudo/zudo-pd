#!/usr/bin/env python3
"""
Generate complete USB-PD modular synthesizer power supply circuit diagram.
Uses Schemdraw to create a block-level schematic showing all 4 stages.
"""

import schemdraw
import schemdraw.elements as elm
from pathlib import Path

# Create output directory
output_dir = Path(__file__).parent.parent / 'doc' / 'static' / 'circuits'
output_dir.mkdir(parents=True, exist_ok=True)

# Initialize drawing
d = schemdraw.Drawing(fontsize=10, font='sans-serif')

# Title
d += elm.Label().label('USB-PD Modular Synthesizer Power Supply - Complete Circuit', fontsize=12, loc='top')
d += elm.Gap().length(0.5)

##############################################################################
# STAGE 1: USB-PD INPUT
##############################################################################

# Start position
start_x = 0
start_y = 0

d.here = (start_x, start_y)

# USB-C Input
d += elm.SourceV().label('USB-C\n15V PD', loc='bottom')
d += elm.Line().right(0.5)
d += elm.Capacitor().label('10µF', loc='bottom')
d += elm.Line().right(0.5)

# CH224D block
d += (ch224d_box := elm.RBox(w=2, h=1.5).label('CH224D\nPD Controller\nCFG: 15V'))
d += elm.Line().right(0.5)
d += (node_15v := elm.Dot().label('+15V', loc='top'))

# Ground path
d.push()
d.here = node_15v.center
d += elm.Capacitor().down().label('10µF', loc='right')
d += elm.Ground()
d.pop()

##############################################################################
# STAGE 2: DC-DC CONVERSION - Path 1 (+13.5V)
##############################################################################

d.here = (node_15v.center[0] + 1, node_15v.center[1])
d += elm.Line().right(0.5)

# LM2596S #1
d += (lm2596_1_box := elm.RBox(w=2.5, h=1.5).label('LM2596S-ADJ #1\nBuck Converter\nR1=2.2k, R2=10k'))
d += elm.Line().right(0.2)
d += elm.Inductor().right().label('33µH', loc='top')
d += elm.Line().right(0.2)
d += (node_135v := elm.Dot().label('+13.5V', loc='top'))

# Ground
d.push()
d += elm.Capacitor().down().label('220µF', loc='right')
d += elm.Ground()
d.pop()

##############################################################################
# STAGE 3: LINEAR REGULATION - +12V
##############################################################################

d.here = (node_135v.center[0] + 1, node_135v.center[1])
d += elm.Line().right(0.3)
d += elm.Capacitor().label('0.33µF', loc='top')
d += elm.Line().right(0.3)

# L7812
d += (l7812_box := elm.RBox(w=1.8, h=1.5).label('L7812CV\n+12V LDO'))
d += elm.Line().right(0.3)
d += elm.Capacitor().label('0.1µF', loc='top')
d += elm.Line().right(0.3)
d += (node_12v := elm.Dot().label('+12V', loc='top'))

# Ground
d.push()
d += elm.Capacitor().down().label('470µF', loc='right')
d += elm.Ground()
d.pop()

##############################################################################
# STAGE 4: PROTECTION - +12V rail
##############################################################################

d.here = (node_12v.center[0] + 1, node_12v.center[1])
d += elm.Line().right(0.2)

# PTC Fuse
d += elm.Resistor().label('PTC\n1.1A', loc='top')
d += elm.Line().right(0.2)

# Glass Fuse
d += elm.Fuse().label('F1\n2A', loc='top')
d += elm.Line().right(0.2)

# TVS Diode
d.push()
d += (tvs_node := elm.Dot())
d += elm.Zener().down().flip().label('SMAJ15A', loc='right')
d += elm.Ground()
d.pop()

d.here = tvs_node.center
d += elm.Line().right(0.5)
d += elm.Dot().label('+12V\nOUT\n1.2A', loc='top', fontsize=11, color='blue')

##############################################################################
# STAGE 2: DC-DC CONVERSION - Path 2 (+7.5V)
##############################################################################

# Start new line below for +5V path
d.here = (node_15v.center[0] + 1, node_15v.center[1] - 3)
d += (branch_15v_2 := elm.Dot())
d += elm.Line().right(0.5)

# LM2596S #2
d += (lm2596_2_box := elm.RBox(w=2.5, h=1.5).label('LM2596S-ADJ #2\nBuck Converter\nR3=1k, R4=10k'))
d += elm.Line().right(0.2)
d += elm.Inductor().right().label('33µH', loc='top')
d += elm.Line().right(0.2)
d += (node_75v := elm.Dot().label('+7.5V', loc='top'))

# Ground
d.push()
d += elm.Capacitor().down().label('220µF', loc='right')
d += elm.Ground()
d.pop()

##############################################################################
# STAGE 3: LINEAR REGULATION - +5V
##############################################################################

d.here = (node_75v.center[0] + 1, node_75v.center[1])
d += elm.Line().right(0.3)
d += elm.Capacitor().label('0.33µF', loc='top')
d += elm.Line().right(0.3)

# L7805
d += (l7805_box := elm.RBox(w=1.8, h=1.5).label('L7805ABD2T\n+5V LDO'))
d += elm.Line().right(0.3)
d += elm.Capacitor().label('0.1µF', loc='top')
d += elm.Line().right(0.3)
d += (node_5v := elm.Dot().label('+5V', loc='top'))

# Ground
d.push()
d += elm.Capacitor().down().label('470µF', loc='right')
d += elm.Ground()
d.pop()

##############################################################################
# STAGE 4: PROTECTION - +5V rail
##############################################################################

d.here = (node_5v.center[0] + 1, node_5v.center[1])
d += elm.Line().right(0.2)

# PTC Fuse
d += elm.Resistor().label('PTC\n0.75A', loc='top')
d += elm.Line().right(0.2)

# Glass Fuse
d += elm.Fuse().label('F2\n1.5A', loc='top')
d += elm.Line().right(0.2)

# TVS Diode
d.push()
d += (tvs_node_5v := elm.Dot())
d += elm.Zener().down().flip().label('PRTR5V0U2X', loc='right')
d += elm.Ground()
d.pop()

d.here = tvs_node_5v.center
d += elm.Line().right(0.5)
d += elm.Dot().label('+5V\nOUT\n0.5A', loc='top', fontsize=11, color='blue')

##############################################################################
# STAGE 2: DC-DC CONVERSION - Path 3 (-15V inverter + -13.5V)
##############################################################################

# Start new line below for -12V path
d.here = (node_15v.center[0] + 1, node_15v.center[1] - 6)
d += (branch_15v_3 := elm.Dot())
d += elm.Line().right(0.5)

# ICL7660 Inverter
d += (icl7660_box := elm.RBox(w=2, h=1.5).label('ICL7660M\nVoltage Inverter\nC+=C-=10µF'))
d += elm.Line().right(0.2)
d += (node_neg15v := elm.Dot().label('-15V', loc='top'))

# Ground
d.push()
d += elm.Capacitor().down().label('10µF', loc='right')
d += elm.Ground()
d.pop()

# LM2596S #3 for -13.5V
d.here = (node_neg15v.center[0] + 0.5, node_neg15v.center[1])
d += elm.Line().right(0.5)
d += (lm2596_3_box := elm.RBox(w=2.5, h=1.5).label('LM2596S-ADJ #3\nBuck Converter\nR5=2.2k, R6=10k'))
d += elm.Line().right(0.2)
d += elm.Inductor().right().label('33µH', loc='top')
d += elm.Line().right(0.2)
d += (node_neg135v := elm.Dot().label('-13.5V', loc='top'))

# Ground
d.push()
d += elm.Capacitor().down().label('220µF', loc='right')
d += elm.Ground()
d.pop()

##############################################################################
# STAGE 3: LINEAR REGULATION - -12V
##############################################################################

d.here = (node_neg135v.center[0] + 1, node_neg135v.center[1])
d += elm.Line().right(0.3)
d += elm.Capacitor().label('0.33µF', loc='top')
d += elm.Line().right(0.3)

# CJ7912
d += (cj7912_box := elm.RBox(w=1.8, h=1.5).label('CJ7912\n-12V LDO'))
d += elm.Line().right(0.3)
d += elm.Capacitor().label('0.1µF', loc='top')
d += elm.Line().right(0.3)
d += (node_neg12v := elm.Dot().label('-12V', loc='top'))

# Ground
d.push()
d += elm.Capacitor().down().label('470µF', loc='right')
d += elm.Ground()
d.pop()

##############################################################################
# STAGE 4: PROTECTION - -12V rail
##############################################################################

d.here = (node_neg12v.center[0] + 1, node_neg12v.center[1])
d += elm.Line().right(0.2)

# PTC Fuse
d += elm.Resistor().label('PTC\n0.9A', loc='top')
d += elm.Line().right(0.2)

# Glass Fuse
d += elm.Fuse().label('F3\n1.5A', loc='top')
d += elm.Line().right(0.2)

# TVS Diode (reversed for negative rail)
d.push()
d += (tvs_node_neg12v := elm.Dot())
d += elm.Zener().down().label('SMAJ15CA', loc='right')
d += elm.Ground()
d.pop()

d.here = tvs_node_neg12v.center
d += elm.Line().right(0.5)
d += elm.Dot().label('-12V\nOUT\n0.8A', loc='top', fontsize=11, color='blue')

##############################################################################
# Vertical connections from +15V node to branch points
##############################################################################

# Connect +15V to branch points
d.here = node_15v.center
d += elm.Line().down(abs(node_15v.center[1] - branch_15v_2.center[1]))

d.here = branch_15v_2.center
d += elm.Line().down(abs(branch_15v_2.center[1] - branch_15v_3.center[1]))

##############################################################################
# Stage labels
##############################################################################

# Add stage labels at top
d += elm.Label().at((2, start_y + 2)).label('STAGE 1', fontsize=9, color='purple')
d += elm.Label().at((2, start_y + 1.7)).label('USB-PD', fontsize=8)

d += elm.Label().at((7, start_y + 2)).label('STAGE 2', fontsize=9, color='green')
d += elm.Label().at((7, start_y + 1.7)).label('DC-DC', fontsize=8)

d += elm.Label().at((13, start_y + 2)).label('STAGE 3', fontsize=9, color='orange')
d += elm.Label().at((13, start_y + 1.7)).label('Linear Reg', fontsize=8)

d += elm.Label().at((18, start_y + 2)).label('STAGE 4', fontsize=9, color='red')
d += elm.Label().at((18, start_y + 1.7)).label('Protection', fontsize=8)

# Save the drawing
output_base = output_dir / 'complete-circuit'

# Save as SVG (primary output)
d.save(f'{output_base}.svg')
print(f'✓ Saved: {output_base}.svg')

# Try to convert SVG to PDF using cairosvg
try:
    import cairosvg
    cairosvg.svg2pdf(url=f'{output_base}.svg', write_to=f'{output_base}.pdf')
    print(f'✓ Saved: {output_base}.pdf')
except ImportError:
    print(f'⚠ Could not save PDF: cairosvg not installed')
    print('  Install: pip install cairosvg')
except Exception as e:
    print(f'⚠ Could not save PDF: {e}')

# Try to convert SVG to PNG
try:
    import cairosvg
    cairosvg.svg2png(url=f'{output_base}.svg', write_to=f'{output_base}.png', dpi=300)
    print(f'✓ Saved: {output_base}.png')
except ImportError:
    print(f'⚠ Could not save PNG: cairosvg not installed')
except Exception as e:
    print(f'⚠ Could not save PNG: {e}')

print('\nCircuit schematic generation complete!')
print(f'Output files saved to: {output_dir}/')
