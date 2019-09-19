heroku config:set HEROKU=1
heroku ps:scale web=1
web: gunicorn app:app --workers 1 --preload
