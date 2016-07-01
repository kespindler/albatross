from albatross import Server
from time import time
import asyncio
import uvloop
import cProfile as cprof
import pstats
from io import StringIO


class TimingMiddleware:
    async def process_request(self, req, res, handler):
        req._start_time = time()

    async def process_response(self, req, res, handler):
        duration = time() - req._start_time
        print('Request took %.4fs' % duration)


class Handler:
    async def on_get(self, req, res):
        await asyncio.sleep(0.1)
        res.write('Hello, world')


class ProfHandler:
    async def on_get(self, req, res):
        prof = cprof.Profile()
        prof.enable()
        await asyncio.sleep(5.0)
        prof.disable()
        prof.create_stats()
        s = StringIO()
        stats_obj = pstats.Stats(prof, stream=s).sort_stats("cumulative")
        stats_obj.print_stats()
        res.write(s.getvalue())


asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
app = Server()
app.add_route('/profile', ProfHandler())
app.add_route('/(?P<name>[a-z]*)', Handler())
# app.add_middleware(TimingMiddleware())
app.serve()
