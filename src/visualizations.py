import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from common import ROOT,CONFIG
from rolling_analysis import rolling
def short(model):
    for pattern,label in [('claude-3-7','Claude 3.7'),('claude-3-5','Claude 3.5'),('r1','DeepSeek R1'),('qwq','QwQ 32B'),('thinking','Qwen3 thinking'),('v3','DeepSeek V3'),('2.5','Qwen2.5')]:
        if pattern in model:return label
    return model.replace('openrouter_','').replace('_','/')
def save(fig,name):
    fig.savefig(ROOT/'outputs/figures'/f'{name}.png',dpi=300,bbox_inches='tight'); fig.savefig(ROOT/'outputs/figures'/f'{name}.svg',bbox_inches='tight'); fig.savefig(ROOT/'outputs/figures'/f'{name}.pdf',bbox_inches='tight');plt.close(fig)
def figures(d):
    d[['core_id','model','symbol_density','zlib_ratio']].to_csv(ROOT/'outputs/figures/model_ecdf_source.csv',index=False)
    models=sorted(d.model.unique()); colors=plt.cm.tab10.colors
    fig,axs=plt.subplots(1,2,figsize=(9,3.2),layout='constrained')
    for j,m in enumerate(models):
        g=d[d.model.eq(m)]
        for ax,col,label in [(axs[0],'symbol_density','Доля символов Unicode S'),(axs[1],'zlib_ratio','Размер zlib / размер UTF-8')]:
            v=np.sort(g[col]); ax.plot(v,np.arange(1,len(v)+1)/len(v),label=short(m),color=colors[j]);ax.set_xlabel(label);ax.set_ylabel('Накопленная доля');ax.grid(alpha=.2)
    axs[0].legend(fontsize=8);save(fig,'model_ecdf')
    # Deterministic inspection exemplar, not a manually selected successful case.
    idx=d.sort_values(['symbol_density','core_id','model'],ascending=[False,True,True]).index[0];r=d.loc[idx]
    fig,ax=plt.subplots(figsize=(9,2.8),layout='constrained')
    for w in CONFIG['rolling_window_tokens']:
        v=rolling(r.reasoning,w);v.to_csv(ROOT/'outputs/tables'/f'rolling_{w}.csv',index=False);v.to_csv(ROOT/'outputs/figures'/f'rolling_symbol_density_source_{w}.csv',index=False);ax.plot(v.start_token,v.symbol_density,label=f'Окно {w}')
    ax.set_xlabel('Позиция в whitespace-токенах');ax.set_ylabel('Доля символов Unicode S');ax.legend();ax.grid(alpha=.2);save(fig,'rolling_symbol_density')
    (ROOT/'outputs/rolling_exemplar.txt').write_text(f'{r.core_id}\n{r.model}\n{r.reasoning}',encoding='utf8')
