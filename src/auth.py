from src.database.database import db
from datetime import *
from src.database.models import Session_token

def loggedInAs(session_token):
    result = Session_token.query.filter_by(session_token=session_token)
    if result.count() == 0:
        return None
    else:
        # Delete session token if it has not been used during the last 3 months
        if datetime.utcnow().timestamp() - result[0].last_access.timestamp() > 3*30*24*3600:
            db.session.delete(result[0])
            db.session.commit();
            return None
        db.session.commit()
        return result[0].user_id
