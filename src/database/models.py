from flask_sqlalchemy import SQLAlchemy
from src.database.database import db
from app import app

association_file_tag = db.Table("association_file_tag",
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True),
    db.Column("file_id", db.Integer, db.ForeignKey("file.id"), primary_key=True)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin = db.Column(db.Boolean, default=False)
    username = db.Column(db.String(32), nullable=False, unique=True)
    max_quota = db.Column(db.BigInteger, nullable=False)
    used_quota = db.Column(db.BigInteger, nullable=False)
    password_hash = db.Column(db.Binary(64), nullable=False)
    password_salt = db.Column(db.Binary(64), nullable=False)
    files = db.relationship("File")
    session_tokens = db.relationship("Session_token")
    tags = db.relationship("Tag")

class Session_token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_token = db.Column(db.String(128), nullable=False, unique=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User")

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False, unique=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), Index=true)
    user = db.relationship("User")
    tags = db.relationship("Tag", secondary=association_file_tag)

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, index=True)
    used_count = db.Column(db.Integer, nullable=False) # How many files use this tag
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    files = db.relationship("File", secondary=association_file_tag)
    user = db.relationship("User")

db.create_all()

def search_by_tags(include, exclude, user_id):
    sql_statement = "SELECT id, filename\
        FROM file\
        WHERE file.user_id=" + str(user_id)
    if include != None and len(include) > 0:
        include = include.split()
        include = list(map(lambda tag: str((lambda result: result.id if result != None else -1)(db.session.query(Tag.id).filter_by(name=tag,user_id=user_id).first())), include))
        include_count = len(include)
        if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite"):
            includeStatement = ",".join(["?" for i in range(len(include))])
        else:
            includeStatement = ",".join(["%s" for i in range(len(include))])
        sql_statement = sql_statement + " AND (SELECT COUNT(*)\
            FROM association_file_tag\
            WHERE association_file_tag.file_id = file.id AND tag_id IN (" + includeStatement + ")) = " + str(include_count)
    else:
        include = []
    if exclude != None and len(exclude) > 0:
        exclude = exclude.split()
        exclude = list(map(lambda tag: str((lambda result: result.id if result != None else -1)(db.session.query(Tag.id).filter_by(name=tag,user_id=user_id).first())), exclude))
        if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite"):
            excludeStatement = ",".join(["?" for i in range(len(exclude))])
        else:
            excludeStatement = ",".join(["%s" for i in range(len(exclude))])
        sql_statement = sql_statement + " AND NOT EXISTS (SELECT id\
            FROM association_file_tag\
            WHERE association_file_tag.file_id = file.id AND tag_id IN (" + excludeStatement + "))"
    else:
        exclude = []
    sql_statement = sql_statement + " ORDER BY id DESC"
    return db.engine.execute(sql_statement, include+exclude).fetchall()
def count_tags(filenames, file_ids):
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite"):
        sql_statement2 = "SELECT tag.name, COUNT(name)\
            FROM association_file_tag\
            LEFT JOIN TAG ON tag_id=tag.id\
            WHERE file_id IN (" + ",".join(["?" for i in range(len(filenames))]) + ")\
            GROUP BY tag.name\
            ORDER BY name"
    else:
        sql_statement2 = "SELECT tag.name, COUNT(name)\
            FROM association_file_tag\
            LEFT JOIN TAG ON tag_id=tag.id\
            WHERE file_id IN (" + ",".join(["%s" for i in range(len(filenames))]) + ")\
            GROUP BY tag.name\
            ORDER BY name"
    if len(filenames) == 0:
        return []
    else:
        return db.engine.execute(sql_statement2, file_ids).fetchall()
