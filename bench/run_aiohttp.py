from aiohttp import web
from urllib.parse import parse_qs


async def hello(request):
    return web.Response(body=b'Hello World')


async def form(request):
    data = await request.read()
    body = data.decode()
    form = parse_qs(data)
    num_fields = len(list(form.keys()))
    return web.Response(body=b'Found %d keys.' % num_fields)


app = web.Application()
app.router.add_route('GET', '/hello', hello)
app.router.add_route('POST', '/form', form)
web.run_app(app, port=8000)
