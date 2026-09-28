"""Preserve string codes; convert only columns whose nonempty values are all T/F."""
import pandas as pd
from common import SOURCE, PROCESSED, ROOT, write_json

def main():
    df=pd.read_csv(SOURCE,dtype=str,keep_default_na=False)
    empty=[c for c in df if df[c].eq('').all()]
    df=df.drop(columns=empty)
    flags=[]
    for c in df:
        vals=set(df[c].unique())-{''}
        if vals and vals <= {'T','F'}:
            df[c]=df[c].map({'T':True,'F':False}).astype('boolean');flags.append(c)
    PROCESSED.mkdir(parents=True,exist_ok=True)
    df.to_parquet(PROCESSED/'events.parquet',compression='zstd',index=False)
    codes=['FORM_AT_SNAP','PENALTY_TYPE','COVERAGE_CONCEPT','PLAY_CONCEPT','OFF_EVENT_ROLE1','OFF_EVENT_ROLE2','DEF_EVENT_ROLE1','DEF_EVENT_ROLE2','YD_TYPE','WHY_NO_CATCH','FUMBLE_CODE','UNIT','EXTRA_PLAY_TYPE','POCKET_LOC','PLAY_ACTION','HANDOFF_TYPE','PLAY_LOC','INITIAL_RUN_DIRECTION','SNAP_HASH']
    write_json(ROOT/'data/codebook.todo.json',{'undecoded':{c:sorted(str(v) for v in df[c].unique() if str(v)) for c in codes if c in df and c not in flags},'droppedEmptyColumns':empty,'booleanColumns':flags})
    print(f'Cleaned {len(df):,} rows × {len(df.columns)} columns; dropped {len(empty)} empty columns.')
if __name__=='__main__':main()
