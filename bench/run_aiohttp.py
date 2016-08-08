from aiohttp import web


async def hello(request):
    return web.Response(body=b'Hello World')


async def form(request):
    data = await request.data()
    num_fields = len(list(data.keys()))
    return web.Response(b'Found %d keys.' % num_fields)


app = web.Application()
app.router.add_route('GET', '/hello', hello)
app.router.add_route('POST', '/form', hello)
web.run_app(app, port=8000)
