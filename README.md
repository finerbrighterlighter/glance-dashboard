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
- Trakt
- TMDB
- NextDNS
- WAQI (air quality)

Changes to .env require restarting containers:
``` bash
docker compose up -d
```

---

## Tracked

Tracked in Git:
- `docker-compose.yml` — deployment definition
- `config/` — Glance configuration (dashboards, widgets)
- `assets/` — custom CSS and static assets
- `.env.example` — required environment variables (no secrets)

Not tracked:
- `.env` — contains secrets
- runtime data / Docker state

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