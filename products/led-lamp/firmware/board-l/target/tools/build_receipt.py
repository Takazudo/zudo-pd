"""Write the build receipt for one Board L target image.

The receipt identifies an UNFLASHED bench candidate: source revision and dirty state,
toolchain, options, CTRL ceiling/profile, input and artifact hashes, and memory usage.
It is not a release, validation or programming approval.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys


def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True).stdout


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def git_identity(here):
    try:
        top = run(["git", "rev-parse", "--show-toplevel"], cwd=here).strip()
        rev = run(["git", "rev-parse", "HEAD"], cwd=here).strip()
        firmware = os.path.relpath(os.path.join(here, "..", ".."), top)
        dirty_repo = run(["git", "status", "--porcelain", "--untracked-files=normal"], cwd=top)
        dirty_fw = run(["git", "status", "--porcelain", "--untracked-files=normal", "--", firmware],
                       cwd=top)
        return {
            "revision": rev,
            "repository_dirty": bool(dirty_repo.strip()),
            "firmware_dirty": bool(dirty_fw.strip()),
            "firmware_dirty_paths": sorted(line[3:] for line in dirty_fw.splitlines() if line),
        }
    except (OSError, subprocess.CalledProcessError) as exc:
        return {"revision": None, "repository_dirty": None, "firmware_dirty": None,
                "error": f"git unavailable: {exc}"}


def dep_inputs(dep_files):
    inputs = set()
    for dep in dep_files:
        with open(dep) as f:
            text = f.read().replace("\\\n", " ")
        for line in text.splitlines():
            if ":" not in line:
                continue
            target, prereqs = line.split(":", 1)
            if not target.strip().endswith(".o"):
                continue  # -MP phony header entries
            inputs.update(prereqs.split())
    return inputs


def memory_usage(size_cmd, elf):
    out = run([size_cmd, "-A", elf])
    sections = {}
    for line in out.splitlines():
        m = re.match(r"^(\.\S+)\s+(\d+)\s+(\d+)", line)
        if m:
            sections[m.group(1)] = int(m.group(2))
    berkeley = run([size_cmd, elf]).splitlines()[1].split()
    text, data, bss = (int(v) for v in berkeley[:3])
    return {
        "text": text, "data": data, "bss": bss,
        "flash_used": text + data, "flash_region": 64 * 1024,
        "ram_static_used": data + bss, "ram_region": 8 * 1024,
        "sections": sections,
    }


def effective_macros(cc, cflags, here):
    probe = '#include "board_l_proposal.h"\n'
    out = subprocess.run([cc, *cflags, "-I", here, "-dM", "-E", "-x", "c", "-"], input=probe,
                         cwd=here, check=True, capture_output=True, text=True).stdout
    macros = {}
    for line in out.splitlines():
        parts = line.split(None, 2)
        if len(parts) == 3 and parts[0] == "#define":
            macros[parts[1]] = parts[2]
    return macros


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--elf", required=True)
    ap.add_argument("--map", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--profile", required=True)
    ap.add_argument("--board-defs", default="")
    ap.add_argument("--default-cap", type=int, required=True)
    ap.add_argument("--cc", required=True)
    ap.add_argument("--size", required=True)
    ap.add_argument("--objcopy", required=True)
    ap.add_argument("--pinned-toolchain", required=True)
    ap.add_argument("--allow-toolchain", default="")
    ap.add_argument("--accept-nondefault-cap", default="")
    ap.add_argument("--deps", nargs="+", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()

    here = os.getcwd()
    with open(a.config) as f:
        config_line = f.read().strip()
    cflags = config_line.split("| cflags=", 1)[1].split(" | ldflags=", 1)[0].split()
    ldflags = config_line.split(" | ldflags=", 1)[1].split()

    macros = effective_macros(a.cc, cflags, here)
    cap = int(macros["CTRL_FULL_CCR"].rstrip("uU"))
    period = int(macros["CTRL_PERIOD_TICKS"].rstrip("uU"))

    image = a.elf + ".image.tmp"
    run([a.objcopy, "-O", "binary", a.elf, image])
    try:
        image_hash, image_len = sha256(image), os.path.getsize(image)
    finally:
        os.remove(image)

    inputs = dep_inputs(a.deps) | {"stm32g031f8_flash.ld", "Makefile"}
    gcc_version = run([a.cc, "--version"]).splitlines()[0]
    dumpversion = run([a.cc, "-dumpversion"]).strip()

    receipt = {
        "schema": "board-l-target-build-receipt/1",
        "status": "UNFLASHED BENCH CANDIDATE",
        "status_note": ("Build-only output. Never flashed or run; not validated, qualified or "
                        "released. Programming a Board L needs separate explicit permission and "
                        "firmware/board-l/BEFORE-PROGRAMMING-CHECKLIST.md."),
        "source": git_identity(here),
        "toolchain": {
            "cc": a.cc,
            "version_line": gcc_version,
            "version": dumpversion,
            "pinned": a.pinned_toolchain,
            "matches_pin": dumpversion == a.pinned_toolchain,
            "pin_override": bool(a.allow_toolchain),
        },
        "options": {
            "profile": a.profile,
            "board_defs": a.board_defs,
            "cflags": cflags,
            "ldflags": ldflags,
            "config_id": hashlib.sha256((config_line + "\n").encode()).hexdigest(),
            "BOARD_L_PRODUCTION": "BOARD_L_PRODUCTION" in macros,
        },
        "ctrl_ceiling": {
            "CTRL_FULL_CCR": cap,
            "CTRL_PERIOD_TICKS": period,
            "CTRL_MIN_CCR": int(macros["CTRL_MIN_CCR"].rstrip("uU")),
            "duty_percent": round(100.0 * cap / period, 2),
            "adopted_default": cap == a.default_cap,
            "assumed_rs1_mohm": 200 if cap == a.default_cap else None,
            "nondefault_acknowledged": bool(a.accept_nondefault_cap),
            "note": ("Default 2407 protects an unchanged RS1 = 200 mOhm board (calculated, typical "
                     "transfer; not measured)." if cap == a.default_cap else
                     "NON-DEFAULT ceiling: valid only for a board with a measured RS1 change."),
        },
        "artifacts": {
            os.path.basename(a.elf): sha256(a.elf),
            os.path.basename(a.map): sha256(a.map),
            "loadable_image_sha256": image_hash,
            "loadable_image_bytes": image_len,
            "note": ("The ELF and map embed the build directory path in debug data; the loadable "
                     "image hash (objcopy -O binary) is path-independent."),
        },
        "memory": memory_usage(a.size, a.elf),
        "inputs": {p: sha256(p) for p in sorted(inputs)},
    }
    with open(a.output, "w") as f:
        json.dump(receipt, f, indent=2, sort_keys=False)
        f.write("\n")
    print(f"receipt: {a.output} ({receipt['status']}, profile {a.profile}, "
          f"CTRL_FULL_CCR {cap}, firmware_dirty {receipt['source'].get('firmware_dirty')})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
