"""Create browser-safe season aggregates from cleaned events."""
import pandas as pd
from common import PROCESSED, publish_json

def n(v):
    try:
        if pd.isna(v) or v == "": return None
        return int(float(v))
    except (ValueError, TypeError): return None

def main():
    df = pd.read_parquet(PROCESSED / "events.parquet")
    df["NEVENT_NUM"] = pd.to_numeric(df["NEVENT"], errors="coerce")
    df = df.sort_values(["GAME_CODE", "NEVENT_NUM"], kind="stable")
    games=[]
    for code, g in df.groupby("GAME_CODE", sort=True):
        first,last=g.iloc[0],g.iloc[-1]
        games.append({"id":str(code),"date":str(first.get("GAME_DATE","")),"type":str(first.get("GAME_TYPE_DESC","")),
          "week":n(first.get("WEEK_NUM")),"home":str(first.get("HOME_TEAM_ABBREV", "")),"away":str(first.get("VISITOR_TEAM_ABBREV", "")),
          "offense":str(last.get("OFF_TEAM_ABBREV","")),"defense":str(last.get("DEF_TEAM_ABBREV","")),
          "offenseScore":n(last.get("OFF_END_SCORE")),"defenseScore":n(last.get("DEF_END_SCORE")),
          "events":int(len(g)),"countedPlays":int((g.get("PLAY_CNTS", pd.Series(False,index=g.index)) == True).sum())})
    teams={}
    for side in ["OFF","DEF"]:
        abbr,name=side+"_TEAM_ABBREV",side+"_TEAM_NAME"
        for a,g in df.groupby(abbr):
            key=str(a).upper()
            if not key: continue
            entry=teams.setdefault(key,{"abbrev":key,"name":str(g[name].dropna().iloc[0]) if name in g and len(g[name].dropna()) else key,"events":0,"countedPlays":0,"games":set()})
            entry["events"]+=len(g); entry["countedPlays"]+=int((g.get("PLAY_CNTS",pd.Series(False,index=g.index)) == True).sum()); entry["games"].update(g["GAME_CODE"].astype(str).unique())
    # Keep interpretable aggregates only; all direction/personnel code fields stay out of labels.
    team_records=[]
    df["OFF_ABBREV_NORMALIZED"]=df["OFF_TEAM_ABBREV"].str.upper()
    counted_plays=df[(df["PLAY_CNTS"]==True)&df["EVENT_NAME"].isin(["Run","Pass Completion","Incomplete Pass","Sack","Intercepted Pass"])]
    event_counts_by_team=counted_plays.groupby(["OFF_ABBREV_NORMALIZED","EVENT_NAME"]).size()
    for t in teams.values():
        a=t["abbrev"]
        event_counts=event_counts_by_team.loc[a] if a in event_counts_by_team.index.get_level_values(0) else pd.Series(dtype="int64")
        total=int(event_counts.sum()); run=int(event_counts.get("Run",0)); passed=int(total-run)
        games_played=[g for g in games if a in (g["offense"].upper(),g["defense"].upper())]
        wins=losses=ties=0
        for game in games_played:
            score=game["offenseScore"]; other=game["defenseScore"]
            if score is None or other is None: continue
            own_score,opp_score=(score,other) if game["offense"].upper()==a else (other,score)
            wins += own_score>opp_score; losses += own_score<opp_score; ties += own_score==opp_score
        t.update({"games":len(games_played),"wins":wins,"losses":losses,"ties":ties,"runEvents":run,"passEvents":passed,"runPassPlays":total,"passRate":round(passed/total,4) if total else None})
        team_records.append(t)
    team_list=sorted([{**t,"games":int(t["games"])} for t in team_records], key=lambda x:x["abbrev"])
    player_cols=[("PASSER","PASSER_FIRST_NAME","PASSER_LAST_NAME"),("RUSHER","RUSHER_FIRST_NAME","RUSHER_LAST_NAME"),("RECEIVER","RECEIVER_FIRST_NAME","RECEIVER_LAST_NAME"),("DEFENDER","DEFENDER_FIRST_NAME","DEFENDER_LAST_NAME"),("SCORING_PLAYER","SCORING_PLAYER_FIRST_NAME","SCORING_PLAYER_LAST_NAME")]
    people={}
    for role,first,last in player_cols:
        if first not in df or last not in df: continue
        subset=df[(df[first]!="")&(df[last]!="")]
        for _,row in subset.iterrows():
            name=f"{row[first]} {row[last]}".strip(); team=str(row.get("DEF_TEAM_ABBREV" if role=="DEFENDER" else "OFF_TEAM_ABBREV","" )).upper(); ident=name+"|"+team
            p=people.setdefault(ident,{"name":name,"team":team,"roles":set(),"events":0})
            p["roles"].add(role); p["events"]+=1
    players=sorted([{**p,"roles":sorted(p["roles"])} for p in people.values()],key=lambda x:(x["name"],x["team"]))
    # Retain game event sequences only as compact drive summaries; no raw event table is browser-published.
    drives=[]
    if "DRIVE_ID" in df:
        valid=df[df["DRIVE_ID"].notna()&(df["DRIVE_ID"]!="")]
        for (game,drive),g in valid.groupby(["GAME_CODE","DRIVE_ID"],sort=True):
            g=g.sort_values("NEVENT_NUM"); f,l=g.iloc[0],g.iloc[-1]
            drives.append({"gameId":str(game),"driveId":str(drive),"team":str(f.get("OFF_TEAM_ABBREV","" )).upper(),"startYard":n(f.get("YD_FROM_GOAL")),"endYard":n(l.get("YD_FROM_GOAL")),"events":len(g),"countedPlays":int((g.get("PLAY_CNTS",pd.Series(False,index=g.index)) == True).sum()),"result":str(l.get("EVENT_NAME",""))})
    situations=[]
    call_examples=[]
    if "DOWN" in df and "YTG" in df:
        plays=df[df["PLAY_CNTS"]==True].copy()
        plays["DOWN_NUM"]=pd.to_numeric(plays["DOWN"],errors="coerce"); plays["YTG_NUM"]=pd.to_numeric(plays["YTG"],errors="coerce")
        plays=plays.dropna(subset=["DOWN_NUM","YTG_NUM"])
        plays["distance"] = pd.cut(plays["YTG_NUM"],[-1,3,6,10,100],labels=["short","medium","standard","long"]).astype(str)
        for (down,distance),g in plays.groupby(["DOWN_NUM","distance"],observed=True):
            situations.append({"down":int(down),"distance":distance,"plays":len(g),"run":int(g["EVENT_NAME"].isin(["Run"]).sum()),"pass":int(g["EVENT_NAME"].isin(["Pass Completion","Incomplete Pass","Sack","Intercepted Pass"]).sum())})
        # Real, legible scrimmage call examples for the mini-game. Exclude continuation/non-scrimmage events.
        candidates=df[(df["PLAY_CNTS"]==True)&(df["FROM_SCRIMMAGE"]==True)&df["EVENT_NAME"].isin(["Run","Pass Completion","Incomplete Pass","Sack","Intercepted Pass"])].copy()
        candidates["DOWN_NUM"]=pd.to_numeric(candidates["DOWN"],errors="coerce"); candidates["YTG_NUM"]=pd.to_numeric(candidates["YTG"],errors="coerce")
        candidates=candidates.dropna(subset=["DOWN_NUM","YTG_NUM"])
        for r in candidates.sample(min(len(candidates),5000),random_state=2025).to_dict(orient="records"):
            event=str(r["EVENT_NAME"]); call="Run" if event=="Run" else "Pass"
            call_examples.append({"gameId":str(r["GAME_CODE"]),"driveId":str(r.get("DRIVE_ID","")),"team":str(r["OFF_TEAM_ABBREV"]).upper(),"quarter":n(r.get("QUARTER")),"clock":n(r.get("PLAY_START_TIME")),"down":int(r["DOWN_NUM"]),"yardsToGo":int(r["YTG_NUM"]),"yardLine":n(r.get("YD_FROM_GOAL")),"yardsGained":n(r.get("YD_GAINED")),"offenseScore":n(r.get("OFF_START_SCORE")),"defenseScore":n(r.get("DEF_START_SCORE")),"scoring":r.get("IS_SCORING_PLAY")==True,"scoringPlayer":" ".join(str(r.get(c,"")).strip() for c in ["SCORING_PLAYER_FIRST_NAME","SCORING_PLAYER_LAST_NAME"] if str(r.get(c,"")).strip()),"call":call,"result":event})
    scoring=[]
    if "IS_SCORING_PLAY" in df:
        for r in df[df["IS_SCORING_PLAY"]==True].to_dict(orient="records"):
            scoring.append({"gameId":str(r["GAME_CODE"]),"event":str(r.get("EVENT_NAME","")),"team":str(r.get("OFF_TEAM_ABBREV","" )).upper(),"quarter":n(r.get("QUARTER")),"clock":n(r.get("PLAY_START_TIME")),"offenseScore":n(r.get("OFF_END_SCORE")),"defenseScore":n(r.get("DEF_END_SCORE")),"player":" ".join(str(r.get(c,"")).strip() for c in ["SCORING_PLAYER_FIRST_NAME","SCORING_PLAYER_LAST_NAME"] if str(r.get(c,"")).strip())})
    publish_json("play_situations.json",call_examples); publish_json("scoring_plays.json",scoring)
    publish_json("games.json",games); publish_json("teams.json",team_list); publish_json("players.json",players); publish_json("drives.json",drives); publish_json("situations.json",situations)
    counted = df[df["PLAY_CNTS"] == True].groupby("GAME_CODE").size()
    sb = next((g for g in games if g["type"] == "Super Bowl"), None)
    publish_json("metadata.json", {"eventRows":len(df),"columnsRetained":len(df.columns)-2,"uniqueEventIds":int(df["PLAY_UNIQUE_ID"].nunique()),"countedEvents":int(len(df[df["PLAY_CNTS"]==True])),"scoringEvents":len(scoring),"countedEventsPerGame":{"min":int(counted.min()),"max":int(counted.max())},"gameTypes":{str(k):int(v) for k,v in df.groupby("GAME_TYPE_DESC")["GAME_CODE"].nunique().items()},"superBowl":sb})
    print(f"Aggregates: {len(games)} games, {len(team_list)} teams, {len(players)} player identities, {len(drives)} drives, {len(situations)} situations.")

if __name__ == "__main__": main()
