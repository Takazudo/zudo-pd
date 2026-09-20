"""Shared net naming and exact-part footprint synchronization for PCB scripts."""

import copy
import json
import uuid


def pcb_net_name(name):
    return name.replace('/', '{slash}')


def serialize(node):
    if isinstance(node, list):
        return '(' + ' '.join(serialize(value) for value in node) + ')'
    return json.dumps(node[1], ensure_ascii=False) if node[0] == 'str' else node[1]


def sync_lcsc_aliases(tree, components):
    """Keep imported footprint supplier aliases consistent with the owning spec."""
    from sexp import atom, find_all
    changes = []
    for fp in find_all(tree, 'footprint'):
        properties = {atom(prop[1]): prop for prop in find_all(fp, 'property')}
        ref = atom(properties['Reference'][2])
        if ref not in components:
            continue
        lcsc = components[ref][2]
        for field in ('LCSC', 'LCSC Part', 'LCSC Part #', 'JLCPCB Part #'):
            if field in properties and atom(properties[field][2]) != lcsc:
                changes.append((ref, field, atom(properties[field][2]), lcsc))
                properties[field][2] = ('str', lcsc)
    return changes


def sync_surface_part(tree, ref, component, library, board_name):
    """Replace a top-side part's exact lands while preserving position and nets.

This deliberately supports the two-terminal protection parts only. Native DRC
must check the changed lands against existing traces after synchronization.
"""
    from sexp import atom, find_all, load
    matches = [fp for fp in find_all(tree, 'footprint')
               if any(atom(prop[1]) == 'Reference' and atom(prop[2]) == ref
                      for prop in find_all(fp, 'property'))]
    assert len(matches) == 1, ref
    fp = matches[0]
    assert atom(find_all(fp, 'layer')[0][1]) == 'F.Cu', 'Only top-side protection parts are supported'
    old_pads = {atom(pad[1]): pad for pad in find_all(fp, 'pad')}
    assert set(old_pads) == {'1', '2'}, 'Review any changed terminal count'
    _, value, lcsc, footprint, dnp, _ = component
    assert not dnp
    canonical = load(library / (footprint.split(':', 1)[1] + '.kicad_mod'))
    assert atom(canonical[0]) == 'footprint', 'Use a modern native footprint file'
    new_pads = find_all(canonical, 'pad')
    assert {atom(pad[1]) for pad in new_pads} == set(old_pads)
    at = find_all(fp, 'at')[0]
    rotation = float(atom(at[3])) if len(at) > 3 else 0
    geometry_tags = {'pad', 'fp_line', 'fp_rect', 'fp_arc', 'fp_circle', 'fp_poly', 'fp_text', 'model'}
    fp[:] = [node for node in fp if not (isinstance(node, list) and node and atom(node[0]) in geometry_tags)]
    fp[1] = ('str', footprint)
    properties = {atom(prop[1]): prop for prop in find_all(fp, 'property')}
    properties['Value'][2] = ('str', value)
    assert 'LCSC' in properties
    for field in ('LCSC', 'LCSC Part', 'LCSC Part #', 'JLCPCB Part #'):
        if field in properties:
            properties[field][2] = ('str', lcsc)
    for index, original in enumerate(canonical):
        if not isinstance(original, list) or not original or atom(original[0]) not in geometry_tags:
            continue
        node = copy.deepcopy(original)
        tag = atom(node[0])
        if tag == 'fp_text' and atom(node[1]) in ('reference', 'value'):
            continue
        if tag == 'fp_text' and atom(node[2]) == '%R':
            node[2] = ('str', '${REFERENCE}')
        for width in find_all(node, 'width'):
            node.remove(width)
            node.append([('atom', 'stroke'), width, [('atom', 'type'), ('atom', 'solid')]])
        # Library UUIDs must not collide with any other placed instance.
        node[:] = [child for child in node if not (isinstance(child, list) and child and atom(child[0]) in ('uuid', 'tstamp'))]
        if tag != 'model':
            node.append([('atom', 'uuid'), ('str', str(uuid.uuid5(uuid.NAMESPACE_URL, f'{board_name}:{ref}:{footprint}:{index}')))])
        if tag in ('pad', 'fp_text'):
            position = find_all(node, 'at')[0]
            local_angle = float(atom(position[3])) if len(position) > 3 else 0
            position[3:] = [('atom', str((local_angle + rotation) % 360))]
        if tag == 'pad':
            number = atom(node[1])
            old_net = find_all(old_pads[number], 'net')
            assert len(old_net) == 1, f'{ref}.{number}: missing net'
            assert not find_all(node, 'net'), 'Canonical pad must not carry a board net'
            node.append(copy.deepcopy(old_net[0]))
        fp.append(node)
