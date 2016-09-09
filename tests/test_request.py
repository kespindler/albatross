import unittest
from albatross import Request
from albatross.http_error import HTTPError
from io import BytesIO


class RequestTest(unittest.TestCase):

    def test_request(self):
        r = Request()
        r.method = 'POST'
        r.on_url(b'/hello/test?foo=baz')
        r.args = {'name': 'test'}
        r.on_header(b'CONTENT-TYPE', b'application/x-www-form-urlencoded')
        r.on_headers_complete()
        r.on_body(b'one=two')
        r.on_message_complete()
        assert r.method == 'POST'
        assert r.path == '/hello/test'
        assert r.query_string == 'foo=baz'
        assert r.form['one'] == 'two'
        assert r.form.get('one') == 'two'
        assert r.form.get('ONE') is None
        with self.assertRaises(HTTPError):
            assert r.form['ONE']

    def test_request_cookie(self):
        r = Request()
        r.on_header(b'COOKIE', b'token=bizbaz; fizzle=bizzle')
        r.on_headers_complete()
        assert r.cookies['token'] == 'bizbaz'
        assert r.cookies['fizzle'] == 'bizzle'
        assert ' fizzle' not in r.cookies

    def test_request_raw_body(self):
        r = Request()
        r.on_body(b'stream')
        assert r.raw_body.getvalue() == b'stream'

    def test_request_json(self):
        r = Request()
        r.on_header(b'Content-Type', b'application/json')
        r.on_headers_complete()
        r._parse_body(BytesIO(b'{"my":"name"}'))
        assert r.form == {'my': 'name'}
