#!/usr/bin/env python3
"""Check held LED generated links against both freshly built sites.

This validates historical destinations and private old-host preservation. C3
routes are syntax proposals, not an adoption or redirect instruction.
"""

import csv
import hashlib
import json
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "circuit/orchestration/campaigns"
C1 = CAMPAIGN / "pd-led-20261116-c1/route-map.tsv"
C3 = CAMPAIGN / "pd-led-20261116-c3/route-contract/result.json"
AUDIT = CAMPAIGN / "pd-led-20261117-integration/c5-link-audit.json"
OLD_HOST = "https://zudo-led-lamp.takazudomodular.com"
LOCKS = {
    C1: "e60f2c64b19957f541d36c66db55c7a66528ea1344950451836376a7a8dba527",
    C3: "63b829cf642f1a537907208aea8ee2577da4945da6a1c4ce984713fdf4bb6d8a",
    AUDIT: "0650ac70484869ba50debb610391f853c09243830ca133a2848d4dde3b7f1362",
}


class Tags(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key == "id" and value is not None:
                self.ids.add(value)
            if tag == "a" and key == "href" and value is not None:
                self.hrefs.append(value)


def html_tags(path):
    tags = Tags()
    tags.feed(path.read_text())
    return tags


def built(dist, route):
    assert route.startswith("/docs/") and route.endswith("/"), route
    return dist / route.lstrip("/") / "index.html"


def check():
    for path, digest in LOCKS.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, f"Source lock: {path}"
    with C1.open(newline="") as stream:
        routes = list(csv.DictReader(stream, delimiter="\t"))
    authored = {row["source_path"]: row for row in routes if row["class"] == "authored"}
    generated = {row["old_route"]: row for row in routes if row["class"] == "generated"}
    proposed = {row["legacy_led_route"]: row for row in json.loads(C3.read_text())["legacy_led_route_map"]}
    assert len(authored) == 34 and len(generated) == 39 and len(proposed) == 35
    links = [row for row in json.loads(AUDIT.read_text())["route_links"]
             if row["target_class"] == "generated"]
    assert len(links) == 60
    led_dist = ROOT / "products/led-lamp/doc/dist"
    pd_dist = ROOT / "doc/dist"
    old_cache = {}
    new_cache = {}
    counts = Counter()
    for row in links:
        split = urlsplit(row["url"])
        route = split.path
        assert not (split.scheme or split.netloc or split.query), row
        assert route in generated and generated[route]["source_path"] == row["target_source"], row
        source = row["source"].removeprefix("products/led-lamp/")
        assert source in authored, row
        old_path = built(led_dist, route)
        assert old_path.is_file(), f"Missing historical generated route: {route}"
        if route not in old_cache:
            old_cache[route] = html_tags(old_path)
        if split.fragment:
            assert split.fragment in old_cache[route].ids, f"Missing historical fragment: {row['url']}"
            counts["fragments"] += 1
        new_route = authored[source]["proposed_route"]
        new_path = built(pd_dist, new_route)
        assert new_path.is_file(), f"Missing private authored page: {new_route}"
        if new_route not in new_cache:
            new_cache[new_route] = html_tags(new_path)
        assert OLD_HOST + row["url"] in new_cache[new_route].hrefs, f"Old-host link changed: {new_route} {row['url']}"
        if built(pd_dist, route).is_file():
            counts["pd_same_path"] += 1
        if route in proposed:
            target = proposed[route]
            assert target["old_id"] == "rec-" + route.removeprefix("/docs/components/records/").strip("/")
            assert target["proposed_route"].startswith("/docs/components/records/led-rec-")
            assert not built(pd_dist, target["proposed_route"]).is_file(), target
            counts["record"] += 1
        else:
            assert route in {
                "/docs/components/", "/docs/components/catalog/",
                "/docs/components/integration/", "/docs/components/records/",
            }, f"Unmapped generated record: {route}"
            counts["section"] += 1
    assert counts == {"fragments": 38, "pd_same_path": 37, "record": 41, "section": 19}, counts
    print(f"PASS: {len(links)} held links, {counts['fragments']} historical fragments, "
          f"{counts['record']} candidate record uses, {counts['section']} section uses, "
          f"{counts['pd_same_path']} PD same-path collision uses")


if __name__ == "__main__":
    check()
