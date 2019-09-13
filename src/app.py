from flask import Flask, url_for, redirect, render_template, request
app = Flask("__name__")

from routes import *

if __name__ == "__main__" :
    if app.config["ENV"] == "development" :
        app.run(debug=1)
    else :
        app.run()
