"""Join cached schedule + stadium coordinates, then archive hourly weather per venue."""
import csv,json,urllib.parse,urllib.request,ssl,certifi,hashlib,time
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from common import ROOT,PUBLIC,PROCESSED,publish_json,write_json
from enrich import fetch

def main():
 schedule=fetch('nflverse_schedule.csv','https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv')
 coords=fetch('stadiums.csv','https://github.com/user-attachments/files/17464644/stadiums.csv')
 rows=[r for r in csv.DictReader(schedule.open()) if r['season']=='2025']
 for r in rows:
  for k in ['away_team','home_team']:r[k]={'LA':'LAR','WSH':'WAS'}.get(r[k],r[k])
 venues={r['stadium_id']:r for r in csv.DictReader(coords.open())}
 overrides=json.loads((ROOT/'data/venue_overrides.json').read_text())
 # ESPN corrects neutral-site stadiums that the schedule still labels with home venues.
 for r in rows:
  if r['location']!='Neutral' or r['game_type']=='SB':continue
  try:
   summary=json.loads(fetch('espn_'+r['espn']+'.json','https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event='+r['espn']).read_text())
   venue=summary['gameInfo']['venue'];name=venue['fullName'];city=venue['address']['city'];country=venue['address']['country'];sid='ESPN'+venue['id']
   known=next((v for v in venues.values() if ('tottenham' in name.lower() and 'tottenham' in v.get('stadium_name','').lower()) or v.get('stadium_name','').lower()==name.lower()),None)
   if not known and name in overrides:known={**overrides[name],'city':city,'country':country}
   if not known:
    query=urllib.parse.urlencode({'q':name+' '+city,'format':'json','limit':1})
    geo=json.loads(fetch('geo_'+sid+'.json','https://nominatim.openstreetmap.org/search?'+query).read_text());time.sleep(1.1)
    if geo:known={'latitude':geo[0]['lat'],'longitude':geo[0]['lon'],'city':city,'country':country}
   if known:venues[sid]=known
   r['stadium_id']=sid;r['stadium']=name;r['roof']='unknown'
  except Exception as e:print('Neutral venue unavailable',r['espn'],str(e));r['stadium_id']='UNVERIFIED_'+r['espn'];r['stadium']='Neutral venue not verified';r['roof']='unknown'
 games=json.loads((PUBLIC/'games.json').read_text());matched={};stadiums={}
 for game in games:
  date=datetime.strptime(game['date'],'%m-%d-%Y').strftime('%Y-%m-%d');teams={game['offense'].upper(),game['defense'].upper()}
  r=next((r for r in rows if r['gameday']==date and {r['away_team'],r['home_team']}==teams),None)
  if not r:continue
  v=venues.get(r['stadium_id']);sid=r['stadium_id'];kickoff=datetime.fromisoformat(date+'T'+(r['gametime'] or '13:00')).replace(tzinfo=ZoneInfo('America/New_York')).astimezone(ZoneInfo('UTC'))
  game.update({'home':r['home_team'],'away':r['away_team'],'week':int(r['week'])})
  match={'stadiumId':sid,'stadium':r['stadium'],'roof':r['roof'],'isDome':r['roof'] in ['dome','closed'],'kickoff':kickoff.isoformat(),'weather':None,'source':'https://github.com/nflverse/nfldata/blob/master/data/games.csv','espnId':r['espn']}
  if v:
   match.update({'lat':float(v['latitude']),'lon':float(v['longitude'])})
   venue=stadiums.setdefault(sid,{'id':sid,'name':r['stadium'],'lat':float(v['latitude']),'lon':float(v['longitude']),'city':v['city'],'country':v['country'],'isDome':match['isDome'],'points':0,'games':[]})
   venue['games'].append(game['id']);venue['points']+=(game['offenseScore']or 0)+(game['defenseScore']or 0)
  matched[game['id']]=match
 def weather(sid):
  ms=[m for m in matched.values() if m['stadiumId']==sid and not m['isDome']];v=stadiums[sid]
  if not ms:return sid,None
  dates=[m['kickoff'][:10] for m in ms];params={'latitude':v['lat'],'longitude':v['lon'],'start_date':min(dates),'end_date':(datetime.fromisoformat(max(dates))+timedelta(days=1)).date().isoformat(),'hourly':'temperature_2m,precipitation,wind_speed_10m','temperature_unit':'fahrenheit','wind_speed_unit':'mph','timezone':'UTC'}
  try:
   p=fetch('weather_'+sid+'_'+hashlib.sha256(urllib.parse.urlencode(params).encode()).hexdigest()[:10]+'.json','https://archive-api.open-meteo.com/v1/archive?'+urllib.parse.urlencode(params));return sid,json.loads(p.read_text())
  except Exception as e:return sid,{'error':str(e)}
 errors=[]
 with ThreadPoolExecutor(max_workers=3) as pool:
  for task in as_completed([pool.submit(weather,sid) for sid in stadiums]):
   sid,w=task.result()
   if not w:continue
   if 'hourly' not in w:errors.append({'stadium':sid,'error':w.get('error')});continue
   h=w['hourly'];lookup={t:i for i,t in enumerate(h['time'])}
   for m in matched.values():
    if m['stadiumId']!=sid or m['isDome']:continue
    rounded=(datetime.fromisoformat(m['kickoff'])+timedelta(minutes=30)).replace(minute=0,second=0);key=rounded.strftime('%Y-%m-%dT%H:%M');i=lookup.get(key)
    if i is not None:m['weather']={'temperatureF':h['temperature_2m'][i],'windMph':h['wind_speed_10m'][i],'precipitationMm':h['precipitation'][i],'hourUTC':key,'source':'Open-Meteo historical reanalysis'}
 publish_json('games.json',games);publish_json('game_venues.json',matched);publish_json('stadiums.json',list(stadiums.values()));write_json(ROOT/'data/stadiums.json',list(stadiums.values()));write_json(PROCESSED/'weather_report.json',{'matchedGames':len(matched),'withWeather':sum(bool(m['weather']) for m in matched.values()),'domeGames':sum(m['isDome'] for m in matched.values()),'errors':errors})
 print('Venue/weather join:',len(matched),'games;',len(stadiums),'venues;',len(errors),'weather fetch errors')
if __name__=='__main__':main()
