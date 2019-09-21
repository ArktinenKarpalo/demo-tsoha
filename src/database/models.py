from flask_sqlalchemy import SQLAlchemy
from src.database.database import db

association_file_tag = db.Table("association_file_tag",
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id")),
    db.Column("file_id", db.Integer, db.ForeignKey("file.id"))
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin = db.Column(db.Boolean, default=False)
    username = db.Column(db.String(32), nullable=False, unique=True)
    max_quota = db.Column(db.Integer, nullable=False)
    used_quota = db.Column(db.Integer, nullable=False)
    password_hash = db.Column(db.Binary(64), nullable=False)
    password_salt = db.Column(db.Binary(64), nullable=False)
    files = db.relationship("File")
    session_tokens = db.relationship("Session_token")

class Session_token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_token = db.Column(db.String(128), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User")

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User")
    tags = db.relationship("Tag", secondary=association_file_tag)


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    files = db.relationship("File", secondary=association_file_tag)

db.create_all()
