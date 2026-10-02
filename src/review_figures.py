"""Figures from paired fixed-width results; no independently sampled windows."""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from common import ROOT
from visualizations import short

def main():
    out=ROOT/'outputs/review_v2';d=pd.read_csv(out/'tables/fixed_window_128.csv');p=pd.read_csv(out/'tables/paired_128.csv');p=p[p.metric.eq('zlib_ratio')]
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11})
    fig,ax=plt.subplots(1,2,figsize=(8,3.0),gridspec_kw={'width_ratios':[1,1.4]},layout='constrained')
    for m,g in d.groupby('model'):
        x=np.sort(g.zlib_ratio);ax[0].plot(x,np.arange(1,len(x)+1)/len(x),label=short(m),linewidth=1.4)
    ax[0].set(xlabel='R (128 whitespace tokens)',ylabel='Cumulative proportion',title='A. Equal-width samples')
    ax[0].legend(fontsize=9.5,loc='lower right');ax[0].grid(alpha=.2)
    y=np.arange(len(p));ax[1].hlines(y,p.ci95_low,p.ci95_high,color='#375b82');ax[1].scatter(p.median_paired_difference,y,color='#aa462e',zorder=3)
    ax[1].axvline(0,color='gray',linewidth=.8);ax[1].set_yticks(y,[short(r.model_a)+' − '+short(r.model_b) for r in p.itertuples()],fontsize=9.5)
    ax[1].set(xlabel='Paired median difference; 95% CI',title='B. Hierarchical bootstrap');ax[1].invert_yaxis();ax[1].grid(axis='x',alpha=.2)
    for suffix in ['png','svg','pdf']:fig.savefig(out/'figures'/('fixed_window_comparison.'+suffix),dpi=300)
    plt.close(fig)
if __name__=='__main__':main()
