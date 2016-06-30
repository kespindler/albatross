from albatross import Server
from time import time


class TimingMiddleware:
    async def process_request(self, req, res, handler):
        req._start_time = time()

    async def process_response(self, req, res, handler):
        duration = time() - req._start_time
        print('Request took %.4fs' % duration)


class Handler:
    async def on_get(self, req, res):
        res.write('OK')


app = Server()
app.add_route('/(?P<name>[a-z]+)', Handler())
app.add_middleware(TimingMiddleware())
app.serve()
