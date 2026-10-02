import json, logging
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CONFIG=json.loads((ROOT/'config.json').read_text(encoding='utf8'))
for directory in ['data/interim','data/processed','data/case_studies','outputs/tables','outputs/figures','outputs/screenshots','outputs/logs','article']:
    (ROOT/directory).mkdir(parents=True,exist_ok=True)
logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s',handlers=[logging.FileHandler(ROOT/'outputs/logs/run.log',encoding='utf8'),logging.StreamHandler()])
def save_json(value,path): (ROOT/path).write_text(json.dumps(value,ensure_ascii=False,indent=2,default=str),encoding='utf8')
