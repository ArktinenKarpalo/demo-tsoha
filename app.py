from flask import Flask, url_for, redirect, render_template, request

app = Flask("__name__")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
if app.config["ENV"] == "development" :
    app.config["SQLALCHEMY_ECHO"] = True

from src.database import database
from src import routes

if __name__ == "__main__" :
    if app.config["ENV"] == "development" :
        app.run(debug=1)
    else :
        app.run()
