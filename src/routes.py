from flask import request, render_template, make_response, render_template_string, send_from_directory, redirect, jsonify
from app import app
from src.database.database import db
from src.database.models import User, Session_token, File, Tag, association_file_tag, search_by_tags, count_tags
from src import auth, utils
import secrets, hashlib, os, math
from PIL import Image

@app.route("/")
def index():
    user_id = auth.loggedInAs(request.cookies.get(key="session_token"))
    if user_id == None:
        return render_template("index.html", logged_in=0)
    else:
        user = User.query.filter_by(id=user_id).first()
        return render_template("index.html", logged_in=1, admin=user.admin)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "GET":
        user_id = auth.loggedInAs(request.cookies.get(key="session_token"))
        if user_id == None:
            return render_template_string("Not logged in"),401
        user = User.query.filter_by(id=user_id).first()
        if user.admin:
            users = User.query.order_by(User.username).all()
            return render_template("admin.html", logged_in=1, admin=1, users=users)
        else:
            return render_template_string("Unauthorized"),401
    elif request.method == "POST":
        user_id = auth.loggedInAs(request.form["session_token"])
        if user_id == None:
            return render_template_string("Unauthorized"), 401
        user = User.query.filter_by(id=user_id).first()
        if user.admin:
            target_user = User.query.filter_by(username = request.form["username"]).first()
            target_user.max_quota = min(max(0, int(request.form["max_quota"])), 1e15)
            if request.form["admin"] == "True":
                target_user.admin = True
            elif request.form["admin"] == "False":
                target_user.admin = False
            db.session.commit()
            return redirect("#")
        else:
            return render_template_string("Unauthorized"), 401

@app.route("/search")
def search():
    user_id = auth.loggedInAs(request.cookies.get(key="session_token"))
    if user_id == None:
        return render_template_string("Couldn't search, not logged in!"), 401
    user = User.query.filter_by(id=user_id).first()
    include = request.args.get("include")
    exclude = request.args.get("exclude")
    search_results = search_by_tags(include, exclude, user_id)
    filenames = [r.filename for r in search_results]
    tags_with_count = count_tags([r.id for r in search_results])

    offset = 0
    limit = 40
    if request.args.get("limit"):
        limit = int(request.args.get("limit"))
    if request.args.get("page"):
        offset = (int(request.args.get("page"))-1)*limit
    pages = math.ceil(len(filenames)/limit)
    current_page = max(1, min(math.ceil(offset/limit)+1, pages))
    return render_template("search.html", filenames=[filenames[i] for i in range(max(0, offset), min(offset+limit, len(filenames)))], logged_in=1, tags=tags_with_count, pages=pages, current_page=current_page, admin=user.admin)

@app.route("/tags")
def tags():
    user_id = auth.loggedInAs(request.cookies.get(key="session_token"))
    return jsonify(db.session.query(Tag.name).filter_by(user_id=user_id).all())

@app.route("/view", methods=["GET", "POST"])
def view():
    filename = request.args.get("filename")
    file = File.query.filter_by(filename=filename).first()
    if request.method == "GET":
        if file == None:
            return render_template_string("The file does not exist")
        user_id = auth.loggedInAs(request.cookies.get(key="session_token"))
        if user_id != file.user_id:
            return render_template_string("Unauthorized"), 401
        tags = [tag.name for tag in file.tags]
        tags.sort()
        user = User.query.filter_by(id=user_id).first()
        return render_template("view.html", filename=filename, tags=tags, logged_in=1, admin=user.admin)
    elif request.method == "POST":
        if file == None:
            return redirect("/")
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
            tags = map(lambda x: x.lower(), request.form["tags_to_add"].split())
            for tag_name in tags:
                if len(tag_name) > 128:
                    continue
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
            try:
                user.used_quota -= os.stat(os.path.join(app.config["UPLOAD_DIRECTORY"], file.filename)).st_size
                os.remove(os.path.join(app.config["UPLOAD_DIRECTORY"], file.filename))
            except FileNotFoundError as err:
                # We can ignore this for the demo on heroku, because heroku deletes saved files after each restart
                pass
            try:
                os.remove(os.path.join(app.config["UPLOAD_DIRECTORY"], "thumb-" + file.filename))
            except FileNotFoundError as err:
                # We can ignore this for the demo on heroku, because heroku deletes saved files after each restart
                pass
            db.session.commit()
            return redirect("/search")

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
            user = User.query.filter_by(id=user_id).first()
            return render_template("upload.html", logged_in=1, used_quota=user.used_quota, max_quota=user.max_quota, admin=user.admin)
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
            thumbnail.thumbnail((300, 300), Image.BILINEAR)
            thumbnail.save(os.path.join(app.config["UPLOAD_DIRECTORY"], "thumb-" + filename))

        return render_template("redirect.html", dest="/search", message="File successfully uploaded! Redirecting soon...")

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
        user = User(username = request.form["username"], admin=False, used_quota=0, max_quota=1e8, password_salt=salt, password_hash=hashed)
        if user.username == "Admin":
            user.admin = True
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
