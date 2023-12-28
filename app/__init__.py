from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import os


flask_app = Flask(__name__, template_folder='View/templates', static_folder='View/static')
flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///my_database.db'
flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
flask_app.secret_key = os.urandom(24) #generate random secret key

db = SQLAlchemy(flask_app)
migrate = Migrate(flask_app, db)

login_manager = LoginManager(flask_app)
login_manager.login_view = 'login'

from app.Controller import routes   #Import routes at the end to avoid circular dependencies