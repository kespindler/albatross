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
REQUEST_STATE_CONTINUE = 1
REQUEST_STATE_COMPLETE = 2


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

    def __init__(self, method=None, path=None, query_string='',
                 args=None, headers=None, form=None, cookies=None):
        self._header_list = []
        self._state = REQUEST_STATE_PROCESSING
        self.method = method
        self.path = path
        self.query_string = query_string
        self.query = None
        self.args = args
        self.headers = ImmutableCaselessMultiDict()
        self.cookies = ImmutableMultiDict()
        self.raw_body = io.BytesIO()
        self.form = form

        if query_string:
            self.query = ImmutableMultiDict(parse.parse_qs(self.query_string))

        if headers:
            self.headers = ImmutableCaselessMultiDict(**headers)

        if cookies:
            self.cookies = ImmutableMultiDict(**cookies)

    def _parse_cookie(self, value):
        cookies = trim_keys(parse.parse_qs(value))
        return ImmutableMultiDict(cookies)

    def _parse_form(self, body_stream):
        # TODO theres probably a way to not read whole body first)
        env = {'REQUEST_METHOD': 'POST'}
        form = cgi.FieldStorage(body_stream, headers=self.headers, environ=env)
        d = {}
        for k in form.keys():
            if form[k].filename:
                d[k] = [FileStorage(form[k])]
            else:
                d[k] = [form[k].value]
        return ImmutableMultiDict(d)

    def _parse_body(self, body_stream):
        content_type = self.headers.get('Content-Type', '')
        if content_type == 'application/json':
            data = body_stream.getvalue().decode()
            self.form = json.loads(data)
        elif content_type.startswith('multipart/form-data'):
            self.form = self._parse_form(body_stream)
        elif content_type == 'application/x-www-form-urlencoded':
            data = body_stream.getvalue().decode()
            self.form = ImmutableMultiDict(parse.parse_qs(data))
        body_stream.seek(0)

    # HTTPRequestParser protocol methods
    def on_url(self, url: bytes):
        parsed = parse_url(url)
        self.path = parsed.path.decode()
        self.query_string = (parsed.query or b'').decode()
        self.query = ImmutableMultiDict(parse.parse_qs(self.query_string))

    def on_header(self, name: bytes, value: bytes):
        self._header_list.append((name.decode(), value.decode()))
        if name.lower() == b'expect' and value == b'100-continue':
            self._state = REQUEST_STATE_CONTINUE

    def on_headers_complete(self):
        self.headers = ImmutableCaselessMultiDict(self._header_list)
        cookie_value = self.headers.get('Cookie')
        if cookie_value:
            self.cookies = self._parse_cookie(cookie_value)

    def on_body(self, body: bytes):
        self.raw_body.write(body)

    def on_message_complete(self):
        self._state = REQUEST_STATE_COMPLETE
        self.raw_body.seek(0)
        self._parse_body(self.raw_body)

    @property
    def finished(self):
        return self._state == REQUEST_STATE_COMPLETE

    @property
    def needs_write_continue(self):
        return self._state == REQUEST_STATE_CONTINUE

    def reset_state(self):
        self._state = REQUEST_STATE_PROCESSING
