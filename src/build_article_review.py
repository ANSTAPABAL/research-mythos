"""Reviewed article: every corpus number loaded from the executed v2 analysis."""
import json,re
import pandas as pd
from docx.shared import Cm,Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from common import ROOT
from build_article import blank_from_template,para,authors,picture,bibliography,decimal
from visualizations import short

TITLE='Сжатые формы текстовых цепочек рассуждения больших языковых моделей: корпусный и сравнительный анализ'
EN='Compressed Forms of Textual Reasoning Traces in Large Language Models: A Comparative Corpus Analysis'
SELECT=[1,3,6,7,8,10,14,19,20,21,22,31,33,34]
OUT=ROOT/'outputs/review_v2'
def js(path):return json.loads(path.read_text(encoding='utf8'))
def head(doc,label):
    p=para(doc,label,indent=False,after=3);p.runs[0].bold=True;p.paragraph_format.keep_with_next=True;p.paragraph_format.space_before=Pt(4)
def source_list():
    old=bibliography();refs=js(ROOT/'data/literature/references.json');out=[]
    for i,n in enumerate(SELECT,1):
        if n==1:kind='Системная карточка'
        elif n==31:kind='Препринт; описание корпуса'
        elif n==33:kind='Препринт; технический отчёт AISI'
        elif n==34:kind='Препринт'
        else:kind='Препринт' if 'citation_arxiv_id' in refs[n-1].get('metadata',{}) else 'Рецензируемая статья'
        out.append(re.sub(r'^\[\d+\]',f'[{i}]',old[n-1])+f' [{kind}].')
    return out
def table(doc,rows,headers,widths):
    t=doc.add_table(rows=1,cols=len(headers));t.autofit=False
    borders=OxmlElement('w:tblBorders')
    for side in ['top','left','bottom','right','insideH','insideV']:
        e=OxmlElement('w:'+side);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'808080');borders.append(e)
    t._tbl.tblPr.append(borders)
    for c,tx in zip(t.rows[0].cells,headers):c.text=tx
    for row in rows:
        for c,tx in zip(t.add_row().cells,row):c.text=str(tx)
    for i,row in enumerate(t.rows):
        pr=row._tr.get_or_add_trPr();no=OxmlElement('w:cantSplit');pr.append(no)
        if i==0:pr.append(OxmlElement('w:tblHeader'))
        for j,c in enumerate(row.cells):
            c.width=Cm(widths[j])
            for p in c.paragraphs:
                p.paragraph_format.first_line_indent=Pt(0);p.paragraph_format.line_spacing=1.;p.paragraph_format.space_before=Pt(0);p.paragraph_format.space_after=Pt(0)
                p.alignment=WD_ALIGN_PARAGRAPH.LEFT if j==0 else WD_ALIGN_PARAGRAPH.CENTER
                for r in p.runs:r.font.name='Times New Roman';r.font.size=Pt(12);r.bold=i==0
    return t
def main():
    m=js(OUT/'manifest.json');ann=js(OUT/'annotation_summary.json');primary=m['eligibility'][0]
    med=pd.read_csv(OUT/'tables/medians_128.csv');full=pd.read_csv(OUT/'tables/whole_trace_medians_primary128.csv').set_index('model');pair=pd.read_csv(OUT/'tables/paired_128.csv')
    key=pair[pair.metric.eq('zlib_ratio')&pair.model_a.str.contains('claude')&pair.model_b.str.contains('deepseek')].iloc[0]
    wc=full.loc[key.model_a];wd=full.loc[key.model_b]
    v={k:decimal(key[k]) for k in ['median_paired_difference','ci95_low','ci95_high','rank_biserial']}
    abstract=(f'В сокращённых текстовых цепочках рассуждения английская речь сочетается с формулами и неполными конструкциями. Исследовано, какие отношения сохраняются при таких сокращениях. В открытом корпусе сопоставлены {m["rows"]} цепочек четырёх моделей по {m["questions"]} одинаковым вопросам. Разработанное ПО рассчитывает признаки на окнах по 128 whitespace-токенов и сохраняет контекст фрагментов; введена схема восьми категорий с первичной ИИ-разметкой 96 примеров. При фиксированной длине отношение размеров zlib/UTF-8 у Claude ниже, чем у DeepSeek: медиана парной разности {v["median_paired_difference"]}, 95% ДИ [{v["ci95_low"]}; {v["ci95_high"]}]. Сравнение полных цепочек даёт противоположный порядок медиан. В размеченных фрагментах обнаружены пропуски связок и маркеры so и therefore; формулы выражают отношения между величинами. Внешние примеры Mythos и Astra иллюстрируют зависимость расшифровки от задачи. Результаты описывают задачную сокращённую запись; независимая проверка разметки человеком пока отсутствует.')
    abstract_en=(f'Shortened textual reasoning traces combine English prose, formulas and incomplete constructions. This study examines which relations survive such shortening. A public corpus provides {m["rows"]:,} traces from four models answering {m["questions"]:,} shared questions. The research software calculates features in 128-whitespace-token windows and retains excerpt context. An eight-category scheme is applied in initial AI-assisted coding of 96 excerpts. At fixed token length, Claude has a lower zlib-to-UTF-8 size ratio than DeepSeek: median paired difference {key.median_paired_difference:.3f}, hierarchical 95% CI [{key.ci95_low:.3f}, {key.ci95_high:.3f}]. Whole-trace medians show the opposite ordering. Coded excerpts contain omitted copulas and inference markers such as so and therefore, while formulas express relations between quantities. Published Mythos and Astra examples illustrate dependence on task context. These observations describe task-conditioned shorthand; independent human validation of the coding is pending.')
    blocks={
    'Введение':[
    'Опубликованная текстовая цепочка рассуждения (reasoning trace) позволяет анализировать языковую запись решения. Она не открывает всех вычислений модели. В официальной карточке Mythos [1] показаны плотные записи с формулами и условными знаками. Их внешний вид ставит лингвистический вопрос: какие отношения ещё выражены словами, а какие приходится восстанавливать из задачи? Работы о наблюдаемости [2] и корпус текстовых цепочек рассуждения [12] рассматривают доступность информации проверяющему, которая не сводится к обычной длине текста.',
    'Проверка соответствия цепочки вычислению требует дополнительных оснований. Препринт об информационном потоке [3] предлагает оценивать причинную роль текста. Рецензируемые исследования показывают, что вмешательство в цепочку меняет ответ, хотя модель может этого не признавать [4], а отсутствие упоминания подсказки не всегда означает отсутствие причинной связи [5]. Формальная проверка в контекстных задачах [6] задаёт другой критерий — допустимость перехода. Поэтому грамматическое восстановление пропуска само по себе не проверяет доказательство.',
    'Текстовые переходы можно описывать как иерархию состояний [7]. Препринт ReasonXL [8] исследует смену естественного языка рассуждения; это не то же самое, что сокращение английской конструкции. Работы о сверхтокенах [9], черновой записи [10] и дистилляции сокращённых цепочек [11] показывают разные способы уменьшения записи. Их протоколы предполагают специально обученные преобразования; для наблюдаемого фрагмента нельзя заранее принять такой механизм. Здесь сопоставляются поверхностные показатели и явные языковые конструкции одного корпуса.',
    'Цель — описать языковые и символические средства сокращения и выявить, какие связи сохраняются в отобранных фрагментах. Для этого сравниваются записи четырёх моделей на одинаковых вопросах и разбираются 96 фрагментов этого же корпуса. Опубликованные фрагменты Astra из технического отчёта AISI [13] и экспериментально вызванные объяснения [14] используются вместе с Mythos как внешние иллюстрации; их режимы получения различаются.'
    ],
    'Материалы и методы':[
    f'Корпус Measuring Chain-of-Thought Monitorability Transcripts [12] закреплён на ревизии a7a8b25ae467. Из 446 208 исходных строк выделены непустые baseline reasoning; поле output не подменяет цепочку. Использованы все {m["questions"]} общих вопроса из {m["tasks"]} задач BBH, MMLU и GPQA, без лимита вопросов на задачу: по одному trace от Claude 3.7 Sonnet, DeepSeek R1 0528, Qwen3 235B A22B thinking 2507 и QwQ 32B. Mythos и Astra в количественном корпусе отсутствуют.',
    f'Краткость измеряется числом whitespace-токенов; алгоритмическая сжимаемость — отношением R размера zlib level 9 к размеру исходного UTF-8; языковое сокращение — размеченными конструкциями. Эти три характеристики не взаимозаменяемы. Основная единица сравнения — вопрос. Из начала, середины и конца каждой цепочки извлечены полные окна по 128 whitespace-токенов с сохранением пробелов; одинаковые позиции исключены. Показатели окон усреднены внутри цепочки. Включены только вопросы, у которых все четыре цепочки достаточно длинны: {primary["complete_questions"]} вопросов, {primary["paired_rows"]} цепочек; исключены {primary["excluded_short_questions"]} вопросов. Окна не считаются независимыми наблюдениями.',
    'S и P — доли символов категорий Unicode S и P среди непробельных знаков. Дополнительно рассчитаны доля пробельных символов во всём тексте, доля прописных среди латинских букв, доля операторов/стрелок по фиксированному набору, плотность emoji и средняя длина последовательности без пробелов. Последние две метрики описательные. H — энтропия эмпирического распределения всех символов, включая пробелы, в битах; она характеризует разнообразие алфавита, а не смысловую плотность.',
    'Для лексической редкости L выделяются последовательности [A-Za-z]+ с одним внутренним апострофом, регистр понижается, дефис разделяет слова; L — доля с Zipf-частотностью wordfreq ниже 2. Имена не исключаются; новые слова не отделяются автоматически, нелатинские слова не входят в этот признак. Повторяемость Q = 1−U/G вычисляется для перекрывающихся четырёхграмм исходных whitespace-токенов: U — число уникальных, G — всех; регистр и пунктуация сохранены.',
    'Для восьми основных показателей сохранены все шесть пар моделей: медианы парных разностей, ранговая бисериальная корреляция и 95% интервалы. Bootstrap: 1000 повторений, seed 20261002; сначала задачи, затем вопросы внутри выбранной задачи, с сохранением пары моделей. Уилкоксон и Holm на 48 проверок приведены в дополнительных таблицах как вопросные тесты; они не учитывают зависимость внутри задачи, поэтому основной вывод опирается на иерархические интервалы. Окна 256 и 512 токенов и только начальные окна служат проверками устойчивости. Отбор цепочек с ≥95% латинских букв сохранил всю основную выборку и не является отдельной проверкой английского языка. Правильность ответа не входит в цель и выводы.',
    'Для разбора выбраны 24 вопроса: 8 с наибольшим S, 8 с наибольшим P среди остальных и 8 случайных; используется максимум показателя среди четырёх моделей вопроса. Все модели дают 96 фрагментов по 40 whitespace-токенов с вопросом и соседним контекстом. Выбрано наиболее символьно насыщенное из доступных окон. Справочник задаёт восемь категорий: эллипсис, символическая замена, необычное словообразование, пропуск аргумента, маркер вывода, смена языка, телеграфный синтаксис, сокращённая ссылка. Граница выделения не считается эллипсисом. Первичная разметка выполнена ИИ-ассистентом с текстовыми основаниями; второго аннотатора нет, согласие не оценивалось. Выборка обогащена знаками, поэтому её частоты не оценивают распространённость в корпусе.',
    'Разработанное ПО на Python и Streamlit использовано для аудита ключей, парного отбора, извлечения неизменённых окон, расчёта признаков, иерархического bootstrap и формирования банка разметки. Интерфейс связывает исходный вопрос, цепочку, локальные показатели и решения по категориям; позволяет выгрузить данные для проверки. Код, конфигурация, зависимости и таблицы подготовлены для репозитория github.com/ANSTAPABAL/research-mythos. Версия публикации и состояние выгрузки фиксируются в материалах проекта.'
    ],
    'Результаты':[
    f'Таблица 1 показывает медианы оконных показателей и длины полных цепочек на тех же 2875 вопросах. Для полных цепочек медиана R у Claude составляет {decimal(wc.zlib_ratio)}, у DeepSeek — {decimal(wd.zlib_ratio)}; длина — {int(wc.whitespace_tokens)} и {int(wd.whitespace_tokens)} токенов соответственно. При окнах одинаковой токенной длины порядок меняется: R равен 0,503 и 0,534. Медиана парной разности Claude−DeepSeek — {v["median_paired_difference"]}, 95% ДИ [{v["ci95_low"]}; {v["ci95_high"]}], ранговый эффект {v["rank_biserial"]}. Это различие регулярности записи, а не измерение её смыслового сокращения.',
    'Во всех трёх сравнениях Claude с другими моделями оконный R ниже; интервалы не включают ноль (рис. 1). Для окон 256 и 512 токенов это направление сохраняется, но состав меняется: подходят 1668 и 576 вопросов соответственно. Поэтому эти срезы не следует трактовать как один и тот же набор наблюдений. Только начальные окна также сохраняют отличие Claude. Для DeepSeek−Qwen3 основной интервал включает ноль, несмотря на малое вопросное p; это показывает значение учёта структуры задач.',
    f'В первичной разметке символическая запись отмечена в {ann["counts"]["symbolic_substitution"]} из 96 фрагментов, эллипсис — в {ann["counts"]["ellipsis"]}, маркеры вывода — в {ann["counts"]["inference_marker"]}, телеграфный синтаксис — в {ann["counts"]["telegraphic_syntax"]}, сокращённые ссылки — в {ann["counts"]["compressed_reference"]}, пропуск аргумента — в {ann["counts"]["argument_omission"]}. Категории пересекаются. Необычное словообразование и смена естественного языка не были отмечены в первичной разметке данной выборки. Это результаты разметки отобранных примеров, требующие независимой проверки, а не межмодельные оценки распространённости.'
    ],
    'Лингвистический разбор корпусных фрагментов':[
    'В A013 (Claude, навигация) «New position: (0, 4)» сохраняет именование состояния, но опускает связку is. Координаты выражают значение без словесного описания двух компонент. Следующее So связывает итог с последовательностью перемещений. Минимальное дополнение «The new position is (0, 4)» восстанавливает грамматику; правильность координат требует проверки предыдущих команд. Стандартная формула сама по себе не является необычным языковым сокращением.',
    'В A026 (DeepSeek, распознавание сарказма) стрелка в «realism → sarcasm» обозначает связь интерпретаций. «For Option B: Has cameras» опускает субъект game, доступный из вопроса. Therefore сохраняет маркировку вывода. В A092 (QwQ, двухзначное число) «Not integer» допускает восстановление «It is not an integer»: отрицание сохранено при пропуске субъекта, связки и артикля. Стрелки связывают арифметические преобразования, но не содержат всех словесных оснований. Фрагмент A040 (QwQ, оператор Гамильтона) использует «that\'s consistent» для ссылки на предшествующую проверку trace(H²).',
    'Контрпример A001 описывает поиск антецедента местоимения полными английскими предложениями. Упомянутое в условии he не размечено автоматически как сокращённая ссылка самой модели. В A032 фазовые сдвиги повторяют список условия; их необычные знаки не приняты за новый лингвистический механизм. Такое разделение помогает переходить от числового выделения участков к проверке конкретной конструкции.'
    ],
    'Иллюстративный анализ опубликованных фрагментов Mythos и Astra':[
    'В тренировочном фрагменте Mythos [1, с. 106–107] формы celled и celling используют английскую основу cell и продуктивные окончания -ed и -ing. Это поддерживает разбор через конверсию и словоизменение. Однако -ed без синтаксического окружения не различает прошедшее время и причастие, а -ing не устанавливает прогрессивный аспект самостоятельно. Масти и стрелки задают локальную нотацию операций. Немецкое verdammt представляет переключение лексического регистра; экспрессивная пунктуация не измеряет эмоциональное состояние модели.',
    'Выдержка raw CoT Astra в оценке AISI [13, с. 7] содержит «User likely scripted continuer prompt never provide explicit, task cannot resolve valid scope.» Likely сохраняет оценку вероятности, never — отрицание, cannot — модальное ограничение. У provide не выражен объект; без контекста нельзя уверенно выбрать его восстановление. Continuer допускает английское образование на -er, но значение этой номинации не устанавливается одним словом. Это отобранный исследователями фрагмент конкретного эпизода, а не типичная цепочка Astra.',
    'В специально вызванном объяснении [14, с. 6] опубликовано: «Subtract first two gives (b-c)(a+b+c-3)=0 so sum3.» First two ссылается на первые два уравнения; so маркирует вывод. Минимальное грамматическое дополнение: «Subtracting the first two equations gives (b−c)(a+b+c−3)=0, so the sum is 3». Оно раскрывает пропуски, но переход ещё требует условия b≠c. Это условие дано в соседнем решении той же задачи. Полное содержательное расширение должно добавить его явно; такое добавление опирается на математический контекст, а не только на английскую грамматику. Вызванное объяснение не подтверждено как дословная нативная скрытая цепочка.',
    'Эти внешние случаи иллюстрируют сохранение морфологии, отрицания и маркеров при сокращении записи, а также границы восстановления. Сопоставима функция языковых связей; частоту явлений и различия Mythos/Astra по разным публикациям сравнивать нельзя.'
    ],
    'Обсуждение':[
    'Лингвистическая часть объясняет, что позволяет читать короткую запись: словесный маркер указывает тип перехода, морфология сохраняет часть грамматической информации, ссылка связывает фрагмент с задачей, формула задаёт отношение величин. Потенциальная экономия записи не означает улучшения ответа. Чтобы установить пользу для модели, нужен эксперимент с раскрытием пропусков и заменой знаков при сохранении содержания; в этом исследовании он не выполнен.',
    'Одинаковое число whitespace-токенов контролирует токенную длину, но не число символов или байтов; математический токен может быть длиннее обычного слова. R зависит также от алфавита и повторов, поэтому его связь с категориями разметки не установлена причинно. Иерархический bootstrap отражает вариацию задач этого корпуса и не гарантирует перенос на другие задачи. Отбор символьно насыщенных фрагментов и ИИ-разметка ограничивают обобщение; повторяемость вычисления не заменяет независимую проверку человеком. Справочник и обезличенный файл подготовлены для неё.'
    ],
    'Заключение':[
    'Предложена проверяемая схема восьми категорий для разбора сокращённых текстовых цепочек, связанная через программный анализатор с исходными фрагментами и контекстом. В корпусных примерах отмечены английские маркеры вывода, а также пропуски связок и аргументов; математические отношения могут выражаться формулами. Оконный анализ показывает, что порядок моделей по алгоритмической сжимаемости меняется относительно сравнения полных цепочек. Опубликованные примеры Mythos и Astra совместимы с задачной сокращённой записью, опирающейся на английскую морфологию, синтаксис и символическую нотацию. Следующий проверяемый этап — независимая человеческая разметка по сохранённому справочнику.'
    ]}
    final=OUT/'final_review'
    checks=js(final/'manifest.json');random=js(final/'random_annotation_summary.json')
    overlap=pd.read_csv(final/'cooccurrence_enriched96.csv',index_col=0)
    blocks['Материалы и методы'][4]=blocks['Материалы и методы'][4].replace('Окна 256 и 512 токенов и только начальные окна служат проверками устойчивости.', 'Проверки устойчивости используют окна 64, 256 и 512 токенов, только начальные окна, а также окна по 800 символов Unicode и 800 байтов UTF-8. Для двух последних размеров рассчитан только R; байтовые срезы сжимаются непосредственно, без декодирования и языковой интерпретации границ. Позиции и усреднение те же; bootstrap сохраняет структуру задача → вопрос.')
    blocks['Материалы и методы'][5]+=' Дополнительно равновероятно выбраны 8 вопросов из всех 3022, затем независимо случайная позиция до 40 токенов каждой цепочки: ещё 32 фрагмента, seed 20261003, без отбора по S или P. Их ИИ-разметка хранится отдельно.'
    lines=[]
    for mode in checks['sensitivity']:
        paired=pd.read_csv(final/(mode['mode']+'_paired.csv'))
        key2=paired[paired.metric.eq('zlib_ratio') & paired.model_a.str.contains('claude') & paired.model_b.str.contains('deepseek')].iloc[0]
        label={'tokens64':'64 токена','characters800':'800 символов','bytes800':'800 байтов'}[mode['mode']]
        lines.append(f"{label}: n={mode['questions']}, Δ={decimal(key2.median_paired_difference)}, ДИ [{decimal(key2.ci95_low)}; {decimal(key2.ci95_high)}]")
        assert (paired[paired.metric.eq('zlib_ratio') & paired.model_a.str.contains('claude')].ci95_high<0).all()
    blocks['Результаты'][1]+=' Дополнительные сравнения Claude−DeepSeek: '+ '; '.join(lines)+'. Во всех трёх срезах R у Claude также ниже Qwen3 и QwQ; интервалы не включают ноль.'
    blocks['Результаты'][2]=blocks['Результаты'][2].replace('Категории пересекаются.',f"Эллипсис и маркер вывода пересекаются в {int(overlap.loc['ellipsis','inference_marker'])} фрагментах; символическая запись и маркер — в {int(overlap.loc['symbolic_substitution','inference_marker'])}. Полная матрица 8×8 сохранена в материалах.")
    blocks['Результаты'][2]+=f" В отдельной случайной выборке из 32 фрагментов отмечены эллипсис ({random['counts']['ellipsis']}), символическая запись ({random['counts']['symbolic_substitution']}), маркер вывода ({random['counts']['inference_marker']}); 16 фрагментов не получили ни одной категории. Малый объём и ИИ-разметка не позволяют оценивать распространённость."
    blocks['Обсуждение'][1]=blocks['Обсуждение'][1].replace('Одинаковое число whitespace-токенов контролирует токенную длину, но не число символов или байтов; математический токен может быть длиннее обычного слова.', 'Проверки на 800 символах и 800 байтах сохраняют направление различий Claude при иных единицах длины; смена состава выборки ограничивает прямое сравнение величин эффектов.')
    # Linguistic analyses are subsections of Results; the five required main sections remain exact.
    from article_editorial import revise
    abstract,abstract_en,blocks=revise(blocks,m,key)
    publication=OUT/'publication_status.json'
    if publication.exists():
        status=js(publication)
        if status.get('remote_verified'):
            blocks['Материалы и методы'][-1]=blocks['Материалы и методы'][-1].replace('подготовлены для репозитория github.com/ANSTAPABAL/research-mythos. Версия публикации и состояние выгрузки фиксируются в материалах проекта.',f'опубликованы в github.com/ANSTAPABAL/research-mythos, версия {status["tag"]}, идентификатор {status["commit"][:12]}.')
    path=ROOT/'article/article_final_v2_3.docx';doc=blank_from_template(path);doc.core_properties.title=TITLE;doc.core_properties.subject='Лингвистика текстовых цепочек; оконный корпусный анализ'
    para(doc,'УДК 004.8',indent=False,after=3)
    p=para(doc,TITLE,style='Title',indent=False,after=3);p.runs[0].bold=True;p.paragraph_format.keep_with_next=True
    authors(doc);para(doc,'Научный руководитель — Белова Татьяна Мухорамовна, кандидат филологических наук, доцент.',indent=False,after=3)
    para(doc,abstract,bold_prefix='Аннотация. ',indent=False,after=3)
    keywords='текстовые цепочки рассуждения; корпусная лингвистика; эллипсис; символическая нотация; алгоритмическая сжимаемость.'
    para(doc,keywords,bold_prefix='Ключевые слова: ',indent=False,after=3)
    p=para(doc,EN,indent=False,after=3);p.runs[0].bold=True;authors(doc,True)
    para(doc,abstract_en,bold_prefix='Abstract. ',indent=False,after=3)
    para(doc,'reasoning traces; corpus linguistics; ellipsis; symbolic notation; algorithmic compressibility.',bold_prefix='Keywords: ',indent=False,after=3)
    for title,texts in blocks.items():
        if title in ['Лингвистический разбор корпусных фрагментов','Иллюстративный анализ опубликованных фрагментов Mythos и Astra']:
            p=para(doc,title,indent=False,after=2);p.runs[0].italic=True;p.paragraph_format.keep_with_next=True
        else:head(doc,title)
        for i,tx in enumerate(texts):
            if title=='Введение' and tx.startswith(('Научная новизна. ','Практическая значимость. ')):
                label,body=tx.split('. ',1);para(doc,body,bold_prefix=label+'. ')
            else:para(doc,tx)
            if title=='Результаты' and i==0:
                para(doc,'Таблица 1. Медианы на вопросах основной оконной выборки',indent=False,after=2)
                rows=[]
                for r in med.itertuples():
                    rows.append([short(r.model),int(full.loc[r.model,'whitespace_tokens']),decimal(r.symbol_density),decimal(r.punctuation_density),decimal(r.char_entropy),decimal(r.zlib_ratio),decimal(r.low_frequency_fraction),decimal(r.repeat_4gram)])
                # Whole-trace and window descriptors use exactly the same eligible questions.
                table(doc,rows,['Модель','Длина¹','S','P','H','R₁₂₈','L','Q'],[3.8,1.8,1.4,1.4,1.4,1.4,1.4,1.4])
                para(doc,'¹ Длина полной цепочки. Все показатели таблицы относятся к одним и тем же 2875 вопросам. H — описательный показатель; дополнительные признаки и все парные эффекты сохранены в CSV.',indent=False,after=3)
                para(doc,'Меньшее R означает более сжимаемую запись. По полным цепочкам Claude выглядит менее сжимаемым, чем DeepSeek, а при одинаковой длине окна — более сжимаемым. Следовательно, сравнение полных цепочек смешивает различия регулярности записи с различиями длины; его нельзя непосредственно трактовать как языковое сокращение.')
                picture(doc,OUT/'figures/fixed_window_comparison.png','Рис. 1. Распределения R и парные разности при окнах 128 токенов')
    head(doc,'Список источников')
    refs=source_list()
    for tx in refs:
        p=para(doc,tx,indent=False);p.alignment=WD_ALIGN_PARAGRAPH.LEFT;p.paragraph_format.left_indent=Cm(.7);p.paragraph_format.first_line_indent=Cm(-.7)
    doc.save(path)
    readable='\n\n'.join(p.text for p in doc.paragraphs)
    (ROOT/'article/manuscript_review_v2.json').write_text(json.dumps({'title_ru':TITLE,'title_en':EN,'abstract_ru':abstract,'abstract_en':abstract_en,'sections':blocks,'sources':refs},ensure_ascii=False,indent=2),encoding='utf8')
    (ROOT/'article/manuscript_readable.txt').write_text(readable,encoding='utf8')
    a=blank_from_template(ROOT/'article/abstract_1page_v2_3.docx');a.core_properties.title=TITLE
    p=para(a,TITLE,style='Title',indent=False,after=4);p.runs[0].bold=True;authors(a)
    para(a,'Научный руководитель — Белова Татьяна Мухорамовна, кандидат филологических наук, доцент.',indent=False,after=3)
    para(a,abstract,after=4)
    para(a,'Программный анализатор связывает числовые показатели с вопросом, исходной записью и основаниями языковой разметки. Это позволяет проверить конкретный пропуск и отделить грамматическое дополнение от добавления условий задачи. Фиксированные окна контролируют длину записи; проверки на токенах, символах и байтах сохраняют направление различий Claude. Mythos и Astra рассматриваются отдельно от количественного корпуса.',after=4)
    para(a,keywords,bold_prefix='Ключевые слова: ',indent=False)
    for p in a.paragraphs:p.paragraph_format.line_spacing=1.5
    a.save(ROOT/'article/abstract_1page_v2_3.docx')
    (OUT/'article_build_manifest.json').write_text(json.dumps({'title':TITLE,'references':len(refs),'abstract_ru_characters':len(abstract),'abstract_en_characters':len(abstract_en),'article_characters':len(readable),'analysis_config_sha256':m['analysis_config_sha256']},ensure_ascii=False,indent=2),encoding='utf8')
    print('Reviewed article built:',len(readable),'characters;',len(refs),'sources; abstract',len(abstract))
if __name__=='__main__':main()
