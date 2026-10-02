"""Research interface for v2 paired windows and transparent initial coding."""
import json
import pandas as pd
import streamlit as st
from common import ROOT
from review_revision import CFG,spans,extra
from metrics import compute
from visualizations import short
OUT=ROOT/'outputs/review_v2'
st.set_page_config(page_title='Корпус текстовых цепочек',layout='wide')
@st.cache_data
def load():return pd.read_parquet(OUT/'all_common_traces.parquet')
@st.cache_data
def annotations():return pd.read_csv(ROOT/'data/annotations/annotation_coded.csv',keep_default_na=False)
screen=st.sidebar.radio('Экран',['Обзор','Просмотр цепочки','Сравнение моделей','Локальные окна','Разметка','Mythos и Astra','Статистика'])
st.sidebar.caption('Версия 2.1 · все общие вопросы · seed 20261002');st.title(screen)
m=json.loads((OUT/'manifest.json').read_text(encoding='utf8'))
if screen=='Обзор':
    for c,label,value in zip(st.columns(4),['Цепочек','Общих вопросов','Задач','Моделей'],[m['rows'],m['questions'],m['tasks'],4]):c.metric(label,value)
    st.write('Токенная длина, алгоритмическая сжимаемость и языковые сокращения рассматриваются отдельно.')
    st.dataframe(pd.DataFrame(m['eligibility']),hide_index=True,use_container_width=True)
    st.image(str(OUT/'figures/fixed_window_comparison.png'),caption='128 whitespace-токенов; одна единица сравнения — вопрос')
    st.info('96 отобранных и 32 независимо случайных фрагмента: первичная ИИ-разметка. Второго аннотатора пока нет; согласие не рассчитано.')
    st.subheader('Дополнительные проверки длины')
    st.dataframe(pd.DataFrame(json.loads((OUT/'final_review/manifest.json').read_text(encoding='utf8'))['sensitivity']),hide_index=True)
elif screen in ['Просмотр цепочки','Локальные окна']:
    d=load();model=st.sidebar.selectbox('Модель',sorted(d.model.unique()),format_func=short);v=d[d.model.eq(model)]
    task=st.sidebar.selectbox('Задача',sorted(v.task.unique()));v=v[v.task.eq(task)]
    core=st.selectbox('Вопрос',sorted(v.core_id.unique()));r=v[v.core_id.eq(core)].iloc[0]
    st.text(r['input']);width=st.select_slider('Размер полного окна',[64,128,256,512],value=128)
    rows=[{**w,**compute(w['text'],False),**extra(w['text'])} for w in spans(r.reasoning,width)]
    if rows:
        w=pd.DataFrame(rows);st.dataframe(w[['start_token','end_token','zlib_ratio','symbol_density','punctuation_density','whitespace_ratio']],hide_index=True,use_container_width=True)
        if screen=='Локальные окна':
            st.line_chart(w.set_index('start_token')[['zlib_ratio','symbol_density','punctuation_density']])
            for z in rows:
                with st.expander(f"Raw [{z['start_token']}:{z['end_token']}]"):st.code(z['text'],language=None)
    else:st.info('Цепочка короче размера окна; неполное окно не включено.')
    if screen=='Просмотр цепочки':
        st.caption('Исходный текст; пробелы и регистр сохранены.');st.text(r.reasoning)
        st.download_button('Скачать цепочку',r.reasoning,file_name=core+'.txt')
elif screen=='Сравнение моделей':
    width=st.selectbox('Размер окна',[128,64,256,512]);d=pd.read_parquet(OUT/'final_review/tokens64.parquet') if width==64 else pd.read_csv(OUT/'tables'/f'fixed_window_{width}.csv')
    metric=st.selectbox('Показатель',CFG['primary_metrics'] if width==64 else CFG['primary_metrics']+CFG['secondary_metrics'])
    st.dataframe(d.groupby('model')[metric].agg(['count','median','mean']).rename(index=short),use_container_width=True)
    st.bar_chart(d.groupby('model')[metric].median().rename(index=short))
    st.caption('Показатели усреднены по окнам внутри цепочки; одинаковые вопросы всех четырёх моделей.')
elif screen=='Разметка':
    sample=st.selectbox('Выборка',['Обогащённая: 96 фрагментов','Случайная: 32 фрагмента'])
    d=annotations() if sample.startswith('Обогащённая') else pd.read_csv(ROOT/'data/annotations/random_coded.csv',keep_default_na=False)
    st.warning('Первичная ИИ-разметка; независимой проверки человеком пока нет. Частоты выборок не являются оценкой корпусной распространённости.')
    labels=['ellipsis','symbolic_substitution','nonce_derivation','argument_omission','inference_marker','code_switching','telegraphic_syntax','compressed_reference']
    model=st.selectbox('Модель',sorted(d.model.unique()),format_func=short);v=d[d.model.eq(model)]
    category=st.selectbox('Категория',['Все']+labels)
    if category!='Все':v=v[v[category].eq(1)]
    if len(v):
        identifier=st.selectbox('Фрагмент',list(v.annotation_id));r=v[v.annotation_id.eq(identifier)].iloc[0]
        st.caption(r.core_id+' · '+r.get('stratum','случайная позиция без отбора по S/P'));st.text(r.question);st.code(r.excerpt,language=None)
        st.write({k:int(r[k]) for k in labels});st.write(r.evidence);st.caption(r.notes)
        with st.expander('Соседний контекст'):st.text(r.preceding);st.text(r.following)
    else:st.info('Подтверждённых примеров категории в этих фрагментах нет.')
    name='annotation_coded.csv' if sample.startswith('Обогащённая') else 'random_coded.csv'
    blind='second_annotator_blind.csv' if sample.startswith('Обогащённая') else 'random_blind.csv'
    st.download_button('Скачать разметку с основаниями',d.to_csv(index=False),file_name=name,mime='text/csv')
    st.download_button('Файл для второго аннотатора',(ROOT/'data/annotations'/blind).read_bytes(),file_name=blind,mime='text/csv')
    with st.expander('Справочник'):st.markdown((ROOT/'data/annotations/CODEBOOK.md').read_text(encoding='utf8'))
elif screen=='Mythos и Astra':
    st.caption('Внешние иллюстрации; Mythos и Astra не входят в количественный корпус.')
    for r in pd.read_csv(ROOT/'data/case_studies/anthropic_mythos.csv').to_dict('records'):
        st.subheader(r['title']);st.write(r['source_url']);st.caption('Страницы '+str(r['source_page']));st.code(r['raw_excerpt'],language=None);st.write(r['manual_notes'])
    st.subheader('Astra: raw CoT, AISI, PDF с. 7');st.write('https://arxiv.org/abs/2609.38415v1')
    st.code('User likely scripted continuer prompt never provide explicit, task cannot resolve valid scope.',language=None)
    st.subheader('Astra: экспериментально вызванное объяснение, PDF с. 6');st.write('https://arxiv.org/abs/2609.26637v1')
    st.code('Subtract first two gives (b-c)(a+b+c-3)=0 so sum3.',language=None)
    st.write('Не подтверждено как дословная нативная скрытая цепочка. equations раскрывает грамматическую ссылку; b≠c для доказательства требует контекста.')
elif screen=='Статистика':
    additional=['tokens64_paired','characters800_paired','bytes800_paired','cooccurrence_enriched96','cooccurrence_random32']
    choice=st.selectbox('Таблица',['paired_128','paired_256','paired_512','sensitivity_first_only','sensitivity_latin95','whole_trace_medians','annotation_counts']+additional)
    d=pd.read_csv(OUT/('final_review' if choice in additional else 'tables')/(choice+'.csv'));show=d.copy()
    for c in ['model','model_a','model_b']:
        if c in show:show[c]=show[c].map(short)
    st.dataframe(show,hide_index=True,use_container_width=True);st.download_button('Скачать CSV',d.to_csv(index=False),file_name=choice+'.csv',mime='text/csv')
    st.caption('ДИ: bootstrap задача → вопрос с сохранением пары. Уилкоксон/Holm не учитывают кластерную зависимость; вывод опирается на иерархические ДИ. Latin95 сохранил все вопросы и не является независимой проверкой английского языка.')
