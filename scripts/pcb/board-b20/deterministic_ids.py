"""Stable native item identities for reproducible B20 zone-fill ordering.

UUIDs are generated metadata, not component identities or electrical contracts.
No position, shape, net, layer, drill or manufacturing setting is changed here.
"""
import collections
import json
import uuid
import pcbnew as p


def stable_id(item, *identity):
    key = 'zudo-pd/board-b20/' + json.dumps(identity, sort_keys=True, separators=(',', ':'))
    item.m_Uuid.Clone(p.KIID(str(uuid.uuid5(uuid.NAMESPACE_URL, key))))


def xy(vector):
    return [int(vector.x), int(vector.y)]


def drawing_key(item):
    key = [item.GetClass(), int(item.GetLayer())]
    if isinstance(item, p.PCB_TEXT):
        key += [item.GetText(), xy(item.GetPosition()), xy(item.GetTextSize()),
                item.GetTextAngle().AsDegrees(), int(item.GetTextThickness()), item.IsMirrored(), item.IsBold()]
    elif item.GetClass() == 'PCB_SHAPE':
        box = item.GetBoundingBox()
        key += [int(item.GetShape()), xy(item.GetStart()), xy(item.GetEnd()), int(item.GetWidth()),
                int(box.GetLeft()), int(box.GetTop()), int(box.GetRight()), int(box.GetBottom())]
    else:
        raise RuntimeError('Unreviewed B20 drawing type for deterministic identity: ' + item.GetClass())
    return key


def drawing_id(item):
    # Board drawings have unique geometry/text in this generator.
    stable_id(item, 'drawing', drawing_key(item), 0)


def builder_ids(board):
    refs = set()
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref in refs:
            raise RuntimeError('Duplicate footprint reference for deterministic identity: ' + ref)
        refs.add(ref)
        stable_id(fp, 'footprint', ref)
        field_names = set()
        for field in fp.GetFields():
            name = field.GetName()
            if name in field_names:
                raise RuntimeError('Duplicate footprint field name for deterministic identity: ' + ref)
            field_names.add(name)
            stable_id(field, 'footprint-field', ref, name)
        counts = collections.Counter()
        for pad in fp.Pads():
            key = [pad.GetNumber(), xy(pad.GetPosition()), xy(pad.GetSize()), xy(pad.GetDrillSize()),
                   pad.GetLayerSet().FmtHex(), int(pad.GetAttribute()), int(pad.GetShape(p.F_Cu))]
            text = json.dumps(key, sort_keys=True)
            stable_id(pad, 'pad', ref, key, counts[text])
            counts[text] += 1
        counts = collections.Counter()
        for item in fp.GraphicalItems():
            key = drawing_key(item)
            text = json.dumps(key, sort_keys=True)
            stable_id(item, 'footprint-graphic', ref, key, counts[text])
            counts[text] += 1
    keys = set()
    for item in board.GetDrawings():
        key = json.dumps(drawing_key(item), sort_keys=True)
        if key in keys:
            raise RuntimeError('Duplicate B20 board drawing identity')
        keys.add(key)
        drawing_id(item)
    for zone in board.Zones():
        if not zone.GetIsRuleArea():
            raise RuntimeError('Builder unexpectedly contains a filled-copper zone')
        stable_id(zone, 'rule-area', zone.GetZoneName(), zone.GetLayerSet().FmtHex())
