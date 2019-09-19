from flask_sqlalchemy import SQLAlchemy
from app import app

db = SQLAlchemy(app)

from src.database import models
models.init()
