#!/usr/bin/env python3
"""Aurora outlook for Trondheim -> assets/aurora/aurora.json for the Norway page.

Sources (all free, no key):
  NOAA SWPC   Kp now (1-minute estimate) and the 3-day Kp forecast (3-hour steps)
  NOAA OVATION  aurora probability nowcast on a 1-degree grid (~900 KB; we keep one cell)
  Open-Meteo  hourly cloud cover, sunrise/sunset and daylight length for Trondheim

"Tonight" = today's sunset -> tomorrow's sunrise (or now -> sunrise if already dark).
Rule of thumb at ~63 N: Kp 2-3 shows low on the northern horizon, ~5 overhead; it
only matters when it is dark (roughly Sep-Apr) and the sky is clear.
Run every 30 min from cron. On failure the previous file is kept.
"""
import json
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

LAT, LON = 63.43, 10.40
TZ = ZoneInfo("Europe/Oslo")
OUT = Path(__file__).resolve().parent.parent / "assets" / "aurora" / "aurora.json"

KP_NOW = "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json"
KP_FORECAST = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index-forecast.json"
OVATION = "https://services.swpc.noaa.gov/json/ovation_aurora_latest.json"
WEATHER = ("https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
           "&hourly=cloud_cover&daily=sunrise,sunset,daylight_duration"
           "&forecast_days=2&timezone=Europe%2FOslo").format(lat=LAT, lon=LON)

BRIGHT_DAYLIGHT_H = 18  # mid-May..July: never dark enough
CLEAR, CLOUDY = 50, 75  # % cloud cover


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "glance-aurora (personal dashboard)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def local(s):
    return datetime.fromisoformat(s).replace(tzinfo=TZ)


def kp_level(kp):
    if kp is None:
        return None
    return "storm" if kp >= 5 else "active" if kp >= 4 else "unsettled" if kp >= 3 else "quiet"


def tonight_window(weather, now):
    d = weather["daily"]
    sunset0, sunrise1 = local(d["sunset"][0]), local(d["sunrise"][1])
    sunrise0 = local(d["sunrise"][0])
    if now < sunrise0 - timedelta(hours=2):  # small hours: the night already running
        return now, sunrise0
    if now < sunrise0:  # last hours before dawn: show the coming night instead
        return local(d["sunset"][0]), sunrise1
    return max(now, sunset0), sunrise1


def build(now=None):
    now = now or datetime.now(TZ)
    weather = get(WEATHER)
    start, end = tonight_window(weather, now)
    bright = weather["daily"]["daylight_duration"][0] / 3600 > BRIGHT_DAYLIGHT_H

    # cloud cover over tonight's hours
    hours = [(local(t), c) for t, c in zip(weather["hourly"]["time"], weather["hourly"]["cloud_cover"])]
    night = [c for t, c in hours if start - timedelta(hours=1) < t <= end and c is not None]

    kp_now = get(KP_NOW)[-1].get("estimated_kp")

    # 3-hour Kp steps overlapping tonight
    steps = []
    for row in get(KP_FORECAST):
        t0 = datetime.fromisoformat(row["time_tag"]).replace(tzinfo=timezone.utc)
        if t0 + timedelta(hours=3) > start and t0 < end:
            steps.append({"t": t0.astimezone(TZ).strftime("%H:%M"), "kp": row["kp"],
                          "observed": row.get("observed") == "observed"})
    kp_max = max((s["kp"] for s in steps), default=None)

    try:
        ov = get(OVATION)
        cell = next((c[2] for c in ov["coordinates"] if c[0] == round(LON) and c[1] == round(LAT)), None)
        ovation = {"pct": cell, "at": ov.get("Forecast Time")}
    except Exception as exc:  # the probability line is optional
        print(f"aurora cache: ovation failed: {exc}", file=sys.stderr)
        ovation = None

    cloud_mean = round(sum(night) / len(night)) if night else None
    verdict, level = judge(bright, kp_max, cloud_mean, min(night) if night else None)
    return {
        "generated": now.isoformat(timespec="minutes"),
        "kp_now": kp_now, "kp_now_level": kp_level(kp_now),
        "tonight": {
            "start": start.strftime("%H:%M"), "end": end.strftime("%H:%M"),
            "kp_max": kp_max, "kp_steps": steps,
            "cloud_start": night[0] if night else None, "cloud_end": night[-1] if night else None,
            "cloud_min": min(night) if night else None, "cloud_mean": cloud_mean,
            "bright": bright,
        },
        "ovation": ovation,
        "verdict": verdict, "verdict_level": level,
    }


def judge(bright, kp_max, cloud_mean, cloud_min):
    """(text, level) with level good | maybe | no."""
    if bright:
        return "Too light at night until autumn", "no"
    if kp_max is None:
        return "No Kp forecast", "no"
    clear_spell = cloud_min is not None and cloud_min < CLEAR
    if kp_max < 2:
        return "Quiet — little to see", "no"
    if cloud_mean is not None and cloud_mean >= CLOUDY and not clear_spell:
        return f"Kp {kp_max:.1f}, but too cloudy", "no"
    if kp_max >= 5:
        return "Strong — look up, not just north", "good"
    if kp_max >= 3:
        return ("Worth a look north" if clear_spell or (cloud_mean or 100) < CLEAR
                else "Worth a look if it clears"), "good" if clear_spell else "maybe"
    return "Maybe low on the northern horizon", "maybe"


def main():
    try:
        data = build()
    except Exception as exc:
        print(f"aurora cache: failed, keeping previous file: {exc}", file=sys.stderr)
        return 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False))
    tmp.replace(OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
