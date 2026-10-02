"""Additional sensitivity checks and unconditioned random excerpts, frozen separately."""
import hashlib,json,re,zlib
import numpy as np
import pandas as pd
from common import ROOT
from metrics import compute
from review_revision import spans,extra,compare,CFG

OUT=ROOT/'outputs/review_v2/final_review'
CONFIG=json.loads((ROOT/'final_review_config.json').read_text(encoding='utf8'))
LABELS=['ellipsis','symbolic_substitution','nonce_derivation','argument_omission','inference_marker','code_switching','telegraphic_syntax','compressed_reference']

def fixed_slices(value,width):
    if len(value)<width:return []
    return [value[i:i+width] for i in sorted({0,(len(value)-width)//2,len(value)-width})]

def complete(frame,models):
    counts=frame.groupby('core_id').model.nunique()
    return frame[frame.core_id.isin(counts[counts.eq(models)].index)].copy()

def random_bank(data):
    rng=np.random.default_rng(CONFIG['seed'])
    selected=rng.choice(sorted(data.core_id.unique()),CONFIG['random_questions'],replace=False)
    rows=[]
    for i,r in enumerate(data[data.core_id.isin(selected)].sort_values(['core_id','model']).itertuples(),1):
        tokens=list(re.finditer(r'\S+',r.reasoning));width=min(CONFIG['random_excerpt_max_tokens'],len(tokens))
        start=int(rng.integers(0,len(tokens)-width+1));a=tokens[start].start();b=tokens[start+width-1].end()
        rows.append({'annotation_id':f'R{i:03d}','core_id':r.core_id,'model':r.model,'task':r.task,'start_char':a,'end_char':b,'start_token':start,'excerpt_tokens':width,'excerpt':r.reasoning[a:b],'question':r.input,'preceding':r.reasoning[max(0,a-250):a],'following':r.reasoning[b:b+250],**{k:'' for k in LABELS},'evidence':'','notes':'','annotator':''})
    return pd.DataFrame(rows)

def cooccurrence(data):
    a=data[LABELS].astype(int)
    return a.T.dot(a)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    d=pd.read_parquet(ROOT/'outputs/review_v2/all_common_traces.parquet');rows={k:[] for k in ['tokens64','characters800','bytes800']}
    for i,r in enumerate(d.itertuples()):
        base={'core_id':r.core_id,'model':r.model,'task':r.task}
        w=spans(r.reasoning,CONFIG['token_width'])
        if w:
            values=[{**compute(x['text'],False),**extra(x['text'])} for x in w]
            rows['tokens64'].append({**base,**{k:float(np.mean([v[k] for v in values])) for k in CFG['primary_metrics']}})
        for key,value,width in [('characters800',r.reasoning,CONFIG['character_width']),('bytes800',r.reasoning.encode('utf8'),CONFIG['byte_width'])]:
            windows=fixed_slices(value,width)
            if windows:
                raw=[x.encode('utf8') if isinstance(x,str) else x for x in windows]
                rows[key].append({**base,'zlib_ratio':float(np.mean([len(zlib.compress(x,9))/len(x) for x in raw])),'mean_raw_bytes':float(np.mean([len(x) for x in raw]))})
        if i%3000==0:print('Sensitivity traces',i,flush=True)
    status=[]
    for key,records in rows.items():
        frame=complete(pd.DataFrame(records),d.model.nunique());frame.to_parquet(OUT/(key+'.parquet'),index=False)
        metrics=CFG['primary_metrics'] if key=='tokens64' else ['zlib_ratio']
        compare(frame,metrics,CFG['bootstrap_repetitions']).to_csv(OUT/(key+'_paired.csv'),index=False)
        frame.groupby('model')[metrics].median().to_csv(OUT/(key+'_medians.csv'))
        status.append({'mode':key,'questions':int(frame.core_id.nunique()),'excluded_questions':int(d.core_id.nunique()-frame.core_id.nunique()),'tasks':int(frame.task.nunique()),'rows':len(frame)})
    bank=random_bank(d);bank.to_csv(ROOT/'data/annotations/random_bank.csv',index=False)
    blind=bank.drop(columns=['model','start_token','excerpt_tokens'])
    for label in LABELS:blind[label+'_unsure']=''
    blind.to_csv(ROOT/'data/annotations/random_blind.csv',index=False)
    coded=pd.read_csv(ROOT/'data/annotations/annotation_coded.csv')
    cooccurrence(coded).to_csv(OUT/'cooccurrence_enriched96.csv')
    old=pd.read_csv(ROOT/'data/annotations/second_annotator_blind.csv')
    for label in LABELS:old[label+'_unsure']=''
    old.to_csv(ROOT/'data/annotations/second_annotator_blind.csv',index=False)
    summary={'sensitivity':status,'random_fragments':len(bank),'random_questions':int(bank.core_id.nunique()),'random_selection':CONFIG['random_population'],'random_seed':CONFIG['seed'],'configuration_sha256':hashlib.sha256((ROOT/'final_review_config.json').read_bytes()).hexdigest(),'human_agreement':'pending; no independent human annotations available','cooccurrence_status':'initial AI-assisted coding; enriched 96 excerpts'}
    (OUT/'manifest.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
