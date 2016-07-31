import unittest
from albatross import Request
from albatross.http_error import HTTPError


class RequestTest(unittest.TestCase):

    def test_request(self):
        r = Request(
            'POST', '/hello/test',
            'foo=baz', raw_body=b'one=two',
            args={'name': 'test'},
            headers={}
        )
        assert r.method == 'POST'
        assert r.path == '/hello/test'
        assert r.query_string == 'foo=baz'
        assert r.form['one'] == 'two'
        assert r.form.get('one') == 'two'
        assert r.form.get('two') is None
        with self.assertRaises(HTTPError):
            assert r.form['three']
