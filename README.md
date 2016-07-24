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
app.add_route('/(?P<name>[a-z]+)', Handler())
app.serve()
```

## Install

    pip3 install albatross3

## Features

- You can read the entire codebase in about 30 minutes.

- It's natively async

- This works with the `uvloop` project, to make your server fast!
