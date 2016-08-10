import unittest
from albatross import Request
from albatross.http_error import HTTPError


class RequestTest(unittest.TestCase):

    def test_request(self):
        r = Request()
        r.headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        r._parse_body(b'one=two')
        assert r.form['one'] == 'two'
        assert r.form.get('one') == 'two'
        assert r.form.get('two') is None
        with self.assertRaises(HTTPError):
            assert r.form['two']

    def test_request_repeated_header(self):
        r = Request()
        r.on_header(b'foo', b'bar')
        r.on_header(b'FOO', b'baz')
        r.on_headers_complete()
        assert r.headers.get_all('foo') == ['bar', 'baz']

    def test_request_cookie(self):
        r = Request()
        r.on_header(b'COOKIE', b'token=bizbaz; fizzle=bizzle')
        r.on_headers_complete()
        assert r.cookies['token'] == 'bizbaz'
        assert r.cookies['fizzle'] == 'bizzle'
        assert ' fizzle' not in r.cookies

    def test_request_raw_body(self):
        r = Request()
        r.headers = {}
        r._parse_body(b'stream')
        assert r.raw_body == b'stream'

    def test_request_json(self):
        r = Request()
        r.headers = {'Content-Type': 'application/json'}
        r._parse_body(b'{"my":"name"}')
        assert r.form == {'my': 'name'}
