import numpy as np
import pandas as pd
import pytest
from review_revision import spans,extra,matched_all,compare

def test_raw_window_preserves_whitespace_and_counts():
    text='a\t b\n c   d  e'
    wins=spans(text,3)
    assert wins[0]['text']=='a\t b\n c'
    assert all(len(w['text'].split())==3 for w in wins)
    assert spans(text,6)==[]
    assert spans('x y z',3)[0]['end_char']==5

def test_punctuation_operator_and_spacing_distinct():
    m=extra('A--b → c = d')
    assert m['operator_arrow_density']==pytest.approx(2/8)
    assert m['uppercase_ratio']==pytest.approx(1/4)
    assert m['whitespace_ratio']==pytest.approx(4/12)
    assert m['mean_run_without_whitespace']==pytest.approx(8/5)

def test_all_questions_no_cap_and_baseline_only():
    rows=[{'scope':'baseline','core_id':f't_{i}','model':m,'reasoning':'a'} for i in range(25) for m in ['a','b']]
    rows += [{'scope':'cue','core_id':'q','model':'a','reasoning':'x'},{'scope':'baseline','core_id':'incomplete','model':'a','reasoning':'x'}]
    d=matched_all(pd.DataFrame(rows))
    assert d.core_id.nunique()==25
    assert len(d)==50

def test_hierarchical_pair_effect_is_seeded():
    rows=[{'core_id':f'{task}_{i}','task':task,'model':m,'zlib_ratio':i/10+(1 if m=='a' else 0)} for task in ['t','u'] for i in range(4) for m in ['a','b']]
    d=pd.DataFrame(rows);a=compare(d,['zlib_ratio'],100);b=compare(d,['zlib_ratio'],100)
    pd.testing.assert_frame_equal(a,b)
    assert a.iloc[0].median_paired_difference==1
    assert a.iloc[0].ci95_low==pytest.approx(1)
    assert a.iloc[0].rank_biserial==1
    assert a.iloc[0].paired_n==8
