#!/usr/bin/env bash
set -euo pipefail

if (( $# != 0 )); then
  echo 'usage: circuit/scripts/check-led-p15-reference.sh' >&2
  exit 2
fi

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)
consumer_record="$repo_root/products/led-lamp/boards/p15-r1-reference.json"
consumer_verifier="$repo_root/products/led-lamp/scripts/checks/verify-p15-reference.py"
owner_verifier="$repo_root/scripts/pcb/board-p15/verify-shared-reference.py"
pinned_owner=8af9e5569c2534c03ce132515d1ec11f4c3f83d3
reviewed_c2=6945f8d4ccd969531b38cb338cecafe224bb2cfb

python3 -c 'import json, sys
record = json.load(open(sys.argv[1]))
owner = record.get("owner", {})
if (owner.get("repository"), owner.get("record_path"), owner.get("record_commit")) != ("https://github.com/Takazudo/zudo-pd", "boards/board-p15/shared-reference.json", sys.argv[2]):
    sys.exit("FAIL: LED P15 owner or original pinned revision changed")' "$consumer_record" "$pinned_owner"

for rev in "$pinned_owner" "$reviewed_c2"; do
  echo "Checking LED consumer and PD owner at $rev"
  python3 "$consumer_verifier" --pd-repo "$repo_root" --pd-rev "$rev"
  python3 "$owner_verifier" --repo "$repo_root" --rev "$rev"
done
