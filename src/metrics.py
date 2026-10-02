"""Observable text proxies; never an estimate of hidden model computation."""
import math, re, unicodedata, zlib
from collections import Counter
from functools import lru_cache
import emoji
from langdetect import DetectorFactory, detect_langs
from wordfreq import zipf_frequency
DetectorFactory.seed=20261002
FUNCTION=set('a an the and or but if then of to for from in on at by with as is are was were be been being it its this that these those we i you he she they them not no so can could should would may might must do does did have has had which what when where who how than'.split())
OPERATORS=set('=+−-*/×÷<>≤≥≠≈∑∏√∞→←↔⇒⇔^%|&~')
MOVES={'tentative':r'\b(?:let.?s try|suppose|assume|perhaps|maybe)\b','verification':r'\b(?:check|verify|confirmed|consistent)\b','backtracking':r'\b(?:wait|instead|reconsider|but actually|alternatively)\b','conclusion':r'\b(?:therefore|thus|answer is|so the answer|conclude)\b','uncertainty':r'\b(?:uncertain|unsure|not sure|might|possibly)\b'}
def entropy(units):
    c=Counter(units); n=sum(c.values())
    if not n:return 0.,0.
    h=-sum((v/n)*math.log2(v/n) for v in c.values())
    return h,h/math.log2(len(c)) if len(c)>1 else 0.
@lru_cache(maxsize=100000)
def freq(word):return zipf_frequency(word,'en')
@lru_cache(maxsize=30000)
def language(text):
    words=' '.join(re.findall(r'[A-Za-z\u0400-\u04ff\u4e00-\u9fff]+',text))[:1600]
    if len(words)<60:return 'und',0.
    try:
        v=detect_langs(words)[0]; return v.lang,float(v.prob)
    except Exception:return 'und',0.
def compute(text,detect_language=True):
    chars=len(text); tok=text.split(); n=len(tok); raw=text.encode('utf8'); comp=zlib.compress(raw,level=9)
    nonspace=[c for c in text if not c.isspace()]; den=max(1,len(nonspace))
    cats=Counter(unicodedata.category(c)[0] for c in nonspace)
    words=re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?",text.lower())
    h,hn=entropy(text); ht,htn=entropy(tok)
    sentences=[s for s in re.split(r'[.!?]+(?:\s|$)|\n+',text) if s.strip()]
    out={'chars':chars,'whitespace_tokens':n,'sentences':len(sentences),'raw_bytes':len(raw),'compressed_bytes':len(comp),'zlib_ratio':len(comp)/max(1,len(raw)),
      'letter_density':cats['L']/den,'digit_density':cats['N']/den,'punctuation_density':cats['P']/den,'symbol_density':cats['S']/den,'operator_density':sum(c in OPERATORS for c in nonspace)/den,'bracket_density':sum(c in '()[]{}' for c in nonspace)/den,'emoji_density':emoji.emoji_count(text)/den,'unusual_unicode_density':sum(ord(c)>127 and not c.isalnum() for c in nonspace)/den,
      'function_word_fraction':sum(w in FUNCTION for w in words)/max(1,len(words)),'low_frequency_fraction':sum(freq(w)<2 for w in words)/max(1,len(words)), 'high_frequency_fraction':sum(freq(w)>=4 for w in words)/max(1,len(words)), 'nonalphabetic_token_fraction':sum(not t.isalpha() for t in tok)/max(1,n),
      'short_segment_fraction':sum(len(s.split())<=4 for s in sentences)/max(1,len(sentences)), 'char_entropy':h,'char_entropy_normalized':hn,'token_entropy':ht,'token_entropy_normalized':htn}
    for k in range(1,5):
        ng=[tuple(tok[i:i+k]) for i in range(max(0,n-k+1))]
        out[f'repeat_{k}gram']=1-len(set(ng))/len(ng) if ng else 0.
    for move,pat in MOVES.items():out['move_'+move]=len(re.findall(pat,text,re.I))/max(1,n)*1000
    if detect_language:
        lang,prob=language(text); out.update(language=lang,language_confidence=prob)
        windows=[' '.join(tok[i:i+128]) for i in sorted(set([0,max(0,n//2-64),max(0,n-128)]))]
        langs=[language(w)[0] for w in windows]
        out['language_switches_sampled']=sum(a!=b and 'und' not in [a,b] for a,b in zip(langs,langs[1:]))
    return out
