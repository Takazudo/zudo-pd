#!/usr/bin/env python3
"""Verify downloadable packages against the reviewed loose files using only stdlib."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "doc/public/assets/enclosure"


def main():
    manifest_bytes = (PUBLIC / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    printable = [p for p in manifest["parts"] if p["group"] in ("print", "coupon")]
    expected = {p["file"] for p in printable} | {"README.md", "manifest.json"}
    with zipfile.ZipFile(PUBLIC / "smoke-reversing-stls.zip") as archive:
        assert len(archive.namelist()) == len(expected), "Unexpected/duplicate entries in print ZIP"
        assert set(archive.namelist()) == expected, "Print ZIP contents differ from manifest"
        assert archive.testzip() is None, "Print ZIP checksum failure"
        assert archive.read("manifest.json") == manifest_bytes, "Print ZIP contains a stale manifest"
        assert archive.read("README.md") == (ROOT / "enclosure/README.md").read_bytes(), "Print ZIP contains a stale assembly guide; regenerate CAD"
        for part in printable:
            actual = hashlib.sha256(archive.read(part["file"])).hexdigest()
            assert actual == part["sha256"], f"Stale or corrupt print ZIP mesh: {part['name']}"
    with zipfile.ZipFile(PUBLIC / "assembly-step.zip") as archive:
        assert archive.namelist() == ["assembly.step"], "Unexpected STEP archive contents"
        assert archive.testzip() is None, "STEP ZIP checksum failure"
        with archive.open("assembly.step") as step:
            assert step.read(64).startswith(b"ISO-10303-21;"), "Not an ISO STEP model"
    for path in PUBLIC.rglob("*"):
        if path.is_file():
            assert path.stat().st_size < 25 * 1024 * 1024, f"Web asset exceeds 25 MiB: {path.name}"
    print(f"Enclosure archives PASS: {len(printable)} matching print STLs, current guide/manifest, valid STEP ZIP")


if __name__ == "__main__":
    main()
