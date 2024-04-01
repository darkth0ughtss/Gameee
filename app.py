from flask import Flask
from werkzeug.urls import url_unquote

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Gameee'


if __name__ == "__main__":
    app.run()
