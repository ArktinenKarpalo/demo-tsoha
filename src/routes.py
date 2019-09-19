from flask import request, render_template, make_response, render_template_string
from app import app
from src.database.database import db
from src.database.models import User, Session_token
import secrets, hashlib

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET" :
        return render_template("register.html")
    elif request.method =="POST" :
        if len(request.form["username"]) < 1:
            return ("Error while registering! Username is too short.")
        if len(request.form["username"]) > 32:
            return ("Error while registering! Username is too long.")
        if len(request.form["password"]) < 1:
            return ("Error while registering! Password is too short.")
        if len(request.form["password"]) > 128:
            return ("Error while registering! Password is too long.")
        if User.query.filter_by(username=request.form["username"]).count() != 0:
            return ("Error while registering! User with the username: " + request.form["username"] + " already exists!")
        salt = secrets.token_bytes(64)
        hashed = hashlib.scrypt(password=request.form["password"].encode(), salt=salt, n=16384, r=8, p=1)
        user = User(username = request.form["username"], admin=False, used_quota=0, max_quota=0, password_salt=salt, password_hash=hashed)
        db.session.add(user)
        db.session.commit()
        return "Registration successful!"

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET" :
       return render_template("login.html")
    elif request.method == "POST" :
        if len(request.form["username"]) < 1:
            return ("Error while logging in! Username is too short.")
        if len(request.form["username"]) > 32:
            return ("Error while logging in! Username is too long.")
        if len(request.form["password"]) < 1:
            return ("Error while logging in! Password is too short.")
        if len(request.form["password"]) > 128:
            return ("Error while logging in! Password is too long.")
        user = User.query.filter_by(username=request.form["username"]).first()
        if user == None:
            return "Username or password invalid!"
        if user.password_hash != hashlib.scrypt(password=request.form["password"].encode(), salt=user.password_salt, n=16384, r=8, p=1):
            return "Username or password invalid!"
        session_token = secrets.token_hex(64)
        sessionToken = Session_token(user_id=user.id, session_token=session_token)
        db.session.add(sessionToken)
        db.session.commit()
        resp = make_response(render_template_string("Login successful!"))
        resp.set_cookie("session_token", session_token)
        return resp
