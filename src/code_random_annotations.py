"""Explicit record of AI-assisted reading of 32 random excerpts with context."""
import json
import pandas as pd
from common import ROOT
from final_review_analysis import LABELS,OUT,cooccurrence
# Recorded decisions after reading each excerpt and adjacent context, not a classifier.
DECISIONS={
1:('et','«- Changes ...», «- No clear joke or wordplay»: списочная запись опускает субъект This edit и конструкцию There is; край «or wordplay» не размечен.'),
2:('','Полные предложения; Puspy процитировано из варианта задания, а не образовано моделью.'),
3:('','Полные английские предложения; края фрагмента не приняты за эллипсис.'),
4:('','Гипотеза о pus и puppy описана полными предложениями; необычный вариант дан в вопросе.'),
5:('','«nine isch nails» скопировано из условия; объяснение содержит выраженные субъекты и связки.'),
6:('r','«NIN» — сокращение ранее названного Nine Inch Nails; цитата Ionch из задания не считается словообразованием модели.'),
7:('','Полные предложения и цитата варианта A; знак замены � не принят за языковую нотацию.'),
8:('','Полные предложения; qnails процитировано из условия.'),
9:('','Субъекты и связки выражены; список вариантов из вопроса не является символической заменой в рассуждении.'),
10:('','«is just plural, not funny» содержит выраженную связку, второй предикат координирован; названия вариантов процитированы.'),
11:('','Начало повторяет варианты задания; дальнейший текст грамматически полный.'),
12:('','Полные предложения; «Option B is» продолжается за границей, что не считается пропуском.'),
13:('eatr','«A) Could be true», «B) Definitely true» опускают субъект statement и связку; последовательность оценок телеграфна. A–D ссылаются на четыре утверждения вопроса.'),
14:('','Вариант B процитирован и объяснён полными предложениями; край «find» связан с предшествующим to.'),
15:('','Полные предложения; But противопоставляет утверждения, а не является маркером вывода по справочнику.'),
16:('','Полные предложения; вопрос «does Jupiter do» продолжается за границей.'),
17:('si','«O(n)» выражает класс сложности; «So, for a sorted array» связывает вывод с предшествующим рассуждением.'),
18:('st','«n-6 to n-1» символически задаёт диапазон; «Indices: n-6, n-5, ...» — локальная заголовочная запись.'),
19:('si','«n-1», «O(n)» выражают количества и сложность; «So the array ...», «So II ...» маркируют выводы.'),
20:('i','«so you have to actually delete it» выводит требование из толкования remove; остальные конструкции полные.'),
21:('i','«so it\'s passive immunity» выводит классификацию из источника антител.'),
22:('i','«So, I need to choose A, B, C, or D» следует из требования формата ответа; само требование процитировано из вопроса.'),
23:('i','«so it\'s adaptive passive immunity» маркирует вывод; it не кодируется автоматически как сокращённая ссылка.'),
24:('','Определения выражены полными конструкциями; конец Natural продолжается за границей.'),
25:('','Полные условные и повествовательные предложения; дефис отделяет пояснение, не символическое отношение.'),
26:('i','«so this doesn\'t explain why ...» маркирует вывод из наблюдаемого паттерна.'),
27:('','Полные английские предложения; край in primary elections — продолжение предложения из контекста.'),
28:('i','«so this might not be the right answer» выводит оценку варианта из несоответствия условию.'),
29:('et','«Short-run unemployment falls: Correct» — заголовочная оценка без связки is correct; несколько однотипных блоков. Данные вариантов повторены, но оценка Correct добавлена моделью.'),
30:('i','«so for a temporary shock, it doesn\'t change» маркирует вывод; список варианта начинается на краю и продолжается за ним.'),
31:('i','«So unemployment falls», «So in Phillips curve terms» связывают шаги; «AD», «SRPC» — стандартные предметные сокращения, не символическое отношение и не новое слово.'),
32:('i','Два «So the SRPC shifts ...» оформляют выводы; последнее предложение продолжается за границей.')}
KEY={'e':'ellipsis','s':'symbolic_substitution','a':'argument_omission','i':'inference_marker','t':'telegraphic_syntax','r':'compressed_reference'}
def main():
    d=pd.read_csv(ROOT/'data/annotations/random_bank.csv').fillna('')
    for idx,row in d.iterrows():
        number=int(row.annotation_id[1:]);codes,evidence=DECISIONS[number]
        for label in LABELS:d.loc[idx,label]=int(label in [KEY[x] for x in codes])
        d.loc[idx,'evidence']=evidence;d.loc[idx,'annotator']='AI assistant; independent human validation pending'
        d.loc[idx,'notes']='Unconditioned random excerpt; boundary truncation excluded; primary coding only.'
    d.to_csv(ROOT/'data/annotations/random_coded.csv',index=False)
    cooccurrence(d).to_csv(OUT/'cooccurrence_random32.csv')
    summary={'fragments':len(d),'questions':int(d.core_id.nunique()),'counts':{k:int(d[k].astype(int).sum()) for k in LABELS},'any_positive':int(d[LABELS].astype(int).any(axis=1).sum()),'status':'AI-assisted; no independent human validation; small question-clustered random sample, no prevalence estimate'}
    (OUT/'random_annotation_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8');print(summary)
if __name__=='__main__':main()
