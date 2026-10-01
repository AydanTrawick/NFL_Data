"""Derive replay scenes, clearly defined production stats, and season chapters."""
import json, math
import pandas as pd
from common import ROOT,PROCESSED,PUBLIC,publish_json,write_json
from aggregate import n

def num(g,c):return pd.to_numeric(g[c],errors='coerce')
def mean(g,c):
 v=num(g,c).mean();return None if pd.isna(v) else round(float(v),2)
def flag(g,c):
 v=g[c].astype(str);known=v.isin(['True','False','T','F']);return round(float(v[known].isin(['True','T']).mean()),4) if known.any() else None

def main():
 d=pd.read_parquet(PROCESSED/'events.parquet');d['order']=num(d,'NEVENT');d=d.sort_values(['GAME_CODE','order']);d['team']=d.OFF_TEAM_ABBREV.str.upper();d['defTeam']=d.DEF_TEAM_ABBREV.str.upper()
 valid=d[(d.PLAY_CNTS==True)&(d.FROM_SCRIMMAGE==True)&d.EVENT_NAME.isin(['Run','Pass Completion','Incomplete Pass','Sack','Intercepted Pass'])].copy()
 games=json.loads((PUBLIC/'games.json').read_text());game_map={g['id']:g for g in games}
 # Clock and counting benchmark: DAL-PHI opener reconciles to NFL official totals.
 opener=valid[valid.GAME_CODE=='2879178'].groupby('team').size().to_dict()
 assert opener=={'DAL':56,'PHI':62},opener
 validation={'gameId':'2879178','officialOffensivePlays':opener,'source':'https://static.www.nfl.com/image/upload/v1757104719/gamecenter/f5908b6d-311e-11f0-b670-ae1250fadad1.pdf','definition':'PLAY_CNTS and FROM_SCRIMMAGE, limited to Run, Pass Completion, Incomplete Pass, Sack, Intercepted Pass','clock':'PLAY_START_TIME is seconds remaining in quarter; opener scoring timestamps reconcile to the NFL gamebook.'}
 publish_json('counting_validation.json',validation)
 scored=[];all_drives=[];chapters=[]
 for gid,g in d.groupby('GAME_CODE',sort=False):
  game=game_map[str(gid)];a=game['offense'].upper();b=game['defense'].upper();events=[];last_scores={a:0,b:0}
  for r in g.to_dict('records'):
   team=r['team'];opp=r['defTeam'];os=n(r['OFF_END_SCORE']);ds=n(r['DEF_END_SCORE']);before=dict(last_scores)
   for t,s in [(team,os),(opp,ds)]:
    if s is not None and r['PLAY_CNTS']==True:last_scores[t]=s
   delta={t:last_scores[t]-before.get(t,0) for t in last_scores};points=max(delta.values(),default=0);scorer=max(delta,key=delta.get) if points>0 else None
   name=' '.join(str(r.get(c,'')).strip() for c in ['SCORING_PLAYER_FIRST_NAME','SCORING_PLAYER_LAST_NAME']).strip()
   ev={'id':str(r['PLAY_UNIQUE_ID']),'order':n(r['NEVENT']),'driveId':str(r.get('DRIVE_ID','')),'driveKey':team+':'+str(r.get('DRIVE_ID','')),'team':team,'opponent':opp,'quarter':n(r['QUARTER']),'clock':n(r['PLAY_START_TIME']),'down':n(r['DOWN']),'yardsToGo':n(r['YTG']),'yardLine':n(r['YD_FROM_GOAL']),'yardsGained':n(r['YD_GAINED']),'hangTime':None if pd.isna(pd.to_numeric(r.get('HANG_TIME'),errors='coerce')) else float(r['HANG_TIME']),'offenseScore':n(r['OFF_START_SCORE']),'defenseScore':n(r['DEF_START_SCORE']),'scoreA':last_scores.get(a,0),'scoreB':last_scores.get(b,0),'scoring':points>0,'counts':bool(r['PLAY_CNTS']==True),'points':points,'scoringPlayer':name,'scoringTeam':scorer,'call':'Run' if r['EVENT_NAME']=='Run' else 'Pass' if r['EVENT_NAME'] in ['Pass Completion','Incomplete Pass','Sack','Intercepted Pass'] else 'Kick' if r['EVENT_NAME'] in ['Punt','Field Goal Attempt','Kick Off','Point after Touchdown'] else 'Event','result':r['EVENT_NAME']}
   # Named player for important non-scoring moments.
   if not ev['scoringPlayer']:
    role='PASSER' if ev['call']=='Pass' else 'RUSHER' if ev['call']=='Run' else 'KICKER'
    ev['scoringPlayer']=' '.join(str(r.get(role+'_'+x,'')) for x in ['FIRST_NAME','LAST_NAME']).strip()
   events.append(ev)
   if points>0:scored.append({**ev,'gameId':str(gid)})
  # Events preserve source order; score is always in the fixed A/B orientation.
  write_json(PUBLIC/'replays'/f'{gid}.json',events)
  for (team,did),dg in g[g.DRIVE_ID.ne('')].groupby(['team','DRIVE_ID'],sort=False):
   dg=dg[dg.FROM_SCRIMMAGE==True]
   if dg.empty:continue
   first,last=dg.iloc[0],dg.iloc[-1];matches=[e for e in events if e['team']==team and e['driveId']==str(did)];delta=sum(e['points'] for e in matches if e['scoringTeam']==team)
   res='TD' if any(e['points']==6 and e['scoringTeam']==team for e in matches) else 'FG' if any(e['points']==3 and e['scoringTeam']==team for e in matches) else 'Punt' if dg.EVENT_NAME.eq('Punt').any() else 'Turnover' if dg.EVENT_NAME.isin(['Intercepted Pass','Defense Recovers Fumb']).any() else str(last.EVENT_NAME)
   # Recovery events have the defense as their offense key and can sit outside the drive group.
   recovery=g[(g['order']>last['order']) & (g['order']<=last['order']+3) & (g.QUARTER==last.QUARTER) & (g.PLAY_START_TIME==last.PLAY_START_TIME) & (g.EVENT_NAME=='Defense Recovers Fumb') & (g.PLAY_CNTS==True)]
   if not recovery.empty and res not in ['TD','FG']:res='Turnover'
   elif n(last.DOWN)==4 and last.EVENT_NAME in ['Run','Pass Completion','Incomplete Pass','Sack'] and (n(last.YD_GAINED) or 0)<(n(last.YTG) or 0) and res not in ['TD','FG','Punt','Turnover']:res='Downs'
   start=n(first.YD_FROM_GOAL);end=n(last.YD_FROM_GOAL);gain=0 if last.EVENT_NAME in ['Punt','Field Goal Attempt'] else (n(last.YD_GAINED) or 0)
   all_drives.append({'gameId':str(gid),'driveId':str(did),'driveKey':team+':'+str(did),'team':team,'startYard':start,'endYard':max(0,min(100,(end or 0)-gain)) if end is not None else None,'events':len(dg),'firstEventId':str(first.PLAY_UNIQUE_ID),'order':int(first['order']),'result':res})
 publish_json('scoring_plays.json',scored);publish_json('drives.json',all_drives)
 teams=json.loads((PUBLIC/'teams_enriched.json').read_text());team_stats={}
 for team,g in valid.groupby('team'):
  defense=valid[valid.defTeam==team];cells=[]
  for down in range(1,5):
   for label,lo,hi in [('short',0,3),('medium',4,6),('standard',7,10),('long',11,100)]:
    s=g[(num(g,'DOWN')==down)&num(g,'YTG').between(lo,hi)];run=int(s.EVENT_NAME.eq('Run').sum());cells.append({'down':down,'distance':label,'run':run,'pass':len(s)-run,'total':len(s)})
  personnel={str(k):int(v) for k,v in g[g.PERSONNEL_PACKAGE.ne('')].PERSONNEL_PACKAGE.value_counts().items()}
  direction={str(k):int(v) for k,v in g[(g.EVENT_NAME=='Run')&g.INITIAL_RUN_DIRECTION.ne('')].INITIAL_RUN_DIRECTION.value_counts().items()}
  team_stats[team]={'team':team,'plays':len(g),'passRate':round(float(g.EVENT_NAME.ne('Run').mean()),4),'motionRate':flag(g,'IS_MOTION'),'screenRate':flag(g,'SCREEN_PASS'),'blitzFacedRate':flag(g,'BLITZ'),'blitzSentRate':flag(defense,'BLITZ'),'menInBox':mean(g,'MEN_IN_BOX'),'releaseTime':mean(g,'QB_RELEASE_TIME'),'heatmap':cells,'personnel':personnel,'directionCodes':direction,'yards':int(num(g,'YD_GAINED').sum())}
 publish_json('team_stats.json',team_stats)
 # Production measures use explicit, counted event classes. No inferred defender roles.
 people={}
 def person(name,team):
  return people.setdefault(name+'|'+team,{'name':name,'team':team,'attempts':0,'completions':0,'passingYards':0,'sacks':0,'carries':0,'receptions':0,'touches':0,'yards':0,'yac':0,'brokenTackles':0,'touchdowns':0,'qbHits':0,'releaseTimes':[],'roles':set()})
 for r in valid.to_dict('records'):
  ev=r['EVENT_NAME'];team=r['team'];yards=n(r['YD_GAINED']) or 0
  for role in ['PASSER','RUSHER','RECEIVER']:
   name=' '.join(str(r.get(role+'_'+x,'')) for x in ['FIRST_NAME','LAST_NAME']).strip()
   if not name:continue
   p=person(name,team);p['roles'].add(role)
   if role=='PASSER':
    if ev in ['Pass Completion','Incomplete Pass','Intercepted Pass']:p['attempts']+=1
    if ev=='Pass Completion':p['completions']+=1;p['passingYards']+=yards
    if ev=='Sack':p['sacks']+=1
    try:
     if r['QB_RELEASE_TIME']!='':p['releaseTimes'].append(float(r['QB_RELEASE_TIME']))
    except (ValueError,TypeError):pass
   touch=(role=='RUSHER' and ev=='Run')or(role=='RECEIVER' and ev=='Pass Completion')
   if touch:
    p['carries' if role=='RUSHER' else 'receptions']+=1;p['touches']+=1;p['yards']+=yards;p['yac']+=(n(r['YD_AFTER_CATCH']) or 0) if role=='RECEIVER' else 0;p['brokenTackles']+=n(r['BROKEN_TACKLES']) or 0
  for role in ['QB_HITTER','QB_HITTER2']:
   name=' '.join(str(r.get(role+'_'+x,'')) for x in ['FIRST_NAME','LAST_NAME']).strip()
   if name:p=person(name,r['defTeam']);p['roles'].add('DEFENDER');p['qbHits']+=1
 for s in scored:
  if s['points']==6 and s['scoringPlayer']:person(s['scoringPlayer'],s['scoringTeam'])['touchdowns']+=1
 old=json.loads((PUBLIC/'players_enriched.json').read_text());enrich={p['name']+'|'+p['team']:p for p in old};players=[]
 for key,p in people.items():
  r=enrich.get(key,{});p.update({k:r.get(k,'') for k in ['headshotUrl','position']});p['roles']=sorted(p['roles']);rt=p.pop('releaseTimes');p['releaseTime']=round(sum(rt)/len(rt),2) if rt else None;p['completionRate']=round(p['completions']/p['attempts'],4) if p['attempts'] else None;p['production']=p['yards']+p['passingYards']/4+p['touchdowns']*20+p['qbHits']*10;players.append(p)
 players.sort(key=lambda p:p['production'],reverse=True)
 for i,p in enumerate(players):p['tier']='LEGEND' if i<len(players)*.05 else 'ELITE' if i<len(players)*.2 else 'ROSTER'
 publish_json('player_stats.json',players)
 high=[p for p in players if p['touches']>=50];missing=[{'name':p['name'],'team':p['team'],'touches':p['touches']} for p in high if not p['headshotUrl']]
 publish_json('touch_match_report.json',{'playersWith50PlusTouches':len(high),'matched':len(high)-len(missing),'coverage':round((len(high)-len(missing))/max(1,len(high)),4),'unmatched':missing,'definition':'Counted rush attempts + completed receptions; returns excluded.'})
 dates=pd.to_datetime(d.GAME_DATE,format='%m-%d-%Y');stages=[('OPENING WEEK','The first statement.',(dates<'2025-09-10')),('MIDSEASON','The league takes shape.',(dates>='2025-09-10')&(dates<'2025-11-01')),('PLAYOFF RACE','Every yard matters.',(dates>='2025-11-01')&(d.GAME_TYPE_DESC=='Regular Season'))]
 for typ,title in [('Wild Card Playoff','WILD CARD'),('Divisional Playoff','DIVISIONAL'),('Conf. Championship','CONFERENCE CHAMPIONSHIP'),('Super Bowl','SUPER BOWL')]:
  assert typ in set(d.GAME_TYPE_DESC),f'Missing postseason type: {typ}'
  stages.append((title,'Win and keep moving.',d.GAME_TYPE_DESC.eq(typ)))
 for title,subtitle,mask in stages:
  g=d[mask];ids=set(g.GAME_CODE.astype(str));v=valid[valid.GAME_CODE.isin(ids)];best=v.loc[num(v,'YD_GAINED').idxmax()] if len(v) else None
  chapters.append({'title':title,'subtitle':subtitle,'games':len(ids),'plays':len(v),'yards':int(num(v,'YD_GAINED').sum()),'points':sum(s['points'] for s in scored if s['gameId'] in ids),'best':None if best is None else {'gameId':str(best.GAME_CODE),'team':best.team,'yards':n(best.YD_GAINED),'event':best.EVENT_NAME,'eventId':str(best.PLAY_UNIQUE_ID),'player':' '.join(str(best.get(('RUSHER' if best.EVENT_NAME=='Run' else 'RECEIVER')+'_'+part,'' )).strip() for part in ['FIRST_NAME','LAST_NAME']).strip(),'passer':' '.join(str(best.get('PASSER_'+part,'')).strip() for part in ['FIRST_NAME','LAST_NAME']).strip() if best.EVENT_NAME=='Pass Completion' else ''}})
 assert sum(c['games'] for c in chapters)==len(games),'Chapters must cover all games'
 publish_json('chapters.json',chapters)
 md=json.loads((PUBLIC/'metadata.json').read_text());md.update({'offensivePlays':len(valid),'offensiveYards':int(num(valid,'YD_GAINED').sum()),'touchdowns':sum(s['points']==6 for s in scored),'scoringEvents':len(scored)});publish_json('metadata.json',md)
 # Only aggregate tables enter the deployable Film Room database.
 analytics=ROOT/'data/analytics';analytics.mkdir(exist_ok=True)
 for name,rows in [('teams',[{k:v for k,v in t.items() if not isinstance(v,(dict,list))} for t in team_stats.values()]),('players',[{k:v for k,v in p.items() if not isinstance(v,(dict,list))} for p in players]),('games',games),('situations',[{'team':team,**c} for team,t in team_stats.items() for c in t['heatmap']])]:
  pd.DataFrame(rows).to_parquet(analytics/f'{name}.parquet',compression='zstd',index=False)
 print(f'Generated {len(games)} full replay timelines, {len(all_drives)} team-specific drives, {len(players)} production cards. Headshots: {len(high)-len(missing)}/{len(high)} eligible players.')
if __name__=='__main__':main()
