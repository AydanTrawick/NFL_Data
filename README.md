# EVERY SNAP

An immersive atlas of the 2025 NFL season, built from 59,415 event records across 285 games.

## Run

```sh
npm ci
npm run build
npm start
```

Open http://localhost:3000. The committed aggregates make a fresh checkout runnable without the private source CSV. `npm run dev` starts development mode.

## Features

Seven-chapter season story; all-game library; complete event timelines with 3D field playback and a mobile/reduced-motion 2D fallback; synchronized score charts, drives and key moments; 32 team hubs; searchable, flippable player production cards and comparison; postseason matchups; Run/Pass quiz with local leaderboard; 36-venue season map and kickoff weather; SQL-backed Film Room with ten prepared questions.

## Data and regeneration

```sh
python3 -m pip install -r requirements.txt
NFL_CSV=/absolute/path/nfl2025events.csv npm run data:all
```

The raw CSV, full cleaned event Parquet, and external caches are ignored. Only minimized replay records and derived aggregates are published. `data/analytics` holds four small Parquet tables used by server-side DuckDB. Enrichment fetches nflverse rosters/branding, ESPN venue corrections and Open-Meteo historical weather at build time.

The offensive counting rule reconciles DAL 56 / PHI 62 with the NFL opening-game book. All 162 players with 50+ rushes plus receptions match a roster headshot. Source code meanings are never guessed: play-action splits and role-based defensive tackles remain unavailable pending a dictionary. See `/about-the-data` and `data/codebook.todo.json`. Replays are yardage illustrations, not tracking data.

## Film Room configuration

Copy `.env.example` to `.env.local`. The ten prepared questions work without credentials. Custom questions require `ANTHROPIC_API_KEY`. Daily AI question limits are currently disabled; the short-term throttle remains at 20 requests per minute per IP per server instance. Configure these privately in Vercel environment settings; never commit secrets. Queries are restricted to a single SELECT on approved aggregate tables, bounded to 500 rows, with a timeout and external DuckDB access disabled.

## Voice assistant

The site-wide ASK THE DATA button supports typed questions, browser speech recognition when available, and ElevenLabs audio replies. Configure `ELEVENLABS_API_KEY` and `ELEVENLABS_VOICE_ID` privately in Vercel; `ELEVENLABS_MODEL_ID` is optional. Custom questions also require the Film Room credentials above. Microphone input requires browser support and permission. Text answers remain available when voice generation fails. Redeploy after changing environment settings.

## Verification

```sh
npm test
npm run typecheck
npx playwright install chromium
npm run build && npm start
# In another terminal:
npm run test:e2e
```

GitHub Actions builds the app, runs 24 data/SQL checks, desktop/mobile Playwright and accessibility checks, then enforces landing Lighthouse performance >=85. Reports are uploaded as workflow artifacts. Local Chromium automation may be blocked by macOS sandbox policy; a skipped or blocked browser run is not a pass.

## Deployment and scope

Import this repository into Vercel as Next.js; `vercel.json` includes the API duration setting and Next's file tracing includes analytics Parquet. Deployments do not require the raw CSV. Custom AI remains disabled until provider credentials are configured.

The implementation uses custom CSS/SVG charts, server-side DuckDB and native Web Audio. It does not install the brief's optional external MCP tooling, Tailwind/shadcn, DuckDB-WASM, chart packages or Howler. Stadium count is 36 because this season includes international venues. Undecoded charting codes intentionally limit some requested statistics. A measured 60fps target and public deployment must be verified in the target environment.
