

class HTTPError(Exception):
    def __init__(self, code, message=None):
        self.status_code = code
        self.message = message or code
