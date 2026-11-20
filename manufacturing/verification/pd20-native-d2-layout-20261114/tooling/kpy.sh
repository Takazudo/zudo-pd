#!/bin/bash
IMG=kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec
exec docker run --rm --platform linux/amd64 --cpus 1 --user 0 -e PYTHONHASHSEED=0 -v "$PWD":"$PWD" -w "$PWD" "$IMG" bash -c 'broadwayd :5 >/dev/null 2>&1 & sleep 1; GDK_BACKEND=broadway BROADWAY_DISPLAY=:5 exec python3 "$@"' kicad-python "$@"
