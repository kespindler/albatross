from flask import Flask
from time import sleep

app = Flask()


@app.route('/hello')
def hello():
    sleep(0.1)
