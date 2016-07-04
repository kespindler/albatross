from albatross import status_codes
import ujson as json


class Response:
    """
    Attributes:
        status_code (str): HTTP status code
        headers (dict): Be careful about case-sensitivity here.
        body (str):

    """
    def __init__(self):
        self.status_code = status_codes.HTTP_200
        self._chunks = []
        self.headers = {
            'Content-Type': 'text/html'
        }

    def clear(self):
        self._chunks = []

    def write(self, string):
        self._chunks.append(string.encode())

    def write_bytes(self, bytes):
        self._chunks.append(bytes)

    def write_json(self, data):
        self.headers['Content-Type'] = 'application/json'
        self._chunks.append(json.dumps(data).encode())

    def redirect(self, location, permanent=False):
        self.headers['Location'] = location
        if permanent:
            self.status_code = status_codes.HTTP_301
        else:
            self.status_code = status_codes.HTTP_302
