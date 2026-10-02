import hashlib, logging
import pandas as pd
from common import ROOT, save_json
def audit():
    audits=[]; baselines=[]; cue_summary=[]
    for f in sorted((ROOT/'data/raw').glob('*/*.parquet')):
        d=pd.read_parquet(f)
        logging.info('Audit %s rows=%d columns=%s',f.name,len(d),list(d.columns))
        d['benchmark']=f.parent.name
        d['reasoning']=d['reasoning'].fillna('').astype(str)
        d['nonempty']=d.reasoning.str.strip().ne('')
        d['text_sha256']=d.reasoning.map(lambda s:hashlib.sha256(s.encode()).hexdigest())
        duplicate_keys=d.duplicated(['model','core_id','scope']).sum()
        bool_valid=d.is_correct.map(lambda x:isinstance(x,bool)).sum()
        compare=d.model_answer.fillna('').eq(d.correct_answer.fillna(''))
        discrepancy=(compare.ne(d.is_correct) & d.model_answer.notna()).sum()
        for model,g in d.groupby('model'):
            b=g[g.scope.eq('baseline')]
            audits.append({'file':str(f.relative_to(ROOT)), 'model':model,'benchmark':f.parent.name,'rows':len(g),'baseline':len(b),'nonempty':int(g.nonempty.sum()),'baseline_nonempty':int(b.nonempty.sum()),'duplicate_keys':int(duplicate_keys),'duplicate_nonempty_text':int(g[g.nonempty].text_sha256.duplicated().sum()),'correctness_bool_rows':int(bool_valid),'label_discrepancies':int(discrepancy),'chars_median_nonempty':float(g.loc[g.nonempty,'reasoning'].str.len().median()) if g.nonempty.any() else None,'invalid_choice_label':int(sum(str(row.correct_answer) not in [chr(65+i) for i in range(len(row.choices))] for row in g.itertuples()))})
        # Cue result summaries are descriptive within-model paired comparisons only.
        base=d[d.scope.eq('baseline')][['model','core_id','is_correct']].rename(columns={'is_correct':'baseline_correct'})
        c=d[d.scope.ne('baseline')].merge(base,on=['model','core_id'],validate='many_to_one')
        for (model,scope),v in c.groupby(['model','scope']):
            cue_summary.append({'model':model,'benchmark':f.parent.name,'scope':scope,'pairs':len(v),'baseline_accuracy':v.baseline_correct.mean(),'cue_accuracy':v.is_correct.mean(),'accuracy_change':(v.is_correct.astype(int)-v.baseline_correct.astype(int)).mean()})
        baselines.append(d[d.scope.eq('baseline')].copy())
        del d
    a=pd.DataFrame(audits); a.to_csv(ROOT/'outputs/tables/data_audit.csv',index=False)
    save_json({'rows':int(a.rows.sum()),'baseline':int(a.baseline.sum()),'nonempty':int(a.nonempty.sum()),'baseline_nonempty':int(a.baseline_nonempty.sum()),'duplicate_keys':int(a.duplicate_keys.sum()),'label_discrepancies':int(a.label_discrepancies.sum()),'files':audits},'outputs/data_audit.json')
    pd.DataFrame(cue_summary).to_csv(ROOT/'outputs/tables/cue_descriptive_paired.csv',index=False)
    b=pd.concat(baselines,ignore_index=True)
    b.to_parquet(ROOT/'data/interim/all_baselines.parquet',index=False)
    return b
if __name__=='__main__':audit()
