"""Fixed-window paired corpus revision following external review."""
import hashlib,itertools,json,logging,re,time
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import rankdata,wilcoxon,spearmanr
from statsmodels.stats.multitest import multipletests
from common import ROOT
from metrics import compute

CFG=json.loads((ROOT/'review_config.json').read_text(encoding='utf8'))
OUT=ROOT/'outputs/review_v2'
OPS=set('=+−*/×÷<>≤≥≠≈∑∏√∞→←↔⇒⇔^%')
METRICS=CFG['primary_metrics']+CFG['secondary_metrics']

def dump(v,name):
    (OUT/name).write_text(json.dumps(v,ensure_ascii=False,indent=2,default=str),encoding='utf8')

def extra(text):
    nonspace=[c for c in text if not c.isspace()]; latin=[c for c in text if c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ']
    runs=re.findall(r'\S+',text)
    return {'whitespace_ratio':sum(c.isspace() for c in text)/max(1,len(text)),
      'uppercase_ratio':sum(c.isupper() for c in latin)/max(1,len(latin)),
      'operator_arrow_density':sum(c in OPS for c in nonspace)/max(1,len(nonspace)),
      'mean_run_without_whitespace':float(np.mean([len(r) for r in runs])) if runs else 0.}

def spans(text,width):
    tokens=list(re.finditer(r'\S+',text));n=len(tokens)
    if n<width:return []
    starts=sorted(set([0,(n-width)//2,n-width]));out=[]
    for start in starts:
        a=tokens[start].start();b=tokens[start+width-1].end()
        out.append({'start_token':start,'end_token':start+width,'start_char':a,'end_char':b,'text':text[a:b]})
    return out

def matched_all(b):
    b=b[b.scope.eq('baseline') & b.reasoning.fillna('').str.strip().ne('')].copy()
    assert not b.duplicated(['model','core_id']).any()
    models=sorted(b.model.unique());counts=b.groupby('core_id').model.nunique()
    ids=counts[counts.eq(len(models))].index
    d=b[b.core_id.isin(ids)].sort_values(['core_id','model']).reset_index(drop=True)
    d['task']=d.core_id.str.replace(r'_\d+$','',regex=True)
    return d

def bootstrap_indices(tasks,repetitions):
    rng=np.random.default_rng(CFG['seed']);groups=[np.flatnonzero(np.asarray(tasks)==t) for t in sorted(set(tasks))]
    return [np.concatenate([rng.choice(groups[j],len(groups[j]),replace=True) for j in rng.integers(0,len(groups),len(groups))]) for _ in range(repetitions)]

def compare(d,metrics,repetitions=1000):
    cores=sorted(d.core_id.unique());tasks=d.drop_duplicates('core_id').set_index('core_id').loc[cores,'task'].to_numpy()
    boot=bootstrap_indices(tasks,repetitions);rows=[]
    for metric in metrics:
        p=d.pivot(index='core_id',columns='model',values=metric).loc[cores]
        assert p.notna().all().all()
        for a,b in itertools.combinations(p.columns,2):
            dif=(p[a]-p[b]).to_numpy();nz=dif[dif!=0];ranks=rankdata(abs(nz))
            rbc=float(np.sum(np.sign(nz)*ranks)/ranks.sum()) if len(nz) else 0.
            pv=float(wilcoxon(dif,method='approx').pvalue) if len(nz) else 1.
            ci=np.quantile([np.median(dif[idx]) for idx in boot],[.025,.975])
            rows.append({'metric':metric,'model_a':a,'model_b':b,'paired_n':len(dif),'tasks':len(set(tasks)),'median_paired_difference':float(np.median(dif)),'ci95_low':float(ci[0]),'ci95_high':float(ci[1]),'rank_biserial':rbc,'p_raw':pv,'bootstrap_unit':'task→question paired'})
    r=pd.DataFrame(rows);r['p_holm']=multipletests(r.p_raw,method='holm')[1]
    return r

def main():
    for path in [OUT,OUT/'tables',OUT/'figures',ROOT/'data/annotations'] :path.mkdir(parents=True,exist_ok=True)
    started=time.time();logging.info('Review revision started config=%s',CFG)
    base=ROOT/'data/interim/all_baselines.parquet'
    if not base.exists():
        from audit_data import audit
        b=audit()
    else:b=pd.read_parquet(base)
    d=matched_all(b);d.to_parquet(OUT/'all_common_traces.parquet',index=False)
    full=[];windows=[];whole_cache={}
    for i,r in enumerate(d.itertuples()):
        v=compute(r.reasoning,False);v.update(extra(r.reasoning));whole_cache[(r.core_id,r.model)]=v
        full.append({'core_id':r.core_id,'model':r.model,'task':r.task,'benchmark':r.benchmark,**v})
        for width in [CFG['primary_width']]+CFG['sensitivity_widths']:
            for win in spans(r.reasoning,width):
                v=compute(win['text'],False);v.update(extra(win['text']))
                windows.append({'core_id':r.core_id,'model':r.model,'task':r.task,'benchmark':r.benchmark,'width':width,**win,**v})
        if i%500==0:logging.info('Review raw windows %d/%d elapsed=%.1fs',i,len(d),time.time()-started)
    full=pd.DataFrame(full);full.to_parquet(OUT/'whole_trace_metrics.parquet',index=False)
    raw=pd.DataFrame(windows);raw.to_parquet(OUT/'raw_windows.parquet',index=False)
    aggregates=[];eligibility=[]
    for width in [CFG['primary_width']]+CFG['sensitivity_widths']:
        w=raw[raw.width.eq(width)];agg=w.groupby(['core_id','model','task','benchmark'],as_index=False)[METRICS+['raw_bytes','compressed_bytes']].mean()
        counts=agg.groupby('core_id').model.nunique();ids=counts[counts.eq(d.model.nunique())].index
        agg=agg[agg.core_id.isin(ids)].copy();agg['width']=width;aggregates.append(agg)
        nwin=w.groupby(['core_id','model']).size();agg['n_windows']=agg.set_index(['core_id','model']).index.map(nwin)
        agg.to_csv(OUT/'tables'/f'fixed_window_{width}.csv',index=False)
        paired=compare(agg,CFG['primary_metrics'],CFG['bootstrap_repetitions']);paired['width']=width
        paired.to_csv(OUT/'tables'/f'paired_{width}.csv',index=False)
        agg.groupby('model')[METRICS].median().to_csv(OUT/'tables'/f'medians_{width}.csv')
        eligibility.append({'width':width,'complete_questions':len(ids),'excluded_short_questions':d.core_id.nunique()-len(ids),'paired_rows':len(agg),'tasks':agg.task.nunique(),'raw_windows_included':int(agg.n_windows.sum())})
        logging.info('Review window width=%d eligible=%d',width,len(ids))
    a=pd.concat(aggregates,ignore_index=True);a.to_parquet(OUT/'fixed_window_metrics.parquet',index=False)
    full.groupby('model')[['whitespace_tokens']+METRICS].median().to_csv(OUT/'tables/whole_trace_medians.csv')
    primary=a[a.width.eq(CFG['primary_width'])]
    full[full.core_id.isin(primary.core_id.unique())].groupby('model')[['whitespace_tokens']+METRICS].median().to_csv(OUT/'tables/whole_trace_medians_primary128.csv')
    key=primary[['core_id','model']];short=d.merge(key,on=['core_id','model'],validate='one_to_one')
    first=raw[raw.width.eq(CFG['primary_width'])&raw.start_token.eq(0)].merge(key,on=['core_id','model'])
    compare(first,CFG['primary_metrics'],CFG['bootstrap_repetitions']).to_csv(OUT/'tables/sensitivity_first_only.csv',index=False)
    latin=short.groupby('core_id').reasoning.apply(lambda s:all(len(re.findall(r'[A-Za-z]',x))/max(1,len(re.findall(r'[^\W\d_]',x)))>=.95 for x in s))
    english=primary[primary.core_id.isin(latin[latin].index)]
    compare(english,CFG['primary_metrics'],CFG['bootstrap_repetitions']).to_csv(OUT/'tables/sensitivity_latin95.csv',index=False)
    primary_checks={'all_shared_questions_used':d.core_id.nunique()==3022,'paired_models':bool(d.groupby('core_id').model.nunique().eq(4).all()),'exact_complete_windows':bool(raw.whitespace_tokens.eq(raw.width).all()),'raw_spans_match':bool(all(r.text==d[(d.core_id==r.core_id)&(d.model==r.model)].iloc[0].reasoning[r.start_char:r.end_char] for r in raw.sample(min(100,len(raw)),random_state=CFG['seed']).itertuples())),'finite_metrics':bool(np.isfinite(a[METRICS]).all().all()),'no_correctness_inference':True}
    assert all(primary_checks.values()),primary_checks
    dump({'questions':int(d.core_id.nunique()),'rows':len(d),'models':sorted(d.model.unique()),'tasks':int(d.task.nunique()),'eligibility':eligibility,'primary_checks':primary_checks,'whole_length_ratio_rho':float(spearmanr(full.whitespace_tokens,full.zlib_ratio).statistic),'sensitivity_latin95_questions':int(english.core_id.nunique()),'elapsed_seconds':time.time()-started,'analysis_config_sha256':hashlib.sha256((ROOT/'review_config.json').read_bytes()).hexdigest()},'manifest.json')
    prepare_annotation(d,primary,raw)
    logging.info('Review analysis complete elapsed=%.1f',time.time()-started)

def prepare_annotation(d,primary,raw):
    rng=np.random.default_rng(CFG['seed']);q=primary.groupby('core_id')[['symbol_density','punctuation_density']].max();picked=[];strata={}
    for stratum,metric in [('high_symbol_density','symbol_density'),('high_punctuation_density','punctuation_density'),('seeded_random',None)]:
        available=q[~q.index.isin(picked)]
        ids=list(available.sort_values(metric,ascending=False,kind='stable').head(8).index) if metric else list(rng.choice(sorted(available.index),8,replace=False))
        picked+=ids;strata.update({i:stratum for i in ids})
    rows=[]
    for i,r in enumerate(d[d.core_id.isin(picked)].sort_values(['core_id','model']).itertuples()):
        w=raw[(raw.core_id==r.core_id)&(raw.model==r.model)&(raw.width==CFG['primary_width'])].sort_values(['symbol_density','start_token'],ascending=[False,True]).iloc[0]
        positions=list(re.finditer(r'\S+',w.text));end=positions[min(CFG['annotation_excerpt_tokens'],len(positions))-1].end();excerpt=w.text[:end]
        rows.append({'annotation_id':f'A{i+1:03d}','core_id':r.core_id,'model':r.model,'task':r.task,'stratum':strata[r.core_id],'start_char':int(w.start_char),'end_char':int(w.start_char+end),'excerpt':excerpt,'question':r.input,'preceding':r.reasoning[max(0,w.start_char-250):w.start_char],'following':r.reasoning[w.start_char+end:w.start_char+end+250],'ellipsis':'','symbolic_substitution':'','nonce_derivation':'','argument_omission':'','inference_marker':'','code_switching':'','telegraphic_syntax':'','compressed_reference':'','evidence':'','notes':'','annotator':''})
    pd.DataFrame(rows).to_csv(ROOT/'data/annotations/annotation_bank.csv',index=False)
    blind=pd.DataFrame(rows).drop(columns=['model','stratum']);blind.to_csv(ROOT/'data/annotations/second_annotator_blind.csv',index=False)
    dump({'fragment_count':len(rows),'questions':len(picked),'selection':'8 highest question-max S, 8 highest P among remainder, 8 seeded random among remainder; all four models; first 40 tokens of candidate complete window with largest S; task context retained','population_estimation':False,'human_agreement':'not available'},'annotation_selection.json')

if __name__=='__main__':main()
