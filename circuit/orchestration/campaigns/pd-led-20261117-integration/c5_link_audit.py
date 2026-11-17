#!/usr/bin/env python3
"""Bind current LED authored links to the accepted C1 route and asset maps.

This is a lexical preflight, not a page move or publication decision.
"""

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
C1 = ROOT / "circuit/orchestration/campaigns/pd-led-20261116-c1"
LINK = re.compile(r"(?:\]\(|\b(?:href|src)=[\"'])(/(?:docs|assets)/[^\s)\"']+)")
REL_LINK = re.compile(r"\]\(((?:\.{1,2}/|#)[^\s)]+)")
FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    with path.open(newline="") as source:
        return list(csv.DictReader(source, delimiter="\t"))


def links(path, pattern):
    fence = None
    for number, line in enumerate(path.read_text().splitlines(), 1):
        marker = FENCE.match(line)
        if marker:
            run = marker.group(1)
            if fence is None:
                fence = run[0], len(run)
            elif run[0] == fence[0] and len(run) >= fence[1]:
                fence = None
            continue
        if fence is None:
            for match in pattern.finditer(line):
                yield number, match.group(1)


def root_route_exists(route):
    stem = ROOT / "doc/src/content/docs" / route.removeprefix("/docs/").strip("/")
    return any(path.is_file() for path in (
        stem.with_suffix(".md"), stem.with_suffix(".mdx"),
        stem / "index.md", stem / "index.mdx",
    ))


def audit():
    route_map = C1 / "route-map.tsv"
    asset_map = C1 / "asset-map.tsv"
    routes = rows(route_map)
    docs_root = ROOT / "products/led-lamp/doc/src/content/docs"
    mapped_pages = {ROOT / "products/led-lamp" / row["source_path"] for row in routes}
    current_pages = set(docs_root.rglob("*.md")) | set(docs_root.rglob("*.mdx"))
    assert current_pages == mapped_pages, {
        "unmapped_pages": sorted(str(path.relative_to(ROOT)) for path in current_pages - mapped_pages),
        "missing_mapped_pages": sorted(str(path.relative_to(ROOT)) for path in mapped_pages - current_pages),
    }
    assets = {row["source_path"]: row for row in rows(asset_map)}
    by_old = {row["old_route"].rstrip("/"): row for row in routes}
    by_source = {str((ROOT / "products/led-lamp" / row["source_path"]).resolve()): row
                 for row in routes}
    authored = [row for row in routes if row["class"] == "authored"]
    assert len(authored) == 34 and len(routes) == 97
    source_locks = {str(path.relative_to(ROOT)): sha256(path) for path in (route_map, asset_map)}
    route_links, relative_links, asset_links = [], [], []
    page_dependencies = {str((ROOT / "products/led-lamp" / row["source_path"]).relative_to(ROOT)):
                         {"authored": 0, "generated": 0, "raw-resource": 0, "assets": 0}
                         for row in authored}
    for row in authored:
        path = ROOT / "products/led-lamp" / row["source_path"]
        assert path.is_file(), path
        source = str(path.relative_to(ROOT))
        source_locks[source] = sha256(path)
        for line, url in links(path, LINK):
            target = url.split("?", 1)[0].split("#", 1)[0].rstrip("/")
            item = {"source": source, "line": line, "url": url}
            if url.startswith("/docs/"):
                mapped = by_old.get(target)
                assert mapped is not None, (source, line, url)
                item.update({
                    "target_class": mapped["class"],
                    "target_source": mapped["source_path"],
                    "proposed_route": mapped["proposed_route"] if mapped["class"] == "authored" else None,
                })
                route_links.append(item)
                page_dependencies[source][mapped["class"]] += 1
            else:
                asset_source = "doc/public" + target
                mapped = assets.get(asset_source)
                assert mapped is not None, (source, line, url)
                item.update({
                    "asset_source": asset_source,
                    "proposed_public_path": mapped["proposed_public_path"],
                    "pd_collision": bool(mapped["pd_same_relative_path"]),
                    "same_bytes": mapped["same_bytes"] == "True",
                    "publication_decision": mapped["publication_decision"],
                })
                asset_links.append(item)
                page_dependencies[source]["assets"] += 1
        for line, url in links(path, REL_LINK):
            item = {"source": source, "line": line, "url": url}
            if url.startswith("#"):
                item["target_class"] = "local-fragment"
            else:
                target = url.split("?", 1)[0].split("#", 1)[0]
                mapped = by_source.get(str((path.parent / target).resolve()))
                assert mapped is not None, (source, line, url)
                item.update({
                    "target_class": mapped["class"],
                    "target_source": mapped["source_path"],
                    "proposed_route": mapped["proposed_route"] if mapped["class"] == "authored" else None,
                })
                page_dependencies[source][mapped["class"]] += 1
            relative_links.append(item)
    old_collisions = sorted(row["old_route"] for row in authored if root_route_exists(row["old_route"]))
    counts = {
        "authored_pages": len(authored),
        "old_route_links": len(route_links),
        "relative_route_links": sum(x["target_class"] != "local-fragment" for x in relative_links),
        "local_fragment_links": sum(x["target_class"] == "local-fragment" for x in relative_links),
        "authored_route_links": sum(x["target_class"] == "authored" for x in route_links),
        "generated_route_links_held": sum(x["target_class"] == "generated" for x in route_links),
        "raw_resource_route_links_held": sum(x["target_class"] == "raw-resource" for x in route_links),
        "asset_links_for_review": len(asset_links),
        "asset_links_with_pd_path_collision": sum(x["pd_collision"] for x in asset_links),
        "old_routes_colliding_with_pd": len(old_collisions),
        "pages_requiring_generated_routes": sum(x["generated"] > 0 for x in page_dependencies.values()),
        "pages_requiring_asset_review": sum(x["assets"] > 0 for x in page_dependencies.values()),
        "pages_without_held_link_or_asset_dependencies": sum(not (x["generated"] or x["raw-resource"] or x["assets"])
                                                           for x in page_dependencies.values()),
    }
    return {
        "scope": "lexical authored LED link preflight; no route, asset or publication adoption",
        "source_locks_sha256": dict(sorted(source_locks.items())),
        "counts": counts,
        "old_routes_colliding_with_pd": old_collisions,
        "page_dependencies": dict(sorted(page_dependencies.items())),
        "route_links": route_links,
        "relative_links": relative_links,
        "asset_links": asset_links,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    output = json.dumps(audit(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    target = HERE / "c5-link-audit.json"
    if args.write:
        target.write_text(output)
    else:
        assert target.read_text() == output, "C5 link audit differs from locked inputs"
    print(json.dumps(json.loads(output)["counts"], sort_keys=True))
