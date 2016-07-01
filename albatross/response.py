from albatross import status_codes


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

    def write(self, string):
        self._chunks.append(string)

    def clear(self):
        self._chunks = []
