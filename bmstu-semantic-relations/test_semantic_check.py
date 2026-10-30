import unittest
from semantic_check import check


class CheckTest(unittest.TestCase):
    def test_relations_and_uncertainty(self):
        case = {'source': {'субъект': ['люди'], 'бюджет': ['Серхио', 'Виктор'], 'число': ['два']},
                'answer': {'субъект': {'value': 'модель', 'status': 'утверждается'},
                           'бюджет': {'value': 'Серхио', 'status': 'утверждается'}}}
        self.assertEqual(check(case), {'субъект': 'нет опоры в размеченных вариантах',
                                       'бюджет': 'неоднозначность представлена как определённость',
                                       'число': 'не указан в разметке ответа'})
        case['answer']['бюджет']['status'] = 'возможно'
        self.assertEqual(check(case)['бюджет'], 'совместимо с разметкой')

    def test_invalid_data_is_rejected(self):
        with self.assertRaises(ValueError):
            check({'source': {'число': []}, 'answer': {}})


if __name__ == '__main__':
    unittest.main()
