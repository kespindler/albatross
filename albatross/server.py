import re
import asyncio
import urllib.parse as parse
from albatross import Request, Response
from albatross.status_codes import HTTP_404


class Server:
    """The core albatross server

    Attributes:
        _handlers (list): a list of route-handler tuples
        _middleware (list): a list of middlewares to process requests
    """
    def __init__(self):
        self._handlers = []
        self._middleware = []

    def get_handler(self, path):
        for route, handler in self._handlers:
            match = route.match(path)
            if match:
                return handler, match.groupdict()
        return None, None

    def add_route(self, route, handler):
        route += '$'
        compiled = re.compile(route)
        self._handlers.append((compiled, handler))

    def add_middleware(self, middleware):
        self._middleware.append(middleware)

    def parse_header_lines(self, lines):
        headers = {}
        for l in lines:
            key, value = l.split(': ', 1)
            headers[key] = value
        return headers

    async def _handle(self, request_reader, response_writer):
        """Takes reader and writer from asyncio loop server and writes the response to the request.

        :param request_reader:
        :param response_writer:
        :return:
        """
        request_line = await request_reader.readline()
        request_line = request_line.decode()
        method, url_string, _ = request_line.split(' ', 2)
        method = method.upper()
        url = parse.urlparse(url_string)

        header_lines = []
        while True:
            l = await request_reader.readline()
            if l == b'\r\n':
                break
            header_lines.append(l.decode())

        headers = self.parse_header_lines(header_lines)

        body = None
        if method in {'POST', 'PUT'}:
            content_length = int(headers.get('Content-Length', 0))
            body = await request_reader.read(content_length)
            body = body.decode()

        path = url.path

        handler, args = self.get_handler(path)

        req = Request(method, path, url.query, body, args)
        res = Response(response_writer)

        for middleware in self._middleware:
            await middleware.process_request(req, res, handler)

        if handler is None:
            res.status_code = HTTP_404
        elif method == 'GET':
            await handler.on_get(req, res)
        elif method == 'POST':
            await handler.on_post(req, res)
        elif method == 'PUT':
            await handler.on_put(req, res)
        elif method == 'DELETE':
            await handler.on_delete(req, res)
        else:
            raise ValueError('Unrecognized method %s' % method)

        for middleware in self._middleware:
            await middleware.process_response(req, res, handler)

        if not res._response_started:
            res.start_response()
        response_writer.write_eof()
        await response_writer.drain()
        response_writer.close()

    def serve(self):
        loop = asyncio.get_event_loop()
        loop.create_task(asyncio.start_server(self._handle, '0.0.0.0', 8000))
        loop.run_forever()
        loop.close()
