# Make sure your virtual environment is activated and you're in the project directory
# Run `flask shell` in your terminal to open a Python shell in the context of your Flask application

from app import flask_app, db
from app.Model.models import User

def make_user_admin(username):
    with flask_app.app_context():
        user = User.query.filter_by(username=username).first()
        if user:
            user.is_admin = True
            db.session.commit()
            print(f"{username} has been made an admin.")
        else:
            print("User not found.")

# Call the function with your username
make_user_admin('Joosh')
