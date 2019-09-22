from flask import request, render_template, make_response, render_template_string, send_from_directory, redirect
from app import app
from src.database.database import db
from src.database.models import User, Session_token, File, Tag, association_file_tag
from src import auth, utils
import secrets, hashlib, os

@app.route("/")
def index():
    if auth.loggedInAs(request.cookies.get(key="session_token")) == None:
        return render_template("index.html", logged_in=0)
    else:
        return render_template("index.html", logged_in=1)

@app.route("/search")
def search():
    user_id = auth.loggedInAs(request.cookies.get(key="session_token"))
    if user_id == None:
        return render_template_string("Couldn't search, not logged in!"), 401
    include = request.args.get("include")
    exclude = request.args.get("exclude")
    sql_statement = "SELECT filename\
        FROM file\
        WHERE file.user_id=" + str(user_id)
    if include != None and len(include) > 0:
        include = include.split()
        include = list(map(lambda tag: "tag_id=" + str((lambda result: result.id if result != None else -1)(db.session.query(Tag.id).filter_by(name=tag,user_id=user_id).first())), include))
        include_count = len(include)
        include = " OR ".join(include)
        sql_statement = sql_statement + " AND (SELECT COUNT(*)\
        FROM association_file_tag\
        WHERE association_file_tag.file_id = file.id AND (" + include + ")) = " + str(include_count)
    if exclude != None and len(exclude) > 0:
        exclude = exclude.split()
        exclude = list(map(lambda tag: "tag_id=" + str((lambda result: result.id if result != None else -1)(db.session.query(Tag.id).filter_by(name=tag,user_id=user_id).first())), exclude))
        exclude = " OR ".join(exclude)
        sql_statement = sql_statement + " AND NOT EXISTS (SELECT id\
            FROM association_file_tag\
            WHERE association_file_tag.file_id = file.id AND (" + exclude + "))"
    filenames = [r.filename for r in db.engine.execute(sql_statement).fetchall()]
    return render_template("search.html", filenames=filenames)

@app.route("/view", methods=["GET", "POST"])
def view():
    filename = request.args.get("filename")
    file = File.query.filter_by(filename=filename).first()
    if request.method == "GET":
        user_id = auth.loggedInAs(request.cookies.get(key="session_token"))
        if user_id != file.user_id:
            return render_template_string("Unauthorized"), 401
        tags = [tag.name for tag in file.tags]
        return render_template("view.html", filename=filename, tags=tags)
    if request.method == "POST":
        user_id = auth.loggedInAs(request.form["session_token"])
        if user_id != file.user_id:
            return render_template_string("Unauthorized"), 401
        if "tag_to_remove" in request.form:
            tag = Tag.query.filter_by(name=request.form["tag_to_remove"], user_id=user_id).first()
            if tag != None:
                if tag.used_count == 1:
                    db.session.delete(tag)
                else:
                    file.tags.remove(tag)
                    tag.used_count -= 1
                db.session.commit()
        else:
            tags = request.form["tags_to_add"].split()
            for tag_name in tags:
                tag = Tag.query.filter_by(name=tag_name, user_id=user_id).first()
                if tag == None:
                    tag = Tag(name=tag_name,user_id=user_id,used_count=1)
                elif db.session.query(association_file_tag).filter_by(file_id=file.id, tag_id=tag.id).first() == None:
                    tag.used_count += 1
                tag.files.append(file)
                db.session.add(tag)
                db.session.flush()
            db.session.commit()
        return redirect("/view?filename="+filename)

@app.route("/js/<path:path>")
def js(path):
    return send_from_directory("js", path)

@app.route("/uploads/<path:path>")
def uploads(path):
    return send_from_directory(app.config["UPLOAD_DIRECTORY"], path)

allowedExtensions = {"jpg", "JPG", "png", "jpeg"}
@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "GET":
        return render_template("upload.html")
    elif request.method == "POST":
        user_id = auth.loggedInAs(request.form["session_token"])
        if user_id == None:
            return render_template_string("Couldn't upload file, not logged in."), 401
        if "file" not in request.files:
            return render_template_string("Missing file."), 400
        file = request.files["file"]
        extension = utils.fileExtension(file.filename)
        if extension not in allowedExtensions:
            return render_template_string("File extension not allowed"), 400
        filename = secrets.token_hex(32) + "." +  extension
        db.session.add(File(user_id=user_id, filename=filename))
        db.session.commit()
        file.save(os.path.join(app.config["UPLOAD_DIRECTORY"], filename))
        return render_template("redirect.html", dest="/", message="File successfully uploaded! Redirecting soon...")

@app.route("/logout")
def logout():
    resp = make_response(render_template("redirect.html", message="Logged out! Redirecting soon...", dest="/"))
    resp.set_cookie("session_token", "")
    return resp

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET" :
        return render_template("register.html")
    elif request.method == "POST" :
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
        resp = make_response(render_template("redirect.html", message="Registration successful! Redirecting soon...", dest="/login"))
        return resp

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
        resp = make_response(render_template("redirect.html", message="Login successful! Redirecting soon...", dest="/"))
        resp.set_cookie("session_token", session_token)
        return resp
