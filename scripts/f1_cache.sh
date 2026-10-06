#!/usr/bin/env bash
# f1api.dev often takes >5s, longer than Glance's fixed custom-api timeout.
# Cache the endpoints into assets/f1/ so the widgets read them locally.
set -u
out="$(dirname "$0")/../assets/f1"
mkdir -p "$out"
fetch() {  # name url
  tmp="$out/.$1.tmp"
  if curl -sf -m 60 "$2" -o "$tmp" && python3 -c 'import json,sys; json.load(open(sys.argv[1]))' "$tmp"; then
    mv "$tmp" "$out/$1.json"
  else
    rm -f "$tmp"; echo "$(date -Is) f1 cache: $1 failed" >&2
  fi
}
fetch next "https://f1api.dev/api/current/next?timezone=Europe/London"
fetch drivers "https://f1api.dev/api/current/drivers-championship"
fetch constructors "https://f1api.dev/api/current/constructors-championship"
