

class HTTPError(Exception):
    def __init__(self, code):
        self.status_code = code
