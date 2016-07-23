import unittest
import asyncio
from albatross import Server
from aiohttp import client
import socket


class Handler:
    async def on_get(self, req, res):
        res.write('Hello World')


def get_free_port():
    s = socket.socket()
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port


class ServerTest(unittest.TestCase):
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

    def get(self, path):
        async def go():
            self.session = client.ClientSession(loop=self.loop)
            response = await self.session.get(self.url + path)
            bytes = await response.read()
            body = bytes.decode()
            return response, body
        return self.loop.run_until_complete(go())

    def test_hello_world(self):
        response, body = self.get('/hello')
        assert body == 'Hello World'
