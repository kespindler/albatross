import re
import asyncio
import urllib.parse as parse
from datetime import datetime
from albatross import Request, Response
from albatross.status_codes import HTTP_404, HTTP_500, HTTP_405
from albatross.http_error import HTTPError
from albatross.data_types import ImmutableCaselessDict
import traceback
from httptools import HttpRequestParser
from albatross.request import (
    REQ_STATE_EXPECT_CONTINUE,
    REQ_STATE_FINISHED,
    REQ_STATE_PROCESSING,
)


def write_cookie(writer, key, value):
    if isinstance(value, tuple):
        value, duration = value
        if isinstance(duration, datetime):
            format = duration.strftime('%a %d %b %Y %H:%M:%S GMT').encode()
            writer.write(b'Set-Cookie: %s=%s;expires=%s\r\n' % (key.encode(), str(value).encode(), format))
        elif isinstance(duration, int):
            writer.write(b'Set-Cookie: %s=%s;max-age=%d\r\n' % (key.encode(), str(value).encode(), duration))
    else:
        writer.write(b'Set-Cookie: %s=%s\r\n' % (key.encode(), str(value).encode()))


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
        self.spoof_options = True

    def get_handler(self, path):
        for route, handler in self._handlers:
            match = route.match(path)
            if match:
                return handler, match.groupdict()
        return None, None

    def add_regex_route(self, route, handler):
        route += '$'
        compiled = re.compile(route)
        self._handlers.append((compiled, handler))

    def add_route(self, route, handler):
        route = re.sub('{([-_a-zA-Z]+)}', '(?P<\g<1>>[^/?]+)', route)
        self.add_regex_route(route, handler)

    def add_middleware(self, middleware):
        self._middleware.append(middleware)

    async def _parse_request(self, request_reader, response_writer):
        req = Request()
        parser = HttpRequestParser(req)

        while True:
            chunk = await request_reader.read(self.max_read_chunk)
            parser.feed_data(chunk)
            if req._state == REQ_STATE_FINISHED:
                break
            elif req._state == REQ_STATE_EXPECT_CONTINUE:
                response_writer.write(b'HTTP/1.1 100 (Continue)\r\n\r\n')
                req._state = REQ_STATE_PROCESSING

        handler, args = self.get_handler(req.path)

        req.method = parser.get_method().decode().upper()
        req.args = args

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
        else:
            raise HTTPError(HTTP_405)

    async def _handle(self, request_reader, response_writer):
        """Takes reader and writer from asyncio loop server and writes the response to the request.

        :param request_reader:
        :param response_writer:
        :return:
        """
        res = Response()

        try:
            req, handler = await self._parse_request(request_reader, response_writer)

            for middleware in self._middleware:
                await middleware.process_request(req, res, handler)

            try:
                await self._route_request(handler, req, res)
            except HTTPError as e:
                self.handle_error(res, e)

            for middleware in self._middleware:
                await middleware.process_response(req, res, handler)
        except Exception as e:
            self.handle_error(res, e)

        self._write_response(res, response_writer)
        await response_writer.drain()
        response_writer.close()

    def handle_error(self, res, e):
        res.clear()
        if isinstance(e, HTTPError):
            res.status_code = e.status_code
            res.write(e.message)
        else:
            res.status_code = HTTP_500
            res.write(res.status_code)
        traceback.print_exc()

    def _write_response(self, res, writer):
        writer.write(b'HTTP/1.1 %s\r\n' % res.status_code.encode())
        for key, value in res.headers.items():
            writer.write(key.encode() + b': ' + str(value).encode() + b'\r\n')
        for key, value in res.cookies.items():
            write_cookie(writer, key, value)
        writer.write(b'\r\n')
        for chunk in res._chunks:
            writer.write(chunk)
        writer.write_eof()

    async def initialize(self):
        pass

    def serve(self, port=8000, host='0.0.0.0'):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.initialize())
        print('Serving on %s:%d' % (host, port))
        loop.create_task(asyncio.start_server(self._handle, host, port))
        loop.run_forever()
        loop.close()
