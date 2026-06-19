# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**CF 悠悠牌资料库** — A static React/Vite single-page app serving as a card reference database for CF Mobile's auto-chess mode (悠悠牌/Zizouqi). Raw game data is extracted from the APK via a multi-stage Python pipeline, then consumed by the frontend as static JSON + images.

**Root layout:**
- `cfuu/` — Frontend app (React 19, Vite 6, TypeScript)
- `autochess_dump/` — Intermediate workspace from APK extraction (JSON, split assets, CAB tests)
- `Maps/` — Raw map binary files
- `*.py` at root — Pipeline scripts (17 Python scripts, each handling one data category's organization/serialization)

See `APK_ANALYSIS_NOTES.md` for APK reverse-engineering details. See `cfuu/PIPELINE.md` for the pipeline workflow. See `cfuu/VIDEO_INTEGRATION.md` for video guide data model.

## Quick Commands

```bash
cd cfuu

npm run dev             # Start Vite dev server (0.0.0.0)
npm run build           # tsc -b && vite build
npm run preview         # Preview production build
npm run pipeline        # Full APK → web asset pipeline (Python, see PIPELINE.md)
npm run pipeline -- --clean  # Clean intermediate data before rebuilding
npm run pipeline -- --from-existing-dump  # Skip APK parse, re-process existing autochess_dump
npm run pipeline -- --skip-build           # Generate public/data only, no vite build
npm run prepare:data  # Copy organized data → public/data/ + normalize JSON
npm run admin          # Start admin API server (port 5174)
npm run deploy         # Build + SCP dist/ to remote server
```

## Architecture

### Frontend (Single-File App)

All UI lives in one file: `cfuu/src/App.tsx` (~1680 lines). Hash-based SPA routing (`#/library/role`, `#/basics/maps`, `#/ai`, `#/videos`) with no router library.

- **Entry**: `cfuu/src/main.tsx` — renders `<App />` into `#root`
- **Data loading**: `cfuu/src/data/loaders.ts` — fetches all static JSON from `/data/` at mount via `loadSiteData()`
- **Types**: `cfuu/src/data/types.ts` — `CardRecord`, `FactionRecord`, `MapRecord`, `VideoGuide`, `RecommendedLineup`, `Summary`
- **Styles**: `cfuu/src/styles/main.css` — ~3000 lines hand-written dark-theme CSS (`#070b11` base), responsive down to 360px
- **Build**: `cfuu/vite.config.ts` — bare `react()` plugin, no extra config

**Pages (hash routes):**

| Route | Content |
|---|---|
| `#/library/all` | Dashboard + full card grid with filters (search, category, faction, keyword, quality) |
| `#/library/role` … `/consume` | Filtered card grid by category |
| `#/library/factions` | Faction overview + detail panel with associated roles |
| `#/basics/guide` | Game rules, shop odds, tips, term glossary |
| `#/basics/maps` | Map library with backgrounds |
| `#/basics/buffs` | Buff/gain card library with search + quality filter |
| `#/ai` | 6 preset strategy builds (board positions, equipment, map, buff picks) |
| `#/videos` | Curated Douyin/Kuaishou video guides with platform/category filters |

### Data Pipeline (Python → Static Assets)

Three phases orchestrated by `cfuu/scripts/rebuild-from-apk.py`:

1. **APK extraction** — Parse Unity serialized tables from APK → extract CAB archives → decode ETC2 texture atlases → `autochess_dump/`
2. **Data processing** — 17 root-level Python scripts (one per category) crop sprites, build image index, organize by type, composite card previews, serialize structured JSON
3. **Web generation** — `cfuu/scripts/prepare-data.mjs` copies organized data to `public/data/`, applies overrides from `cfuu/data/`, normalizes factions/maps, produces `cards.json`, `factions-normalized.json`, etc.

**Pipeline scripts (root-level, run sequentially):**

| Phase | Scripts |
|---|---|
| Extract | `parse_autochess_unity.py`, `prepare_zizouqi_cabs.py`, `extract_cf_cab_textures.py` |
| Crop | `crop_zizouqi_sprites.py`, `extract_ua257_texture10_slices.py`, `extract_ladder_icons.py` |
| Index | `build_zizouqi_card_image_index.py` |
| Organize | `organize_zizouqi_{roles,weapons,throwables,items,consume_buffs,fetters,maps,zhiyuan}.py` |
| Preview | `build_zizouqi_{role,weapon,throwable,item,consume}_card_previews.py`, `compose_zizouqi_card_preview.py` |
| Serialize | `serialize_zizouqi_role_data.py`, `serialize_zizouqi_weapon_data.py`, `serialize_zizouqi_item_like_data.py`, `serialize_zizouqi_faction_data.py` |

### Admin & Overrides

**Admin UI**: `cfuu/admin/index.html` — standalone HTML/CSS/JS panel served at `/admin/` by the admin server.

**Admin server**: `cfuu/scripts/admin-server.mjs` — plain Node.js HTTP server on port 5174:
- Serves static files (`/admin/` → admin UI, rest → `public/`)
- REST API for CRUD on cards, videos, lineups, faction overrides
- Backs up JSON to `cfuu/data/override-backups/` before each write, then re-runs `prepare-data.mjs`

**Override files** in `cfuu/data/`:
- `card-overrides.json` — name/faction/keyword/description overrides for existing cards
- `custom-cards.json` — newly added custom cards
- `faction-overrides.json` — faction name/description/keyword overrides
- `video-guides.json` — curated video guide entries
- `recommended-lineups.json` — lineup strategy data

### Deployment

`cfuu/scripts/deploy.mjs` reads `.env.deploy` (DEPLOY_HOST, DEPLOY_USER, DEPLOY_SSH_KEY), builds the project, tarballs `dist/`, SCPs to remote server, and extracts.

## Key Conventions

- **No framework CSS** — all styling is hand-written dark theme (`#070b11` base)
- **No router library** — hash-based routing via `window.location.hash`
- **No backend** — entirely static. Admin server is a local development convenience only
- **Chinese UI** — all user-facing text is zh-CN
- **Card qualities**: grey → green → blue → purple → gold → red (order matters for sorting)
- **Categories**: role, weapon, throwable, item, consume, buff
- **Images**: card PNGs in `public/assets/cards/{category}/`, faction icons in `public/assets/cards/fetters/`
- **Video guides**: manual curation from Douyin/Kuaishou; popularity is snapshot data, not live API
- **Lineup data**: 6 preset strategies hardcoded in `App.tsx` (`lineupBuilds` array) plus `data/recommended-lineups.json` for admin-managed additions
- **Intermediate workspace** `autochess_dump/` grows through each pipeline phase. Clean with `--clean` flag
