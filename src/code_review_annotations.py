"""Recorded AI-assisted judgments after reading all 96 excerpts and context.

This is a transparent record, not an automatic linguistic classifier, human
annotation or independent validation. Blank bank remains available separately.
"""
import json
import pandas as pd
from common import ROOT

# e=ellipsis, s=symbolic substitution, a=argument omission, i=inference marker,
# t=telegraphic syntax, r=compressed reference. No verified nonce/code switching.
J={
9:('t','1. Opinion/Evaluation; 2. Size: перечень категорий вместо предикативных предложений.'),
11:('t','1. Opinion; 2. Size; 3. Age: заголовочная запись классификации; цитируемые варианты ответа не размечены как эллипсис модели.'),
13:('esit','New position: (0, 4): восстановима связка is; -> связывает команду с перемещением; So вводит вывод.'),
14:('esit','Perfect balance: неполная оценочная предикация; Start: (0,0), 9 forward: (0,9): краткие блоки; +9 -9=0: отношение; Therefore: вывод.'),
15:('esitr','net zero: связка опущена; Forward: 9, Backward: 5 +4 =9: блоки; So 9-9=0: вывод; That\'s a simpler way отсылает к суммированию перемещений.'),
16:('r','those instructions отсылает к последовательности команд вопроса, а не повторяет её.'),
17:('st','Position += Direction = ...: алгоритмические присваивания и пронумерованные шаги; начало/конец обрезаны границей фрагмента, не эллипсисом модели.'),
18:('s','1+5+1+6 = выражает сумму; результат 13 находится в следующем контексте; обрезка не считается синтаксическим пропуском.'),
19:('ei','here only once: восстановимо the left turn occurs; So вводит выбор ответа. Начальное предложение продолжается из preceding.'),
20:('esit','Still facing east: восстановимо we are; Second/Third/Fourth образуют короткие блоки; (1+5, 0) = (6,0): символическое вычисление; so вводит результат.'),
21:('s','(0, 10 - 9) = (0, 1): символически выражено отношение состояний; граница фрагмента не считается эллипсисом.'),
22:('esi','-5 + 5 = 0, so (0,0): so вводит результат с опущенной предикацией position is.'),
23:('eaitr','So total 15 steps South: опущена связка; ends at start: не выражен субъект path; Which as above отсылает к прежнему расчёту; Alternative approach: краткий блок.'),
24:('etr','Starting at (0,0) facing north: we are восстанавливается в описании движения; 1. 10 steps north: (0,10): блок состояния; that\'s the starting point указывает на (0,0) из preceding.'),
26:('esaitr','realism → sarcasm: символическое следование; For Option B: Has cameras: опущен субъект game; so not sarcastic: связка; Therefore: вывод; Option B указывает на утверждение вопроса.'),
29:('s','f(\\theta) = ...: стандартная формула, выражающая отношение; это не свидетельство нового слова или языка.'),
30:('st','Im[f(0)] = (1/k) * sum ≈ ...: формула; чередование коротких инструкций и вычислительных блоков.'),
31:('esi','Definitely relativistic: восстановимо the electron is; p / ħ: отношение импульса и волнового числа; so связывает энергии. MeV — термин, не новое слово.'),
33:('s','V(\\vec{r},t) = ... и A(\\vec{r},t) = ...: формулы потенциалов; начальное correct answer is продолжает preceding, пропуск не размечен.'),
34:('estr','same V, and A proportional to v^2: опущена связка is и оформлены краткие блоки; same V требует сопоставления с потенциалом другого варианта; математический знаменатель заменяет словесную запись.'),
35:('esit','μ₀ = 1/(ε₀ c²): отношение; so вводит преобразование; not sure: восстановимо I am; чередование формул и коротких самопроверок.'),
36:('ir','So yes: вывод; Which is exactly what option A says отсылает к формуле в preceding и варианту вопроса. Неполное (c d обрезано выделением, не моделью.'),
37:('s','det(H - lambda I) = ...: вычислительное отношение; LaTeX не является переключением естественного языка.'),
38:('esit','Second term: формульный блок; So determinant is: опущен the перед исчисляемым determinant; So вводит вывод; = связывает преобразования.'),
39:('s','H = ε σ · n: стандартное обозначение отношения в задаче; не доказательство необычной компрессии.'),
40:('sir','(ε)^2 + (-ε)^2 = 2 ε²: отношение; Therefore/So: выводы; that\'s consistent отсылает к сопоставлению суммы квадратов с trace(H^2) в preceding.'),
41:('s','(abcde)^M = ... = abcdeba: рекурсивные преобразования; abcdeba — переменные/строка, не новое лексическое производное.'),
42:('esr','Similar to a^M: фрагмент с опущенным субъектом b^M; b^M = b b: отношение; computed earlier отсылает к прежнему вычислению a^M, значение aa повторено ниже.'),
43:('esait','e^M = e: отношение; so holds: не выражен субъект доказываемое свойство; Inductive step: локальный заголовочный блок; so вводит вывод.'),
45:('si','0.0042 < 0.0051: сравнение; So вводит исключение варианта, продолжение this value is too small сохранено в following.'),
46:('esit','52/1000 = 520/10000: отношение; so greater than: опущены субъект и связка; Similarly/числовые проверки образуют краткие локальные блоки; so: вывод.'),
47:('si','0.0042 < 0.0051: сравнение; So/so связывают вывод о диапазоне с вычислением.'),
49:('sit','p <= 23 - (m + a): отношение; So: вывод; Rearranging to isolate p: заголовок шага между формулами.'),
51:('si','m + r > 14: отношение; So выводит его из условия о цене.'),
52:('si','23 - (M + P): формульная запись остатка; So связывает вычисление с ограничением для клея.'),
53:('st','A=F, B=T, C=F и ~A = T: символьная таблица истинности и блоки по строкам; F/T — логические значения, не английское словообразование.'),
54:('estr','T/F кодируют значения в таблице; no (P1 F): опущена связка в P1 is F; строки Row5/Row6: блоки; P1 обозначает первую посылку вопроса.'),
55:('sir','A=F, B=F: условия; Therefore: выводы; Premise1/Premise2 — краткие ссылки на формулы посылок из вопроса/preceding.'),
56:('s','~A ∧ ~B, (A ∨ C) ∨ B: формальные посылки в объяснении; обычная логическая нотация.'),
57:('st','D ⊃ (~E ⊃ F), T/F: формальные отношения и табличные строки; разделитель --|--- — Markdown, не новый язык.'),
58:('esitr','~D ⊃ E = ... = F: отношение; so not all true: опущены premises are; P1/P2/P3: ссылки на посылки; краткие блоки по строкам.'),
59:('eaitr','Alternatively, maybe using logical equivalences: опущено we can use; Premise3: ~E: краткий блок и ссылка на посылку; So we know: вывод.'),
60:('si','D=T, E=F, F=F: запись значений; So переводит словесное условие варианта в символы.'),
65:('sir','f(f(2)) = f(3) = 1: вычисление; so/So: выводы; this point отсылает к ранее рассмотренному x=1, y=f(5) в preceding.'),
66:('es','but still unknown: восстановимо f(f(1)) is; (1, f(f(1))) выражает координаты возможной точки. Обычное it отдельно не размечено.'),
67:('si','x = 1 gives f(f(1)) = f(5): отношение; So вводит заключение о двух определимых точках.'),
68:('sir','ab + cd = ...: выражение; so/So: выводы; either of those отсылает к названным (2,1) и (3,5).'),
69:('s','x^2 + 85 = (x - 17)^2: равенство; right-hand side — обычный математический термин, не новое слово.'),
70:('sit','Simplify/Divide both sides: короткие заголовки операций с формулами; so вводит промежуточное равенство. Императивы не считаются пропуском аргумента.'),
71:('si','(a - b)^2 = a^2 - 2ab + b^2: тождество; so/So: выводы.'),
72:('esitr','Not equal: опущены обе сравниваемые величины и are; Left/Right: краткие вычислительные блоки; Therefore: вывод; A/B/D ссылаются на варианты вопроса.'),
73:('s','V = pi integral ...: отношение объёма и интеграла; стандартная нотация.'),
74:('esai','47π/12 ≈ 3.916π: отношение; not in options: восстановимо result is; so must be symmetric: не выражен субъект planes; so: вывод.'),
75:('sit','At -1: ... = -11/3: краткий блок вычисления; So вводит разность интегральных границ.'),
76:('si','z = -1 and z =1: границы; So вводит выбор ответа.'),
77:('s','x(t) = cos^2 t, y(t) = sin t: параметрическая запись кривой; обычная математическая нотация.'),
78:('esi','so likely length or area: восстановимо the target is; r^2 = a^2 cos 2θ: формула; so: вывод. lemniscate — термин, не новое производное.'),
79:('s','area is (1/2) integral ... = ...: преобразование математического выражения; Then здесь порядок операции, отдельным маркером вывода не размечен.'),
81:('i','So we\'re looking for: следствие из переформулированного ограничения на последовательности.'),
83:('esi','number of sequences is: опущен the; 2^n: формула количества; So/so: вывод. sum from n=1 to 4 допускает императивное чтение, аргумент не размечен.'),
84:('sitr','2^1 = 2, 2^2 =4: вычисления; For n=1/n=2: блоки; so that must be the answer: вывод; C is 30 связывает индекс с вариантом из вопроса.'),
85:('sr','y <= -|x| + 3: неравенство; second inequality отсылает к упорядоченной паре ограничений вопроса.'),
86:('st','Sum B = y1 x2 + ... = 0: отношение и краткие блоки суммирования с индексами.'),
87:('s','y >= |x| и y <= -|x| + 3: формальная запись области; стандартные неравенства, не отдельный код.'),
88:('s','y ≥ |x| и y ≤ -|x| + 3: формальная запись области; вводное Okay, so не размечено как логический вывод.'),
89:('s','10a + b, a >= 1: запись числа и ограничения его разряда; обычные буквенные переменные.'),
90:('es','a=9, b=21 invalid: опущено is; математическая запись параметров; Earlier не имеет достаточного антецедента в локальном контексте, compressed_reference=0.'),
91:('es','n = 10: проверка; Switched is 01: восстановимо switched number, номинальное ядро опущено.'),
92:('esit','76 -8b=3 → -8b= -73: преобразование; Not integer: опущено it is an; a=4/a=5/a=6: краткие блоки; so invalid/So: выводы.')
}
MAP=dict(e='ellipsis',s='symbolic_substitution',a='argument_omission',i='inference_marker',t='telegraphic_syntax',r='compressed_reference')
LABELS=list(MAP.values())+['nonce_derivation','code_switching']
def main():
    folder=ROOT/'data/annotations';d=pd.read_csv(folder/'annotation_bank.csv',keep_default_na=False)
    for c in LABELS:d[c]=0
    for n,(labels,evidence) in J.items():
        mask=d.annotation_id.eq(f'A{n:03d}')
        for label in labels:d.loc[mask,MAP[label]]=1
        d.loc[mask,'evidence']=evidence
    d['annotator']='AI-assisted initial coding; no human second annotator'
    d['notes']='Границы выделения не считаются эллипсисом; нули означают отсутствие подтверждённого примера в данном фрагменте.'
    negative=d[LABELS].sum(axis=1).eq(0)
    d.loc[negative,'evidence']='В пределах фрагмента — связная английская проза или повторение вариантов вопроса; по справочнику подтверждённого примера категорий не выделено.'
    d.loc[d.annotation_id.eq('A032'),'notes']='Значения фазовых сдвигов повторяют список условия; символы в скопированном списке отдельно не размечены.'
    d.loc[d.annotation_id.eq('A080'),'notes']='Математические варианты ответа повторены из вопроса; формула решения в этом фрагменте отсутствует.'
    d.to_csv(folder/'annotation_coded.csv',index=False)
    summary={'n_fragments':len(d),'n_questions':d.core_id.nunique(),'positive_fragments':int((~negative).sum()),'counts':{c:int(d[c].sum()) for c in LABELS},'by_model':d.groupby('model')[LABELS].sum().to_dict('index'),'status':'AI-assisted initial coding; independent human validation pending','agreement':None,'prevalence_estimate':False}
    (ROOT/'outputs/review_v2/annotation_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
    d.groupby('model')[LABELS].sum().to_csv(ROOT/'outputs/review_v2/tables/annotation_counts.csv')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
