import logging
import numpy as np
import pandas as pd
from common import ROOT, CONFIG, save_json
def select(b):
    b=b[b.nonempty].drop_duplicates(['model','core_id']).copy()
    b['task']=b.core_id.str.replace(r'_\d+$','',regex=True)
    models=sorted(b.model.unique())
    # Exposing model families are defined by actual nonempty reasoning, not provider name.
    counts=b.groupby('model').size()
    selected_models=list(counts[counts>0].index)
    b=b[b.model.isin(selected_models)]
    common_ids=b.groupby('core_id').model.nunique()
    ids=set(common_ids[common_ids.eq(len(selected_models))].index)
    matched=b[b.core_id.isin(ids)]
    rng=np.random.default_rng(CONFIG['seed']); chosen=[]; strata=[]
    for task,g in matched.groupby('task',sort=True):
        available=sorted(g.core_id.unique()); n=min(CONFIG['per_task_max'],len(available))
        chosen.extend(rng.choice(available,n,replace=False)); strata.append({'task':task,'available_common_ids':len(available),'sampled_core_ids':n})
    d=matched[matched.core_id.isin(chosen)].sort_values(['core_id','model']).reset_index(drop=True)
    d.to_parquet(ROOT/'data/processed/sample.parquet',index=False)
    pd.DataFrame(strata).to_csv(ROOT/'outputs/tables/sample_strata.csv',index=False)
    save_json({'seed':CONFIG['seed'],'models':selected_models,'all_nonempty_baseline_rows':len(b),'all_common_core_ids':len(ids),'sampled_core_ids':d.core_id.nunique(),'sample_rows':len(d),'tasks':d.task.nunique(),'benchmarks':d.groupby('benchmark').size().to_dict(),'selected_core_ids':sorted(chosen)},'outputs/sample_selection.json')
    logging.info('Selected matched sample rows=%d cores=%d models=%d',len(d),d.core_id.nunique(),len(selected_models))
    return d
if __name__=='__main__':select(pd.read_parquet(ROOT/'data/interim/all_baselines.parquet'))
