from albatross import status_codes


class Response:
    """
    Attributes:
        status_code (str): HTTP status code
        _writer (str): Where to write the response
        content_type (str):
        headers (dict): Be careful about case-sensitivity here.

    """
    def __init__(self, writer):
        self._writer = writer
        self.status_code = status_codes.HTTP_200
        self.content_type = 'text/html'
        self.headers = {}
        self._response_started = False

    def start_response(self):
        self._writer.write(b'HTTP/1.0 %s\r\n' % self.status_code.encode())
        self._writer.write(b'Content-Type: %s\r\n' % self.content_type.encode())
        for key, value in self.headers.items():
            self._writer.write(key.encode() + b': ' + value.encode())

        self._writer.write(b'\r\n')

    def write(self, string):
        """Once you start writing, the headers are fixed.
        """
        if not self._response_started:
            self.start_response()
            self._response_started = True
        self._writer.write(string.encode())
