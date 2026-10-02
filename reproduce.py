"""One-command primary reproduction, after installing requirements."""
import argparse,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'.deps'));sys.path.insert(0,str(ROOT/'src'))
def main():
    p=argparse.ArgumentParser();p.add_argument('--offline',action='store_true',help='Reuse downloaded immutable parquet files');args=p.parse_args()
    if not args.offline:
        from fetch_data import main as fetch;fetch()
    from review_revision import main as analyze;analyze()
    from code_review_annotations import main as coding;coding()
    from final_review_analysis import main as additional;additional()
    from code_random_annotations import main as random_coding;random_coding()
    from review_figures import main as figures;figures()
    from build_article_review import main as article;article()
    import pytest
    raise SystemExit(pytest.main([str(ROOT/'tests'),'-q','--junitxml='+str(ROOT/'outputs/pytest_report.xml')]))
if __name__=='__main__':main()
