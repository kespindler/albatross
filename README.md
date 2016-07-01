# Albatross

I wanted to see how simple it is to make an modern async web framework. (python3.5 only)

It turns out - it's dead simple.

	from albatross import Server
	import asyncio

	class Handler:
		async def on_get(self, req, res):
			await asyncio.sleep(0.1)
			res.write('Hello, %s' % req.args['name'])


	app = Server()
	app.add_route('/(?P<name>[a-z]+)', Handler())
	app.serve()

## Usage

Create an app. Create handlers that have async functions `on_get`, `on_post`, etc. Call add_route with regex-based routes
to add the handlers. Call `app.serve()`.

See `examples/` for examples.

## Features

- You can read the entire codebase in about 10 minutes.
  There are probably many non-HTTP-compliant and subtle bugs as a consequence, but
  it works for building simple or moderately complex servers right now!

- It's natively async

- This works with the awesome `uvloop` project. It doesn't yet work with pypy3, because they don't support python3.5.
  Let's make it happen!

## Framework

The entire framework is 4 files at the moment:

- status_codes.py - blatantly copied from Falcon, because they did such a great job with that framework.
- server.py - the web server you instantiate, add routes & handlers, and allows you to serve
- request.py - a web request object
- response.py - a web response object

Each of those is less than 100 lines or so.

## Current Gotchas

- Be careful with casing on HTTP headers. The framework should force standardization, but currently they are case-sensitive.

## Todo

- tests: tests are a good idea. I should write some.
