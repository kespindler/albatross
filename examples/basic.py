from albatross import Server
from time import time
import asyncio
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass


class TimingMiddleware:
    async def process_request(self, req, res, handler):
        req._start_time = time()

    async def process_response(self, req, res, handler):
        duration = time() - req._start_time
        print('Request took %.4fs' % duration)


class Handler:
    async def on_post(self, req, res):
        await asyncio.sleep(0.1)
        res.write('OK')


app = Server()
app.add_route('/hello/{name}', Handler())
app.add_regex_route('/.*', Handler())
# app.add_middleware(TimingMiddleware())
app.serve()
