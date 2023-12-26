# reset_database.py
from app import db, flask_app

with flask_app.app_context():
    db.drop_all()
    db.create_all()
    print("Database has been reset.")
