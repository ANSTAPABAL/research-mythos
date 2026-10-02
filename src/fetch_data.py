"""Download immutable public sources, recording checksums and HTTP evidence."""
import concurrent.futures, hashlib, json, re, time, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT/'config.json').read_text())
BASE = 'https://huggingface.co/datasets/'+CONFIG['dataset']+'/resolve/'+CONFIG['revision']+'/'
def get(url, path):
    path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists():
        for attempt in range(3):
            try:
                req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.anthropic.com/'})
                with urllib.request.urlopen(req,timeout=180) as r, path.with_suffix(path.suffix+'.part').open('wb') as f:
                    while block:=r.read(1024*1024): f.write(block)
                path.with_suffix(path.suffix+'.part').replace(path)
                break
            except Exception:
                if attempt==2: raise
                time.sleep(2)
    return {'url':url,'path':str(path.relative_to(ROOT)), 'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
def main():
    meta=json.load(urllib.request.urlopen('https://huggingface.co/api/datasets/'+CONFIG['dataset']+'/revision/'+CONFIG['revision'],timeout=60))
    (ROOT/'data/raw').mkdir(parents=True,exist_ok=True)
    (ROOT/'data/raw/dataset_metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf8')
    files=[x['rfilename'] for x in meta['siblings'] if x['rfilename'].endswith('.parquet') or x['rfilename'] in ['LICENSE','README.md']]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        manifest=list(pool.map(lambda x:get(BASE+x,ROOT/'data/raw'/x),files))
    for name,url in {
      'proceedings_template.docx':'https://s3-oris.bmstu.ru/cms.bmstu.ru/linguistics/proceedings_template.docx',
      'requirements_paper.docx':'https://s3-oris.bmstu.ru/cms.bmstu.ru/linguistics/requirements_paper.docx',
      'anthropic_system_card.pdf':'https://www-cdn.anthropic.com/57a52ea7d8f0e54e8a542e908266086df425cdf5/Claude%20Fable%205%20&%20Claude%20Mythos%205%20System%20Card.pdf',
      'openai_transcript.pdf':'https://alignment.openai.com/metagaming/transcripts/rl-late-sandbagging-qa-no-goal-no-sandbag.pdf',
      'astra_aisi.pdf':'https://arxiv.org/pdf/2609.38415v1',
      'astra_extracted.pdf':'https://arxiv.org/pdf/2609.26637v1'
    }.items():
        try: manifest.append(get(url,ROOT/'data/sources'/name))
        except Exception as e: manifest.append({'url':url,'error':str(e)})
    (ROOT/'data/source_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(manifest,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
