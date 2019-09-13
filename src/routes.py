from flask import request, render_template
from app import app

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET" :
        return render_template("register.html")
    elif request.method =="POST" :
        return request.form

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET" :
       return render_template("login.html")
    elif request.method == "POST" :
        return request.form
