import pandas as pd
from metrics import compute
def rolling(text,window=128):
    tok=text.split(); rows=[]
    for start in range(0,max(1,len(tok)-window+1),max(1,window//2)):
        chunk=' '.join(tok[start:start+window]); r=compute(chunk,False)
        r.update(start_token=start,end_token=min(start+window,len(tok)),text=chunk); rows.append(r)
    return pd.DataFrame(rows)
