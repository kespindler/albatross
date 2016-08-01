import unittest
from albatross import Response
from albatross.status_codes import HTTP_301, HTTP_302


class RequestTest(unittest.TestCase):

    def test_request(self):
        r = Response()
        r.redirect('/')
        assert r.headers['Location'] == '/'
        assert r.status_code == HTTP_302

        r.redirect('/another', permanent=True)
        assert r.headers['Location'] == '/another'
        assert r.status_code == HTTP_301
