#!/usr/bin/env python3
"""YouTube's /feeds/videos.xml backend has been returning 404 for every channel
since 2026-10-04, which breaks Glance's built-in `videos` widget. List each
channel's latest long-form uploads with yt-dlp instead and write them to
assets/youtube/videos.json for the custom-api "Videos" widget in home.yml.

Dates come from yt-dlp's approximate_date (the "3 days ago" text), so they are
day-precision. Run hourly from cron.

Each video also gets `cc` for the English-caption badge:
  manual  an English subtitle track uploaded by the channel
  auto    no manual track, English-language video with YouTube speech captions
  none    neither (auto-translated English exists on nearly everything, so ignored)
Results are kept in captions.json; only videos under RECHECK_DAYS old without
manual subs are looked up again, since channels often add subs after upload.
"""
import glob
import json
import subprocess
import sys
import time
from pathlib import Path

CHANNELS = [
    "UCDNvRZRgvkBTUkQzFoT_8rA",
    "UC3egV8AyVrnwUEOkGZB-s2Q",
    "UCQ2O-iftmnlfrBuNsUUTofQ",
    "UCaKod3X1Tn4c7Ci0iUKcvzQ",
    "UChJof4NntaxU1VoJI8zt-Kw",
]
PER_CHANNEL = 8
LIMIT = 25  # same as Glance's videos widget default

RECHECK_DAYS = 7

OUT = Path(__file__).resolve().parent.parent / "assets" / "youtube" / "videos.json"
CAPTIONS = OUT.with_name("captions.json")
# Full video lookups need a JS runtime; yt-dlp only looks for deno by default.
NODE = (sorted(glob.glob(str(Path.home() / ".config/nvm/versions/node/*/bin/node"))) or [None])[-1]


def channel_videos(channel_id):
    proc = subprocess.run(
        ["/usr/bin/uvx", "yt-dlp@latest", "-J", "--flat-playlist",
         "-I", f"1:{PER_CHANNEL}",
         "--extractor-args", "youtubetab:approximate_date",
         f"https://www.youtube.com/channel/{channel_id}/videos"],
        capture_output=True, text=True, timeout=180,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip().splitlines()[-1] if proc.stderr else "yt-dlp failed")
    data = json.loads(proc.stdout)
    author = data.get("channel") or data.get("uploader") or channel_id
    author_url = f"https://www.youtube.com/channel/{channel_id}"
    for e in data.get("entries") or []:
        if not e.get("id") or not e.get("timestamp"):
            continue
        yield {
            "id": e["id"],
            "title": e.get("title") or "",
            "url": f"https://www.youtube.com/watch?v={e['id']}",
            "thumbnail": f"https://i.ytimg.com/vi/{e['id']}/hqdefault.jpg",
            "timestamp": int(e["timestamp"]),
            "author": author,
            "author_url": author_url,
        }


def caption_status(info):
    if any(k.split("-")[0] == "en" for k in info.get("subtitles") or {}):
        return "manual"
    lang = (info.get("language") or "").split("-")[0]
    auto = info.get("automatic_captions") or {}
    if lang == "en" and any(k.split("-")[0] == "en" for k in auto):
        return "auto"
    return "none"


def add_captions(videos):
    cache = json.loads(CAPTIONS.read_text()) if CAPTIONS.exists() else {}
    now = time.time()
    todo = [
        v for v in videos
        if v["id"] not in cache
        or (cache[v["id"]] != "manual" and now - v["timestamp"] < RECHECK_DAYS * 86400)
    ]
    if todo:
        cmd = ["/usr/bin/uvx", "yt-dlp@latest", "--ignore-errors", "--skip-download", "-j"]
        if NODE:
            cmd[3:3] = ["--js-runtimes", f"node:{NODE}"]
        proc = subprocess.run(cmd + [v["url"] for v in todo], capture_output=True, text=True, timeout=600)
        for line in proc.stdout.splitlines():
            info = json.loads(line)
            cache[info["id"]] = caption_status(info)
    for v in videos:
        v["cc"] = cache.get(v["id"], "none")
    keep = {v["id"] for v in videos}
    tmp = CAPTIONS.with_suffix(".tmp")
    tmp.write_text(json.dumps({k: s for k, s in cache.items() if k in keep}))
    tmp.replace(CAPTIONS)


def main():
    videos, failed = [], []
    for ch in CHANNELS:
        try:
            videos.extend(channel_videos(ch))
        except Exception as exc:  # keep the other channels
            failed.append(ch)
            print(f"youtube cache: {ch} failed: {exc}", file=sys.stderr)

    if not videos:
        print("youtube cache: no videos fetched, keeping previous file", file=sys.stderr)
        return 1
    # A channel that failed this run keeps its videos from the previous file.
    if failed and OUT.exists():
        old = json.loads(OUT.read_text()).get("videos", [])
        failed_urls = {f"https://www.youtube.com/channel/{c}" for c in failed}
        videos.extend(v for v in old if v["author_url"] in failed_urls)

    videos.sort(key=lambda v: v["timestamp"], reverse=True)
    videos = videos[:LIMIT]
    for v in videos:
        v.setdefault("id", v["url"].rsplit("=", 1)[-1])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        add_captions(videos)
    except Exception as exc:  # badges are optional; never block the video list
        print(f"youtube cache: captions failed: {exc}", file=sys.stderr)
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps({"videos": videos}, ensure_ascii=False))
    tmp.replace(OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
