# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**CF 悠悠牌资料库** — A static React/Vite single-page app that serves as a comprehensive card reference database for CF Mobile's auto-chess mode (悠悠牌/Zizouqi). Data is extracted from the game APK via a Python pipeline, then consumed by the frontend as static JSON + images.

## Quick Commands

```bash
npm run dev          # Start Vite dev server (0.0.0.0)
npm run build        # tsc -b && vite build
npm run preview      # Preview production build
npm run pipeline     # Run the full APK → web asset pipeline (Python)
npm run admin        # Start local admin API server (port 5174)
npm run deploy       # SSH deploy dist/ to remote server
npm run prepare:data # Copy organized data → public/data/ + generate normalized JSON
```

## Architecture

### Frontend (Single-File App)

All UI lives in one file: [src/App.tsx](src/App.tsx) (~1680 lines). It uses hash-based SPA routing (`#/library/role`, `#/basics/maps`, `#/ai`, `#/videos`) with no external router library.

**Entry**: [src/main.tsx](src/main.tsx) — renders `<App />` into `#root`.

**Data loading**: [src/data/loaders.ts](src/data/loaders.ts) — fetches all static JSON from `/data/` at mount via `loadSiteData()`.

**Types**: [src/data/types.ts](src/data/types.ts) — `CardRecord`, `FactionRecord`, `MapRecord`, `VideoGuide`, `RecommendedLineup`, `Summary`.

**Styles**: [src/styles/main.css](src/styles/main.css) — ~3000 lines of dark-theme CSS, fully responsive down to 360px. No CSS framework.

### Pages (hash routes)

| Route | Content |
|---|---|
| `#/library/all` | Dashboard + full card grid with filters (search, category tabs, faction, keyword, quality) |
| `#/library/role` … `/consume` | Filtered card grid by category |
| `#/library/factions` | Faction overview cards + detail panel with associated roles |
| `#/basics/guide` | Game rules, shop odds, tips, term glossary |
| `#/basics/maps` | Map library with backgrounds |
| `#/basics/buffs` | Buff/gain card library with search + quality filter |
| `#/ai` | Recommended lineup builds (6 preset strategies with board positions, equipment, map, buff picks) |
| `#/videos` | Curated Douyin/Kuaishou video guides with platform/category filters |

### Data Pipeline (Python → Static Assets)

See [PIPELINE.md](PIPELINE.md) for full details. The pipeline transforms a CF Mobile APK into web-ready JSON + images.

**Three phases** orchestrated by `scripts/rebuild-from-apk.py`:

1. **APK extraction** — Parse Unity serialized tables from APK, extract CAB archives, decode ETC2 texture atlases → `autochess_dump/`
2. **Data processing** — Crop sprites, build image index, organize by category, composite card previews, serialize structured JSON (~20 sequential Python scripts at project root)
3. **Web generation** — `npm run prepare:data` copies organized data to `public/data/`, applies overrides from `data/`, normalizes factions/maps, produces `cards.json`, `factions-normalized.json`, etc.

**Intermediate workspace**: `autochess_dump/` grows through each phase. Clean with `--clean` flag.

### Admin & Overrides

**Admin UI**: [admin/index.html](admin/index.html) — standalone HTML/CSS/JS admin panel served at `/admin/` by the admin server.

**Admin server**: `scripts/admin-server.mjs` — plain Node.js HTTP server on port 5174 that:
- Serves static files (`/admin/` → admin UI, rest → `public/`)
- Provides REST API for CRUD on cards, videos, lineups, faction overrides
- Backs up JSON to `data/override-backups/` before each write, then re-runs `prepare-data.mjs`

**Override files** in `data/`:
- `card-overrides.json` — name/faction/keyword/description overrides for existing cards
- `custom-cards.json` — newly added custom cards
- `faction-overrides.json` — faction name/description/keyword overrides
- `video-guides.json` — curated video guide entries
- `recommended-lineups.json` — lineup strategy data

### Deployment

`scripts/deploy.mjs` reads `.env.deploy` (DEPLOY_HOST, DEPLOY_USER, DEPLOY_SSH_KEY, etc.), builds the project, tarballs `dist/`, SCPs to remote server, and extracts.

## Key Conventions

- **No framework CSS** — all styling is hand-written CSS with dark theme (`#070b11` base).
- **No router library** — hash-based routing via `window.location.hash`.
- **No backend** — entirely static. Admin server is a local development convenience only.
- **Chinese UI** — all user-facing text is in Chinese (zh-CN).
- **Card qualities**: grey → green → blue → purple → gold → red (order matters for sorting).
- **Categories**: role, weapon, throwable, item, consume, buff.
- **Images**: card PNGs live in `public/assets/cards/{category}/`, faction icons in `public/assets/cards/fetters/`.
- **Video guides**: manual curation from Douyin/Kuaishou. Popularity is snapshot data, not live API.
- **Lineup data**: 6 preset strategies hardcoded in App.tsx (`lineupBuilds` array) plus `data/recommended-lineups.json` for admin-managed additions.
