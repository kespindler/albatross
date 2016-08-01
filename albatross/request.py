from albatross.data_types import ImmutableMultiDict
from albatross.compat import json
import urllib.parse as parse
import cgi
import io


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

    def __init__(self, method, path, query_string, raw_body, args, headers):
        self.method = method
        self.path = path
        self.query_string = query_string
        self.query = ImmutableMultiDict(parse.parse_qs(query_string))
        self.args = args
        self.headers = headers
        self.raw_body = None
        self.form = None
        if raw_body:
            self._parse_body(raw_body)
        if 'Cookie' in headers:
            self.cookies = self._parse_cookie(headers['Cookie'])
        else:
            self.cookies = ImmutableMultiDict()

    def _parse_cookie(self, value):
        cookies = trim_keys(parse.parse_qs(value))
        return ImmutableMultiDict(cookies)

    def _parse_form(self, raw_body):
        # TODO theres probably a way to not read whole body first)
        fp = io.BytesIO(raw_body)
        form = cgi.FieldStorage(fp, headers=self.headers, environ={'REQUEST_METHOD': 'POST'})
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
