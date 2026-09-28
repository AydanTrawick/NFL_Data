# EVERY SNAP

An event-level 2025 NFL season atlas built with Next.js 15 and TypeScript.

## Local setup

```sh
npm ci
python3 -m pip install -r requirements.txt
npm run data:build
npm run data:enrich
npm run build
npm run start
```

Open `http://localhost:3000`. For development, use `npm run dev`.

The data pipeline reads the source CSV from the iCloud path used for this project. Set `NFL_CSV=/path/to/nfl2025events.csv` to use another location. `data:build` creates a private cleaned Parquet file and browser-safe aggregate JSON. `data:enrich` caches nflverse team colors/logos and the 2025 weekly roster under ignored `data/external/`, then writes matched, minimized JSON outputs. The original event CSV is not copied into the app or served to browsers.

## Current scope

- Cinematic landing page, data notes, team hubs, game-flow summaries with a lazy-loaded 3D sampled-event field replay, playoff bracket, player search, and a Run/Pass mini-game.
- Team branding and player headshots are joined from nflverse at build time.
- Player-name mismatches are written to `data/processed/player_match_report.json`.
- `PLAY_CNTS` is reported as a source event flag, not a verified snap count. Unmapped numeric and letter codes stay undecoded in `data/codebook.todo.json`.

The replay animates a sampled event excerpt from each game's source events; it does not reconstruct every snap or verified drive sequence. It includes playback, speed, scrubbing, broadcast/All-22 camera framing, scorebug, team colors, scoring banners, and a small-screen 2D fallback. The supplied dataset does not include verified stadium coordinates, so the weather and stadium map are not included. Player pages provide searchable, enriched player identities and headshots, but not the brief's unverified role-specific production stat cards. The Film Room route explains that it is offline without a configured model key and safe query runtime.

The player headshot join report is in `data/processed/player_match_report.json`. The brief's ≥95% benchmark cannot be computed from this dataset because its player role appearances are not verified touches; matched coverage is reported without claiming that threshold.
