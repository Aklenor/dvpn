from flask import Flask

app = Flask(__name__)
app.debug = True

from front_flask import routes
