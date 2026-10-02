"""Paired inference over shared questions; cluster-robust correctness model."""
import itertools, logging, warnings
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon, rankdata, spearmanr, kruskal
from statsmodels.stats.multitest import multipletests
import statsmodels.api as sm
import statsmodels.formula.api as smf
from common import CONFIG,ROOT,save_json
def paired_tests(d,repetitions=1000):
    rng=np.random.default_rng(CONFIG['seed']); rows=[]
    for metric in CONFIG['primary_metrics']:
        p=d.pivot(index='core_id',columns='model',values=metric)
        for a,b in itertools.combinations(p.columns,2):
            v=p[[a,b]].dropna(); dif=(v[a]-v[b]).to_numpy(); nz=dif[dif!=0]
            ranks=rankdata(abs(nz)); rbc=float(np.sum(np.sign(nz)*ranks)/ranks.sum()) if len(nz) else 0.
            test=wilcoxon(dif,method='approx') if len(nz) else None
            draws=dif[rng.integers(0,len(dif),size=(repetitions,len(dif)))]; ci=np.quantile(np.median(draws,axis=1),[.025,.975])
            rows.append({'metric':metric,'model_a':a,'model_b':b,'paired_n':len(dif),'median_paired_difference':float(np.median(dif)),'ci95_low':float(ci[0]),'ci95_high':float(ci[1]),'rank_biserial':rbc,'p_raw':test.pvalue if test else 1.})
    r=pd.DataFrame(rows); r['p_holm']=multipletests(r.p_raw,method='holm')[1]
    return r
def analyze(d):
    p=paired_tests(d,CONFIG['bootstrap_repetitions']); p.to_csv(ROOT/'outputs/tables/paired_tests.csv',index=False)
    summary=d.groupby(['model','benchmark'])[CONFIG['primary_metrics']+['whitespace_tokens','is_correct']].agg(['count','median','mean','std'])
    summary.to_csv(ROOT/'outputs/tables/descriptive_by_benchmark.csv')
    d.groupby('model')[CONFIG['primary_metrics']+['whitespace_tokens','is_correct']].median().to_csv(ROOT/'outputs/tables/model_medians.csv')
    descriptive=[]
    for m in CONFIG['primary_metrics']:
        k=kruskal(*[g[m].values for _,g in d.groupby('model')]); descriptive.append({'metric':m,'H':k.statistic,'p_descriptive':k.pvalue,'limitation':'Model groups share questions; use paired_tests for primary inference'})
    pd.DataFrame(descriptive).to_csv(ROOT/'outputs/tables/kruskal_descriptive.csv',index=False)
    # Bootstrap question clusters jointly, so multiple model records move together.
    rng=np.random.default_rng(CONFIG['seed']); cores=list(d.core_id.unique()); grp={k:g.index.to_numpy() for k,g in d.groupby('core_id')}; corr=[]
    for a,b in [('symbol_density','zlib_ratio'),('whitespace_tokens','zlib_ratio'),('char_entropy','low_frequency_fraction')]:
        rho=spearmanr(d[a],d[b]).statistic; boot=[]
        for _ in range(CONFIG['bootstrap_repetitions']):
            idx=np.concatenate([grp[k] for k in rng.choice(cores,len(cores),replace=True)]); boot.append(spearmanr(d.loc[idx,a],d.loc[idx,b]).statistic)
        lo,hi=np.quantile(boot,[.025,.975]); corr.append({'a':a,'b':b,'rho':rho,'ci95_low':lo,'ci95_high':hi,'bootstrap_unit':'core_id'})
    pd.DataFrame(corr).to_csv(ROOT/'outputs/tables/spearman.csv',index=False)
    reg=d.copy(); reg['correct']=reg.is_correct.astype(int); reg['log_tokens']=np.log1p(reg.whitespace_tokens)
    for m in CONFIG['primary_metrics']:reg[m+'_z']=(reg[m]-reg[m].mean())/reg[m].std()
    formula='correct ~ '+' + '.join(m+'_z' for m in CONFIG['primary_metrics'])+' + I(symbol_density_z ** 2) + C(model) + C(task) + log_tokens'
    try:
        fit=smf.glm(formula,reg,family=sm.families.Binomial()).fit(cov_type='cluster',cov_kwds={'groups':reg.core_id},maxiter=100)
        ci=fit.conf_int(); pd.DataFrame({'term':fit.params.index,'coefficient':fit.params.values,'se_cluster':fit.bse.values,'p_raw':fit.pvalues.values,'ci95_low':ci[0].values,'ci95_high':ci[1].values,'odds_ratio':np.exp(np.clip(fit.params.values,-700,700))}).to_csv(ROOT/'outputs/tables/logistic_coefficients.csv',index=False)
        save_json({'formula':formula,'n':len(reg),'clusters':reg.core_id.nunique(),'converged':fit.converged,'deviance':fit.deviance,'caution':'Associational model; quadratic term is exploratory; task separation may destabilize fixed-effect coefficients'},'outputs/logistic_fit.json')
    except Exception as e:save_json({'error':str(e),'formula':formula},'outputs/logistic_fit.json'); logging.exception('Logit failed')
    sens=[]
    for name,sub in [('no_top1pct',d[d.whitespace_tokens.le(d.groupby('model').whitespace_tokens.transform(lambda x:x.quantile(.99)))]),('english_only',d[d.language.eq('en')])]:
        rr=paired_tests(sub,300); rr['sensitivity']=name; sens.append(rr)
    pd.concat(sens).to_csv(ROOT/'outputs/tables/sensitivity_pairs.csv',index=False)
    save_json({'sample_rows':len(d),'core_ids':d.core_id.nunique(),'models':d.model.nunique(),'tasks':d.task.nunique(),'pairwise_tests':len(p),'significant_holm':int(p.p_holm.lt(.05).sum()),'english_rows':int(d.language.eq('en').sum()),'symbol_medians':d.groupby('model').symbol_density.median().to_dict(),'token_medians':d.groupby('model').whitespace_tokens.median().to_dict(),'zlib_medians':d.groupby('model').zlib_ratio.median().to_dict(),'accuracy':d.groupby('model').is_correct.mean().to_dict()},'outputs/article_numbers.json')
