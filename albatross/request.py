from albatross.data_types import ImmutableMultiDict, CaselessDict
import urllib.parse as parse
import ujson as json
import re
import cgi
import io


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
        self.query = parse.parse_qs(query_string)
        self.args = args
        self.headers = headers
        self.form = None
        if raw_body:
            self._parse_body(raw_body)
        if 'Cookie' in headers:
            self.cookies = self._parse_cookie(headers['Cookie'])
        else:
            self.cookies = ImmutableMultiDict()

    def _parse_cookie(self, value):
        cookie_pairs = re.findall('(\w+)=([^,;]+)', value)
        return ImmutableMultiDict(cookie_pairs)

    def _parse_form(self, raw_body):
        # TODO theres probably a way to not read whole body first)
        fp = io.BytesIO(raw_body)
        headers = {k.lower(): v for k, v in self.headers.items()}
        form = cgi.FieldStorage(fp, headers=headers, environ={'REQUEST_METHOD': 'POST'})
        return form

    def _parse_body(self, raw_body):
        content_type = self.headers.get('Content-Type', '')
        if content_type == 'application/json':
            self.form = json.loads(raw_body.decode())
        elif content_type.startswith('multipart/form-data'):
            self.form = self._parse_form(raw_body)
        else:
            self.form = ImmutableMultiDict(parse.parse_qs(raw_body.decode()))
