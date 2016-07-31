import unittest
import asyncio
from albatross import Server
from aiohttp import client
import socket
from datetime import datetime


class Handler:
    async def on_get(self, req, res):
        res.write('Hello World')

    async def on_post(self, req, res):
        name = req.form['name']
        res.write_json({'name': name})
        res.cookies['success'] = 'true'
        res.cookies['expires_at'] = ('test1', datetime.utcnow())
        res.cookies['expires_in'] = ('test1', 100)


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
        self.server = self.loop.run_until_complete(
            asyncio.start_server(self.server._handle, '127.0.0.1', self.port, loop=self.loop)
        )

    def tearDown(self):
        self.server.close()

    def request(self, method, path, data=None):
        async def go():
            self.session = client.ClientSession(loop=self.loop)
            response = await self.session.request(method, self.url + path, data=data)
            bytes = await response.read()
            body = bytes.decode()
            return response, body
        return self.loop.run_until_complete(go())

    def test_hello_world(self):
        response, body = self.request('GET', '/hello')
        assert body == 'Hello World'

    def test_hello_world_post(self):
        response, body = self.request('POST', '/hello', data='name=mouse')
        assert body == '{"name":"mouse"}', body
        assert response.cookies['success'].value == 'true', response.cookies
