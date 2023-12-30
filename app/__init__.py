from flask import Flask
from .Model.database import setup_db
from .admin_views import MyAdminIndexView, LoginManager, Admin, UserAdminView
import os
from flask_babel import Babel

basedir = os.path.abspath(os.path.dirname(__file__))

flask_app = Flask(__name__, instance_relative_config=True, template_folder='View/templates', static_folder='View/static')
flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance/my_database.db')
flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
flask_app.secret_key = os.urandom(24)

babel = Babel(flask_app)

setup_db(flask_app)

login_manager = LoginManager(flask_app)
login_manager.login_view = 'login'

admin = Admin(flask_app, index_view=MyAdminIndexView())
from .Model.models import User, db

admin.add_view(UserAdminView(User, db.session))

from app.Controller import routes
