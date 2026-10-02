import math,zlib
import numpy as np
import pandas as pd
import pytest
from metrics import compute,entropy
from rolling_analysis import rolling
from statistical_analysis import paired_tests
import preprocess

@pytest.fixture
def miniature():
    rows=[]
    for core in range(12):
        for model in ['a','b']:
            row={'core_id':f'task_{core}','model':model,'benchmark':'fixture','nonempty':True,'reasoning':'x → y' if model=='a' else 'x y'}
            row.update(compute(row['reasoning'],False));row['zlib_ratio']+=core/100
            rows.append(row)
    rows.append({'core_id':'task_99','model':'a','benchmark':'fixture','nonempty':True,'reasoning':'unmatched'})
    rows.append({'core_id':'task_100','model':'b','benchmark':'fixture','nonempty':False,'reasoning':''})
    return pd.DataFrame(rows)

def test_entropy_distribution():
    assert entropy('aabb')==pytest.approx((1.,1.))
    assert entropy('aaaa')==(0.,0.)
    assert entropy('')==(0.,0.)

def test_unicode_denominator_and_compression_units():
    text='a → b 2 !';m=compute(text,False)
    assert m['symbol_density']==pytest.approx(1/5)
    assert m['digit_density']==pytest.approx(1/5)
    assert m['punctuation_density']==pytest.approx(1/5)
    assert m['zlib_ratio']==pytest.approx(len(zlib.compress(text.encode('utf8'),9))/len(text.encode('utf8')))

def test_empty_and_repetition():
    assert all(math.isfinite(x) for x in compute('',False).values())
    assert compute('a b a b a b',False)['repeat_2gram']==pytest.approx(3/5)

@pytest.mark.parametrize('width',[64,128,256])
def test_rolling_uses_declared_half_overlap(width):
    r=rolling(' '.join(['a']*(3*width)),width)
    assert np.all(r.end_token-r.start_token==width)
    assert np.all(np.diff(r.start_token)==width//2)

def test_selection_matches_questions_and_repeats_seed(miniature,tmp_path,monkeypatch):
    monkeypatch.setattr(preprocess,'ROOT',tmp_path)
    for p in ['data/processed','outputs/tables']:(tmp_path/p).mkdir(parents=True)
    monkeypatch.setattr(preprocess,'save_json',lambda *args:None)
    a=preprocess.select(miniature);b=preprocess.select(miniature)
    pd.testing.assert_frame_equal(a,b)
    assert a.groupby('core_id').model.nunique().eq(2).all()
    assert not set(a.core_id)&{'task_99','task_100'}
    assert not a.duplicated(['core_id','model']).any()

def test_paired_statistics_and_holm(miniature):
    d=miniature[miniature.core_id.ne('task_99')&miniature.nonempty]
    a=paired_tests(d,100);b=paired_tests(d,100)
    pd.testing.assert_frame_equal(a,b)
    assert a.paired_n.eq(12).all()
    assert a.p_holm.ge(a.p_raw).all()
    s=a[a.metric.eq('symbol_density')].iloc[0]
    assert s.median_paired_difference==pytest.approx(1/3)
    assert s.rank_biserial==1.
    assert s.ci95_low==pytest.approx(1/3)
    zero=a[a.metric.eq('repeat_4gram')].iloc[0]
    assert zero.p_raw==1.
    assert zero.rank_biserial==0.
