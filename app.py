from flask import Flask, url_for, redirect, render_template, request

app = Flask("__name__")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
if app.config["ENV"] == "development" :
    app.config["SQLALCHEMY_ECHO"] = True


if __name__ == "__main__" :
    from src.database import database
    from src.routes import *
    if app.config["ENV"] == "development" :
        app.run(debug=1)
    else :
        app.run()
