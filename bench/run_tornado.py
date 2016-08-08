import tornado.ioloop
import tornado.web


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello World")


class FormHandler(tornado.web.RequestHandler):

    def post(self):
        num_fields = len(list(self.request.arguments.keys()))
        self.write('Found %d keys.' % num_fields)


def make_app():
    return tornado.web.Application([
        (r'/hello', MainHandler),
        (r'/form', FormHandler),
    ])


if __name__ == '__main__':
    app = make_app()
    app.listen(8000)
    tornado.ioloop.IOLoop.current().start()
