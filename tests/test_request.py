import unittest
from albatross import Request
from albatross.http_error import HTTPError


class RequestTest(unittest.TestCase):

    def test_request(self):
        r = Request(
            'POST', '/hello/test',
            'foo=baz', raw_body=b'one=two',
            args={'name': 'test'},
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        assert r.method == 'POST'
        assert r.path == '/hello/test'
        assert r.query_string == 'foo=baz'
        assert r.form['one'] == 'two'
        assert r.form.get('one') == 'two'
        assert r.form.get('two') is None
        with self.assertRaises(HTTPError):
            assert r.form['three']

    def test_request_cookie(self):
        r = Request(
            'GET', '/hello',
            None, None, args={'name': 'test'},
            headers={
                'Cookie': 'token=bizbaz'
            }
        )
        assert r.cookies['token'] == 'bizbaz'

    def test_request_raw_body(self):
        r = Request(
            'POST', '/hello',
            None, b'stream', args={},
            headers={}
        )
        assert r.raw_body == b'stream'

    def test_request_json(self):
        r = Request(
            'POST', '/hello',
            None, b'{"my":"name"}', args={},
            headers={
                'Content-Type': 'application/json'
            }
        )
        assert r.form == {'my': 'name'}
