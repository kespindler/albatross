from albatross import Server


class Handler:
    async def on_get(self, req, res):
        res.write('Hello World')


class FormHandler:
    async def on_post(self, req, res):
        num_fields = len(list(req.form.keys()))
        res.write('Found %d keys.' % num_fields)


app = Server()
app.add_route('/hello', Handler())
app.add_route('/form', FormHandler())
app.serve(port=8000)
