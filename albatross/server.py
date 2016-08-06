# h11 code adapted from https://h11.readthedocs.io/en/latest/examples.html
#  A simple HTTP server implemented using h11 and Curio:
#   http://curio.readthedocs.org/
#   (so requires python 3.5+).

import re
import asyncio
import urllib.parse as parse
from itertools import count
from datetime import datetime
from albatross import Request, Response
from albatross.status_codes import HTTP_404, HTTP_500, HTTP_405
from albatross.http_error import HTTPError
from albatross.data_types import ImmutableCaselessDict
import traceback
from wsgiref.handlers import format_date_time
import h11

class Server:
    """The core albatross server

    Attributes:
        _handlers (list): a list of route-handler tuples
        _middleware (list): a list of middlewares to process requests
    """

    _next_id = count()

    def __init__(self):
        self._handlers = []
        self._middleware = []
        self.max_read_chunk = 1024*1024
        self.spoof_options = True
        self.conn = h11.Connection(h11.SERVER)
        self.ident = " ".join([
            "albatross-server/{}".format(h11.__version__),
            h11.PRODUCT_ID,
        ]).encode("ascii")
        self._obj_id = next(Server._next_id)

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

    def basic_headers(self):
        # HTTP requires these headers in all responses (client would do
        # something different here)
        return [
            ("Date", format_date_time(None).encode("ascii")),
            ("Server", self.ident),
        ]

    def info(self, *args):
        # Little debugging method
        # print("{}:".format(self._obj_id), *args)
        return

    async def send(self, event):
        assert type(event) is not h11.ConnectionClosed
        data = self.conn.send(event)

        try:
            self.writer.write(data)
        except Exception as e:
            print(e)

    async def _read_from_peer(self, reader):
        if self.conn.they_are_waiting_for_100_continue:
            go_ahead = h11.InformationalResponse(
                status_code=100,
                headers=self.basic_headers())
            await self.send(go_ahead)
        try:
            data = await reader.read(self.max_read_chunk)
        except ConnectionError:
            # They've stopped listening. Not much we can do about it here.
            data = b""
        self.conn.receive_data(data)

    async def next_event(self, reader):
        while True:
            event = self.conn.next_event()
            if event is h11.NEED_DATA:
                await self._read_from_peer(reader)
                continue
            return event


    def _parse_header_lines(self, lines):
        headers = {}
        for l in lines:
            try:
                key, value = l.split(':', 1)
                headers[key] = value.strip()
            except ValueError:
                pass
        return ImmutableCaselessDict(*headers.items())

    async def _parse_request(self, request_reader):
        # Read next event and see if it is a request

        event = await self.next_event(request_reader)

        if type(event) is h11.Request:

            # Gather request parts
            path = event.target.decode("ascii")
            method = event.method.decode("ascii")
            headers = [(name.decode("ascii"), value.decode("ascii"))
                       for (name, value) in event.headers]
            query = ""
            raw_body = ""

            # Now get any data
            while True:
                event = await self.next_event(request_reader)
                if type(event) is h11.EndOfMessage:
                    break
                assert type(event) is h11.Data
                raw_body += event.data.decode("ascii")

            handler, args = self.get_handler(path)

            req = Request(method, path, query, raw_body, args, headers)

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

        self.reader = request_reader
        self.writer = response_writer

        res = Response()

        try:
            req, handler = await self._parse_request(request_reader)

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

        await self._write_response(res, response_writer)
        await response_writer.drain()
        response_writer.close()

        if self.conn.our_state is h11.MUST_CLOSE:
            self.info("connection is not reusable, so shutting down")
            return
        else:
            try:
                self.info("trying to re-use connection")
                self.conn.start_next_cycle()
            except h11.ProtocolError:
                states = self.conn.states
                self.info("unexpected state", states, "-- bailing out")
                return

    def handle_error(self, res, e):
        res.clear()
        if isinstance(e, HTTPError):
            res.status_code = e.status_code
            res.write(e.message)
        else:
            res.status_code = HTTP_500
            res.write(res.status_code)
        traceback.print_exc()

    async def send_simple_response(self, status_code, content_type, body):
        self.info("Sending", status_code,
                  "response with", len(body), "bytes")
        headers = self.basic_headers()
        headers.append(("Content-Type", content_type))
        headers.append(("Content-Length", str(len(body))))

        res = h11.Response(status_code=200, headers=headers)

        await self.send(res)
        await self.send(h11.Data(data=body))
        await self.send(h11.EndOfMessage())

    async def _write_response(self, res, writer):
        content_type = "text/plain"
        body = res._chunks[0]
        await self.send_simple_response(res.status_code, content_type, body)

    async def initialize(self):
        pass

    def serve(self, port=8000, host='0.0.0.0'):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.initialize())
        print('Serving on %s:%d' % (host, port))
        loop.create_task(asyncio.start_server(self._handle, host, port))
        loop.run_forever()
        loop.close()
