"""Board B 20 V switcher-direct DRAFT (unvalidated paper draft; separate from board_b_spec).

This is a separate spec on purpose. Board B (board_b_spec.py) is the S3 design that was
ordered on 2026-09-20; editing it in place would orphan the as-ordered schematic and
its inventory placements, integration rules and observed runs. This draft is not bound
to the central inventory, has no PCB, and adopts nothing. New ICs are SHORTLISTED
candidates (component-board-b20-draft-candidates); values marked R_PROPOSED /
C_PROPOSED have no owner record.

Architecture (scripts/pcb/calculate-board-b20-draft.py has the arithmetic; phase 7 folds in
the independent review of bad5ddf):
- VIN is Board P VBUS_OUT (20 V contract, J5 pins 1/2). Three TI TPS54560DDAR run from
  VIN: U1 +12 V buck, U2 +5 V buck, U3 -12 V inverting buck-boost with its GND/PAD on
  M12_RAW (VIN + |Vout| <= 37.6 V against the 60 V operating limit). Compensation is
  per stage (review finding 11): bucks near fsw/10, the inverter near 15 kHz, below
  its about 92 kHz right-half-plane zero.
- Each converter output passes an LC post-filter to the *_PRE node, then the shunt to the
  *_SH node, then a back-to-back CSD18543Q3A pair to the terminal.
- Supervisory supply P5_SUP (review finding 7): U14 AP63201WU-7 from VIN, about 4.98 V.
  It powers U10 REF5025, the INA301 VS and ALERT pull-up, every servo, window, limit
  and tracking-reference comparator, the latches and the discharge hold-up. A fault in
  the +5 V converter no longer takes its own supervision with it.
- Precision servo: OPA2187 integrators compare each *_SH node (after the shunt, 0.1 %
  dividers) with REF5025 and inject a bounded current into the converter FB node.
  Only the switch-pair drop is outside the loop. The integrators are sized for a loop
  time constant of about 5 ms (review finding 2), so the rails settle within about
  30 ms of P5_SUP, well before the earliest enable (RDY >= 0.2 s).
- Common tracking start (review finding 5 and the contract start-skew rule): RAMP rises
  from 0 toward 2.083 V (REF25 through 20k, 100k load, 1 uF, tau 16.7 ms), reset by a
  BSS138 while EN_N is high. U13 (on VIN) closes +12 = 7.98 x RAMP and +5 = 3.32 x RAMP
  around the switch pairs; U9B closes -12 = -8.06 x RAMP. In the phase-7 ngspice runs
  the ramps start within 0.55-2.26 ms of each other (FAIL against 0.41 ms), +12 exceeds
  |-12| by at most 0.24 V, and band entry order is -12, +12, then +5. Once RAMP passes each
  target the amplifier saturates and the pair is fully on (zener-clamped VGS).
- Limiter: U11/U12 INA301A3 (transparent mode) with LIMIT dividers designed with the
  80 uA ILIMIT x R_TH term (review finding 1); the -12 V shunt pair is compared by U9A.
  Any trip pulls FAULT_N. The limiter trips; hard-short let-through is not bounded.
- Disable: EN_N high drives BSS138 pulldowns on the +12 and +5 gates and, through the
  Q24 / Q25 level shifter, on the -12 gate; the tracking reference is reset as well.
- Windows: U6/U7/U8 OPA2187 OV/UV comparators on each terminal (UV gated by ARM),
  U5B VIN undervoltage (16.95 V against REF/2). All pull the FAULT_N bus through BSS138s.
- Latch: Q30/Q31 fault latch on FAULT_N, held reset during power-on by Q32 (POR 10-36 ms).
  Enable latch Q33/Q34 is set by RDY (PDOK valid for 0.21-0.71 s) and reset by the fault
  latch. Re-plug (loss of P5_SUP) is the only reset.
- Discharge hold-up (review finding 8): CDH (10 uF) charges from the enabled-high node
  EN_E through the Q57 body diode and RDH. When EN_E falls (disable, fault or loss of
  P5_SUP), Q56 and Q54 turn on from CDH alone and drive the discharge switches for about
  0.5-1.4 s; nothing recharges CDH until the next enable.
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
    'BSS': ('BSS138-7-F', 'BSS138-7-F', 'C40912', 'zudo-pd:SOT-23_DIODES-DS30144-SUGGESTED'),
    'PFET': ('DMP3036SFG-7', 'DMP3036SFG-7', 'C461081', 'zudo-pd:PowerDI3333-8_DMP3036SFG'),
    'Z11': ('BZT52C11-7-F_C92321', 'BZT52C11-7-F', 'C92321', 'zudo-pd:SOD-123_L2.8-W1.8-LS3.7-RD'),
    'C10U50': ('GRM32ER71H106KA12L', '10uF 50V X7R', 'C77102', 'zudo-pd:C1210'),
    'C47P': ('25SVPF47M', '47uF 25V polymer', 'C136280', 'zudo-pd:CAP-SMD_BD6.3-L6.6-W6.6-FD'),
    'C100U': ('RVT1H101M0810', '100uF 50V', 'C970687', 'zudo-pd:CAP-SMD_BD8.0-L8.3-W8.3-LS9.0-FD'),
    'C100N': ('CC0603KRX7R9BB104', '100nF/50V', 'C14663', 'zudo-pd:C0603'),
    'C1U': ('CL10A105KB8NNNC', '1uF 50V', 'C15849', 'zudo-pd:C0603'),
    'C470N': ('CL10B474KA8NNNC', '470nF', 'C1623', 'zudo-pd:C0603'),
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
    'AP63': ('AP63201WU-7', 'AP63201WU-7', 'C2071044', 'zudo-pd:TSOT-23-6_L2.9-W1.6-P0.95-LS2.8-BR'),
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
def buck(n, u, raw, pre, rt_top, rc, cc, chf):
    part(u, 'TPS', ('1', f'{n}_BOOT'), ('2', 'VIN'), ('3', f'{n}_EN'), ('4', f'{n}_RT'), ('5', f'{n}_FB'),
         ('6', f'{n}_COMP'), ('7', 'GND'), ('8', f'{n}_SW'), ('9', 'GND'))
    two(f'C{n}IN', 'C10U50', 'VIN', 'GND')
    two(f'C{n}BT', 'C100N', f'{n}_BOOT', f'{n}_SW')
    two(f'R{n}RT', 'RP174K', f'{n}_RT', 'GND')
    rprop(f'R{n}EN1', '470k 1%', 'VIN', f'{n}_EN')
    rprop(f'R{n}EN2', '39k 1%', f'{n}_EN', 'GND')
    rprop(f'R{n}CP', rc, f'{n}_COMP', f'{n}_CZ')
    cprop(f'C{n}CP', cc, f'{n}_CZ', 'GND')
    cprop(f'C{n}HF', chf, f'{n}_COMP', 'GND')
    rprop(f'R{n}FT', rt_top, raw, f'{n}_FB')
    two(f'R{n}FB', 'RP10K', f'{n}_FB', 'GND')
    two(f'L{n}', 'L10U', f'{n}_SW', raw)
    part(f'D{n}', 'DSCH', ('1', f'{n}_SW'), ('2', 'GND'))
    two(f'C{n}O1', 'C10U50', raw, 'GND')
    two(f'C{n}O2', 'C10U50', raw, 'GND')
    two(f'L{n}F', 'L10U', raw, pre)
    part(f'C{n}F1', 'C47P', ('1', pre), ('2', 'GND'))
    two(f'C{n}F2', 'C10U50', pre, 'GND')


buck('A', 'U1', 'P12_RAW', 'P12_PRE', '145k 0.1%', '10k 1%', '6.8nF C0G', '47pF C0G')
buck('B', 'U2', 'P5_RAW', 'P5_PRE', '54.9k 0.1%', '4.02k 1%', '27nF C0G', '150pF C0G')

# U3 inverting buck-boost: IC GND and PAD on M12_RAW, inductor to system GND
part('U3', 'TPS', ('1', 'C_BOOT'), ('2', 'VIN'), ('3', 'C_EN'), ('4', 'C_RT'), ('5', 'C_FB'),
     ('6', 'C_COMP'), ('7', 'M12_RAW'), ('8', 'C_SW'), ('9', 'M12_RAW'))
two('CCIN1', 'C10U50', 'VIN', 'M12_RAW')
two('CCIN2', 'C10U50', 'VIN', 'M12_RAW')
two('CCBT', 'C100N', 'C_BOOT', 'C_SW')
two('RCRT', 'RP174K', 'C_RT', 'M12_RAW')
rprop('RCEN1', '470k 1%', 'VIN', 'C_EN')
rprop('RCEN2', '39k 1%', 'C_EN', 'M12_RAW')
rprop('RCCP', '8.2k 1%', 'C_COMP', 'C_CZ')
cprop('CCCP', '47nF C0G', 'C_CZ', 'M12_RAW')
cprop('CCHF', '150pF C0G', 'C_COMP', 'M12_RAW')
rprop('RCFT', '145k 0.1%', 'GND', 'C_FB')
two('RCFB', 'RP10K', 'C_FB', 'M12_RAW')
two('LC', 'L10U', 'C_SW', 'GND')
part('DC', 'DSCH', ('1', 'C_SW'), ('2', 'M12_RAW'))
for i in range(1, 5):
    two(f'CCO{i}', 'C10U50', 'GND', 'M12_RAW')
two('LCF', 'L10U', 'M12_RAW', 'M12_PRE')
part('CCF1', 'C47P', ('1', 'GND'), ('2', 'M12_PRE'))
two('CCF2', 'C10U50', 'GND', 'M12_PRE')

# ---------------------------------------------------------------- supervisory supply P5_SUP
# AP63201WU-7: 1 FB, 2 EN, 3 VIN, 4 GND, 5 SW, 6 BST; 0.8 V x (1 + 52.3k / 10k) = 4.98 V
part('U14', 'AP63', ('1', 'SUP_FB'), ('2', 'VIN'), ('3', 'VIN'), ('4', 'GND'), ('5', 'SUP_SW'), ('6', 'SUP_BST'))
two('CSIN', 'C10U50', 'VIN', 'GND')
two('CSBT', 'C100N', 'SUP_BST', 'SUP_SW')
two('LS', 'L10U', 'SUP_SW', 'P5_SUP')
two('CSO1', 'C10U50', 'P5_SUP', 'GND')
two('CSO2', 'C10U50', 'P5_SUP', 'GND')
part('CSO3', 'C47P', ('1', 'P5_SUP'), ('2', 'GND'))
rprop('RSFT', '52.3k 0.1%', 'P5_SUP', 'SUP_FB')
two('RSFB', 'RP10K', 'SUP_FB', 'GND')

# ---------------------------------------------------------------- reference
part('U10', 'REF', ('1', None), ('2', 'P5_SUP'), ('3', None), ('4', 'GND'), ('5', 'REF_NR'),
     ('6', 'REF25'), ('7', None), ('8', None))
two('C10IN', 'C1U', 'P5_SUP', 'GND')
two('C10NR', 'C1U', 'REF_NR', 'GND')
two('C10O', 'C10U1206', 'REF25', 'GND')

# ---------------------------------------------------------------- servo loops (sense after the shunt)
# +12: 12.1517 V = 2.5 x (1 + 15.52k / 4.02k)
two('RS1A', 'RP11K5', 'P12_SH', 'S12_X')
two('RS1B', 'RP4K02', 'S12_X', 'S12')
two('RS1C', 'RP4K02', 'S12', 'GND')
# +5: 5.0840 V = 2.5 x (1 + 184k / 178.02k)
two('RS2A', 'RP174K', 'P5_SH', 'S5_X')
two('RS2B', 'RP10K', 'S5_X', 'S5')
two('RS2C', 'RP174K', 'S5', 'S5_Y')
two('RS2D', 'RP4K02', 'S5_Y', 'GND')
opa('U4', 'P5_SUP', 'GND', ('S12', 'I12_N', 'SV12'), ('S5', 'I5_N', 'SV5'))
two('C4D', 'C100N', 'P5_SUP', 'GND')
rprop('RI12', '100k 0.1%', 'REF25', 'I12_N')
cprop('CI12', '1.5nF C0G', 'SV12', 'I12_N')
rprop('RJ12', '1M 1%', 'SV12', 'A_FB')
rprop('RI5', '100k 0.1%', 'REF25', 'I5_N')
cprop('CI5', '1.5nF C0G', 'SV5', 'I5_N')
rprop('RJ5', '1M 1%', 'SV5', 'B_FB')
# -12: |V| = 2.5 x 34.5k / 7.11k = 12.1308 V at M12_SH; S12N = 0 V at the setpoint
two('RS3A', 'RP3K09', 'REF25', 'S12N_X')
two('RS3B', 'RP4K02', 'S12N_X', 'S12N')
two('RS3C', 'RP11K5', 'S12N', 'S12N_Y')
two('RS3D', 'RP11K5', 'S12N_Y', 'S12N_Z')
two('RS3E', 'RP11K5', 'S12N_Z', 'M12_SH')
rprop('RI12N', '100k 0.1%', 'S12N', 'I12N_N')
opa('U5', 'P5_SUP', 'M12_PRE', ('GND', 'I12N_N', 'SV12N'), ('REF125', 'VIN_DIV', 'VINUV_CMP'))
two('C5DP', 'C100N', 'P5_SUP', 'GND')
two('C5DN', 'C100N', 'GND', 'M12_PRE')
cprop('CI12N', '270pF C0G', 'SV12N', 'I12N_N')
rprop('RJ12N', '4.7M 1%', 'SV12N', 'C_FB')
# VIN undervoltage at 16.95 V: 1.25 V at VIN_DIV
two('RVR1', 'RP8K2', 'REF25', 'REF125')
two('RVR2', 'RP8K2', 'REF125', 'GND')
rprop('RVU1', '221k 0.1%', 'VIN', 'VIN_DIV')
rprop('RVU2', '17.6k 0.1%', 'VIN_DIV', 'GND')
nfet('Q40', 'VINUV_CMP', 'GND', 'FAULT_N')

# ---------------------------------------------------------------- shunts, limiters
# Phase 9: +12 / -12 use one 10 mOhm 0.1 % 15 ppm/C 2512 shunt (RESI PCSR2512BR010M6 C23067428,
# distributor listing only, no owner record) so the trip minimum clears the start-into-full-load
# floor (2.0327 / 1.9289 A); +5 keeps the PE1206 20 mOhm part.
rprop('RSH1', '10mR 0.1% 2512 PCSR2512BR010M6', 'P12_PRE', 'P12_SH', fp='zudo-pd:R2512_DRAFT')
two('RSH2', 'SHUNT', 'P5_PRE', 'P5_SH')
rprop('RSH3', '10mR 0.1% 2512 PCSR2512BR010M6', 'M12_SH', 'M12_PRE', fp='zudo-pd:R2512_DRAFT')
# LIMIT = REF25 x Rb / (Ra + Rb) + ILIMIT (80 uA) x (Ra || Rb)
part('U11', 'INA', ('1', 'P5_SUP'), ('2', None), ('3', 'LIM12'), ('4', 'GND'), ('5', 'GND'),
     ('6', 'FAULT_N'), ('7', 'P12_SH'), ('8', 'P12_PRE'))
two('C11D', 'C100N', 'P5_SUP', 'GND')
rprop('RL1A', '649 0.1%', 'REF25', 'LIM12')
rprop('RL1B', '2.74k 0.1%', 'LIM12', 'GND')
part('U12', 'INA', ('1', 'P5_SUP'), ('2', None), ('3', 'LIM5'), ('4', 'GND'), ('5', 'GND'),
     ('6', 'FAULT_N'), ('7', 'P5_SH'), ('8', 'P5_PRE'))
two('C12D', 'C100N', 'P5_SUP', 'GND')
two('RL2A', 'RP3K09', 'REF25', 'LIM5')
rprop('RL2B', '1.5k 0.1%', 'LIM5', 'GND')
# -12 limiter: trip when M12_SH - M12_PRE > 33 / 20333 x |M12_PRE|
rprop('RL3A', '10.2k 0.1%', 'GND', 'LIM12N_X')
rprop('RL3B', '10.1k 0.1%', 'LIM12N_X', 'LIM12N')
two('RL3C', 'RP33', 'LIM12N', 'M12_PRE')
# U9B is the -12 tracking amplifier (see below)
opa('U9', 'P5_SUP', 'M12_PRE', ('M12_SH', 'LIM12N', 'ILIM12N_CMP'), ('TRK12N', 'TRK12N_FB', 'M12_DRV'))
two('C9DP', 'C100N', 'P5_SUP', 'GND')
two('C9DN', 'C100N', 'GND', 'M12_PRE')
nfet('Q41', 'ILIM12N_CMP', 'GND', 'FAULT_N')

# ---------------------------------------------------------------- common tracking reference
rprop('RRMP', '20k 0.1%', 'REF25', 'RAMP')
two('CRMP', 'C1U', 'RAMP', 'GND')
two('CRMP2', 'C470N', 'RAMP', 'GND')   # phase 9: 1.47 uF keeps every clamped slope in the contract
two('RRMD', 'R100K', 'EN_N', 'RAMP_RST')
two('CRMD', 'C100N', 'RAMP_RST', 'GND')
nfet('Q12', 'RAMP_RST', 'GND', 'RAMP')

# ---------------------------------------------------------------- output switches, tracked
# +12 = (1 + 69.8k / 10k) x RAMP and +5 = (1 + 23.2k / 10k) x RAMP; U13 runs from VIN.
# Pre-bias start: while disabled, Q24 (M12_OFFX at P5_SUP) pulls each inverting input up
# through 100k and a BSS138 body diode (Q59-Q61), so every amplifier rests at its low rail.
# At enable the gates are released at once, but RAMP stays reset for 12-23 ms (RRMD/CRMD);
# the 10M offsets to M12_PRE set small targets (+85 mV, +28 mV, -52 mV), so each loop
# brings its pair to the edge of conduction before RAMP moves (no dead-zone wind-up).
# Phase-7 ngspice runs: 1 nF integrators limit-cycled at no load (-12 V stepped at up to
# 6.9 V/ms with 1.2-1.6 A pulses); 10 nF, plus a 10k damping zero on the -12 V loop,
# gives smooth ramps (see manufacturing/board-b-20v-switcher-direct-draft.md section 5).
opa('U13', 'VIN', 'GND', ('RAMP_P12', 'TRK12', 'P12_DRV'), ('RAMP_P5', 'TRK5', 'P5_DRV'))
two('C13D', 'C100N', 'VIN', 'GND')
rprop('RT12A', '69.8k 0.1%', 'P12_OUT', 'TRK12')
two('RT12B', 'RP10K', 'TRK12', 'GND')
cprop('CT12', '10nF C0G', 'P12_DRV', 'TRK12')
rprop('RT12O', '10M 1%', 'M12_PRE', 'TRK12')
two('RT12P', 'R100K', 'M12_OFFX', 'TRK12_PX')
nfet('Q59', 'TRK12_PX', 'TRK12_PX', 'TRK12')
rprop('RT5A', '23.2k 0.1%', 'P5_OUT', 'TRK5')
two('RT5B', 'RP10K', 'TRK5', 'GND')
cprop('CT5', '10nF C0G', 'P5_DRV', 'TRK5')
rprop('RT5O', '10M 1%', 'M12_PRE', 'TRK5')
two('RT5P', 'R100K', 'M12_OFFX', 'TRK5_PX')
nfet('Q60', 'TRK5_PX', 'TRK5_PX', 'TRK5')
# -12: TRK12N = 0 V when M12_OUT = -(806k / 100k) x RAMP
rprop('RT12NA', '100k 0.1%', 'RAMP_M12', 'TRK12N')
rprop('RT12NB', '806k 0.1%', 'TRK12N', 'M12_OUT')
two('RT12NC', 'R4K7', 'TRK12N_FB', 'GND')
cprop('CT12N', '10nF C0G', 'M12_DRV', 'TRK12N_Z')
rprop('RT12NZ', '10k 1%', 'TRK12N_Z', 'TRK12N_FB')
rprop('RT12NO', '10M 1%', 'M12_PRE', 'TRK12N_FB')
two('RT12NP', 'R100K', 'M12_OFFX', 'TRK12N_PX')
nfet('Q61', 'TRK12N_PX', 'TRK12N_PX', 'TRK12N_FB')
# Phase 9 start-order clamps (drawn, PROPOSED values): each tracking reference is min(RAMP, level) through a
# precision clamp (OPA2187 + BSS138 body diode pulling RAMP_x down through 1k from RAMP).
#   MABS  = 0.150 x |M12_OUT|                                  (U15A inverting, 15k / 100k)
#   +12 level = 0.9182 x MABS + 0.0818 x 0.6234 V  ->  V(+12) <= 1.099 x |-12| + 0.407 V
#   -12 level = 0.13582 x V(+12)                   ->  |-12| <= 1.095 x V(+12)
#   +5  level = MABS                               ->  V(+5) <= 0.498 x |-12|
# so -12 cannot start before +12, +12 alone stays <= 0.41 V, and +5 stays <= 0.8 V until
# |-12| >= 1.61 V (and +12 >= 1.45 V). See manufacturing/board-b-20v-switcher-direct-draft.md 5b.
# U15/U16 run from P5_SUP / M12_PRE like U9: with a GND negative rail the clamp output could not
# pull a RAMP_x node below one body-diode drop (about 0.4 V), which would let |-12| reach about
# 3 V while +12 is still at 0 V.
opa('U15', 'P5_SUP', 'M12_PRE', ('GND', 'MABS_N', 'MABS'), ('LVL12', 'RAMP_P12', 'CLP12_O'))
two('C15D', 'C100N', 'P5_SUP', 'GND')
two('C15DN', 'C100N', 'GND', 'M12_PRE')
rprop('RMA1', '100k 0.1%', 'M12_OUT', 'MABS_N')
rprop('RMA2', '15k 0.1%', 'MABS_N', 'MABS')
rprop('RLV1', '8.87k 0.1%', 'MABS', 'LVL12')
rprop('RLV2', '92k 0.1%', 'LVL12', 'VX12')
rprop('RVX1', '30.1k 0.1%', 'REF25', 'VX12')
two('RVX2', 'RP10K', 'VX12', 'GND')
opa('U16', 'P5_SUP', 'M12_PRE', ('LVLM12', 'RAMP_M12', 'CLPM12_O'), ('MABS', 'RAMP_P5', 'CLP5_O'))
two('C16D', 'C100N', 'P5_SUP', 'GND')
two('C16DN', 'C100N', 'GND', 'M12_PRE')
rprop('RLM1', '64.9k 0.1%', 'P12_OUT', 'LVLM12')
rprop('RLM2', '10.2k 0.1%', 'LVLM12', 'GND')
two('RCP1', 'R1K', 'RAMP', 'RAMP_P12')
two('RCP2', 'R1K', 'RAMP', 'RAMP_M12')
two('RCP3', 'R1K', 'RAMP', 'RAMP_P5')
nfet('Q62', 'RAMP_P12', 'RAMP_P12', 'CLP12_O')   # body diode RAMP_P12 -> CLP12_O
nfet('Q63', 'RAMP_M12', 'RAMP_M12', 'CLPM12_O')
nfet('Q64', 'RAMP_P5', 'RAMP_P5', 'CLP5_O')
# +12 pair
power_nfet('Q1', 'P12_CS', 'P12_G', 'P12_SH')
power_nfet('Q2', 'P12_CS', 'P12_G', 'P12_OUT')
zener('DZ1', 'P12_G', 'P12_CS')
two('RG1', 'R10K0805', 'P12_DRV', 'P12_G')
two('RG1P', 'R100K', 'P12_G', 'P12_CS')
nfet('Q10', 'EN_N', 'GND', 'P12_G')
# +5 pair
power_nfet('Q3', 'P5_CS', 'P5_G', 'P5_SH')
power_nfet('Q4', 'P5_CS', 'P5_G', 'P5_OUT')
zener('DZ2', 'P5_G', 'P5_CS')
two('RG2', 'R10K0805', 'P5_DRV', 'P5_G')
two('RG2P', 'R100K', 'P5_G', 'P5_CS')
nfet('Q11', 'EN_N', 'GND', 'P5_G')
# -12 pair; disable pulldown through a P5_SUP-referenced level shifter
power_nfet('Q5', 'M12_CS', 'M12_G', 'M12_SH')
power_nfet('Q6', 'M12_CS', 'M12_G', 'M12_OUT')
zener('DZ3', 'M12_G', 'M12_CS')
two('RG3', 'R10K0805', 'M12_DRV', 'M12_G')
two('RG3P', 'R100K', 'M12_G', 'M12_CS')
pfet('Q24', 'P5_SUP', 'EN_E', 'M12_OFFX')
two('RG3A', 'R56K', 'M12_OFFX', 'M12_OFF')
two('RG3B', 'R100K', 'M12_OFF', 'M12_PRE')
nfet('Q25', 'M12_OFF', 'M12_PRE', 'M12_G')

# ---------------------------------------------------------------- windows (terminal sense)
# +12: OV 12.39 V, UV 11.765 V; +5: OV 5.15 V, UV 4.93 V (2.5 V at the divider node)
for rail, out, ovt, ovb, uvt, uvb, u in (('12', 'P12_OUT', '54.2k 0.1%', '13.7k 0.1%', '232k 0.1%', '62.6k 0.1%', 'U6'),
                                         ('5', 'P5_OUT', '10.6k 0.1%', '10k 0.1%', '10.4k 0.1%', '10.7k 0.1%', 'U7')):
    rprop(f'ROV{rail}A', ovt, out, f'OV{rail}_DIV')
    rprop(f'ROV{rail}B', ovb, f'OV{rail}_DIV', 'GND')
    rprop(f'RUV{rail}A', uvt, out, f'UV{rail}_DIV')
    rprop(f'RUV{rail}B', uvb, f'UV{rail}_DIV', 'GND')
    opa(u, 'P5_SUP', 'GND', (f'OV{rail}_DIV', 'REF25', f'OV{rail}_CMP'), ('REF25', f'UV{rail}_DIV', f'UV{rail}_CMP'))
    two(f'C{u}D', 'C100N', 'P5_SUP', 'GND')
nfet('Q42', 'OV12_CMP', 'GND', 'FAULT_N')
nfet('Q43', 'UV12_CMP', 'ARM_GND', 'FAULT_N')
nfet('Q44', 'OV5_CMP', 'GND', 'FAULT_N')
nfet('Q45', 'UV5_CMP', 'ARM_GND', 'FAULT_N')
# -12: node = 0 V at the threshold; OV |V| 12.285 V, UV |V| 11.87 V
rprop('ROVNA', '40.7k 0.1%', 'REF25', 'OVN_DIV')
rprop('ROVNB', '200k 0.1%', 'OVN_DIV', 'M12_OUT')
rprop('RUVNA', '41.7k 0.1%', 'REF25', 'UVN_DIV')
rprop('RUVNB', '198k 0.1%', 'UVN_DIV', 'M12_OUT')
opa('U8', 'P5_SUP', 'M12_PRE', ('GND', 'OVN_DIV', 'OVN_CMP'), ('UVN_DIV', 'GND', 'UVN_CMP'))
two('C8DP', 'C100N', 'P5_SUP', 'GND')
two('C8DN', 'C100N', 'GND', 'M12_PRE')
nfet('Q46', 'OVN_CMP', 'GND', 'FAULT_N')
nfet('Q47', 'UVN_CMP', 'ARM_GND', 'FAULT_N')

# ---------------------------------------------------------------- fault latch, enable latch, timing
two('RF1', 'R10K0805', 'P5_SUP', 'FAULT_N')
two('CF1', 'C100N', 'P5_SUP', 'FAULT_N')
nfet('Q30', 'FLT_L', 'GND', 'FAULT_N')
pfet('Q31', 'P5_SUP', 'FAULT_N', 'FLT_LX')
two('RF2', 'R4K7', 'FLT_LX', 'FLT_L')
two('RF3', 'R100K', 'FLT_L', 'GND')
two('CF3', 'C100N', 'FLT_L', 'GND')
# power-on reset: POR_H high for 10-36 ms holds FLT_L low
two('RP1', 'R100K', 'P5_SUP', 'POR_N')
two('CP1', 'C1U', 'POR_N', 'GND')
nfet('Q35', 'POR_N', 'GND', 'POR_H')
two('RP2', 'R100K', 'P5_SUP', 'POR_H')
nfet('Q32', 'POR_H', 'GND', 'FLT_L')
# PDOK (Board P open drain, low = contract valid, UNSOURCED polarity) -> RDY after 0.21-0.71 s
two('RPD', 'R10K0805', 'P5_SUP', 'PDOK')
nfet('Q36', 'PDOK', 'GND', 'RDY')
two('RRDY1', 'R100K', 'P5_SUP', 'RDY_X')
two('RRDY2', 'R100K', 'RDY_X', 'RDY')
two('CRDY', 'C10U1206', 'RDY', 'GND')
# enable latch: EN_N low = enabled; set by RDY while FAULT_N high, reset by FLT_L
two('REN', 'R10K0805', 'P5_SUP', 'EN_N')
nfet('Q37', 'RDY', 'EN_SET', 'EN_N')
nfet('Q38', 'FAULT_N', 'GND', 'EN_SET')
nfet('Q33', 'EN_E', 'GND', 'EN_N')
pfet('Q34', 'P5_SUP', 'EN_N', 'EN_EX')
two('RE1', 'R4K7', 'EN_EX', 'EN_E')
two('RE2', 'R100K', 'EN_E', 'GND')
nfet('Q39', 'FLT_L', 'GND', 'EN_E')
# ARM: rises 0.1-0.36 s after enable; gates UV and PDOK-loss faults
two('RARM', 'R100K', 'P5_SUP', 'ARM')
two('CARM', 'C10U1206', 'ARM', 'GND')
nfet('Q48', 'EN_N', 'GND', 'ARM')
nfet('Q49', 'ARM', 'GND', 'ARM_GND')
nfet('Q50', 'PDOK', 'ARM_GND', 'FAULT_N')

# ---------------------------------------------------------------- discharge with hold-up
# CDH charges from EN_E through the Q57 body diode (gate and source on EN_E) and RDH only
# while enabled; when EN_E falls, Q56 / Q54 turn on from CDH alone.
nfet('Q57', 'EN_E', 'EN_E', 'DH_X')
two('RDH', 'R56K', 'DH_X', 'DIS_C')
two('CDH', 'C10U1206', 'DIS_C', 'GND')
pfet('Q56', 'DIS_C', 'EN_E', 'DIS_P')
two('R60', 'R100K', 'DIS_P', 'GND')
nfet('Q51', 'DIS_P', 'GND', 'P12_DX')
rprop('RX12', '100 1% 1206', 'P12_DX', 'P12_OUT', fp='zudo-pd:R1206_DRAFT')
nfet('Q52', 'DIS_P', 'GND', 'P5_DX')
rprop('RX5', '33 1% 1206', 'P5_DX', 'P5_OUT', fp='zudo-pd:R1206_DRAFT')
pfet('Q54', 'DIS_C', 'EN_E', 'M12_DGX')
rprop('R61', '470k 1%', 'M12_DGX', 'M12_DG')
rprop('R62', '1M 1%', 'M12_DG', 'M12_OUT')
nfet('Q55', 'M12_DG', 'M12_OUT', 'M12_DX')
rprop('RXN', '150 1% 1206', 'GND', 'M12_DX', fp='zudo-pd:R1206_DRAFT')


# VIN arrives from Board P through J5 and GND is the system return; these flags declare the
# external source role for ERC only (no PCB or BOM part).
ERC_POWER_FLAGS = {
    'GND': (25.4, 800.1),
    'VIN': (76.2, 800.1),
}


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
