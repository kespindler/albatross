import re
import asyncio
import urllib.parse as parse
from albatross import Request, Response
from albatross.status_codes import HTTP_404, HTTP_500, HTTP_405
from albatross.http_error import HTTPError
import traceback


class Server:
    """The core albatross server

    Attributes:
        _handlers (list): a list of route-handler tuples
        _middleware (list): a list of middlewares to process requests
    """
    def __init__(self):
        self._handlers = []
        self._middleware = []
        self.max_read_chunk = 1024*1024
        self.debug = False
        self.spoof_options = True

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

    def _parse_header_lines(self, lines):
        headers = {}
        for l in lines:
            try:
                key, value = l.split(':', 1)
                headers[key] = value.strip()
            except ValueError:
                pass
        return headers

    async def _parse_request(self, request_reader):
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

        headers = self._parse_header_lines(header_lines)

        body = None
        if method in {'POST', 'PUT'}:
            body_parts = []
            content_length = int(headers.get('Content-Length', 0))
            while content_length > 0:
                read_chunk = max(content_length, self.max_read_chunk)
                body = await request_reader.read(read_chunk)
                body_parts.append(body.decode())
                content_length -= read_chunk
            body = ''.join(body_parts)

        path = url.path
        query = url.query

        handler, args = self.get_handler(path)

        req = Request(method, path, query, body, args, headers)

        return req, handler

    async def _route_request(self, handler, req, res):
        method = req.method
        if handler is None:
            raise HTTPError(HTTP_404)
        elif method == 'GET' and hasattr(handler, 'on_get'):
            await handler.on_get(req, res)
        elif method == 'POST' and hasattr(handler, 'on_post'):
            await handler.on_post(req, res)
        elif method == 'PUT' and hasattr(handler, 'on_put'):
            await handler.on_put(req, res)
        elif method == 'DELETE' and hasattr(handler, 'on_delete'):
            await handler.on_delete(req, res)
        elif method == 'OPTIONS':
            if hasattr(handler, 'on_options'):
                await handler.on_options(req, res)
            elif self.spoof_options:
                res.headers['Allow'] = 'GET,POST,DELETE,PUT'
        else:
            raise HTTPError(HTTP_405)

    async def _handle(self, request_reader, response_writer):
        """Takes reader and writer from asyncio loop server and writes the response to the request.

        :param request_reader:
        :param response_writer:
        :return:
        """
        req, handler = await self._parse_request(request_reader)

        res = Response()

        try:
            for middleware in self._middleware:
                await middleware.process_request(req, res, handler)

            await self._route_request(handler, req, res)
        except Exception as e:
            res.clear()
            if isinstance(e, HTTPError):
                res.status_code = e.status_code
            else:
                res.status_code = HTTP_500
            self.handle_error(res, e)

        for middleware in self._middleware:
            await middleware.process_response(req, res, handler)

        self._write_response(res, response_writer)
        await response_writer.drain()
        response_writer.close()

    def handle_error(self, res, e):
        res.write(res.status_code)
        traceback.print_exc()

    def _write_response(self, res, writer):
        writer.write(b'HTTP/1.0 %s\r\n' % res.status_code.encode())
        for key, value in res.headers.items():
            writer.write(key.encode() + b': ' + value.encode() + b'\r\n')
        writer.write(b'\r\n')
        for chunk in res._chunks:
            writer.write(chunk)
        writer.write_eof()

    async def initialize(self):
        pass

    def serve(self, port=8000, host='0.0.0.0', debug=False):
        if debug:
            self.debug = True

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.initialize())
        print('Serving on %s:%d' % (host, port))
        loop.create_task(asyncio.start_server(self._handle, host, port))
        loop.run_forever()
        loop.close()
