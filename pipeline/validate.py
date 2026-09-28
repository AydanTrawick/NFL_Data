import json
import pandas as pd
from common import PROCESSED,write_json

def main():
 d=pd.read_parquet(PROCESSED/'events.parquet');g=json.loads((PROCESSED/'games.json').read_text());t=json.loads((PROCESSED/'teams.json').read_text());sb=next(x for x in g if x['type']=='Super Bowl')
 assert len(d)==59415 and d.PLAY_UNIQUE_ID.nunique()==len(d)
 assert len(g)==285 and len(t)==32
 assert sorted([sb['offenseScore'],sb['defenseScore']])==[13,29]
 report={'eventRows':len(d),'games':len(g),'teams':len(t),'superBowl':sb,'status':'passed','caveat':'PLAY_CNTS includes special-teams events; it is not an offensive snap total.'}
 write_json(PROCESSED/'validation.json',report);print(json.dumps(report,indent=2))
if __name__=='__main__':main()
