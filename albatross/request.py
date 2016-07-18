import urllib.parse as parse
import ujson as json
import re


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
    def __init__(self, method, path, query_string, body, args, headers):
        self.method = method
        self.path = path
        self.query_string = query_string
        self.body = body
        self.query = parse.parse_qs(query_string)
        self.args = args
        self.headers = headers
        self.cookies = {}
        self.form = None
        if body:
            self._parse_body()
        if 'Cookie' in headers:
            self.cookies = self._parse_cookie(headers['Cookie'])

    def _parse_cookie(self, value):
        cookie_pairs = re.findall('(\w+)=([^,;]+)', value)
        return dict(cookie_pairs)

    def _parse_form(self):
        content_type = self.headers['Content-Type']
        marker = 'boundary='
        index = content_type.find(marker)
        boundary = '--' + content_type[index + len(marker):]
        values = {}
        for group in re.findall('name=\"([a-zA-Z0-9-]+)\"\r\n\r\n(.*?)\r\n' + boundary, self.body,  re.MULTILINE):
            values[group[0]] = group[1]
        return values

    def _parse_body(self):
        content_type = self.headers['Content-Type']
        if content_type == 'application/x-www-form-urlencoded':
            self.form = parse.parse_qs(self.body)
        elif content_type == 'application/json':
            self.form = json.loads(self.body)
        elif content_type.startswith('multipart/form-data'):
            self.form = self._parse_form()
