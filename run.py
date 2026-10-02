"""Entry point also compatible with the isolated bundled Python interpreter."""
import runpy,sys
from pathlib import Path
root=Path(__file__).resolve().parent
if (root/'.deps').exists():sys.path.insert(0,str(root/'.deps'))
sys.path.insert(0,str(root/'src'))
script=sys.argv[1] if len(sys.argv)>1 else 'run_analysis'
sys.argv=sys.argv[1:]
runpy.run_path(str(root/'src'/f'{script}.py'),run_name='__main__')
