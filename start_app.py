import sys
from pathlib import Path
root=Path(__file__).resolve().parent
if (root/'.deps').exists():sys.path.insert(0,str(root/'.deps'))
sys.path.insert(0,str(root/'src'))
from streamlit.web import cli
sys.argv=['streamlit','run',str(root/'src/app_review.py'),'--global.developmentMode','false','--server.address','127.0.0.1','--server.port','8501','--server.headless','true','--browser.gatherUsageStats','false']
cli.main()
