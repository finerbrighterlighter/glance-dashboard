#!/usr/bin/env bash
# Shared-in (external) devices come back from the Tailscale admin API with an
# empty name; only the local client knows their MagicDNS names. Export
# nodeId -> short name for the Glance Tailscale widget.
set -u
out="$(dirname "$0")/../assets/tailscale"
mkdir -p "$out"
tailscale status --json | python3 -c '
import json, sys
d = json.load(sys.stdin)
names = {p["ID"]: p["DNSName"].split(".")[0] for p in d.get("Peer", {}).values() if p.get("DNSName")}
json.dump(names, sys.stdout)
' > "$out/.names.tmp" && mv "$out/.names.tmp" "$out/names.json"
