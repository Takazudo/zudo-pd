"""Exact native pad-to-filled-polygon contacts used by the ground-cluster check."""


def pad_polygon_contacts(pads, polygons, polygon_sets):
    """Yield contacts including pad-edge overlap when the pad center is outside fill.

    Callers must group pads and polygons by the same net. polygon_sets retain holes. A bounding-box overlap or a same-net label alone
    is insufficient: KiCad's effective copper shape must collide with filled copper.
    """
    for pad_index, pad in enumerate(pads):
        for polygon_index, (layer, _outline) in enumerate(polygons):
            if pad.IsOnLayer(layer) and polygon_sets[polygon_index].Collide(pad.GetEffectiveShape(layer), 0):
                yield pad_index, polygon_index
