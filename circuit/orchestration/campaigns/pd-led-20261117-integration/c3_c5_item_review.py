#!/usr/bin/env python3
"""Replay item-level, private C3/C5 evidence dispositions without adoption."""

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from c3_c5_decisions import C1, C3, DOCS, HERE, ROOT, create, route_exists, tsv


PACKAGE = Path("products/led-lamp/manufacturing/jlcpcb/2026-09-19")
PACKAGE_LOCKS = {
    "README.md": "9b76a5487fa98a0bc0314a1f2c30bdc34fd2052e84e38a6552d40915df87d919",
    "board-p/bom.csv": "7969f3915955af36251a000f3f036c0ad5efa4dc3009568403e3335577cc613f",
    "board-p/cpl.csv": "b49d46968241d2ffe98624f50d85aa9d9b8c57c1209664247e4662bb1fb4c3e4",
    "board-p/excluded.csv": "8d75d33f3f7ff0ff2433029e43f9392e2b8572126c3b65290b354e0fd7012996",
    "board-l/bom.csv": "d93c0632e11ae46383d3ad9e8ee2e13f7fab8384d1f6799b9d85c6b6588eacf1",
    "board-l/cpl.csv": "70a6d1e84b138b7e7a76724c6c541c7859ea7a6b51f7c67feb01c1477976a7d0",
    "board-l/excluded.csv": "fcb250995455936f56f41e5c6f639ba52af03eaf263dd963a3144ca9fb3e9274",
    "swd-adapter/bom.csv": "55f853eb8b0378019736111bf43db5c1a63deca5a50c1babc75e0fd4b0e796b7",
    "swd-adapter/cpl.csv": "db32808364b585cdd860c614e44b876a2391ca106202eeb4a6686ddab97a254c",
    "swd-adapter/excluded.csv": "5c8ce3dd092262692385e08e783fd1bc89890fdaf1f1196d0042e9fd07370636",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob(path):
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def checked_git_blob(path, expected):
    actual = git_blob(path)
    assert actual == expected, f"CAD source blob changed: {path}"
    return actual


def load_csv(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def owner(root, record_id):
    for manifest in sorted(root.glob("component-*/manifest.json")):
        if any(row["record_id"] == record_id for row in json.loads(manifest.read_text())["records"]):
            return manifest.parent
    raise AssertionError(f"No owner for {record_id} in {root}")


def record_evidence(root, record_id):
    home = owner(root, record_id)
    sources = [row for row in json.loads((home / "sources.json").read_text())["sources"]
               if row["record_id"] == record_id and row.get("sha256")]
    pin_file = home / "pin-map.json"
    pins = [row for row in json.loads(pin_file.read_text())["pin_maps"]
            if row["record_id"] == record_id] if pin_file.exists() else []
    return {
        "owner": str(home.relative_to(ROOT)),
        "source_sha256": sorted({row["sha256"] for row in sources}),
        "pin_map": pins[0] if pins else None,
        "owner_file_sha256": {name: digest(home / name) for name in
                              ("manifest.json", "sources.json", "pin-map.json") if (home / name).exists()},
    }


def find_bom(rows, refdes):
    return [row for row in rows if refdes in row["Designator"].split(",")]


def build():
    create()  # includes all C1, C3 and C5 source locks and route/asset holds
    for name, expected in PACKAGE_LOCKS.items():
        assert digest(ROOT / PACKAGE / name) == expected, f"LED package changed: {name}"
    c3 = json.loads((C3 / "reconciliation.json").read_text())
    c5 = json.loads((HERE / "c5-link-audit.json").read_text())
    routes = tsv(C1 / "route-map.tsv")
    output = {"schema": "private-c3-c5-item-review-v1", "package_source_locks_sha256": PACKAGE_LOCKS,
              "identity": [], "dnp": [], "cad": [], "pages": []}
    led_owners = ROOT / "products/led-lamp/.claude/skills"
    pd_owners = ROOT / ".claude/skills"
    for line in c3["line_reconciliation"]:
        overlap = line["pd_overlap"]
        if overlap:
            led = record_evidence(led_owners, line["led_record_id"])
            pd = record_evidence(pd_owners, overlap["record_id"])
            common = sorted(set(led["source_sha256"]) & set(pd["source_sha256"]))
            led_pin, pd_pin = led.pop("pin_map"), pd.pop("pin_map")
            output["identity"].append({
                "line_id": line["led_line_id"], "led_record_id": line["led_record_id"],
                "pd_record_id": overlap["record_id"], "different_fields": overlap["identity_field_differences"],
                "led_identity": line["identity"], "pd_identity": overlap["identity"],
                "shared_source_sha256": common, "led": led, "pd": pd,
                "pin_rows_equal": bool(led_pin and pd_pin and led_pin["pins"] == pd_pin["pins"]),
                "footprint_names_equal": bool(led_pin and pd_pin and led_pin["footprint"] == pd_pin["footprint"]),
                "status": "exact identity conflict; keep distinct" if overlap["identity_field_differences"]
                          else "equal identity text; independent use/pin/CAD review held",
            })
        if line["led_line_dnp"]:
            for placement in line["placements"]:
                board, ref = placement["source_board"], placement["refdes"]
                root = ROOT / PACKAGE / board
                bom, cpl, excluded = (load_csv(root / f"{part}.csv")
                                      for part in ("bom", "cpl", "excluded"))
                matching_bom = find_bom(bom, ref)
                matching_cpl = [row for row in cpl if row["Designator"] == ref]
                matching_excluded = [row for row in excluded if row["Designator"] == ref]
                assert len(matching_bom) <= 1 and len(matching_cpl) <= 1 and len(matching_excluded) <= 1
                assert bool(matching_bom) == bool(matching_cpl) != bool(matching_excluded), (board, ref)
                if matching_bom:
                    assert matching_bom[0]["JLCPCB Part #"] == line["identity"]["lcsc"]
                else:
                    assert matching_excluded[0]["LCSC"] == line["identity"]["lcsc"]
                output["dnp"].append({
                    "line_id": line["led_line_id"], "board": board, "refdes": ref,
                    "historical_line_dnp": True, "package_bom": matching_bom[0] if matching_bom else None,
                    "package_cpl": matching_cpl[0] if matching_cpl else None,
                    "package_excluded": matching_excluded[0] if matching_excluded else None,
                    "candidate_disposition": "2026-09-19 export excludes placement" if matching_excluded else
                                             "2026-09-19 export requests placement despite line-level DNP",
                    "physical_fit": "unverified", "current_design_adoption": "held",
                })
    assert len(output["identity"]) == 17 and len(output["dnp"]) == 7
    assert Counter("excluded" if row["package_excluded"] else "requested" for row in output["dnp"]) == {"excluded": 4, "requested": 3}
    assert "including all connector headers" in (ROOT / PACKAGE / "README.md").read_text()
    assert "Hand-fit a pin strip" in (ROOT / "products/led-lamp/doc/src/content/docs/architecture/board-l.mdx").read_text()
    assert "exactly two hand-fit/DNP connectors" in (ROOT / "products/led-lamp/doc/src/content/docs/architecture/swd-adapter.mdx").read_text()
    rebound = json.loads((HERE / "c3-input-rebind.json").read_text())["cad_pd_git_blobs"]
    for row in c3["cad_path_collisions"]:
        pd_path, led_path = ROOT / row["relative_path"], ROOT / row["led_destination"]
        assert pd_path.is_file() and led_path.is_file()
        pd_blob = row["pd_blob"]
        if row["relative_path"] in rebound:
            assert rebound[row["relative_path"]]["reconciled"] == pd_blob and not row["same_bytes"]
            pd_blob = rebound[row["relative_path"]]["current"]
        checked_git_blob(pd_path, pd_blob)
        checked_git_blob(led_path, row["led_blob"])
        assert (pd_path.read_bytes() == led_path.read_bytes()) == row["same_bytes"]
        pd_pads = re.findall(r'\(pad\s+"?([^"\s)]+)', pd_path.read_text()) if pd_path.suffix == ".kicad_mod" else []
        led_pads = re.findall(r'\(pad\s+"?([^"\s)]+)', led_path.read_text()) if led_path.suffix == ".kicad_mod" else []
        output["cad"].append({"relative_path": row["relative_path"], "pd_git_blob": pd_blob,
                              "led_git_blob": row["led_blob"], "same_bytes": row["same_bytes"],
                              "pd_size_bytes": pd_path.stat().st_size, "led_size_bytes": led_path.stat().st_size,
                              "pd_pad_numbers": sorted(pd_pads), "led_pad_numbers": sorted(led_pads),
                              "pad_number_multiset_equal": sorted(pd_pads) == sorted(led_pads) if pd_pads or led_pads else None,
                              "disposition": "separate CAD roots; native/physical equivalence unproved"})
    assert len(output["cad"]) == 21 and sum(not row["same_bytes"] for row in output["cad"]) == 20
    for row in routes:
        if row["class"] != "authored":
            continue
        source = ROOT / "products/led-lamp" / row["source_path"]
        assert source.is_file() and route_exists(row["proposed_route"])
        source_name = str(source.relative_to(ROOT))
        held_generated = [link for link in c5["route_links"] if link["source"] == source_name
                          and link["target_class"] == "generated"]
        held_assets = [link for link in c5["asset_links"] if link["source"] == source_name]
        output["pages"].append({
            "source": source_name, "source_sha256": digest(source), "old_route": row["old_route"],
            "development_route": row["proposed_route"], "generated_links_held": len(held_generated),
            "asset_links_held": len(held_assets), "old_route_pd_collision": row["old_route"] in c5["old_routes_colliding_with_pd"],
            "status": "editorial review candidate; no identified held generated link or asset" if
                      not held_generated and not held_assets else "resolve exact held links/assets before publication review",
        })
    assert len(output["pages"]) == 34 and sum(row["status"].startswith("editorial") for row in output["pages"]) == 25
    assert sum(row["old_route_pd_collision"] for row in output["pages"]) == 3
    assert sum(row["generated_links_held"] for row in output["pages"]) == 60
    assert sum(row["asset_links_held"] for row in output["pages"]) == 12
    output["base_review_sha256"] = digest(HERE / "c3-c5-candidates.json")
    output["counts"] = {"identity_conflicts": 4, "same_text_overlaps": 13,
                        "dnp_export_excluded": 4, "dnp_export_requested": 3,
                        "cad_collisions": 21, "page_editorial_candidates": 25,
                        "pages_with_held_dependencies": 9, "old_route_collisions": 3}
    return output


def markdown(data):
    lines = ["---", "title: C3 and C5 item evidence", "sidebar_position: 5", "---", "",
             "# C3 and C5 item evidence", "",
             "> **Review record only.** This is a per-item reading of retained sources. It does not adopt shared component identities, fitted state, CAD or publication.", "",
             "## Overlapping part identities", "",
             "The exact source digest and owner-file locks for every row are in the machine-readable bundle. A shared source or equal pin rows is evidence for review, not proof of shared use or CAD equivalence.", "",
             "| LED line | Different identity fields | Shared retained source hashes | Pin rows equal | Disposition |",
             "| --- | --- | ---: | --- | --- |"]
    for row in data["identity"]:
        lines.append(f'| `{row["line_id"]}` | {", ".join(row["different_fields"]) or "none"} | '
                     f'{len(row["shared_source_sha256"])} | {"yes" if row["pin_rows_equal"] else "no/unavailable"} | {row["status"]} |')
    lines += ["", "The four exact text conflicts are STUSB4500 manufacturer spelling, AO3401A manufacturer spelling, SMAJ20A package/footprint dimensions, and PESD24VS1UB order suffix. The SMAJ20A footprint names and pin text also differ; retain separate footprints. Shared source hashes do not resolve those project-specific choices.", "",
              "## Seven historical DNP flags against the dated export", "",
              "The 2026-09-19 BOM/CPL/excluded files and upload-set README are locked in the bundle. This is the export's requested population, not evidence of an assembled board. Authored Board L/SWD pages describe hand-fit headers, while the upload-set README requests all connector headers for JLCPCB soldering. Keep that unresolved document disagreement visible.", "",
              "| Board/refdes | 2026-09-19 export | Historical line flag | Current design/physical state |",
              "| --- | --- | --- | --- |"]
    for row in data["dnp"]:
        lines.append(f'| `{row["board"]}/{row["refdes"]}` | {row["candidate_disposition"]} | DNP | held / unverified |')
    lines += ["", "**Recommendation:** treat Board P D6/D7/R17/R18 as excluded in that dated package; treat Board L J3 and SWD J1/J2 as requested placements in that dated package. Do not copy the line DNP flag to those three placements. Reconcile the current board and supplier preview before any assembly or manufacturing claim.", "",
              "## CAD files", "",
              "All 21 same-relative paths were compared as current bytes against the preserved C3 map. Only the KiCad project file is equal-byte; 20 paths differ. Footprint pad-number multisets are inspected but say nothing about pad geometry or model placement. The full per-path Git blob IDs, sizes and pad lists are in the bundle. Retain product-specific roots.", "",
              "| Relative path | Bytes | Pad numbers |", "| --- | --- | --- |"]
    for row in data["cad"]:
        pads = row["pad_number_multiset_equal"]
        pad_status = "same count/numbers" if pads else "different count/numbers" if pads is False else "n/a"
        lines.append(f'| `{row["relative_path"]}` | {"equal" if row["same_bytes"] else "different"} | {pad_status} |')
    lines += ["", "## Authored page candidates", "",
              "Every copied page has an exact source digest in the bundle and a published historical copy route. Twenty-five pages have no *detected* held generated-route or asset dependency; all still need editorial and publication review. The other nine have item-specific dependencies. Three legacy routes collide with PD, so blanket same-host redirects cannot preserve them.", "",
              "| Old route | Historical copy route | Held generated links | Held asset links | PD collision |",
              "| --- | --- | ---: | ---: | --- |"]
    for row in data["pages"]:
        lines.append(f'| `{row["old_route"]}` | `{row["development_route"]}` | '
                     f'{row["generated_links_held"]} | {row["asset_links_held"]} | '
                     f'{"yes" if row["old_route_pd_collision"] else "no"} |')
    lines += ["", "The [machine-readable item review](https://github.com/Takazudo/zudo-pd/blob/codex/c3-c5-item-evidence-20261117-01/circuit/orchestration/campaigns/pd-led-20261117-integration/c3-c5-item-evidence.json) retains exact source hashes, BOM/CPL rows, owner files, CAD blobs and page paths. Publication, preview and physical work remain held.", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = build()
    outputs = {HERE / "c3-c5-item-evidence.json": json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
               DOCS / "catalog/item-evidence.mdx": markdown(result)}
    for path, content in outputs.items():
        if args.write:
            path.write_text(content)
        else:
            assert path.read_text() == content, f"Item review drift: {path}"
    print(json.dumps(result["counts"], sort_keys=True))
