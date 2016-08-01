import unittest
from albatross.data_types import ImmutableMultiDict, CaselessDict


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
