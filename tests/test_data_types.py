import unittest
from albatross.data_types import (
    ImmutableMultiDict, CaselessDict,
    ImmutableCaselessMultiDict
)


class ImmutableMultiDictTest(unittest.TestCase):
    def test_immutable(self):
        z = ImmutableMultiDict(**{'one': ['two', 'three']})
        with self.assertRaises(TypeError):
            z.update({})
        assert z.get_all('one') == ['two', 'three']
        assert z.get_all('two') is None


class CaselessDictTest(unittest.TestCase):
    def test_caselesss(self):
        z = CaselessDict(**{'One': 'two'})
        assert z['one'] == 'two'
        z.update({'Three': 'four'})
        assert z['three'] == 'four'
        z.update([('FIVE', 'six')])
        assert z['five'] == 'six'
        for k in z:
            assert k in z

        assert z.get('two') is None

    def test_caseless_update(self):
        z = CaselessDict(One='two')
        z.update(two=2)
        assert z['TWO'] == 2

    def test_caseless_iterable_init(self):
        z = CaselessDict([
            ('ONE', 1),
            ('TWO', 2),
            ('THREE', 3),
        ])
        assert z['one'] == 1
        assert z['tWO'] == 2
        assert z['thRee'] == 3


class ImmutableCaselessMultiDictTest(unittest.TestCase):
    def test_immutable_caseless_multi_dict(self):
        z = ImmutableCaselessMultiDict([
            ('one', 1),
            ('ONE', 'I'),
            ('tWO', 2),
            ('TwO', 'II'),
        ])

        assert z['one'] == 1, z
        assert z.get('one') == 1
        assert z.get_all('one') == [1, 'I']

        assert z['TWO'] == 2
        assert z.get('Two') == 2
        assert z.get_all('TWO') == [2, 'II']

        assert z.get('three') is None
        assert z.get_all('three') is None
