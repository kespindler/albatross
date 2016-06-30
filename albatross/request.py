import urllib.parse as parse


class Request:
    """
    Attributes:
        method (str): One of GET, POST, PUT, DELETE
        path (str): Full request path
        query_string (str): Full query string
        query (dict): dict of the request query
        body (str): Request body
        args (dict): Dictionary of named parameters in route regex
    """
    def __init__(self, method, path, query_string, body, args):
        self.method = method
        self.path = path
        self.query_string = query_string
        self.body = body
        self.query = parse.parse_qs(query_string)
        self.args = args
