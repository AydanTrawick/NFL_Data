"""Cache nflverse teams/rosters and join by full player name plus team abbreviation.

Network access is required only for the first run. Raw enrichment downloads are kept in
data/external/ (never published); the outputs here contain the minimal public fields.
"""
import csv, json, re, ssl, urllib.request
import certifi
from pathlib import Path
from common import ROOT, PROCESSED, PUBLIC, write_json

EXTERNAL=ROOT/"data"/"external"
SOURCES={
  "teams_colors_logos.csv":"https://raw.githubusercontent.com/nflverse/nflverse-pbp/master/teams_colors_logos.csv",
  "roster_weekly_2025.csv":"https://github.com/nflverse/nflverse-data/releases/download/weekly_rosters/roster_weekly_2025.csv",
}

def fetch(name,url):
    path=EXTERNAL/name
    if not path.exists():
        EXTERNAL.mkdir(parents=True,exist_ok=True)
        req=urllib.request.Request(url,headers={"User-Agent":"every-snap-data-pipeline/1.0"})
        with urllib.request.urlopen(req,timeout=30,context=ssl.create_default_context(cafile=certifi.where())) as response: path.write_bytes(response.read())
    return path

def norm(s): return re.sub(r"[^a-z]","",(s or "").lower())

def main():
    try:
        team_path=fetch(*next((n,u) for n,u in SOURCES.items() if n.startswith("teams_")))
        roster_path=fetch(*next((n,u) for n,u in SOURCES.items() if n.startswith("roster_")))
    except Exception as e:
        raise SystemExit(f"nflverse enrichment unavailable ({e}). Retry pipeline/enrich.py when network access is available.")
    with team_path.open(encoding="utf-8-sig",newline="") as f:
        palette={r["team_abbr"].upper():{"name":r["team_name"],"color":r["team_color"],"secondaryColor":r["team_color2"],"logo":r["team_logo_espn"],"wordmark":r["team_wordmark"]} for r in csv.DictReader(f)}
    # Weekly roster may repeat a person; index by season team + normalized first/last name.
    roster={}
    with roster_path.open(encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            team=(r.get("team") or r.get("team_abbr") or "").upper()
            season=str(r.get("season",""))
            if season and season!="2025": continue
            full=(r.get("full_name") or r.get("display_name") or r.get("player_name") or "").strip()
            parts=full.split()
            if not parts: continue
            key=(team,norm(parts[0]),norm(" ".join(parts[1:])))
            roster.setdefault(key,r)
    players=json.loads((PROCESSED/"players.json").read_text(encoding="utf-8"))
    matched=[]; unmatched=[]
    for p in players:
        name=p["name"].split(); key=(p["team"],norm(name[0]) if name else "",norm(" ".join(name[1:])))
        r=roster.get(key)
        if r:
            p["headshotUrl"]=r.get("headshot_url") or r.get("headshot") or ""
            p["position"]=r.get("position") or r.get("pos") or ""
            p["matchedName"]=r.get("full_name") or r.get("display_name") or p["name"]
            if p["headshotUrl"]: matched.append(p)
            else: unmatched.append({"name":p["name"],"team":p["team"],"roles":p["roles"],"events":p["events"],"reason":"roster match has no headshot URL"})
        else:
            unmatched.append({"name":p["name"],"team":p["team"],"roles":p["roles"],"events":p["events"]})
    enriched_teams=json.loads((PROCESSED/"teams.json").read_text(encoding="utf-8"))
    for team in enriched_teams: team.update(palette.get(team["abbrev"],{}))
    write_json(PROCESSED/"players_enriched.json",matched); write_json(PUBLIC/"players_enriched.json",matched)
    write_json(PROCESSED/"teams_enriched.json",enriched_teams); write_json(PUBLIC/"teams_enriched.json",enriched_teams)
    write_json(PROCESSED/"player_match_report.json",{"matched":len(matched),"unmatched":len(unmatched),"unmatchedPlayers":unmatched})
    high=[p for p in players if p["events"]>=50]
    headshot_keys={p["name"]+"|"+p["team"] for p in matched}
    summary={"players":len(players),"headshotMatches":len(matched),"unmatched":len(unmatched),"playersWith50PlusRoleAppearances":len(high),"headshotMatchesAmong50PlusRoleAppearances":sum((p["name"]+"|"+p["team"]) in headshot_keys for p in high)}
    write_json(PROCESSED/"player_match_summary.json",summary); write_json(PUBLIC/"player_match_summary.json",summary)
    print(f"Team colors/logos: {sum(bool(t.get('logo')) for t in enriched_teams)}/{len(enriched_teams)}; player headshot/name matches: {len(matched)}/{len(players)} ({len(unmatched)} unmatched; see data/processed/player_match_report.json).")

if __name__=="__main__": main()
