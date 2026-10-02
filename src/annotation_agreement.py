"""Compare supplied independent annotations; never fill missing human decisions."""
import argparse,json
import numpy as np
import pandas as pd
from final_review_analysis import LABELS

def binary_agreement(a,b):
    a=np.asarray(a,dtype=int);b=np.asarray(b,dtype=int)
    if not len(a):return {'n':0,'raw_agreement':None,'cohen_kappa':None}
    if len(a)!=len(b) or not np.isin(a,[0,1]).all() or not np.isin(b,[0,1]).all():raise ValueError('Two aligned binary vectors required')
    observed=float(np.mean(a==b));pa=float(a.mean());pb=float(b.mean());chance=pa*pb+(1-pa)*(1-pb)
    return {'n':len(a),'raw_agreement':observed,'cohen_kappa':float((observed-chance)/(1-chance)) if chance<1 else None,'positive_rate_a':pa,'positive_rate_b':pb,'kappa_note':'undefined for identical constant labels' if chance==1 else 'interpret alongside raw agreement and prevalence'}

def evaluate(first,second):
    for data in [first,second]:
        if data.annotation_id.duplicated().any():raise ValueError('Duplicate annotation IDs')
    if set(first.annotation_id)!=set(second.annotation_id):raise ValueError('Annotation IDs must match the complete blind batch')
    a=first.set_index('annotation_id');b=second.set_index('annotation_id').loc[a.index]
    for field in ['excerpt','question','preceding','following']:
        if not a[field].fillna('').equals(b[field].fillna('')):raise ValueError('Source text mismatch: '+field)
    rows=[];disputes=[]
    for label in LABELS:
        x=pd.to_numeric(a[label],errors='coerce');y=pd.to_numeric(b[label],errors='coerce')
        provided=b[label].fillna('').astype(str).str.strip().ne('')
        if (provided&y.isna()).any():raise ValueError('Unrecognised independent decision: '+label)
        if not x.dropna().isin([0,1]).all():raise ValueError('Nonbinary initial label: '+label)
        if not y.dropna().isin([0,1]).all():raise ValueError('Nonbinary human label: '+label)
        valid=x.notna()&y.notna();unsure=pd.to_numeric(b.get(label+'_unsure',pd.Series(0,index=b.index)),errors='coerce').fillna(0)
        if label+'_unsure' in b:
            raw_unsure=b[label+'_unsure'].fillna('').astype(str).str.strip()
            parsed=pd.to_numeric(b[label+'_unsure'],errors='coerce')
            if (raw_unsure.ne('')&parsed.isna()).any():raise ValueError('Unrecognised unsure flag')
        if not unsure.isin([0,1]).all():raise ValueError('Unsure flag must be 0/1')
        stats=binary_agreement(x[valid],y[valid]);certain=valid&unsure.eq(0)
        rows.append({'category':label,**stats,'missing_human':int(y.isna().sum()),'uncertain_human':int((valid&unsure.eq(1)).sum()),'certain_only':binary_agreement(x[certain],y[certain])})
        for idx in a.index[valid&((x!=y)|unsure.eq(1))]:
            disputes.append({'annotation_id':idx,'category':label,'initial_ai':int(x[idx]),'independent':int(y[idx]),'unsure':int(unsure[idx]),'excerpt':a.loc[idx,'excerpt'],'initial_evidence':a.loc[idx,'evidence'],'independent_evidence':b.loc[idx,'evidence'],'adjudicated_label':'','adjudicator':'','resolution_reason':''})
    return rows,pd.DataFrame(disputes,columns=['annotation_id','category','initial_ai','independent','unsure','excerpt','initial_evidence','independent_evidence','adjudicated_label','adjudicator','resolution_reason'])

def main():
    p=argparse.ArgumentParser();p.add_argument('--first',required=True);p.add_argument('--second',required=True);p.add_argument('--output',required=True);args=p.parse_args()
    from pathlib import Path
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    second=pd.read_csv(args.second)
    if second[LABELS].isna().all().all():
        (out/'agreement.json').write_text(json.dumps({'status':'pending','reason':'No independent decisions supplied; no agreement calculated'},indent=2),encoding='utf8');print('Pending: independent annotation file is blank');return
    if second.annotator.fillna('').str.strip().eq('').any():raise ValueError('Identify the independent annotator on all rows; human status must be confirmed by the actual contributor')
    stats,disputes=evaluate(pd.read_csv(args.first),second)
    (out/'agreement.json').write_text(json.dumps({'status':'supplied independent decisions; contributor identity and human provenance require confirmation','categories':stats},ensure_ascii=False,indent=2),encoding='utf8')
    disputes.to_csv(out/'adjudication.csv',index=False)
if __name__=='__main__':main()
