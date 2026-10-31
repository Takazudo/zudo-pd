"""Board B 20 V switcher-direct DRAFT (unvalidated paper draft; separate from board_b_spec).

This is a separate spec on purpose. Board B (board_b_spec.py) is the S3 design that was
ordered on 2026-09-20; editing it in place would orphan the as-ordered schematic and
its inventory placements, integration rules and observed runs. This draft is not bound
to the central inventory, has no PCB, and adopts nothing. New ICs are SHORTLISTED
candidates (component-board-b20-draft-candidates); values marked R_PROPOSED /
C_PROPOSED have no owner record.

Architecture (scripts/pcb/calculate-board-b20-draft.py has the arithmetic):
- VIN is Board P VBUS_OUT (20 V contract, J5 pins 1/2). The LT3015 and both LT1963A
  regulators are removed; three TI TPS54560DDAR run from VIN: U1 +12.15 V buck, U2
  +5.08 V buck, U3 -12.15 V inverting buck-boost with its GND/PAD on M12_RAW. The
  inverter IC sees VIN + |Vout| <= 37.6 V against its 60 V operating limit; this
  replaces the old U4 40 V margin problem.
- Each converter output passes an LC post-filter (ASPI-0630LR 10 uH + 25SVPF47M +
  GRM32 10 uF) to the *_PRE node. Ripple at the load is ideal-LC arithmetic only, so the
  < 1 mVp-p gate stays OPEN.
- Precision servo: OPA2187 integrators compare each *_PRE node (0.1 % dividers) with
  U10 REF5025 and inject a bounded current into the converter FB node through 1 Mohm
  (4.7 Mohm on the inverter). The shunt and switch drop are outside this loop and are
  budgeted against the source band.
- Limiter: U11/U12 INA301A3 (transparent mode) on 20 mOhm PE1206 shunts for +12 V
  (two in parallel) and +5 V, LIMIT from REF dividers; the -12 V shunt pair is compared
  directly by U9 OPA2187 against a 33 ohm / 20.5 kohm divider from GND to M12_PRE. Any
  trip pulls FAULT_N. The limiter trips; it does not limit let-through.
- Reverse blocking: back-to-back CSD18543Q3A pairs (common source) on every rail, each
  with a BZT52C11 VGS clamp. +12/+5 gates ramp from VIN through R and a gate capacitor;
  -12 is driven from P5_PRE through Q24 DMP3036 with a Miller capacitor and Q25 fast
  turn-off. EN_N high disables all three at once.
- Windows: U6/U7/U8 OPA2187 OV/UV comparators on each terminal (UV gated by ARM),
  U5B VIN undervoltage (16.95 V against REF/2). All pull the FAULT_N bus through BSS138s.
- Latch: Q30 BSS138 / Q31 DMP3036 cross-coupled latch on FAULT_N, held reset during
  power-on by Q32. Re-plug (loss of P5_PRE) is the only reset. Enable latch Q33/Q34 is
  set by RDY (PDOK valid for about 150 ms, RC) and reset by the fault latch.
- Discharge: a one-shot from EN_N (C60/R60) drives BSS138 discharge switches with 100 /
  150 / 33 ohm loads (+12 / -12 / +5), sized so +5 V reaches 0.8 V first and the analog
  rails fall within the calculated capacitance-ratio window at zero load.
Footprints named *_DRAFT do not exist yet; no PCB is part of this draft.
"""

PROJECT_NAME = 'board-b20-draft'
OUT = 'boards/board-b20-draft/board-b20-draft.kicad_sch'
PAPER = 'A0'

COMPONENTS = {}
NETS = {}
NO_CONNECT = []
LABEL_OVERRIDES = {}

_PITCH_X, _PITCH_Y, _COLS = 50.8, 30.48, 22
_ORIGIN = (25.4, 25.4)

# exact owner-record parts: (symbol, value, lcsc, footprint)
P = {
    'TPS': ('TPS54560DDAR', 'TPS54560DDAR', 'C31966', 'zudo-pd:HSOP-8_TPS54560DDA_DRAFT'),
    'OPA': ('OPA2187IDGKR', 'OPA2187IDGKR', 'C2863562', 'zudo-pd:VSSOP-8_DGK_DRAFT'),
    'REF': ('REF5025AIDR', 'REF5025AIDR', 'C11341', 'zudo-pd:SOIC-8_D_DRAFT'),
    'INA': ('INA301A3IDGKR', 'INA301A3IDGKR', 'C2861552', 'zudo-pd:VSSOP-8_DGK_DRAFT'),
    'SHUNT': ('PE1206FRF470R02L', '20mR 1% 1W', 'C164156', 'zudo-pd:R1206_DRAFT'),
    'L10U': ('ASPI-0630LR-100M-T15', '10uH', 'C1334133', 'zudo-pd:ASPI-0630LR_L7.5-W6.85'),
    'DSCH': ('SDT5A60SA-13', 'SDT5A60SA-13', 'C3024223', 'zudo-pd:SMA_Diodes_SDT5A60SA_C3024223'),
    'NFET': ('CSD18543Q3A', 'CSD18543Q3A', 'C840100', 'zudo-pd:VSON-8_L3.3-W3.3-P0.65_CSD18543Q3A'),
    'BSS': ('BSS138-7-F', 'BSS138-7-F', 'C40912', 'zudo-pd:SOT-23_L2.9-W1.3-P1.90-LS2.4-BR'),
    'PFET': ('DMP3036SFG-7', 'DMP3036SFG-7', 'C461081', 'zudo-pd:PowerDI3333-8_DMP3036SFG'),
    'Z11': ('BZT52C11-7-F_C92321', 'BZT52C11-7-F', 'C92321', 'zudo-pd:SOD-123_L2.8-W1.8-LS3.7-RD'),
    'C10U50': ('GRM32ER71H106KA12L', '10uF 50V X7R', 'C77102', 'zudo-pd:C1210'),
    'C47P': ('25SVPF47M', '47uF 25V polymer', 'C136280', 'zudo-pd:CAP-SMD_BD6.3-L6.6-W6.6-FD'),
    'C100U': ('RVT1H101M0810', '100uF 50V', 'C970687', 'zudo-pd:CAP-SMD_BD8.0-L8.3-W8.3-LS9.0-FD'),
    'C100N': ('CC0603KRX7R9BB104', '100nF/50V', 'C14663', 'zudo-pd:C0603'),
    'C1U': ('CL10A105KB8NNNC', '1uF 50V', 'C15849', 'zudo-pd:C0603'),
    'C10U1206': ('CL31A106KBHNNNE', '10uF 50V', 'C13585', 'zudo-pd:C1206'),
    'J5': ('PM254V-11-06-H85', 'PM254V-11-06-H85', 'C2832269', 'zudo-pd:HDR-TH_6P-P2.54-V-F'),
    'SCREW': ('WJ500V-5.08-2P', 'WJ500V-5.08-2P', 'C8465', 'zudo-pd:WJ500V-5.08-2P_C8465'),
    'R100K': ('0603WAF1003T5E', '100k', 'C25803', 'zudo-pd:R0603'),
    'R150K': ('0603WAF1503T5E', '150k', 'C22807', 'zudo-pd:R0603'),
    'R56K': ('0603WAF5602T5E', '56k', 'C23206', 'zudo-pd:R0603'),
    'R4K7': ('0603WAF4701T5E', '4.7k', 'C23162', 'zudo-pd:R0603'),
    'R10K0805': ('0805W8F1002T5E', '10k', 'C17414', 'zudo-pd:R0805'),
    'R1K': ('0603WAF1001T5E', '1k', 'C21190', 'zudo-pd:R0603'),
    'RP10K': ('RT0603BRD0710KL', '10k 0.1%', 'C95204', 'zudo-pd:R0603'),
    'RP174K': ('RT0603BRD07174KL', '174k 0.1%', 'C861163', 'zudo-pd:R0603'),
    'RP158K': ('RT0603BRE07158KL', '158k 0.1%', 'C861679', 'zudo-pd:R0603'),
    'RP4K02': ('RT0603BRD074K02L', '4.02k 0.1%', 'C705781', 'zudo-pd:R0603'),
    'RP11K5': ('RT0603BRD0711K5L', '11.5k 0.1%', 'C705719', 'zudo-pd:R0603'),
    'RP10K5': ('RT0603BRD0710K5L', '10.5k 0.1%', 'C861077', 'zudo-pd:R0603'),
    'RP8K2': ('RT0603BRD078K2L', '8.2k 0.1%', 'C861589', 'zudo-pd:R0603'),
    'RP3K09': ('RT0603BRD073K09L', '3.09k 0.1%', 'C861371', 'zudo-pd:R0603'),
    'RP680': ('RT0603BRD07680RL', '680 0.1%', 'C861519', 'zudo-pd:R0603'),
    'RP33': ('RT0603BRD0733RL', '33 0.1%', 'C861332', 'zudo-pd:R0603'),
}


def _place():
    n = len(COMPONENTS)
    return (_ORIGIN[0] + (n % _COLS) * _PITCH_X, _ORIGIN[1] + (n // _COLS) * _PITCH_Y)


def part(ref, key, *pin_nets):
    sym, value, lcsc, fp = P[key]
    COMPONENTS[ref] = (sym, value, lcsc, fp, False, _place())
    for pin, net in pin_nets:
        if net is None:
            NO_CONNECT.append(f'{ref}.{pin}')
        else:
            NETS.setdefault(net, []).append(f'{ref}.{pin}')


def rprop(ref, value, a, b, fp='zudo-pd:R0603'):
    COMPONENTS[ref] = ('R_PROPOSED', value, '', fp, False, _place())
    NETS.setdefault(a, []).append(f'{ref}.1')
    NETS.setdefault(b, []).append(f'{ref}.2')


def cprop(ref, value, a, b, fp='zudo-pd:C0603'):
    COMPONENTS[ref] = ('C_PROPOSED', value, '', fp, False, _place())
    NETS.setdefault(a, []).append(f'{ref}.1')
    NETS.setdefault(b, []).append(f'{ref}.2')


def two(ref, key, a, b):
    part(ref, key, ('1', a), ('2', b))


def nfet(ref, g, s, d):   # BSS138: 1 G, 2 S, 3 D
    part(ref, 'BSS', ('1', g), ('2', s), ('3', d))


def pfet(ref, s, g, d):   # DMP3036SFG-7: 1-3 S, 4 G, 5-9 D
    part(ref, 'PFET', ('1', s), ('2', s), ('3', s), ('4', g), ('5', d), ('6', d), ('7', d), ('8', d), ('9', d))


def power_nfet(ref, s, g, d):   # CSD18543Q3A: 1-3 S, 4 G, 5-9 D
    part(ref, 'NFET', ('1', s), ('2', s), ('3', s), ('4', g), ('5', d), ('6', d), ('7', d), ('8', d), ('9', d))


def zener(ref, k, a):
    part(ref, 'Z11', ('1', k), ('2', a))


def opa(ref, vp, vn, a, b):
    """a/b = (plus, minus, out) or None for an unused channel wired as a grounded follower."""
    pins = [('8', vp), ('4', vn)]
    for (pp, pm, po), ch in ((('3', '2', '1'), a), (('5', '6', '7'), b)):
        if ch is None:
            spare = f'{ref}_SPARE_{po}'
            pins += [(pp, 'GND'), (pm, spare), (po, spare)]
        else:
            pins += [(pp, ch[0]), (pm, ch[1]), (po, ch[2])]
    part(ref, 'OPA', *pins)


# ---------------------------------------------------------------- connectors / input
part('J5', 'J5', ('1', 'VIN'), ('2', 'VIN'), ('3', None), ('4', 'PDOK'), ('5', 'GND'), ('6', 'GND'))
part('J6', 'SCREW', ('1', 'GND'), ('2', 'M12_OUT'))
part('J7', 'SCREW', ('1', 'P5_OUT'), ('2', 'P12_OUT'))
part('C1', 'C100U', ('1', 'VIN'), ('2', 'GND'))
two('C2', 'C10U50', 'VIN', 'GND')


# ---------------------------------------------------------------- converters
def buck(n, u, raw, pre, rt_top):
    part(u, 'TPS', ('1', f'{n}_BOOT'), ('2', 'VIN'), ('3', f'{n}_EN'), ('4', f'{n}_RT'), ('5', f'{n}_FB'),
         ('6', f'{n}_COMP'), ('7', 'GND'), ('8', f'{n}_SW'), ('9', 'GND'))
    two(f'C{n}IN', 'C10U50', 'VIN', 'GND')
    two(f'C{n}BT', 'C100N', f'{n}_BOOT', f'{n}_SW')
    two(f'R{n}RT', 'RP174K', f'{n}_RT', 'GND')
    rprop(f'R{n}EN1', '470k 1%', 'VIN', f'{n}_EN')
    rprop(f'R{n}EN2', '39k 1%', f'{n}_EN', 'GND')
    rprop(f'R{n}CP', '20k 1%', f'{n}_COMP', f'{n}_CZ')
    cprop(f'C{n}CP', '4.7nF C0G', f'{n}_CZ', 'GND')
    cprop(f'C{n}HF', '47pF C0G', f'{n}_COMP', 'GND')
    rprop(f'R{n}FT', rt_top, raw, f'{n}_FB')
    two(f'R{n}FB', 'RP10K', f'{n}_FB', 'GND')
    two(f'L{n}', 'L10U', f'{n}_SW', raw)
    part(f'D{n}', 'DSCH', ('1', f'{n}_SW'), ('2', 'GND'))
    two(f'C{n}O1', 'C10U50', raw, 'GND')
    two(f'C{n}O2', 'C10U50', raw, 'GND')
    two(f'L{n}F', 'L10U', raw, pre)
    part(f'C{n}F1', 'C47P', ('1', pre), ('2', 'GND'))
    two(f'C{n}F2', 'C10U50', pre, 'GND')


buck('A', 'U1', 'P12_RAW', 'P12_PRE', '145k 0.1%')
buck('B', 'U2', 'P5_RAW', 'P5_PRE', '54.9k 0.1%')

# U3 inverting buck-boost: IC GND and PAD on M12_RAW, inductor to system GND
part('U3', 'TPS', ('1', 'C_BOOT'), ('2', 'VIN'), ('3', 'C_EN'), ('4', 'C_RT'), ('5', 'C_FB'),
     ('6', 'C_COMP'), ('7', 'M12_RAW'), ('8', 'C_SW'), ('9', 'M12_RAW'))
two('CCIN1', 'C10U50', 'VIN', 'M12_RAW')
two('CCIN2', 'C10U50', 'VIN', 'M12_RAW')
two('CCBT', 'C100N', 'C_BOOT', 'C_SW')
two('RCRT', 'RP174K', 'C_RT', 'M12_RAW')
rprop('RCEN1', '470k 1%', 'VIN', 'C_EN')
rprop('RCEN2', '39k 1%', 'C_EN', 'M12_RAW')
rprop('RCCP', '20k 1%', 'C_COMP', 'C_CZ')
cprop('CCCP', '4.7nF C0G', 'C_CZ', 'M12_RAW')
cprop('CCHF', '47pF C0G', 'C_COMP', 'M12_RAW')
rprop('RCFT', '145k 0.1%', 'GND', 'C_FB')
two('RCFB', 'RP10K', 'C_FB', 'M12_RAW')
two('LC', 'L10U', 'C_SW', 'GND')
part('DC', 'DSCH', ('1', 'C_SW'), ('2', 'M12_RAW'))
for i in range(1, 5):
    two(f'CCO{i}', 'C10U50', 'GND', 'M12_RAW')
two('LCF', 'L10U', 'M12_RAW', 'M12_PRE')
part('CCF1', 'C47P', ('1', 'GND'), ('2', 'M12_PRE'))
two('CCF2', 'C10U50', 'GND', 'M12_PRE')

# ---------------------------------------------------------------- reference
part('U10', 'REF', ('1', None), ('2', 'P5_PRE'), ('3', None), ('4', 'GND'), ('5', 'REF_NR'),
     ('6', 'REF25'), ('7', None), ('8', None))
two('C10IN', 'C1U', 'P5_PRE', 'GND')
two('C10NR', 'C1U', 'REF_NR', 'GND')
two('C10O', 'C10U1206', 'REF25', 'GND')

# ---------------------------------------------------------------- servo loops (post-filter sense)
# +12: 12.1517 V = 2.5 x (1 + 15.52k / 4.02k)
two('RS1A', 'RP11K5', 'P12_PRE', 'S12_X')
two('RS1B', 'RP4K02', 'S12_X', 'S12')
two('RS1C', 'RP4K02', 'S12', 'GND')
# +5: 5.0840 V = 2.5 x (1 + 184k / 178.02k)
two('RS2A', 'RP174K', 'P5_PRE', 'S5_X')
two('RS2B', 'RP10K', 'S5_X', 'S5')
two('RS2C', 'RP174K', 'S5', 'S5_Y')
two('RS2D', 'RP4K02', 'S5_Y', 'GND')
opa('U4', 'P5_PRE', 'GND', ('S12', 'I12_N', 'SV12'), ('S5', 'I5_N', 'SV5'))
two('C4D', 'C100N', 'P5_PRE', 'GND')
rprop('RI12', '100k 0.1%', 'REF25', 'I12_N')
two('CI12', 'C1U', 'SV12', 'I12_N')
rprop('RJ12', '1M 1%', 'SV12', 'A_FB')
rprop('RI5', '100k 0.1%', 'REF25', 'I5_N')
two('CI5', 'C1U', 'SV5', 'I5_N')
rprop('RJ5', '1M 1%', 'SV5', 'B_FB')
# -12: |V| = 2.5 x 34.5k / 7.11k = 12.1308 V; S12N = 0 V at the setpoint
two('RS3A', 'RP3K09', 'REF25', 'S12N_X')
two('RS3B', 'RP4K02', 'S12N_X', 'S12N')
two('RS3C', 'RP11K5', 'S12N', 'S12N_Y')
two('RS3D', 'RP11K5', 'S12N_Y', 'S12N_Z')
two('RS3E', 'RP11K5', 'S12N_Z', 'M12_PRE')
rprop('RI12N', '100k 0.1%', 'S12N', 'I12N_N')
opa('U5', 'P5_PRE', 'M12_PRE', ('GND', 'I12N_N', 'SV12N'), ('REF125', 'VIN_DIV', 'VINUV_CMP'))
two('C5DP', 'C100N', 'P5_PRE', 'GND')
two('C5DN', 'C100N', 'GND', 'M12_PRE')
two('CI12N', 'C1U', 'SV12N', 'I12N_N')
rprop('RJ12N', '4.7M 1%', 'SV12N', 'C_FB')
# VIN undervoltage at 16.95 V: 1.25 V at VIN_DIV, so the input stays below (V+) - 2 V at VIN overshoot
two('RVR1', 'RP8K2', 'REF25', 'REF125')
two('RVR2', 'RP8K2', 'REF125', 'GND')
rprop('RVU1', '221k 0.1%', 'VIN', 'VIN_DIV')
rprop('RVU2', '17.6k 0.1%', 'VIN_DIV', 'GND')
nfet('Q40', 'VINUV_CMP', 'GND', 'FAULT_N')

# ---------------------------------------------------------------- shunts, limiters
two('RSH1A', 'SHUNT', 'P12_PRE', 'P12_SH')
two('RSH1B', 'SHUNT', 'P12_PRE', 'P12_SH')
two('RSH2', 'SHUNT', 'P5_PRE', 'P5_SH')
two('RSH3A', 'SHUNT', 'M12_SH', 'M12_PRE')
two('RSH3B', 'SHUNT', 'M12_SH', 'M12_PRE')
part('U11', 'INA', ('1', 'P5_PRE'), ('2', None), ('3', 'LIM12'), ('4', 'GND'), ('5', 'GND'),
     ('6', 'FAULT_N'), ('7', 'P12_SH'), ('8', 'P12_PRE'))
two('C11D', 'C100N', 'P5_PRE', 'GND')
two('RL1A', 'RP680', 'REF25', 'LIM12')
two('RL1B', 'RP3K09', 'LIM12', 'GND')
part('U12', 'INA', ('1', 'P5_PRE'), ('2', None), ('3', 'LIM5'), ('4', 'GND'), ('5', 'GND'),
     ('6', 'FAULT_N'), ('7', 'P5_SH'), ('8', 'P5_PRE'))
two('C12D', 'C100N', 'P5_PRE', 'GND')
two('RL2A', 'RP3K09', 'REF25', 'LIM5_X')
two('RL2B', 'RP11K5', 'LIM5_X', 'LIM5')
two('RL2C', 'RP8K2', 'LIM5', 'GND')
# -12 limiter: trip when M12_SH - M12_PRE > 33 / 20533 x |M12_PRE|
two('RL3A', 'RP10K5', 'GND', 'LIM12N_X')
two('RL3B', 'RP10K', 'LIM12N_X', 'LIM12N')
two('RL3C', 'RP33', 'LIM12N', 'M12_PRE')
opa('U9', 'P5_PRE', 'M12_PRE', ('M12_SH', 'LIM12N', 'ILIM12N_CMP'), None)
two('C9DP', 'C100N', 'P5_PRE', 'GND')
two('C9DN', 'C100N', 'GND', 'M12_PRE')
nfet('Q41', 'ILIM12N_CMP', 'GND', 'FAULT_N')

# ---------------------------------------------------------------- output switches
# +12: back-to-back CSD18543Q3A, gate ramp from VIN (164.7k x 100 nF)
power_nfet('Q1', 'P12_CS', 'P12_G', 'P12_SH')
power_nfet('Q2', 'P12_CS', 'P12_G', 'P12_OUT')
zener('DZ1', 'P12_G', 'P12_CS')
two('RG1A', 'R150K', 'VIN', 'P12_GX')
two('RG1B', 'R10K0805', 'P12_GX', 'P12_GY')
two('RG1C', 'R4K7', 'P12_GY', 'P12_G')
two('CG1', 'C100N', 'P12_G', 'GND')
nfet('Q10', 'EN_N', 'GND', 'P12_G')
# +5: gate ramp from VIN (150k x 300 nF)
power_nfet('Q3', 'P5_CS', 'P5_G', 'P5_SH')
power_nfet('Q4', 'P5_CS', 'P5_G', 'P5_OUT')
zener('DZ2', 'P5_G', 'P5_CS')
two('RG2', 'R150K', 'VIN', 'P5_G')
two('CG2A', 'C100N', 'P5_G', 'GND')
two('CG2B', 'C100N', 'P5_G', 'GND')
two('CG2C', 'C100N', 'P5_G', 'GND')
nfet('Q11', 'EN_N', 'GND', 'P5_G')
# -12: common-source pair driven from P5_PRE through Q24; Miller C to the output
power_nfet('Q5', 'M12_CS', 'M12_G', 'M12_SH')
power_nfet('Q6', 'M12_CS', 'M12_G', 'M12_OUT')
zener('DZ3', 'M12_G', 'M12_CS')
pfet('Q24', 'P5_PRE', 'EN_N', 'M12_Y')
two('RG3A', 'R150K', 'M12_Y', 'M12_GX')
two('RG3B', 'R56K', 'M12_GX', 'M12_G')
two('RG3Y', 'R56K', 'M12_Y', 'M12_CS')
two('CG3', 'C100N', 'M12_G', 'M12_OUT')
pfet('Q25', 'M12_G', 'M12_Y', 'M12_CS')

# ---------------------------------------------------------------- windows (terminal sense)
# +12: OV 12.39 V, UV 11.765 V; +5: OV 5.15 V, UV 4.93 V (2.5 V at the divider node)
for rail, out, ovt, ovb, uvt, uvb, u in (('12', 'P12_OUT', '54.2k 0.1%', '13.7k 0.1%', '232k 0.1%', '62.6k 0.1%', 'U6'),
                                         ('5', 'P5_OUT', '10.6k 0.1%', '10k 0.1%', '10.4k 0.1%', '10.7k 0.1%', 'U7')):
    rprop(f'ROV{rail}A', ovt, out, f'OV{rail}_DIV')
    rprop(f'ROV{rail}B', ovb, f'OV{rail}_DIV', 'GND')
    rprop(f'RUV{rail}A', uvt, out, f'UV{rail}_DIV')
    rprop(f'RUV{rail}B', uvb, f'UV{rail}_DIV', 'GND')
    opa(u, 'P5_PRE', 'GND', (f'OV{rail}_DIV', 'REF25', f'OV{rail}_CMP'), ('REF25', f'UV{rail}_DIV', f'UV{rail}_CMP'))
    two(f'C{u}D', 'C100N', 'P5_PRE', 'GND')
nfet('Q42', 'OV12_CMP', 'GND', 'FAULT_N')
nfet('Q43', 'UV12_CMP', 'ARM_GND', 'FAULT_N')
nfet('Q44', 'OV5_CMP', 'GND', 'FAULT_N')
nfet('Q45', 'UV5_CMP', 'ARM_GND', 'FAULT_N')
# -12: node = 0 V at the threshold; OV |V| 12.285 V, UV |V| 11.87 V
rprop('ROVNA', '40.7k 0.1%', 'REF25', 'OVN_DIV')
rprop('ROVNB', '200k 0.1%', 'OVN_DIV', 'M12_OUT')
rprop('RUVNA', '41.7k 0.1%', 'REF25', 'UVN_DIV')
rprop('RUVNB', '198k 0.1%', 'UVN_DIV', 'M12_OUT')
opa('U8', 'P5_PRE', 'M12_PRE', ('GND', 'OVN_DIV', 'OVN_CMP'), ('UVN_DIV', 'GND', 'UVN_CMP'))
two('C8DP', 'C100N', 'P5_PRE', 'GND')
two('C8DN', 'C100N', 'GND', 'M12_PRE')
nfet('Q46', 'OVN_CMP', 'GND', 'FAULT_N')
nfet('Q47', 'UVN_CMP', 'ARM_GND', 'FAULT_N')

# ---------------------------------------------------------------- fault latch, enable latch, timing
two('RF1', 'R10K0805', 'P5_PRE', 'FAULT_N')
two('CF1', 'C100N', 'P5_PRE', 'FAULT_N')
nfet('Q30', 'FLT_L', 'GND', 'FAULT_N')
pfet('Q31', 'P5_PRE', 'FAULT_N', 'FLT_LX')
two('RF2', 'R4K7', 'FLT_LX', 'FLT_L')
two('RF3', 'R100K', 'FLT_L', 'GND')
two('CF3', 'C100N', 'FLT_L', 'GND')
# power-on reset: POR_H high for ~100 ms holds FLT_L low
two('RP1', 'R100K', 'P5_PRE', 'POR_N')
two('CP1', 'C1U', 'POR_N', 'GND')
nfet('Q35', 'POR_N', 'GND', 'POR_H')
two('RP2', 'R100K', 'P5_PRE', 'POR_H')
nfet('Q32', 'POR_H', 'GND', 'FLT_L')
# PDOK (Board P open drain, low = contract valid, UNSOURCED polarity) -> RDY after ~150 ms
two('RPD', 'R10K0805', 'P5_PRE', 'PDOK')
nfet('Q36', 'PDOK', 'GND', 'RDY')
two('RRDY', 'R150K', 'P5_PRE', 'RDY')
two('CRDY', 'C1U', 'RDY', 'GND')
# enable latch: EN_N low = enabled; set by RDY while FAULT_N high, reset by FLT_L
two('REN', 'R10K0805', 'P5_PRE', 'EN_N')
nfet('Q37', 'RDY', 'EN_SET', 'EN_N')
nfet('Q38', 'FAULT_N', 'GND', 'EN_SET')
nfet('Q33', 'EN_E', 'GND', 'EN_N')
pfet('Q34', 'P5_PRE', 'EN_N', 'EN_EX')
two('RE1', 'R4K7', 'EN_EX', 'EN_E')
two('RE2', 'R100K', 'EN_E', 'GND')
nfet('Q39', 'FLT_L', 'GND', 'EN_E')
# ARM: rises ~0.1-0.36 s after enable; gates UV and PDOK-loss faults
two('RARM', 'R100K', 'P5_PRE', 'ARM')
two('CARM', 'C10U1206', 'ARM', 'GND')
nfet('Q48', 'EN_N', 'GND', 'ARM')
nfet('Q49', 'ARM', 'GND', 'ARM_GND')
nfet('Q50', 'PDOK', 'ARM_GND', 'FAULT_N')

# ---------------------------------------------------------------- discharge (one-shot from EN_N)
cprop('C60', '4.7uF 16V X7R', 'EN_N', 'DIS_P', fp='zudo-pd:C0805')
two('R60', 'R100K', 'DIS_P', 'GND')
nfet('Q51', 'DIS_P', 'GND', 'P12_DX')
rprop('RX12', '100 1% 1206', 'P12_DX', 'P12_OUT', fp='zudo-pd:R1206_DRAFT')
nfet('Q52', 'DIS_P', 'GND', 'P5_DX')
rprop('RX5', '33 1% 1206', 'P5_DX', 'P5_OUT', fp='zudo-pd:R1206_DRAFT')
nfet('Q53', 'DIS_P', 'GND', 'DIS_N')
two('R61', 'R10K0805', 'P5_PRE', 'DIS_N')
pfet('Q54', 'P5_PRE', 'DIS_N', 'M12_DG')
two('R62', 'R100K', 'M12_DG', 'M12_OUT')
nfet('Q55', 'M12_DG', 'M12_OUT', 'M12_DX')
rprop('RXN', '150 1% 1206', 'GND', 'M12_DX', fp='zudo-pd:R1206_DRAFT')


def _annotate():
    """Give every builder-named reference (CAIN, RS1A, LC ...) a KiCad prefix+number."""
    import re
    keep = {r for r in COMPONENTS if re.fullmatch(r'[A-Z]+[0-9]+', r)}
    used = {}
    for r in keep:
        m = re.fullmatch(r'([A-Z]+)([0-9]+)', r)
        used.setdefault(m.group(1), set()).add(int(m.group(2)))
    rename = {}
    for r in COMPONENTS:
        if r in keep:
            continue
        prefix = r[0]
        n = 1
        while n in used.setdefault(prefix, set()):
            n += 1
        used[prefix].add(n)
        rename[r] = f'{prefix}{n}'
    def sub(pin):
        ref, num = pin.rsplit('.', 1)
        return f'{rename.get(ref, ref)}.{num}'
    for r in list(COMPONENTS):
        if r in rename:
            COMPONENTS[rename[r]] = COMPONENTS.pop(r)
    for net in NETS:
        NETS[net] = [sub(p) for p in NETS[net]]
    NO_CONNECT[:] = [sub(p) for p in NO_CONNECT]
    return rename


BUILDER_REFS = _annotate()
