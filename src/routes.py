from flask import request, render_template, make_response, render_template_string, send_from_directory, redirect
from app import app
from src.database.database import db
from src.database.models import User, Session_token, File, Tag, association_file_tag
from src import auth, utils
import secrets, hashlib, os
from PIL import Image

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
    sql_statement = "SELECT id, filename\
        FROM file\
        WHERE file.user_id=" + str(user_id)
    if include != None and len(include) > 0:
        include = include.split()
        include = list(map(lambda tag: str((lambda result: result.id if result != None else -1)(db.session.query(Tag.id).filter_by(name=tag,user_id=user_id).first())), include))
        include_count = len(include)
        includeStatement = ",".join(["?" for i in range(len(include))])
        sql_statement = sql_statement + " AND (SELECT COUNT(*)\
            FROM association_file_tag\
            WHERE association_file_tag.file_id = file.id AND tag_id IN (" + includeStatement + ")) = " + str(include_count)
    else:
        include = []
    if exclude != None and len(exclude) > 0:
        exclude = exclude.split()
        exclude = list(map(lambda tag: str((lambda result: result.id if result != None else -1)(db.session.query(Tag.id).filter_by(name=tag,user_id=user_id).first())), exclude))
        excludeStatement = ",".join(["?" for i in range(len(exclude))])
        sql_statement = sql_statement + " AND NOT EXISTS (SELECT id\
            FROM association_file_tag\
            WHERE association_file_tag.file_id = file.id AND tag_id IN (" + excludeStatement + "))"
    else:
        exclude = []
    sql_results = db.engine.execute(sql_statement, include+exclude).fetchall()
    filenames = [r.filename for r in sql_results]
    sql_statement2 = "SELECT tag.name, COUNT(name)\
        FROM association_file_tag\
        LEFT JOIN TAG ON tag_id=tag.id\
        WHERE file_id IN (" + ",".join(["?" for i in range(len(filenames))]) + ")\
        GROUP BY tag_id\
        ORDER BY name"
    sql_results2 = db.engine.execute(sql_statement2, [r.id for r in sql_results]).fetchall()
    return render_template("search.html", filenames=filenames, logged_in=1, tags=sql_results2)

@app.route("/view", methods=["GET", "POST"])
def view():
    filename = request.args.get("filename")
    file = File.query.filter_by(filename=filename).first()
    if request.method == "GET":
        user_id = auth.loggedInAs(request.cookies.get(key="session_token"))
        if user_id != file.user_id:
            return render_template_string("Unauthorized"), 401
        tags = [tag.name for tag in file.tags]
        return render_template("view.html", filename=filename, tags=tags, logged_in=1)
    elif request.method == "POST":
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
            return redirect("/view?filename="+filename)
        elif "tags_to_add" in request.form:
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
        elif "delete" in request.form:
            for tag in file.tags:
                if tag.used_count == 1:
                    db.session.delete(tag)
                else:
                    tag.used_count -= 1
            db.session.flush()
            db.session.delete(file)
            user = User.query.filter_by(id=user_id).first()
            user.used_quota -= os.stat(os.path.join(app.config["UPLOAD_DIRECTORY"], file.filename)).st_size
            db.session.commit()
            os.remove(os.path.join(app.config["UPLOAD_DIRECTORY"], file.filename))
            os.remove(os.path.join(app.config["UPLOAD_DIRECTORY"], "thumb-" + file.filename))
            return redirect("/search")

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
        user_id = auth.loggedInAs(request.cookies.get(key="session_token"))
        if user_id == None:
            return render_template_string("Please log in first"), 401
        else:
            return render_template("upload.html", logged_in=1)
    elif request.method == "POST":
        user_id = auth.loggedInAs(request.form["session_token"])
        if user_id == None:
            return render_template_string("Couldn't upload file, not logged in."), 401
        if "file" not in request.files:
            return render_template_string("Missing file."), 400
        for file in request.files.getlist("file"):
            extension = utils.fileExtension(file.filename)
            if extension not in allowedExtensions:
                return render_template_string("File extension not allowed"), 400
            filename = secrets.token_hex(32) + "." +  extension
            file_row = File(user_id=user_id, filename=filename)
            db.session.add(file_row)
            db.session.flush()
            file.save(os.path.join(app.config["UPLOAD_DIRECTORY"], filename))
            user = User.query.filter_by(id=user_id).first()
            upload_size = os.stat(os.path.join(app.config["UPLOAD_DIRECTORY"], filename)).st_size
            if user.max_quota < user.used_quota + upload_size:
                os.remove(os.path.join(app.config["UPLOAD_DIRECTORY"], filename))
                db.session.delete(file_row)
                db.session.commit()
                return render_template_string("Couldn't upload all files! User quota exceeded"), 400
            user.used_quota += upload_size
            db.session.commit()
            thumbnail = Image.open(os.path.join(app.config["UPLOAD_DIRECTORY"], filename))
            thumbnail.thumbnail((300, 300))
            thumbnail.save(os.path.join(app.config["UPLOAD_DIRECTORY"], "thumb-" + filename))

        return render_template("redirect.html", dest="/", message="File successfully uploaded! Redirecting soon...")

@app.route("/logout")
def logout():
    resp = make_response(render_template("redirect.html", message="Logged out! Redirecting soon...", dest="/"))
    resp.set_cookie("session_token", "")
    return resp

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET" :
        user_id = auth.loggedInAs(request.cookies.get(key="session_token"))
        if user_id == None:
            return render_template("register.html", logged_in=0)
        else:
            return render_template("redirect.html", dest="/", message="Already logged in! Redirecting soon...")
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
        user = User(username = request.form["username"], admin=False, used_quota=0, max_quota=1e9, password_salt=salt, password_hash=hashed)
        db.session.add(user)
        db.session.commit()
        resp = make_response(render_template("redirect.html", message="Registration successful! Redirecting soon...", dest="/login"))
        return resp

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET" :
        user_id = auth.loggedInAs(request.cookies.get(key="session_token"))
        if user_id == None:
            return render_template("login.html", logged_in=0)
        else:
            return render_template("redirect.html", message="Already logged in! Redirecting soon...", dest="/")
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
