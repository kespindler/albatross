from albatross.data_types import (
    ImmutableMultiDict,
    ImmutableCaselessMultiDict
)
from albatross.compat import json
import urllib.parse as parse
from httptools import parse_url
import cgi
import io


REQUEST_STATE_PROCESSING = 0
REQUEST_STATE_COMPLETE = 1


def trim_keys(d):
    return {k.strip(): v for k, v in d.items()}


class FileStorage:

    def __init__(self, field_storage):
        self.filename = field_storage.filename
        self.value = field_storage.value


class Request:
    """
    Attributes:
        method (str): One of GET, POST, PUT, DELETE
        path (str): Full request path
        query_string (str): Full query string
        query (dict): dict of the request query
        body (str): Request body
        args (dict): Dictionary of named parameters in route regex
        form (dict): Dictionary of body parameters
    """

    def __init__(self):
        self.method = None
        self.path = None
        self.query_string = ''
        self.query = None
        self.args = None  # TODO
        self.headers = ImmutableCaselessMultiDict()
        self.raw_body = None
        self.form = None
        self._header_list = []
        self._state = REQUEST_STATE_PROCESSING
        self.cookies = ImmutableMultiDict()

    def _parse_cookie(self, value):
        cookies = trim_keys(parse.parse_qs(value))
        return ImmutableMultiDict(cookies)

    def _parse_form(self, raw_body):
        # TODO theres probably a way to not read whole body first)
        fp = io.BytesIO(raw_body)
        env = {'REQUEST_METHOD': 'POST'}
        form = cgi.FieldStorage(fp, headers=self.headers, environ=env)
        d = {}
        for k in form.keys():
            if form[k].filename:
                d[k] = [FileStorage(form[k])]
            else:
                d[k] = [form[k].value]
        return ImmutableMultiDict(d)

    def _parse_body(self, raw_body):
        content_type = self.headers.get('Content-Type', '')
        if content_type == 'application/json':
            self.form = json.loads(raw_body.decode())
        elif content_type.startswith('multipart/form-data'):
            self.form = self._parse_form(raw_body)
        elif content_type == 'application/x-www-form-urlencoded':
            self.form = ImmutableMultiDict(parse.parse_qs(raw_body.decode()))
        else:
            self.raw_body = raw_body

    # HTTPRequestParser protocol methods
    def on_url(self, url: bytes):
        parsed = parse_url(url)
        self.path = parsed.path.decode()
        self.query_string = (parsed.query or b'').decode()
        self.query = ImmutableMultiDict(parse.parse_qs(self.query_string))

    def on_header(self, name: bytes, value: bytes):
        self._header_list.append((name.decode(), value.decode()))

    def on_headers_complete(self):
        self.headers = ImmutableCaselessMultiDict(self._header_list)
        cookie_value = self.headers.get('Cookie')
        if cookie_value:
            self.cookies = self._parse_cookie(cookie_value)

    def on_body(self, body: bytes):
        self._parse_body(body)

    def on_message_complete(self):
        self._state = REQUEST_STATE_COMPLETE

    @property
    def finished(self):
        return self._state == REQUEST_STATE_COMPLETE
