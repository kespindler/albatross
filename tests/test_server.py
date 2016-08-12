import unittest
import asyncio
from albatross import Server
from albatross.compat import json
from aiohttp import client
import socket
from datetime import datetime
from hashlib import md5
from time import time

BODY = b'--------------------------5969313f95a69716\r\nContent-Disposition: form-data; name="key1"\r\n\r\nvalue1\r\n--------------------------5969313f95a69716\r\nContent-Disposition: form-data; name="upload"; filename="test.txt"\r\nContent-Type: text/plain\r\n\r\nwhat a great file\n\r\n--------------------------5969313f95a69716--\r\n'  # noqa


class Handler:
    async def on_get(self, req, res):
        res.write('Hello World')

    async def on_post(self, req, res):
        name = req.form['name']
        res.write_json({'name': name})
        res.cookies['success'] = 'true'
        res.cookies['expires_at'] = ('test1', datetime.utcnow())
        res.cookies['expires_in'] = ('test1', 100)

    async def on_put(self, req, res):
        m = md5()
        m.update(req.form['upload'].value)
        res.write_json({
            'upload': req.form['upload'].filename,
            'hash': m.hexdigest(),
            'value': req.form['key1']
        })


class TimingMiddleware:
    async def process_request(self, req, res, handler):
        req._start_time = time()

    async def process_response(self, req, res, handler):
        duration = time() - req._start_time
        res.headers['Duration'] = duration


def get_free_port():
    s = socket.socket()
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port


class ServerIntegrationTest(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.server = Server()
        self.server.add_route('/hello', Handler())

        self.port = get_free_port()
        self.url = 'http://127.0.0.1:%d' % (self.port, )
        self.async_server = self.loop.run_until_complete(
            asyncio.start_server(
                self.server._handle, '127.0.0.1', self.port, loop=self.loop
            )
        )

    def tearDown(self):
        self.async_server.close()

    def request(self, method, path, data=None, headers=None):
        async def go():
            self.session = client.ClientSession(loop=self.loop)
            response = await self.session.request(
                method, self.url + path,
                data=data, headers=headers
            )
            bytes = await response.read()
            body = bytes.decode()
            self.session.close()
            return response, body
        return self.loop.run_until_complete(go())

    def test_hello_world(self):
        response, body = self.request('GET', '/hello')
        assert body == 'Hello World'

    def test_hello_world_post(self):
        response, body = self.request(
            'POST', '/hello',
            data='name=mouse', headers={
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        )
        assert body == '{"name":"mouse"}', body
        assert response.cookies['success'].value == 'true', response.cookies

    def test_hello_world_put(self):
        response, body = self.request(
            'PUT', '/hello',
            data=BODY, headers={
                'Content-Type': 'multipart/form-data; boundary=------------------------5969313f95a69716'  # noqa
            }
        )
        assert response.status == 200, response.status
        assert json.loads(body) == {
            'upload': 'test.txt',
            'hash': 'f4b099a273213d89d4161f64c05aaf13',
            'value': 'value1',
        }

    def test_malformed_boundary(self):
        response, body = self.request(
            'PUT', '/hello',
            data='name=mouse', headers={
                'Content-Type': 'multipart/form-data'
            }
        )
        assert response.status == 500, response.status

    def test_not_found(self):
        response, body = self.request('GET', '/notfound')
        assert response.status == 404

    def test_with_middleware(self):
        self.server.add_middleware(TimingMiddleware())
        response, body = self.request('GET', '/hello')
        assert float(response.headers['Duration'])


class FakeHandler:
    def __init__(self, n):
        self.n = n


class ServerUnitTest(unittest.TestCase):
    def setUp(self):
        self.server = Server()
        self.server.add_route('/hello/{name}', FakeHandler(1))
        self.server.add_route('/hello', FakeHandler(2))
        self.server.add_route('/hello/{another}/motd', FakeHandler(3))

    def test_simple_route(self):
        handler, args = self.server.get_handler('/hello/test')
        assert handler.n == 1
        assert args == {'name': 'test'}, args

        handler, args = self.server.get_handler('/hello')
        assert handler.n == 2
        assert args == {}

        handler, args = self.server.get_handler('/hello/test/motd')
        assert handler.n == 3
        assert args == {'another': 'test'}

        handler, args = self.server.get_handler('/hello/')
        assert handler is None
        assert args is None
