from flask import Flask, url_for, redirect, render_template, request
import os

app = Flask("__name__")

if os.environ.get("HEROKU"):
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
    app.config["SQLALCHEMY_ECHO"] = True

from src.database import database
from src.routes import *

if __name__ == "__main__":
    if app.config["ENV"] == "development":
        app.run(debug=1)
    else:
        app.run()
