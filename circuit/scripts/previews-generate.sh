#!/usr/bin/env bash
# Footprint preview generation through the pinned KiCad oracle image.
# The generator bind-mounts a mkdtemp directory (mode 0700, owned by the caller),
# but the KiCad image defaults to its unprivileged "kicad" user, which cannot read
# that mount. This wrapper puts a docker shim first on PATH that runs every
# container as the invoking uid:gid with a writable HOME; other docker commands
# (version, image inspect, pull) pass through unchanged.
set -euo pipefail

real_docker="$(command -v docker)"
shim_dir="$(mktemp -d "${TMPDIR:-/tmp}/zudo-pd-preview-docker.XXXXXX")"
cleanup() {
  rm -f -- "$shim_dir/docker"
  rmdir -- "$shim_dir"
}
trap cleanup EXIT

cat > "$shim_dir/docker" <<SHIM
#!/usr/bin/env bash
if [ "\${1:-}" = run ]; then
  shift
  exec "$real_docker" run --user "$(id -u):$(id -g)" --env HOME=/tmp "\$@"
fi
exec "$real_docker" "\$@"
SHIM
chmod 755 "$shim_dir/docker"

PATH="$shim_dir:$PATH" pnpm exec zudo-circuit-doc footprints generate "$@"
