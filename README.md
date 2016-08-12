[![Build Status](https://travis-ci.org/kespindler/albatross.svg?branch=master)](https://travis-ci.org/kespindler/albatross)

# Albatross

A modern, fast, simple, natively-async web framework. (Python3.5 only)

```python
from albatross import Server
import asyncio


class Handler:
    async def on_get(self, req, res):
        await asyncio.sleep(0.1)
        res.write('Hello, %s' % req.args['name'])


app = Server()
app.add_route('/{name})', Handler())
app.serve()
```

### Notes for Usage

For now (pre 1.0.0), I'm making no claims about API stability (but will try to avoid it!). That said,
I'm using this framework for some small projects, and it is a joy to work in!
Reach out if you want to use this, as I'm happy to incorporate your feedback!

## Install

    pip3 install albatross3

## Features

- You can read the entire codebase in about 30 minutes.

- It's natively async. Doing `await` database calls or controller calls in your views just works!

- This works with the `uvloop` project, to make your server fast!

## Benchmarks

- My benchmarks indicate that albatross is as fast as aiohttp, both of which are twice as fast as
  tornado. You can run the benchmarks by poking around in the `bench/` folder.

