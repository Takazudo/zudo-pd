"""Required review coverage independent of mutable geometry metadata."""
from collections import Counter


def validate_coverage(pours, constraints):
    required = {'U2.21': ('GND', 4), 'Q1.9': ('VBUS_OUT', 4), 'Q3.9': ('EF_IN', 3)}
    vias = [v for v in pours['vias'] if 'thermal_owner' in v]
    counts = Counter(v['thermal_owner'] for v in vias)
    if counts != Counter({owner: count for owner, (_, count) in required.items()}):
        raise ValueError(f'Incomplete or changed R1–R3 review coverage: {counts}')
    if any(v['net'] != required[v['thermal_owner']][0] for v in vias):
        raise ValueError('Thermal owner net contract changed')
    if set(constraints) != {'C30', 'C34'}:
        raise ValueError('R4 requires both C30 and C34')
    for ref, expected in {'C30': ('U1.23', '2'), 'C34': ('U1.21', '1')}.items():
        spec = constraints[ref]
        if (spec['ic_pad'], spec['capacitor_pad']) != expected or not 0 < spec['max_distance_mm'] <= (3.0 if ref == 'C30' else 2.5):
            raise ValueError(f'Changed R4 pin/distance contract: {ref}')
