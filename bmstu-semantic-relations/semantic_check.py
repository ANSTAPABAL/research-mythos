"""Проверка вручную размеченных смысловых элементов: python semantic_check.py examples.json."""
import json
import sys
from pathlib import Path


def check(case):
    if not isinstance(case, dict) or not isinstance(case.get('source'), dict) or not isinstance(case.get('answer'), dict):
        raise ValueError('У примера должны быть объекты source и answer')
    if not case['source']:
        raise ValueError('source не может быть пустым')
    results = {}
    for field, alternatives in case['source'].items():
        if not isinstance(alternatives, list) or not alternatives or any(not isinstance(v, str) or not v for v in alternatives):
            raise ValueError(f'{field}: ожидается непустой список текстовых вариантов')
        answer = case['answer'].get(field)
        if answer is None:
            results[field] = 'не указан в разметке ответа'
            continue
        if not isinstance(answer, dict) or not isinstance(answer.get('value'), str) or not answer['value'] or answer.get('status') not in ('утверждается', 'возможно'):
            raise ValueError(f'{field}: нужны value и status (утверждается или возможно)')
        if answer['value'] not in alternatives:
            results[field] = 'нет опоры в размеченных вариантах'
        elif len(set(alternatives)) > 1 and answer['status'] == 'утверждается':
            results[field] = 'неоднозначность представлена как определённость'
        else:
            results[field] = 'совместимо с разметкой'
    return results


def main():
    if len(sys.argv) != 2:
        raise ValueError('Использование: python semantic_check.py examples.json')
    cases = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8-sig'))
    if not isinstance(cases, list) or not cases:
        raise ValueError('Ожидается непустой массив примеров')
    for case in cases:
        print(f"\n{case.get('id', 'Пример')}: {case.get('description', '')}")
        for field, result in check(case).items():
            print(f'  {field}: {result}')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f'Ошибка: {error}', file=sys.stderr)
        sys.exit(1)
