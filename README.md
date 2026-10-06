# Glance Dashboard

Personal Glance dashboard configuration.

This repository is designed to be **cloned and brought up with minimal thought**.

---

## Quick Start (copy & paste)

```bash
mkdir -p ~/containers && cd ~/containers
git clone git@github.com:finerbrighterlighter/glance-dashboard.git glance
cd glance
cp .env.example .env
docker compose up -d
```

Then open Glance in your browser (compose publishes container port 8080 on host 3080):
```
http://localhost:3080
```
Clone into `~/containers/glance`: the cron lines below use that path.

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

Videos widget ("Watch", on Fun): count-based, not a date window. `youtube_cache.py` takes the newest
8 uploads per channel (`PER_CHANNEL`), merges them and keeps the newest 25 (`LIMIT`).
Channels that upload often take more of the row. Each card gets an EN patch:
solid = English subtitles from the channel, dashed = YouTube auto captions (English videos only).

Changes to .env require restarting containers:
``` bash
docker compose up -d
```

---

## Pages

Layout chosen 2026-10-06 by a debate between agents arguing from semantic, structural and
cognitive perspectives (cited NN/g and Glance docs/source), judged blind.

| Page | Left / main | Right |
|---|---|---|
| **Home** (landing) | search strip on top; YNAB · Thailand and AI usage side by side; Academic / Professional bookmarks; Research tabs (medRxiv, arXiv stat.ME, arXiv stat.AP+q-bio.PE, My papers) | clock (Pyinmana, Tokyo, Trondheim), Bangkok weather, air quality |
| **Homelab** | server stats, NextDNS, Tailscale devices | service monitor, Docker containers, What's Up Docker and releases side by side |
| **Fun** | Baseball (MLB scores, r/baseball) and F1 (next race, drivers, teams, r/formula1) side by side; Watch (YouTube); Korean variety subreddits; r/apple and r/ynab | Last.fm, Anime Airing (AniList: my list, popular), xkcd |
| **Norway** | Trondheim clock, NOK rate (THB, MMK, JPY, USD, EUR) / NRK tabs (Trøndelag, Toppsaker, Norge, Urix) | Trondheim weather, Aurora outlook |

Widgets that read other local projects:
- **YNAB · Thailand** — `assets/ynab/ynab.json`, written 4x/day by `~/Sandbox/ynab/glance.py`
  (the YNAB dashboard's Now-tab numbers). Title links to the YNAB dashboard (:8086).
- **AI usage** — the usage dashboard's `/api/now` over Tailscale Serve (:8084); the dashboard
  only listens on 127.0.0.1, so Glance cannot use localhost for it.

## Look

`assets/user.css` restyles Glance to match the YNAB and usage dashboards: paper/ink palette
with one gold accent, Newsreader + Karla (self-hosted in `assets/fonts/`), hairlines instead of
cards. The palette is the `theme` block in `config/glance.yml` (dark default, `editorial-light`
preset); with the default theme the page follows the system light/dark setting (CSS media
query mirroring the `editorial-light` values — keep both in sync). Widget-specific styles are
prefixed `.ynab-*`, `.usage-*`, `.aurora-*`, `.yt-*`. Nav logo: the duck from htunteza.com.
Glance v0.8.6: some functions in the upstream docs (e.g. `FloatOr`) are not in this release.

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