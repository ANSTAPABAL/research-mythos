import numpy as np
import pandas as pd
from final_review_analysis import fixed_slices,random_bank,cooccurrence,LABELS
from annotation_agreement import binary_agreement

def test_utf8_units():
    text='я🙂ab'*240
    chars=fixed_slices(text,800);raw=fixed_slices(text.encode('utf8'),800)
    assert all(len(x)==800 for x in chars+raw)
    assert any(len(x.encode('utf8'))>800 for x in chars)
    assert fixed_slices('short',800)==[]

def test_random_excerpt_can_include_short_trace_and_retains_source():
    data=pd.DataFrame([{'core_id':str(i),'model':m,'task':'task','input':'Q','reasoning':'a b c' if i==0 else ' '.join(str(j) for j in range(100))} for i in range(8) for m in ['A','B','C','D']])
    a=random_bank(data);b=random_bank(data)
    assert a.equals(b) and len(a)==32 and a.core_id.nunique()==8
    for r in a.itertuples():
        source=data[(data.core_id==r.core_id)&(data.model==r.model)].iloc[0].reasoning
        assert r.excerpt==source[r.start_char:r.end_char]
    assert set(a[a.core_id.eq('0')].excerpt_tokens)=={3}
    assert a[a.core_id.ne('0')].start_token.nunique()>1

def test_agreement_known_disagreement_and_constant_labels():
    r=binary_agreement([0,0,1,1],[0,1,1,1])
    assert r['raw_agreement']==.75 and r['cohen_kappa']==.5
    assert binary_agreement([0,0],[0,0])['cohen_kappa'] is None
    assert binary_agreement([],[])['raw_agreement'] is None

def test_overlapping_categories_count_intersections():
    d=pd.DataFrame(0,index=range(3),columns=LABELS);d.loc[[0,1],'ellipsis']=1;d.loc[[1,2],'inference_marker']=1
    m=cooccurrence(d)
    assert m.loc['ellipsis','ellipsis']==2 and m.loc['ellipsis','inference_marker']==1
    assert m.equals(m.T)
