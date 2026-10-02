import json
from streamlit.testing.v1 import AppTest
from common import ROOT
def main():
    app=AppTest.from_file(str(ROOT/'src/app_review.py'),default_timeout=30).run()
    assert len(app.exception)==0,str(app.exception)
    assert [x.value for x in app.metric]==['12088','3022','43','4']
    checked=['Обзор']
    for screen in ['Сравнение моделей','Разметка','Статистика']:
        app.sidebar.radio[0].set_value(screen).run();assert len(app.exception)==0,str(app.exception)
        if screen=='Сравнение моделей':app.selectbox[0].set_value(64).run()
        if screen=='Разметка':
            app.selectbox[0].set_value('Случайная: 32 фрагмента').run()
            assert app.selectbox[3].value.startswith('R')
        if screen=='Статистика':app.selectbox[0].set_value('bytes800_paired').run()
        assert len(app.exception)==0,str(app.exception)
        checked.append(screen)
    result={'status':'PASS','method':'Streamlit AppTest executes real app and widget state transitions','screens':checked,'new_controls':['64-token comparison','32 random coded excerpts','800-byte paired statistics']}
    (ROOT/'outputs/review_v2/final_review/app_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(result)
if __name__=='__main__':main()
