#!/usr/bin/env python3
"""Fail-closed numeric orientation audit for the ST-LINK/V2 SWD adapter."""

from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

import board_l_spec
import swd_adapter_spec
from sexp import atom, find_all, load


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def mapping_from_spec(spec, ref):
    result = {}
    for net_name, nodes in spec.NETS.items():
        for node in nodes:
            node_ref, pin = node.split('.')
            if node_ref == ref:
                result[pin] = net_name
    for node in spec.NO_CONNECT:
        node_ref, pin = node.split('.')
        if node_ref == ref:
            result[pin] = 'NC'
    return result


def reference_of(footprint):
    for prop in find_all(footprint, 'property'):
        if atom(prop[1]) == 'Reference':
            return atom(prop[2])
    raise AssertionError('PCB footprint has no Reference property')


def pcb_pad_map(path):
    board = load(path)
    footprints = find_all(board, 'footprint')
    require(len(footprints) == 2, f'adapter PCB must contain exactly two footprints, got {len(footprints)}')
    result = {}
    geometry = {}
    library_ids = {}
    rotations = {}
    for footprint in footprints:
        ref = reference_of(footprint)
        require(ref in {'J1', 'J2'}, f'unexpected adapter footprint {ref}')
        library_ids[ref] = atom(footprint[1])
        at = find_all(footprint, 'at')[0]
        rotations[ref] = float(atom(at[3])) if len(at) > 3 else 0.0
        result[ref] = {}
        geometry[ref] = {}
        for pad in find_all(footprint, 'pad'):
            number = atom(pad[1])
            shape = atom(pad[3])
            pad_at = find_all(pad, 'at')[0]
            net = find_all(pad, 'net')
            result[ref][number] = atom(net[0][1]) if net else 'NC'
            geometry[ref][number] = (shape, float(atom(pad_at[1])), float(atom(pad_at[2])))
    require(rotations == {'J1': 0.0, 'J2': 0.0}, f'connector rotations changed: {rotations}')
    return result, geometry, library_ids


def pad_geometry(path):
    footprint = load(path)
    pads = {}
    for pad in find_all(footprint, 'pad'):
        number = atom(pad[1])
        shape = atom(pad[3])
        at = find_all(pad, 'at')[0]
        pads[number] = (shape, float(atom(at[1])), float(atom(at[2])))
    return footprint, pads


expected_j1 = {
    '1': 'VAPP', '2': 'VAPP',
    '3': 'GND', '4': 'GND', '5': 'GND', '6': 'GND',
    '7': 'SWDIO', '8': 'GND', '9': 'SWCLK', '10': 'GND',
    '11': 'NC', '12': 'GND', '13': 'NC', '14': 'GND',
    '15': 'NRST', '16': 'GND', '17': 'NC', '18': 'GND',
    '19': 'NC', '20': 'GND',
}
expected_j2 = {'1': 'SWDIO', '2': 'SWCLK', '3': 'NRST', '4': 'VAPP', '5': 'GND'}
expected_board_l_j3 = {'1': 'SWDIO', '2': 'SWCLK', '3': 'NRST', '4': 'V3P3', '5': 'GND'}

require(mapping_from_spec(swd_adapter_spec, 'J1') == expected_j1, 'adapter schematic J1 mapping drifted')
require(mapping_from_spec(swd_adapter_spec, 'J2') == expected_j2, 'adapter schematic J2 mapping drifted')
require(mapping_from_spec(board_l_spec, 'J3') == expected_board_l_j3, 'Board L J3 order drifted')

pcb, pcb_geometry, pcb_library_ids = pcb_pad_map(
    ROOT / 'boards/swd-adapter/swd-adapter.kicad_pcb'
)
require(
    pcb_library_ids == {
        'J1': 'zudo-led-lamp:IDC-TH_20P-P2.54-V-R2-C10-S2.54',
        'J2': 'zudo-led-lamp:HDR-TH_5P-P2.54-V-M',
    },
    f'adapter PCB footprint assignment drifted: {pcb_library_ids}',
)
for ref, expected in (('J1', expected_j1), ('J2', expected_j2)):
    actual = {
        pin: ('NC' if net.startswith('unconnected-') else net)
        for pin, net in pcb[ref].items()
    }
    require(actual == expected, f'adapter PCB {ref} pad/net mapping drifted: {actual}')

j1_tree, j1_pads = pad_geometry(
    ROOT / 'footprints/kicad/IDC-TH_20P-P2.54-V-R2-C10-S2.54.kicad_mod'
)
require(len(j1_pads) == 20, 'J1 canonical footprint must have 20 pads')
require(j1_pads['1'] == ('rect', -11.43, 1.27), f'J1 pin 1 geometry drifted: {j1_pads["1"]}')
require(j1_pads['2'] == ('circle', -11.43, -1.27), f'J1 pin 2 geometry drifted: {j1_pads["2"]}')
require(j1_pads['19'] == ('circle', 11.43, 1.27), f'J1 pin 19 geometry drifted: {j1_pads["19"]}')
require(j1_pads['20'] == ('circle', 11.43, -1.27), f'J1 pin 20 geometry drifted: {j1_pads["20"]}')
require(pcb_geometry['J1'] == j1_pads, 'J1 PCB pad geometry differs from the canonical footprint')
key_text = [item for item in find_all(j1_tree, 'fp_text') if len(item) > 2 and atom(item[2]) == 'KEY']
require(len(key_text) == 1, 'J1 shroud key marker is missing or ambiguous')
key_at = find_all(key_text[0], 'at')[0]
require(float(atom(key_at[2])) > j1_pads['1'][2], 'J1 key marker is no longer on the pin-1/odd-row side')

_, j2_pads = pad_geometry(ROOT / 'footprints/kicad/HDR-TH_5P-P2.54-V-M.kicad_mod')
require(j2_pads['1'] == ('rect', -5.08, 0.0), f'J2 pin 1 geometry drifted: {j2_pads["1"]}')
require(j2_pads['5'] == ('circle', 5.08, 0.0), f'J2 pin order drifted: {j2_pads["5"]}')
require(pcb_geometry['J2'] == j2_pads, 'J2 PCB pad geometry differs from the canonical footprint')

end_to_end = {'7': '1', '9': '2', '15': '3', '1': '4', '2': '4'}
for j1_pin, one_by_five_pin in end_to_end.items():
    require(expected_j1[j1_pin] == expected_j2[one_by_five_pin], f'J1.{j1_pin} does not reach J2.{one_by_five_pin}')
    board_l_net = expected_board_l_j3[one_by_five_pin]
    require(
        board_l_net == expected_j2[one_by_five_pin] or (board_l_net, expected_j2[one_by_five_pin]) == ('V3P3', 'VAPP'),
        f'J2.{one_by_five_pin} does not reach the intended Board L J3 pin',
    )
require(expected_j1['19'] == 'NC', 'ST-LINK/V2 3.3 V output pin 19 must remain isolated')

print('PASS: SWD adapter numeric orientation; 20-pin ribbon -> J1 -> PCB -> J2 -> straight cable -> Board L J3')
