# Albatross

I wanted to see how simple it is to make an modern async web framework. (python3.5 only)

It turns out - it's dead simple.

## Features

The entire framework is 4 files at the moment:

- status_codes.py - blatantly copied from Falcon, because they did such a great job with that framework.
- server.py - the web server you instantiate, add routes & handlers, and allows you to serve
- request.py - a web request object
- response.py - a web response object

Each of those is no less than 100 or so lines.

## Todo

- tests
    python3 example_app.py