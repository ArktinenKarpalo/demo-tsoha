from src.database.database import db
from src.database.models import Session_token

def loggedInAs(session_token):
    result = db.session.query(Session_token.user_id).filter_by(session_token=session_token)
    if result.count() == 0:
        return None
    else:
        return result[0].user_id
