# Glance Dashboard

Personal Glance dashboard configuration.

This repository is designed to be **cloned and brought up with minimal thought**.

---

## Quick Start (copy & paste)

```bash
mkdir -p ~/containers && cd ~/containers
git clone git@github.com:finerbrighterlighter/glance-dashboard.git
cd glance-dashboard
cp .env.example .env
docker compose up -d
```

Then open Glance in your browser (default):
```
http://localhost:8080
```

---

## One time setup

After copying `.env.example` → `.env`, fill in the required API keys:
- GitHub (releases widget) 
- Tailscale
- Last.fm
- NextDNS
- WAQI (air quality)
- `WUD_URL=wud:3000` (Glance joins WUD's `wud_default` network; WUD must be running first)

Some widgets read caches written by scripts in `scripts/`. Add them to the host crontab
(they need `tailscale` and `uvx` on the host):
```cron
5 * * * *    ~/containers/glance/scripts/youtube_cache.py    # YouTube RSS feeds are down; yt-dlp instead
15 * * * *   ~/containers/glance/scripts/f1_cache.sh         # f1api.dev is slower than Glance's timeout
*/15 * * * * ~/containers/glance/scripts/tailscale_names.sh  # names for devices shared into the tailnet
*/30 * * * * ~/containers/glance/scripts/aurora_cache.py      # Trondheim aurora outlook (NOAA + Open-Meteo)
```
Run each once by hand after cloning so the widgets have data immediately.

Videos widget (Home): count-based, not a date window. `youtube_cache.py` takes the newest
8 uploads per channel (`PER_CHANNEL`), merges them and keeps the newest 25 (`LIMIT`).
Channels that upload often take more of the row. Each card gets an EN patch:
solid = English subtitles from the channel, dashed = YouTube auto captions (English videos only).

Changes to .env require restarting containers:
``` bash
docker compose up -d
```

---

## Tracked

Tracked in Git:
- `compose.yaml` — deployment definition
- `scripts/` — cache scripts for widgets (see cron above)
- `config/` — Glance configuration (dashboards, widgets)
- `assets/` — custom CSS (`user.css`), self-hosted fonts and static assets
- `.env.example` — required environment variables (no secrets)

Not tracked:
- `.env` — contains secrets
- runtime data / Docker state
- widget caches (`assets/f1`, `assets/youtube`, `assets/tailscale`, `assets/aurora`) and `assets/ynab`

---

## Updating

Pull latest config changes:
```bash
git pull
docker compose up -d
```

---

#### Notes

- `.env` is intentionally ignored by Git
- This repo is meant to be reproducible, not stateful
- If something breaks, delete the folder and redeploy — no data is lost